#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from urllib.parse import urlparse

from notebooklm_mcp.api_client import NotebookLMClient
from notebooklm_mcp.auth import load_cached_tokens


DEEP_FIRST = os.getenv("NOTEBOOKLM_DEEP_FIRST", "1") == "1"
DEEP_TIMEOUT_SEC = int(os.getenv("NOTEBOOKLM_DEEP_TIMEOUT", "1200"))
MAX_SOURCES = int(os.getenv("NOTEBOOKLM_MAX_SOURCES", "0"))
TARGET_SOURCES = int(os.getenv("NOTEBOOKLM_TARGET_SOURCES", "25"))
REQUIRE_STUDIO_ARTIFACT = os.getenv("NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT", "1") == "1"
RECENCY_WINDOW_YEARS = int(os.getenv("NOTEBOOKLM_RECENCY_WINDOW_YEARS", "2"))
SOURCE_TOPUP_ROUNDS = int(os.getenv("NOTEBOOKLM_SOURCE_TOPUP_ROUNDS", "4"))


TRUSTED = {
    "mss.go.kr": 6,
    "kised.or.kr": 6,
    "k-startup.go.kr": 6,
    "kostat.go.kr": 6,
    "moef.go.kr": 5,
    "openai.com": 5,
    "oecd.org": 6,
    "worldbank.org": 5,
    "mckinsey.com": 5,
    "weforum.org": 5,
    "arxiv.org": 5,
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


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def source_score(src: dict) -> int:
    domain = get_domain(src.get("url") or "")
    title = (src.get("title") or "").lower()
    score = TRUSTED.get(domain, 1)
    if any(k in title for k in ["report", "white paper", "official", "statistics", "policy", "research"]):
        score += 1
    return score


def is_time_sensitive_topic(topic: str) -> bool:
    t = topic.lower()
    keys = ["ai", "인공지능", "스타트업", "정책", "규제", "트렌드", "시장", "생태계", "growth"]
    return any(k in t for k in keys)


def recency_bonus(src: dict, time_sensitive: bool) -> int:
    if not time_sensitive:
        return 0
    text = " ".join([
        str(src.get("title") or ""),
        str(src.get("description") or ""),
        str(src.get("url") or ""),
    ])
    years = [int(y) for y in re.findall(r"(20\\d{2})", text)]
    if not years:
        return 0
    current_year = time.localtime().tm_year
    latest = max(years)
    age = current_year - latest
    if age <= RECENCY_WINDOW_YEARS:
        return 3
    if age <= RECENCY_WINDOW_YEARS + 2:
        return 1
    return -1


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


def pick_sources(sources: list[dict], target_count: int | None = None, time_sensitive: bool = True) -> list[dict]:
    src = dedupe(sources)
    for s in src:
        s["_score"] = source_score(s) + recency_bonus(s, time_sensitive=time_sensitive)
    src = sorted(src, key=lambda x: x["_score"], reverse=True)
    if target_count is None:
        return src
    if MAX_SOURCES > 0:
        target_count = max(1, min(target_count, MAX_SOURCES))
    else:
        target_count = max(1, target_count)
    yt, article = split_sources(src)
    yt = sorted(yt, key=lambda x: x["_score"], reverse=True)
    article = sorted(article, key=lambda x: x["_score"], reverse=True)

    # Keep balance constraints as much as possible while aiming for target_count.
    min_yt = 3 if target_count >= 10 else min(1, target_count)
    min_article = 7 if target_count >= 10 else max(0, target_count - min_yt)

    picked = yt[:min_yt] + article[:min_article]
    if len(picked) < target_count:
        remain = [s for s in sorted(src, key=lambda x: x["_score"], reverse=True) if s not in picked]
        picked.extend(remain[: target_count - len(picked)])
    return picked[:target_count]


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


def poll_research(
    client: NotebookLMClient,
    notebook_id: str,
    task_id: str,
    timeout_sec: int,
    call_timeout_sec: int = 30,
) -> dict | None:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(client.poll_research, notebook_id, task_id)
                result = fut.result(timeout=call_timeout_sec)
        except FutureTimeout:
            # Per-call timeout: don't get stuck; continue polling loop.
            continue
        if result and result.get("status") == "completed":
            return result
        time.sleep(8)
    return None


def next_numbered_prefix(client: NotebookLMClient) -> int:
    notebooks = client.list_notebooks() or []
    max_n = 0
    for nb in notebooks:
        title = getattr(nb, "title", "") or ""
        m = re.match(r"^(\d{2})_", title)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def find_reusable_notebook(client: NotebookLMClient, base_name: str):
    """Find latest numbered notebook matching base_name, e.g. 04_<base_name>."""
    notebooks = client.list_notebooks() or []
    candidates = []
    for nb in notebooks:
        title = getattr(nb, "title", "") or ""
        m = re.match(r"^(\d{2})_(.+)$", title)
        if not m:
            continue
        num = int(m.group(1))
        body = m.group(2)
        if body == base_name or base_name in body or body in base_name:
            candidates.append((num, nb))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def ask(client: NotebookLMClient, notebook_id: str, prompt: str, timeout: float = 200.0) -> str:
    for _ in range(3):
        try:
            r = client.query(notebook_id, query_text=prompt, timeout=timeout)
            if r and r.get("answer"):
                return (r.get("answer") or "").strip()
        except Exception:
            time.sleep(4)
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "topic_reports_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    tokens = load_cached_tokens()
    if not tokens:
        raise RuntimeError("NotebookLM auth not found.")

    client = NotebookLMClient(cookies=tokens.cookies, csrf_token=tokens.csrf_token, session_id=tokens.session_id)
    time_sensitive = is_time_sensitive_topic(args.topic)
    print(
        f"[policy] time_sensitive={time_sensitive} recency_window_years={RECENCY_WINDOW_YEARS}",
        flush=True,
    )

    idx = next_numbered_prefix(client)
    base = args.name or f"AI콘텐츠_{args.topic}"

    # Reuse existing notebook first (prevents unnecessary creation)
    existing = find_reusable_notebook(client, base)
    if existing:
        nb = existing
        notebook_name = getattr(nb, "title", f"{idx:02d}_{base}")
        print(f"[reuse] notebook={notebook_name} ({nb.id})", flush=True)
    else:
        notebook_name = f"{idx:02d}_{base}"
        nb = client.create_notebook(title=notebook_name)
        if not nb:
            raise RuntimeError("Failed to create notebook.")
        print(f"[create] notebook={notebook_name} ({nb.id})", flush=True)

    client.configure_chat(
        nb.id,
        goal="custom",
        custom_prompt="리서치 보고서 스타일, 정책/데이터 근거 중심, 한국어",
        response_length="longer",
    )

    current_sources = client.get_notebook_sources_with_types(nb.id)
    current_sources, deleted_failed = prune_failed_sources(client, nb.id, current_sources)
    print(
        f"[source] existing_current={len(current_sources)} deleted_failed={deleted_failed} "
        f"target_min={TARGET_SOURCES}",
        flush=True,
    )

    deep_task = None
    deep_polled = None

    # If there are no imported sources but there is completed research, import from that first.
    if len(current_sources) < TARGET_SOURCES:
        try:
            existing_research = client.poll_research(nb.id)
            if existing_research and existing_research.get("status") == "completed" and existing_research.get("source_count", 0) > 0:
                rs = [s for s in (existing_research.get("sources") or []) if s.get("url")]
                if rs:
                    selected_from_existing = pick_sources(
                        rs,
                        target_count=None,
                        time_sensitive=time_sensitive,
                    )
                    imported_existing = client.import_research_sources(
                        nb.id,
                        task_id=existing_research["task_id"],
                        sources=selected_from_existing,
                    )
                    current_sources = client.get_notebook_sources_with_types(nb.id)
                    print(
                        f"[reuse-import] from existing research imported={len(imported_existing)} current={len(current_sources)} target={TARGET_SOURCES}",
                        flush=True,
                    )
        except Exception as e:
            print(f"[reuse-import] skipped due to error: {e}", flush=True)

    # Start new deep/fast research only when current sources are insufficient.
    if DEEP_FIRST and len(current_sources) < TARGET_SOURCES:
        try:
            q = (
                f"{args.topic}에 대한 deep research를 수행해줘. "
                "한국 정부 정책/지원, 스타트업 성장지표, 해외 비교, 유튜브/아티클 출처를 포함."
            )
            deep_task = client.start_research(nb.id, query=q, source="web", mode="deep")
            if deep_task:
                deep_polled = poll_research(client, nb.id, deep_task["task_id"], timeout_sec=DEEP_TIMEOUT_SEC)
        except Exception:
            deep_task = deep_task

    all_sources = []
    queries = [
        (
            f"{args.topic} "
            + ("prioritize sources from the last 2 years " if time_sensitive else "")
            + "Korean government startup growth policy impact with global benchmarks include URLs"
        ),
        (
            f"{args.topic} site:youtube.com interviews policy analysis startup ecosystem "
            + ("last 2 years preferred" if time_sensitive else "")
        ),
        (
            f"{args.topic} official statistics reports papers oecd worldbank "
            + ("prefer recent 2-year materials for fast-changing AI/startup trend context" if time_sensitive else "")
        ),
    ]
    last_task_id = ""
    round_no = 0
    while len(current_sources) < TARGET_SOURCES and round_no < SOURCE_TOPUP_ROUNDS:
        round_no += 1
        for q in queries:
            s = client.start_research(nb.id, query=q, source="web", mode="fast")
            if not s:
                continue
            last_task_id = s["task_id"]
            r = poll_research(client, nb.id, s["task_id"], timeout_sec=420)
            if not r:
                continue
            all_sources.extend(r.get("sources", []))
            selected_now = pick_sources(
                all_sources,
                target_count=None,
                time_sensitive=time_sensitive,
            )
            existing_urls = {(x.get("url") or "").strip() for x in current_sources if x.get("url")}
            selected_now = [x for x in selected_now if (x.get("url") or "").strip() and (x.get("url") or "").strip() not in existing_urls]
            if selected_now and last_task_id:
                _ = client.import_research_sources(nb.id, task_id=last_task_id, sources=selected_now)
                current_sources = client.get_notebook_sources_with_types(nb.id)
                current_sources, deleted_round = prune_failed_sources(client, nb.id, current_sources)
                print(
                    f"[source] topup_round={round_no} imported_attempt={len(selected_now)} "
                    f"deleted_failed={deleted_round} current={len(current_sources)} target_min={TARGET_SOURCES}",
                    flush=True,
                )
            if len(current_sources) >= TARGET_SOURCES:
                break

    imported = []
    selected = []
    if len(current_sources) < TARGET_SOURCES:
        selected = pick_sources(
            all_sources,
            target_count=None,
            time_sensitive=time_sensitive,
        )
        existing_urls = {(x.get("url") or "").strip() for x in current_sources if x.get("url")}
        selected = [x for x in selected if (x.get("url") or "").strip() and (x.get("url") or "").strip() not in existing_urls]
        imported = client.import_research_sources(nb.id, task_id=last_task_id, sources=selected)
        current_sources = client.get_notebook_sources_with_types(nb.id)
        current_sources, deleted_failed = prune_failed_sources(client, nb.id, current_sources)
        print(
            f"[source] imported_new={len(imported)} deleted_failed={deleted_failed} "
            f"current={len(current_sources)} target_min={TARGET_SOURCES}",
            flush=True,
        )
    else:
        print("[source] skip new research/import due to sufficient existing sources", flush=True)
    src_ids = [s["id"] for s in current_sources if s.get("id")]

    # NotebookLM report artifact
    report = client.create_report(
        nb.id,
        source_ids=(src_ids[:MAX_SOURCES] if MAX_SOURCES > 0 else src_ids),
        report_format="Briefing Doc",
        language="ko",
    )

    studio_status = None
    for _ in range(45):
        sts = client.poll_studio_status(nb.id)
        aid = (report or {}).get("artifact_id")
        if isinstance(sts, list):
            hit = next((x for x in sts if x.get("artifact_id") == aid), None)
            if hit:
                studio_status = hit
                if hit.get("status") == "completed":
                    break
        time.sleep(4)

    deep_report = ask(
        client,
        nb.id,
        f"현재 노트북 소스만 근거로 '{args.topic}' 딥리서치 보고서를 개조식으로 작성해줘.",
    )

    if REQUIRE_STUDIO_ARTIFACT and (not studio_status or studio_status.get("status") != "completed"):
        raise RuntimeError("Studio report artifact not completed.")

    summary = {
        "topic": args.topic,
        "notebook_name": notebook_name,
        "notebook_id": nb.id,
        "notebook_url": nb.url,
        "deep_task": deep_task,
        "deep_polled_status": (deep_polled or {}).get("status") if deep_polled else "fallback_to_fast",
        "selected_source_count": len(selected),
        "imported_source_count": len(imported),
        "current_source_count": len(current_sources),
        "youtube_count": len([s for s in current_sources if re.search(r"youtube\\.com|youtu\\.be", (s.get("url") or "").lower())]),
        "studio_result": report,
        "studio_status": studio_status,
    }

    (out_dir / f"{notebook_name}_deep_report.md").write_text(deep_report, encoding="utf-8")
    (out_dir / f"{notebook_name}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
