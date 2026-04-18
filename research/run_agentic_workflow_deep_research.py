#!/usr/bin/env python3
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from notebooklm_mcp.api_client import NotebookLMClient
from notebooklm_mcp.auth import load_cached_tokens

DEEP_FIRST = os.getenv("NOTEBOOKLM_DEEP_FIRST", "1") == "1"
DEEP_TIMEOUT_SEC = int(os.getenv("NOTEBOOKLM_DEEP_TIMEOUT", "1200"))
MAX_SOURCES = int(os.getenv("NOTEBOOKLM_MAX_SOURCES", "0"))
TARGET_SOURCES = int(os.getenv("NOTEBOOKLM_TARGET_SOURCES", "25"))
SOURCE_TOPUP_ROUNDS = int(os.getenv("NOTEBOOKLM_SOURCE_TOPUP_ROUNDS", "4"))
REQUIRE_STUDIO_ARTIFACT = os.getenv("NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT", "1") == "1"
POLICY_PATH = os.getenv(
    "NOTEBOOKLM_AGENTIC_POLICY_PATH",
    "docs/notebooklm/AGENTIC_WORKFLOW_POLICY.json",
)


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


TRUSTED = {
    "openai.com": 6,
    "anthropic.com": 6,
    "google.com": 5,
    "deepmind.google": 6,
    "microsoft.com": 5,
    "aws.amazon.com": 5,
    "arxiv.org": 6,
    "mckinsey.com": 5,
    "weforum.org": 5,
    "stanford.edu": 5,
    "mit.edu": 5,
    "youtube.com": 2,
    "youtu.be": 2,
}
FAILED_TITLE_HINTS = [
    "failed",
    "error",
    "unavailable",
    "not found",
    "404",
    "삭제",
    "접근할 수",
    "가져올 수",
    "로드할 수",
    "불러올 수",
]


def source_score(src: dict) -> int:
    domain = get_domain(src.get("url") or "")
    title = (src.get("title") or "").lower()
    score = TRUSTED.get(domain, 1)
    if any(k in title for k in ["official", "research", "report", "benchmark", "paper"]):
        score += 1
    return score


