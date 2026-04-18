#!/usr/bin/env python3
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from notebooklm_mcp.api_client import NotebookLMClient
from notebooklm_mcp.auth import load_cached_tokens


@dataclass
class Topic:
    key: str
    keyword: str
    notebook_name: str
    research_direction: str


TOPICS = [
    Topic(
        key="foundation_models",
        keyword="AI 기반모델과 멀티모달 LLM",
        notebook_name="AI콘텐츠_기반모델",
        research_direction="모델 아키텍처, 추론 성능, 멀티모달 확장, 오픈소스/상용 모델 비교",
    ),
    Topic(
        key="development_ecosystem",
        keyword="AI 개발생태계와 MLOps/RAG",
        notebook_name="AI콘텐츠_개발생태계",
        research_direction="RAG 프레임워크, 벡터DB, 배포 파이프라인, 운영 모니터링",
    ),
    Topic(
        key="business_applications",
        keyword="AI 비즈니스 활용과 ROI",
        notebook_name="AI콘텐츠_비즈니스활용",
        research_direction="산업별 적용 사례, KPI/ROI, 생산성 개선, 도입 실패/성공 요인",
    ),
    Topic(
        key="ethics_governance",
        keyword="AI 윤리 규제 거버넌스",
        notebook_name="AI콘텐츠_윤리거버넌스",
        research_direction="규제 동향, 책임 있는 AI, 리스크/컴플라이언스, 설명가능성(XAI)",
    ),
    Topic(
        key="future_trends",
        keyword="AI 미래전망과 에이전트 시대",
        notebook_name="AI콘텐츠_미래트렌드",
        research_direction="AI 에이전트, AGI 로드맵, 차세대 컴퓨팅, 인력/산업 구조 변화",
    ),
]


def numbered_notebook_name(index: int, base_name: str) -> str:
    return f"{index:02d}_{base_name}"


NOTEBOOKLM_ONLY = os.getenv("NOTEBOOKLM_ONLY", "1") == "1"
ADAPTIVE_LOAD = os.getenv("NOTEBOOKLM_ADAPTIVE_LOAD", "1") == "1"
OVERLOAD_LIMIT = int(os.getenv("NOTEBOOKLM_OVERLOAD_LIMIT", "2"))
TOPIC_TARGET = int(os.getenv("NOTEBOOKLM_TOPIC_TARGET", str(len(TOPICS))))
DEEP_FIRST = os.getenv("NOTEBOOKLM_DEEP_FIRST", "1") == "1"
DEEP_TIMEOUT_SEC = int(os.getenv("NOTEBOOKLM_DEEP_TIMEOUT", "1200"))
MAX_SOURCES = int(os.getenv("NOTEBOOKLM_MAX_SOURCES", "0"))
TARGET_SOURCES = int(os.getenv("NOTEBOOKLM_TARGET_SOURCES", "25"))
REQUIRE_STUDIO_ARTIFACT = os.getenv("NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT", "1") == "1"
RECENCY_WINDOW_YEARS = int(os.getenv("NOTEBOOKLM_RECENCY_WINDOW_YEARS", "2"))
SOURCE_TOPUP_ROUNDS = int(os.getenv("NOTEBOOKLM_SOURCE_TOPUP_ROUNDS", "4"))
POLICY_PATH = os.getenv(
    "NOTEBOOKLM_AGENTIC_POLICY_PATH",
    "docs/notebooklm/AGENTIC_WORKFLOW_POLICY.json",
)
OVERLOAD_EVENTS = 0


def is_overload_error(err: Exception | str) -> bool:
    text = str(err).lower()
    overload_signals = [
        "connecterror",
        "readtimeout",
        "timed out",
        "nodename nor servname",
        "429",
        "too many requests",
        "overload",
    ]
    return any(sig in text for sig in overload_signals)


def mark_overload_if_needed(err: Exception | str) -> None:
    global OVERLOAD_EVENTS
    if is_overload_error(err):
        OVERLOAD_EVENTS += 1
        print(f"[overload] detected count={OVERLOAD_EVENTS}: {err}", flush=True)