def dedupe(items: list[dict]) -> list[dict]:
    out, seen = [], set()
    for s in items:
        key = (s.get("url") or "").strip() or (s.get("title") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def split_sources(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    yt, article = [], []
    for s in sources:
        u = (s.get("url") or "").lower()
        if "youtube.com" in u or "youtu.be" in u:
            yt.append(s)
        else:
            article.append(s)
    return yt, article


def pick_sources(sources: list[dict]) -> list[dict]:
    src = dedupe(sources)
    for s in src:
        s["_score"] = source_score(s)
    yt, article = split_sources(src)
    yt = sorted(yt, key=lambda x: x["_score"], reverse=True)
    article = sorted(article, key=lambda x: x["_score"], reverse=True)
    picked = yt[:3] + article[:7]
    if len(picked) < 10:
        remain = [s for s in sorted(src, key=lambda x: x["_score"], reverse=True) if s not in picked]
        picked.extend(remain[: 10 - len(picked)])
    if len(picked) < TARGET_SOURCES:
        remain = [s for s in sorted(src, key=lambda x: x["_score"], reverse=True) if s not in picked]
        picked.extend(remain[: TARGET_SOURCES - len(picked)])
    return picked[:MAX_SOURCES] if MAX_SOURCES > 0 else picked


def is_failed_source(source: dict) -> bool:
    title = (source.get("title") or "").lower()
    url = (source.get("url") or "").strip().lower()
    if not source.get("id"):
        return True
    if not url:
        return True
    return any(h in title for h in FAILED_TITLE_HINTS)


def prune_failed_sources(client: NotebookLMClient, notebook_id: str, current_sources: list[dict]) -> tuple[list[dict], int]:
    failed_ids = [s.get("id") for s in current_sources if s.get("id") and is_failed_source(s)]
    deleted = 0
    for sid in failed_ids:
        try:
            if client.delete_source(sid):
                deleted += 1
        except Exception:
            continue
    refreshed = client.get_notebook_sources_with_types(notebook_id)
    return refreshed, deleted


def poll_research(client: NotebookLMClient, notebook_id: str, task_id: str, timeout_sec: int = 240) -> dict | None:
    start = time.time()
    while time.time() - start < timeout_sec:
        result = client.poll_research(notebook_id, task_id)
        if result and result.get("status") == "completed":
            return result
        time.sleep(8)
    return None


def ask(client: NotebookLMClient, notebook_id: str, prompt: str, timeout: float = 180.0) -> str:
    for _ in range(3):
        try:
            r = client.query(notebook_id, query_text=prompt, timeout=timeout)
            if r and r.get("answer"):
                return (r.get("answer") or "").strip()
        except Exception:
            time.sleep(5)
    return ""


def next_numbered_prefix(client: NotebookLMClient) -> int:
    notebooks = client.list_notebooks() or []
    max_n = 0
    for nb in notebooks:
        title = getattr(nb, "title", "") or ""
        m = re.match(r"^(\d{2})_", title)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "agentic_workflow_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    policy_file = (root / POLICY_PATH).resolve()
    policy = json.loads(policy_file.read_text(encoding="utf-8"))

    tokens = load_cached_tokens()
    if not tokens:
        raise RuntimeError("NotebookLM auth not found. Run notebooklm-mcp-auth first.")

    client = NotebookLMClient(
        cookies=tokens.cookies,
        csrf_token=tokens.csrf_token,
        session_id=tokens.session_id,
    )

    idx = next_numbered_prefix(client)
    notebook_name = f"{idx:02d}_AI콘텐츠_AgenticWorkflow"
    print(f"[start] notebook={notebook_name}", flush=True)
    notebook = client.create_notebook(title=notebook_name)
    if not notebook:
        raise RuntimeError("Failed to create notebook.")

    client.configure_chat(
        notebook.id,
        goal="custom",
        custom_prompt="리서치 보고서 스타일, 근거 중심, 개조식 우선",
        response_length="longer",
    )

    # 1) Deep-first mode (long timeout), fallback to fast on failure/timeout.
    deep_task = None
    deep_polled = None
    if DEEP_FIRST:
        try:
            print(f"[deep] start timeout={DEEP_TIMEOUT_SEC}s", flush=True)
            deep_query = (
                "Agentic Workflow에 대해 Deep Research 수행. "
                "글로벌 베스트 프랙티스, 아키텍처 패턴, 운영/관측, 보안/거버넌스, 실패사례 포함."
            )
            deep_task = client.start_research(notebook.id, query=deep_query, source="web", mode="deep")
            if deep_task:
                print(f"[deep] task={deep_task['task_id']}", flush=True)
                deep_polled = poll_research(client, notebook.id, deep_task["task_id"], timeout_sec=DEEP_TIMEOUT_SEC)
                print(f"[deep] status={(deep_polled or {}).get('status', 'timeout')}", flush=True)
        except Exception as e:
            print(f"[deep] fallback to fast due to error: {e}", flush=True)

    # 2) Stable fast research for importable URLs
    all_sources = []
    queries = [
        "Agentic Workflow high quality global sources with YouTube and technical articles, include URLs",
        "Agentic workflow orchestration framework best practices site:youtube.com OR technical blogs (global channels first)",
        "Agentic workflow evaluation observability security governance global case studies and benchmark reports",
    ]
    last_task_id = ""
    for q in queries:
        print(f"[fast] query={q[:80]}", flush=True)
        started = client.start_research(notebook.id, query=q, source="web", mode="fast")
        if not started:
            continue
        last_task_id = started["task_id"]
        print(f"[fast] task={last_task_id}", flush=True)
        polled = poll_research(client, notebook.id, started["task_id"], timeout_sec=300)
        if polled:
            print(f"[fast] completed count={polled.get('source_count')}", flush=True)
            all_sources.extend(polled.get("sources", []))
            picked_now = pick_sources(all_sources)
            yt, article = split_sources(picked_now)
            if len(picked_now) >= TARGET_SOURCES and len(yt) >= 3 and len(article) >= 7:
                break

    selected = pick_sources(all_sources)
    if not selected:
        raise RuntimeError("No sources collected.")
    print(f"[source] selected={len(selected)} (target_min={TARGET_SOURCES}, max={MAX_SOURCES})", flush=True)

    imported = client.import_research_sources(notebook.id, task_id=last_task_id, sources=selected)
    current_sources = client.get_notebook_sources_with_types(notebook.id)
    current_sources, deleted_failed = prune_failed_sources(client, notebook.id, current_sources)
    print(
        f"[source] imported={len(imported)} deleted_failed={deleted_failed} current={len(current_sources)}",
        flush=True,
    )

    topup_round = 0
    while len(current_sources) < TARGET_SOURCES and topup_round < SOURCE_TOPUP_ROUNDS:
        topup_round += 1
        refill_query = (
            "Agentic Workflow latest high quality global sources "
            "with at least 5 YouTube and 20 article/report URLs"
        )
        started = client.start_research(notebook.id, query=refill_query, source="web", mode="fast")
        if started:
            last_task_id = started["task_id"]
            polled = poll_research(client, notebook.id, started["task_id"], timeout_sec=300)
            if polled:
                all_sources.extend(polled.get("sources", []))
        refill_sources = pick_sources(all_sources)
        existing_urls = {(x.get("url") or "").strip() for x in current_sources if x.get("url")}
        refill_sources = [
            x for x in refill_sources
            if (x.get("url") or "").strip() and (x.get("url") or "").strip() not in existing_urls
        ]
        if not refill_sources:
            break
        _ = client.import_research_sources(notebook.id, task_id=last_task_id, sources=refill_sources)
        current_sources = client.get_notebook_sources_with_types(notebook.id)
        current_sources, deleted_failed = prune_failed_sources(client, notebook.id, current_sources)
        print(
            f"[source] topup_round={topup_round} imported_attempt={len(refill_sources)} "
            f"deleted_failed={deleted_failed} current={len(current_sources)} target_min={TARGET_SOURCES}",
            flush=True,
        )

    # 3) Deep research report in notebook (NotebookLM-only grounding)
    deep_report_prompt = (
        "현재 노트북 소스만 근거로 Agentic Workflow 딥리서치 보고서를 작성해줘. "
        "개조식, 핵심 프레임워크, 설계원칙, 실패패턴, 운영 체크리스트를 포함."
    )
    deep_report = ask(client, notebook.id, deep_report_prompt)
    print(f"[deep_report] chars={len(deep_report)}", flush=True)

    # 4) Fact Synthesizer
    synthesis_prompt = policy["prompts"]["fact_synthesis"]
    synthesis = ask(client, notebook.id, synthesis_prompt)
    print(f"[synthesis] chars={len(synthesis)}", flush=True)

    # 5) Blog Writer
    blog_prompt = policy["prompts"]["blog_writer"]
    blog_post = ask(client, notebook.id, blog_prompt)
    if len(blog_post) < 4000:
        blog_post = ask(client, notebook.id, "위 글을 더 구체화해서 4,500자 이상으로 확장해줘.")
    print(f"[blog_writer] chars={len(blog_post)}", flush=True)

    # 6) Quality Gate
    gate_prompt = f"{policy['prompts']['quality_gate']}\n\n[초안]\n{blog_post}"
    gate_result = ask(client, notebook.id, gate_prompt, timeout=220.0)
    gate_status = "PASS" if gate_result.strip().startswith("PASS") else "FAIL"
    if gate_status == "FAIL":
        rewrite_prompt = f"{policy['prompts']['rewrite']}\n\n[품질게이트 피드백]\n{gate_result}\n\n[초안]\n{blog_post}"
        rewritten = ask(client, notebook.id, rewrite_prompt, timeout=220.0)
        if len(rewritten) >= 3500:
            blog_post = rewritten
    print(f"[quality_gate] status={gate_status} final_chars={len(blog_post)}", flush=True)

    # 5) Enforce NotebookLM-internal deliverable (Studio report artifact)
    source_ids = [s["id"] for s in current_sources if s.get("id")]
    studio_result = None
    studio_status = None
    if source_ids:
        try:
            studio_result = client.create_report(
                notebook.id,
                source_ids=(source_ids[:MAX_SOURCES] if MAX_SOURCES > 0 else source_ids),
                report_format="Blog Post",
                language="ko",
            )
            # poll list-based status
            for _ in range(30):
                statuses = client.poll_studio_status(notebook.id)
                if isinstance(statuses, list):
                    aid = (studio_result or {}).get("artifact_id")
                    matched = next((x for x in statuses if x.get("artifact_id") == aid), None)
                    if matched:
                        studio_status = matched
                        if matched.get("status") == "completed":
                            break
                time.sleep(4)
            print(f"[studio] artifact={(studio_result or {}).get('artifact_id')} status={(studio_status or {}).get('status')}", flush=True)
        except Exception as e:
            print(f"[studio] create/poll failed: {e}", flush=True)

    if REQUIRE_STUDIO_ARTIFACT:
        if not studio_result or not studio_status or studio_status.get("status") != "completed":
            raise RuntimeError("Studio artifact not completed. NotebookLM-internal generation requirement failed.")

    summary = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "notebook_name": notebook_name,
        "notebook_id": notebook.id,
        "notebook_url": notebook.url,
        "deep_task": deep_task,
        "deep_polled_status": (deep_polled or {}).get("status") if deep_polled else "fallback_to_fast",
        "selected_source_count": len(selected),
        "imported_source_count": len(imported),
        "current_source_count": len(current_sources),
        "youtube_count": len([s for s in current_sources if re.search(r"youtube\\.com|youtu\\.be", (s.get("url") or "").lower())]),
        "blog_chars": len(blog_post),
        "policy_name": policy.get("name"),
        "fact_synthesis_chars": len(synthesis),
        "quality_gate_status": gate_status,
        "quality_gate_feedback": gate_result,
        "studio_result": studio_result,
        "studio_status": studio_status,
    }

    (out_dir / f"{notebook_name}_deep_report.md").write_text(deep_report, encoding="utf-8")
    (out_dir / f"{notebook_name}_fact_synthesis.md").write_text(synthesis, encoding="utf-8")
    (out_dir / f"{notebook_name}_blog_post.md").write_text(blog_post, encoding="utf-8")
    (out_dir / f"{notebook_name}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