TRUSTED_DOMAINS = {
    "openai.com": 6,
    "anthropic.com": 6,
    "deepmind.google": 6,
    "ai.google": 5,
    "google.com": 5,
    "microsoft.com": 5,
    "aws.amazon.com": 5,
    "arxiv.org": 6,
    "nature.com": 6,
    "science.org": 6,
    "ieee.org": 5,
    "acm.org": 5,
    "mckinsey.com": 5,
    "weforum.org": 5,
    "oecd.org": 5,
    "europa.eu": 5,
    "nvidia.com": 4,
    "github.com": 4,
    "huggingface.co": 4,
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


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def source_score(src: dict) -> int:
    url = src.get("url") or ""
    title = src.get("title") or ""
    domain = get_domain(url)
    score = TRUSTED_DOMAINS.get(domain, 1)
    if any(k in title.lower() for k in ["official", "report", "paper", "research", "benchmark"]):
        score += 1
    if "youtube.com" in domain or "youtu.be" in domain:
        if any(k in title.lower() for k in ["google", "openai", "anthropic", "deepmind", "stanford", "mit"]):
            score += 1
    return score


def is_time_sensitive_topic(text: str) -> bool:
    t = (text or "").lower()
    keys = ["ai", "인공지능", "스타트업", "정책", "규제", "트렌드", "시장", "생태계", "growth"]
    return any(k in t for k in keys)


def recency_bonus(src: dict, time_sensitive: bool) -> int:
    if not time_sensitive:
        return 0
    blob = " ".join([
        str(src.get("title") or ""),
        str(src.get("description") or ""),
        str(src.get("url") or ""),
    ])
    years = [int(y) for y in re.findall(r"(20\\d{2})", blob)]
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


def dedupe_sources(sources: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for s in sources:
        url = (s.get("url") or "").strip()
        title = (s.get("title") or "").strip()
        key = url or title
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def split_sources(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    yt, article = [], []
    for s in sources:
        url = (s.get("url") or "").lower()
        if "youtube.com" in url or "youtu.be" in url:
            yt.append(s)
        else:
            article.append(s)
    return yt, article


def pick_sources(sources: list[dict], min_total: int | None = None, time_sensitive: bool = True) -> list[dict]:
    if min_total is None:
        min_total = TARGET_SOURCES
    if MAX_SOURCES > 0:
        min_total = max(1, min(min_total, MAX_SOURCES))
    else:
        min_total = max(1, min_total)

    sources = dedupe_sources(sources)
    for s in sources:
        s["_score"] = source_score(s) + recency_bonus(s, time_sensitive=time_sensitive)
    yt, article = split_sources(sources)
    yt = sorted(yt, key=lambda x: x["_score"], reverse=True)
    article = sorted(article, key=lambda x: x["_score"], reverse=True)

    min_yt = 3 if min_total >= 10 else min(1, min_total)
    min_article = 7 if min_total >= 10 else max(0, min_total - min_yt)
    picked = []
    picked.extend(yt[:min_yt])
    picked.extend(article[:min_article])

    if len(picked) < min_total:
        remain = [s for s in sorted(sources, key=lambda x: x["_score"], reverse=True) if s not in picked]
        picked.extend(remain[: max(0, min_total - len(picked))])

    return picked[:min_total]


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


def poll_until_done(client: NotebookLMClient, notebook_id: str, task_id: str, timeout_sec: int = 1200) -> dict:
    start = time.time()
    while True:
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(client.poll_research, notebook_id, task_id)
                result = fut.result(timeout=30)
        except Exception as e:
            if isinstance(e, FutureTimeout):
                # Per-call timeout, keep polling without hanging.
                continue
            mark_overload_if_needed(e)
            raise
        if result:
            print(
                f"[poll] notebook={notebook_id} task={task_id} status={result.get('status')} "
                f"count={result.get('source_count')}",
                flush=True,
            )
        if result and result.get("status") == "completed":
            return result
        if time.time() - start > timeout_sec:
            raise TimeoutError(f"Research polling timeout for task {task_id}")
        time.sleep(8)


def run_fast_research_collect(client: NotebookLMClient, notebook_id: str, query: str) -> tuple[str, list[dict]]:
    print(f"[fast] start research: {query[:120]}", flush=True)
    started = client.start_research(notebook_id, query=query, source="web", mode="fast")
    if not started:
        return "", []
    polled = poll_until_done(client, notebook_id, started["task_id"], timeout_sec=600)
    return started["task_id"], polled.get("sources", [])


def ensure_sources_mix(client: NotebookLMClient, notebook_id: str, topic: Topic) -> tuple[str, list[dict]]:
    all_sources = []
    last_task_id = ""
    time_sensitive = is_time_sensitive_topic(topic.keyword + " " + topic.research_direction)
    queries = [
        (
            f"{topic.keyword} 관련 최신 고품질 자료를 수집해줘. "
            + ("최근 2년 자료를 우선 반영해줘. " if time_sensitive else "")
            + "YouTube URL 최소 5개와 기사/리포트 URL 최소 15개를 포함하고, "
            "공식 문서/연구기관/업계 리더 소스를 우선해줘. "
            "영문 기반 해외 고품질 소스도 적극 포함해줘."
        ),
        f"{topic.keyword} site:youtube.com 고품질 강의, 키노트, 전문가 인터뷰 중심으로 URL 수집 (해외 채널 우선) " + ("최근 2년 우선" if time_sensitive else ""),
        f"{topic.keyword} research papers, official technical blogs, global industry reports 중심 URL 수집 " + ("recent 2 years preferred" if time_sensitive else ""),
    ]
    for q in queries:
        task_id, sources = run_fast_research_collect(client, notebook_id, q)
        if task_id:
            last_task_id = task_id
        all_sources.extend(sources)
        picked = pick_sources(all_sources, min_total=TARGET_SOURCES, time_sensitive=time_sensitive)
        yt, article = split_sources(picked)
        if len(picked) >= TARGET_SOURCES and len(yt) >= 3 and len(article) >= 7:
            break
    selected = pick_sources(all_sources, min_total=TARGET_SOURCES, time_sensitive=time_sensitive)
    return last_task_id, (selected[:MAX_SOURCES] if MAX_SOURCES > 0 else selected)


def ask(client: NotebookLMClient, notebook_id: str, prompt: str, timeout: float = 180.0) -> str:
    for i in range(3):
        try:
            result = client.query(notebook_id, query_text=prompt, timeout=timeout)
            if result and result.get("answer"):
                return (result.get("answer") or "").strip()
        except Exception as e:
            mark_overload_if_needed(e)
            print(f"[ask] retry={i+1} error={type(e).__name__}: {e}", flush=True)
            time.sleep(5)
    return ""


def main() -> None:
    if not NOTEBOOKLM_ONLY:
        raise RuntimeError("Policy violation: NOTEBOOKLM_ONLY must be enabled.")

    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "ai_content_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    policy_file = (root / POLICY_PATH).resolve()
    policy = json.loads(policy_file.read_text(encoding="utf-8"))

    tokens = load_cached_tokens()
    if not tokens:
        raise RuntimeError("NotebookLM auth token not found. Run notebooklm-mcp-auth first.")

    client = NotebookLMClient(
        cookies=tokens.cookies,
        csrf_token=tokens.csrf_token,
        session_id=tokens.session_id,
    )

    run_data: dict = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "topics": [],
        "notebooks": [],
        "best_sources": [],
        "summary": {},
    }

    notebook_records = []
    planned_topics = TOPICS[: max(1, min(TOPIC_TARGET, len(TOPICS)))]
    print(
        f"[policy] NOTEBOOKLM_ONLY={NOTEBOOKLM_ONLY} ADAPTIVE_LOAD={ADAPTIVE_LOAD} "
        f"TOPIC_TARGET={len(planned_topics)} OVERLOAD_LIMIT={OVERLOAD_LIMIT} "
        f"DEEP_FIRST={DEEP_FIRST} DEEP_TIMEOUT_SEC={DEEP_TIMEOUT_SEC} "
        f"MAX_SOURCES={MAX_SOURCES} TARGET_SOURCES={TARGET_SOURCES} "
        f"RECENCY_WINDOW_YEARS={RECENCY_WINDOW_YEARS}",
        flush=True,
    )

    for idx, topic in enumerate(planned_topics, start=1):
        notebook_name = numbered_notebook_name(idx, topic.notebook_name)
        print(f"[topic] start: {notebook_name}", flush=True)
        try:
            nb = client.create_notebook(title=notebook_name)
            if not nb:
                raise RuntimeError(f"Failed to create notebook: {notebook_name}")
            print(f"[topic] created notebook: {nb.id}", flush=True)
            topic_time_sensitive = is_time_sensitive_topic(topic.keyword + " " + topic.research_direction)

            client.configure_chat(
                nb.id,
                goal="custom",
                custom_prompt="리서치 보고서 스타일로 작성. 근거 중심, 개조식 우선.",
                response_length="longer",
            )

            deep_started = None
            deep_result = {}
            if DEEP_FIRST:
                try:
                    deep_query = (
                        f"[{topic.keyword}]에 대해 Deep Research를 수행해줘. "
                        "글로벌 사례, 유튜브/아티클 균형, 아키텍처/운영/거버넌스 관점 포함."
                    )
                    deep_started = client.start_research(nb.id, query=deep_query, source="web", mode="deep")
                    if deep_started:
                        print(f"[deep] start task={deep_started['task_id']}", flush=True)
                        deep_result = poll_until_done(
                            client,
                            nb.id,
                            deep_started["task_id"],
                            timeout_sec=DEEP_TIMEOUT_SEC,
                        )
                        print(
                            f"[deep] completed status={deep_result.get('status')} count={deep_result.get('source_count')}",
                            flush=True,
                        )
                except Exception as e:
                    mark_overload_if_needed(e)
                    print(f"[deep] fallback to fast due to error: {e}", flush=True)

            task_id, selected_sources = ensure_sources_mix(client, nb.id, topic)
            if not task_id:
                raise RuntimeError(f"Failed to collect research task for: {notebook_name}")
            if MAX_SOURCES > 0:
                selected_sources = selected_sources[:MAX_SOURCES]
            print(
                f"[source] selected: {len(selected_sources)} (target_min={TARGET_SOURCES}, max={MAX_SOURCES})",
                flush=True,
            )

            imported = client.import_research_sources(nb.id, task_id=task_id, sources=selected_sources)
            current_sources = client.get_notebook_sources_with_types(nb.id)
            current_sources, deleted_failed = prune_failed_sources(client, nb.id, current_sources)
            print(
                f"[source] imported={len(imported)} deleted_failed={deleted_failed} current={len(current_sources)}",
                flush=True,
            )

            # Top up until valid source count reaches target minimum.
            topup_round = 0
            while len(current_sources) < TARGET_SOURCES and topup_round < SOURCE_TOPUP_ROUNDS:
                topup_round += 1
                refill_task_id, refill_candidates = ensure_sources_mix(client, nb.id, topic)
                if not refill_task_id or not refill_candidates:
                    break
                existing_urls = {(x.get("url") or "").strip() for x in current_sources if x.get("url")}
                refill_candidates = [
                    x for x in refill_candidates
                    if (x.get("url") or "").strip() and (x.get("url") or "").strip() not in existing_urls
                ]
                if not refill_candidates:
                    break
                _ = client.import_research_sources(nb.id, task_id=refill_task_id, sources=refill_candidates)
                current_sources = client.get_notebook_sources_with_types(nb.id)
                current_sources, deleted_failed = prune_failed_sources(client, nb.id, current_sources)
                print(
                    f"[source] topup_round={topup_round} imported_attempt={len(refill_candidates)} "
                    f"deleted_failed={deleted_failed} current={len(current_sources)} target_min={TARGET_SOURCES}",
                    flush=True,
                )

            article_prompt = (
                policy["prompts"]["blog_writer"]
                + f"\n주제: {topic.keyword}"
            )
            article_text = ask(client, nb.id, article_prompt)
            if len(article_text) < 4000:
                article_text = ask(
                    client,
                    nb.id,
                    f"방금 작성한 글을 확장해서 4,500자 이상으로 다시 작성해줘. 주제: {topic.keyword}",
                )
            print(f"[article] generated chars={len(article_text)} for {notebook_name}", flush=True)

            synthesis = ask(client, nb.id, policy["prompts"]["fact_synthesis"])
            gate_prompt = f"{policy['prompts']['quality_gate']}\n\n[초안]\n{article_text}"
            gate_result = ask(client, nb.id, gate_prompt, timeout=220.0)
            gate_status = "PASS" if gate_result.strip().startswith("PASS") else "FAIL"
            if gate_status == "FAIL":
                rewrite_prompt = f"{policy['prompts']['rewrite']}\n\n[품질게이트 피드백]\n{gate_result}\n\n[초안]\n{article_text}"
                rewritten = ask(client, nb.id, rewrite_prompt, timeout=220.0)
                if len(rewritten) >= 3500:
                    article_text = rewritten
            print(f"[quality_gate] {notebook_name} status={gate_status}", flush=True)

            # Enforce NotebookLM-internal deliverable via Studio report artifact
            src_ids = [s["id"] for s in current_sources if s.get("id")]
            studio_result = None
            studio_status = None
            if src_ids:
                try:
                    studio_result = client.create_report(
                        nb.id,
                        source_ids=(src_ids[:MAX_SOURCES] if MAX_SOURCES > 0 else src_ids),
                        report_format="Blog Post",
                        language="ko",
                    )
                    for _ in range(30):
                        statuses = client.poll_studio_status(nb.id)
                        if isinstance(statuses, list):
                            aid = (studio_result or {}).get("artifact_id")
                            matched = next((x for x in statuses if x.get("artifact_id") == aid), None)
                            if matched:
                                studio_status = matched
                                if matched.get("status") == "completed":
                                    break
                        time.sleep(4)
                    print(
                        f"[studio] {notebook_name} artifact={(studio_result or {}).get('artifact_id')} status={(studio_status or {}).get('status')}",
                        flush=True,
                    )
                except Exception as e:
                    mark_overload_if_needed(e)
                    print(f"[studio] {notebook_name} create/poll failed: {e}", flush=True)

            if REQUIRE_STUDIO_ARTIFACT:
                if not studio_result or not studio_status or studio_status.get("status") != "completed":
                    raise RuntimeError(f"Studio artifact not completed for {notebook_name}")

            record = {
                "topic_key": topic.key,
                "keyword": topic.keyword,
                "research_direction": topic.research_direction,
                "notebook_name": notebook_name,
                "notebook_id": nb.id,
                "notebook_url": nb.url,
                "deep_research_task": deep_started,
                "deep_research_report": ask(
                    client,
                    nb.id,
                    f"[{topic.keyword}]에 대해 현재 노트북 소스만 근거로 딥리서치 보고서를 개조식으로 작성해줘.",
                ),
                "selected_sources": selected_sources,
                "imported_sources": imported,
                "current_sources": current_sources,
                "article_text": article_text,
                "policy_name": policy.get("name"),
                "fact_synthesis": synthesis,
                "quality_gate_status": gate_status,
                "quality_gate_feedback": gate_result,
                "studio_result": studio_result,
                "studio_status": studio_status,
            }
            notebook_records.append(record)

            (out_dir / f"{notebook_name}_article.md").write_text(article_text, encoding="utf-8")
            (out_dir / f"{notebook_name}_fact_synthesis.md").write_text(synthesis, encoding="utf-8")
            (out_dir / f"{notebook_name}_deep_report.md").write_text(
                record["deep_research_report"], encoding="utf-8"
            )
            (out_dir / "run_summary.partial.json").write_text(
                json.dumps({"notebooks": notebook_records}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[topic] done: {notebook_name}", flush=True)
        except Exception as e:
            mark_overload_if_needed(e)
            if ADAPTIVE_LOAD and OVERLOAD_EVENTS >= OVERLOAD_LIMIT:
                print(
                    "[policy] overload threshold reached. "
                    "Stop adding more topics and proceed with completed notebooks only.",
                    flush=True,
                )
                break
            raise

    if not notebook_records:
        raise RuntimeError("No notebooks completed. Cannot continue.")

    # Best 5 source selection across 5 notebooks
    source_pool = []
    for rec in notebook_records:
        for s in rec["current_sources"]:
            url = s.get("url") or ""
            if not url:
                continue
            source_pool.append(
                {
                    "url": url,
                    "title": s.get("title") or "",
                    "topic": rec["keyword"],
                    "score": source_score(s),
                }
            )

    merged = {}
    for s in source_pool:
        key = s["url"]
        if key not in merged:
            merged[key] = {**s, "appearances": 1}
        else:
            merged[key]["appearances"] += 1
            merged[key]["score"] = max(merged[key]["score"], s["score"])

    ranked = sorted(
        merged.values(),
        key=lambda x: (x["appearances"], x["score"]),
        reverse=True,
    )
    best5 = ranked[:5]

    # Notebook 6 creation with best 5 sources (or fewer if adaptive load reduced scope)
    nb6_name = numbered_notebook_name(len(notebook_records) + 1, "AI콘텐츠_통합베스트소스")
    nb6 = client.create_notebook(title=nb6_name)
    if not nb6:
        raise RuntimeError("Failed to create synthesis notebook")

    client.configure_chat(
        nb6.id,
        goal="custom",
        custom_prompt="리서치 보고서 스타일로 작성. 소스 근거를 명시하고 비교분석 중심.",
        response_length="longer",
    )

    for s in best5:
        client.add_url_source(nb6.id, s["url"])
    time.sleep(20)
    print(f"[synthesis] notebook created={nb6.id} sources={len(best5)}", flush=True)

    discussion = "자동 점수 기반 토론 결과:\n" + "\n".join(
        [f"- {i+1}. {s['title']} | {s['url']} | appearances={s['appearances']} score={s['score']}" for i, s in enumerate(best5)]
    )

    article6_prompt = (
        "현재 노트북 소스만 근거로 AI 통합전략 아티클을 작성해줘. "
        "한국어 4,000자 이상, 시장/기술/비즈니스/윤리/미래전망을 모두 포함해줘."
    )
    article6 = ask(client, nb6.id, article6_prompt)
    if len(article6) < 4000:
        article6 = ask(client, nb6.id, "방금 통합전략 글을 4,500자 이상으로 확장해서 다시 작성해줘.")

    (out_dir / f"{nb6_name}_discussion.md").write_text(discussion, encoding="utf-8")
    (out_dir / f"{nb6_name}_article.md").write_text(article6, encoding="utf-8")

    # Save summary
    run_data["topics"] = [
        {
            "keyword": t.keyword,
            "notebook_name": t.notebook_name,
            "research_direction": t.research_direction,
        }
        for t in planned_topics
    ]
    run_data["notebooks"] = notebook_records
    run_data["best_sources"] = best5
    run_data["summary"] = {
        "notebook_count": len(notebook_records) + 1,
        "output_dir": str(out_dir),
        "synthesis_notebook_id": nb6.id,
        "synthesis_notebook_url": nb6.url,
        "policy": {
            "NOTEBOOKLM_ONLY": NOTEBOOKLM_ONLY,
            "ADAPTIVE_LOAD": ADAPTIVE_LOAD,
            "OVERLOAD_LIMIT": OVERLOAD_LIMIT,
            "TOPIC_TARGET": len(planned_topics),
            "OVERLOAD_EVENTS": OVERLOAD_EVENTS,
        },
    }

    (out_dir / "run_summary.json").write_text(
        json.dumps(run_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Human-readable index
    lines = []
    lines.append("# NotebookLM AI Content Pipeline Results")
    lines.append("")
    lines.append("## 1) MECE 5 Keywords")
    for t in TOPICS:
        lines.append(f"- {t.keyword}: {t.research_direction}")
    lines.append("")
    lines.append("## 2) Created Notebooks")
    for rec in notebook_records:
        lines.append(f"- {rec['notebook_name']} ({rec['notebook_url']})")
        lines.append(f"  - imported sources: {len(rec['imported_sources'])}")
        yt_count = len([s for s in rec['current_sources'] if re.search(r'youtube\\.com|youtu\\.be', (s.get('url') or '').lower())])
        lines.append(f"  - current sources: {len(rec['current_sources'])}, youtube: {yt_count}")
    lines.append("")
    lines.append("## 3) Best 5 Sources")
    for i, s in enumerate(best5, 1):
        lines.append(f"- {i}. {s['title']} ({s['url']})")
    lines.append("")
    lines.append("## 4) Output Files")
    lines.append(f"- {out_dir}")
    lines.append("- 6개 아티클 파일 포함")

    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
