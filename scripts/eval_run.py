"""RAG 고정 질문셋 평가 러너.

docs/rag/questions.json의 고정 질문셋을 FastAPI `/chat` 엔드포인트로 호출하고,
GUIDE 4항의 기록 항목을 raw.json으로 저장한 뒤 summary.md로 집계한다.

실행 전 준비
------------
    conda activate rag_env
    docker compose up -d qdrant
    python index_documents.py
    uvicorn server:app --reload

실행 예시
---------
    python scripts/eval_run.py --config baseline --repeat 3

실행 횟수 규칙 (RAG_EVALUATION_QUESTIONS.md 12항)
------------------------------------------------
- 정확도 지표: 질문셋 전체(23문항)를 1회 실행한다.
- 시간 지표  : questions.json의 timing_question_ids(대표 7문항)만 --repeat 횟수만큼 실행한다.
  1회차는 정확도 실행과 공유하고, 2회차 이후만 추가 호출한다.

보안
----
이 스크립트는 .env를 읽지 않는다(`dotenv`를 import하지 않는다).
환경변수가 필요한 경우 os.environ에서만 읽으며, 값은 출력·저장하지 않는다.
OPENAI_API_KEY는 이 스크립트가 아니라 `uvicorn server:app` 프로세스에서 사용된다.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUESTIONS = REPO_ROOT / "docs" / "rag" / "questions.json"
DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "rag" / "results"

# server.py가 Routing을 구현하기 전에는 응답에 선택 Collection 정보가 없다.
NO_ROUTING_LABEL = "ALL(3) - Routing 미적용"


# ---------------------------------------------------------------- 입력/호출


def load_questions(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("questions"):
        raise ValueError(f"질문셋이 비어 있습니다 : {path}")

    return data


def call_chat(api_base, endpoint, question, timeout):
    """server.py의 /chat을 호출하고 (응답 dict, 클라이언트 측 소요 ms)를 돌려준다."""

    url = api_base.rstrip("/") + endpoint
    body = json.dumps({"question": question}).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    start = time.perf_counter()

    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    client_ms = round((time.perf_counter() - start) * 1000, 2)

    return payload, client_ms


# ---------------------------------------------------------------- 자동 집계


def resolve_collection(file_name, collection_map):
    return collection_map.get(file_name, f"UNKNOWN({file_name})")


def build_expected_keys(question):
    """기대 근거를 (collection, chunk_index) 집합으로 변환한다."""

    keys = set()

    for item in question.get("expected", []):
        for chunk_index in item.get("chunks", []):
            keys.add((item["collection"], chunk_index))

    return keys


def evaluate_stage(question, docs, collection_map, available):
    """한 단계(검색 / Re-ranking)의 정답 chunk 포함 여부와 최상위 순위를 계산한다.

    `available`이 False면(응답에 해당 필드가 없으면) 모든 값을 None으로 두어
    summary.md에 "미측정"으로 표기되게 한다.
    """

    if not available:
        return {
            "available": False,
            "k": None,
            "hit": None,
            "best_rank": None,
            "matched_keys": []
        }

    expected_keys = build_expected_keys(question)

    # 문서 범위 밖 질문은 기대 근거가 없으므로 Hit 판정 대상이 아니다.
    if not expected_keys:
        return {
            "available": True,
            "k": len(docs),
            "hit": None,
            "best_rank": None,
            "matched_keys": []
        }

    matched = []

    for doc in docs:
        key = (
            resolve_collection(doc.get("file"), collection_map),
            doc.get("chunk")
        )
        if key in expected_keys:
            matched.append({
                "rank": doc.get("rank"),
                "collection": key[0],
                "chunk_index": key[1]
            })

    return {
        "available": True,
        "k": len(docs),
        "hit": bool(matched),
        "best_rank": min((m["rank"] for m in matched), default=None),
        "matched_keys": matched
    }


def evaluate_items(question, answer):
    """기대 항목 키워드가 답변에 포함됐는지 센다(자동 보조 지표).

    문자열 포함 검사이므로 최종 정답/누락 판정은 사람이 확인해야 한다.
    """

    groups = question.get("expected_items") or []

    if not groups:
        return {"matched": None, "total": None, "missing": []}

    text = answer or ""
    missing = []
    matched = 0

    for group in groups:
        if any(keyword in text for keyword in group):
            matched += 1
        else:
            missing.append(group[0])

    return {"matched": matched, "total": len(groups), "missing": missing}


def evaluate_refusal(answer, refusal_patterns):
    """문서 범위 밖 질문의 거절 여부를 문자열 기준으로 판정한다(자동 보조 지표)."""

    text = answer or ""

    return any(pattern in text for pattern in refusal_patterns)


def run_once(question, run_index, api_base, endpoint, timeout, data):
    collection_map = data["collections"]
    refusal_patterns = data.get("refusal_patterns", [])

    record = {
        "question_id": question["id"],
        "type": question["type"],
        "run": run_index,
        "question": question["question"],
        "out_of_scope": bool(question.get("out_of_scope")),
    }

    try:
        payload, client_ms = call_chat(
            api_base, endpoint, question["question"], timeout
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:
        record["error"] = f"{type(error).__name__}: {error}"
        return record

    timings = payload.get("timings_ms", {})
    retrieved_docs = payload.get("retrieved_docs", []) or []
    answer = payload.get("answer", "")

    # server.py가 Re-ranking 전 후보를 응답하지 않는 버전이면 미측정으로 처리한다.
    has_candidates = "retrieval_candidates" in payload
    retrieval_candidates = payload.get("retrieval_candidates") or []

    record.update({
        # server.py가 selected_collections를 응답하기 시작하면 그 값을 사용한다.
        "selected_collections": payload.get("selected_collections", NO_ROUTING_LABEL),
        "retrieval_top_k": payload.get("retrieval_top_k"),
        "retrieval_candidate_count": payload.get("retrieval_candidate_count"),
        "rerank_candidate_count": payload.get("rerank_candidate_count"),
        "final_context_count": payload.get("retrieved_count"),
        "multi_query_used": payload.get("multi_query_used"),
        "multi_queries": payload.get("queries", []),
        "retrieved_docs": [
            {
                "rank": doc.get("rank"),
                "collection": resolve_collection(doc.get("file"), collection_map),
                "file": doc.get("file"),
                "chunk_index": doc.get("chunk"),
                "splitter": doc.get("splitter"),
                "retriever_score": doc.get("retriever_score"),
                "rerank_score": doc.get("rerank_score"),
                # 본문 전체는 raw.json 크기를 키우므로 앞부분만 저장한다.
                "text_excerpt": (doc.get("text") or "")[:200]
            }
            for doc in retrieved_docs
        ],
        # Re-ranking 전 검색 후보 (server.py의 디버그 필드)
        "retrieval_candidates": [
            {
                "rank": doc.get("rank"),
                "collection": resolve_collection(doc.get("file"), collection_map),
                "file": doc.get("file"),
                "chunk_index": doc.get("chunk"),
                "score": doc.get("score"),
                "passed_to_reranker": doc.get("passed_to_reranker"),
                "text_excerpt": (doc.get("text") or "")[:200]
            }
            for doc in retrieval_candidates
        ],
        "multi_query_ms": timings.get("multi_query"),
        "retrieval_ms": timings.get("retrieval"),
        "reranking_ms": timings.get("reranking"),
        "gpt_ms": timings.get("gpt"),
        "total_ms": timings.get("total", payload.get("response_time_ms")),
        "client_total_ms": client_ms,
        "answer": answer,
        "source": payload.get("sources", []),
        "top_rerank_score": payload.get("top_rerank_score"),
    })

    # 검색 단계(Re-ranking 전)와 Re-ranking 단계를 따로 집계한다.
    record["auto_retrieval_stage"] = evaluate_stage(
        question, retrieval_candidates, collection_map, has_candidates
    )
    record["auto_rerank_stage"] = evaluate_stage(
        question, retrieved_docs, collection_map, True
    )
    record["auto_items"] = evaluate_items(question, answer)
    record["auto_refused"] = (
        evaluate_refusal(answer, refusal_patterns)
        if question.get("out_of_scope")
        else None
    )

    return record


# ---------------------------------------------------------------- 요약 작성


def mean(values):
    values = [v for v in values if isinstance(v, (int, float))]

    if not values:
        return None

    return round(sum(values) / len(values), 2)


def fmt(value, suffix=""):
    if value is None:
        return "미측정"

    return f"{value}{suffix}"


def fmt_dash(value):
    """측정은 했지만 해당 값이 없는 경우(정답 chunk 미포함 등)는 미측정과 구분한다."""

    return "-" if value is None else str(value)


def relative_to_repo(path):
    """가능하면 저장소 기준 상대 경로로 표시한다(문서에 절대 경로를 남기지 않기 위함)."""

    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def quote_arg(value):
    """공백이 포함된 인자를 그대로 재실행할 수 있게 따옴표로 감싼다."""

    text = str(value)

    return f'"{text}"' if (" " in text or text == "") else text


def md_escape(text):
    """표 셀 안에서 줄바꿈과 파이프가 깨지지 않게 정리한다."""

    if text is None:
        return ""

    return re.sub(r"\s*\n\s*", " ", str(text)).replace("|", "\\|").strip()


def write_summary(path, data, runs, args, started_at, finished_at):
    questions = {q["id"]: q for q in data["questions"]}
    timing_ids = args.timing_ids

    first_runs = [r for r in runs if r["run"] == 1]
    ok_first = [r for r in first_runs if "error" not in r]
    errors = [r for r in runs if "error" in r]

    lines = []
    add = lines.append

    add(f"# 평가 결과 요약 — `{args.config}`")
    add("")
    add("`scripts/eval_run.py`가 자동 생성한 파일이다. 수동 편집 시 재실행하면 덮어써진다.")
    add("")
    add("---")
    add("")

    # ---- 테스트 조건
    add("## 테스트 조건")
    add("")
    add(f"- config: `{args.config}`")
    add(f"- 실행 시각: {started_at} ~ {finished_at}")
    add(f"- 실행 환경: Conda `rag_env` / Qdrant `6333` / FastAPI")
    add(f"- 호출 대상: `POST {args.api_base.rstrip('/')}{args.endpoint}` (server.py)")
    add(f"- 질문셋: `{relative_to_repo(args.questions_file)}` (v{data.get('version')}, {len(data['questions'])}문항)")
    add(f"- Re-ranker: {args.reranker}")
    add("- 평가 횟수")
    add(f"  - 정확도 지표(Hit@K, 정답 여부, 정보 누락, Hallucination): **{len(first_runs)}문항 × 1회**")
    add(
        f"  - 시간 지표(retrieval / reranking / gpt / total): "
        f"**대표 {len(timing_ids)}문항 × {args.repeat}회 평균, 회차별 값 병기**"
    )
    add(f"  - 시간 지표 대표 문항: {', '.join(f'`{i}`' for i in timing_ids)}")
    add("- top_k / 후보 수는 `vectorstore/retriever.py`의 질문 유형 판단에 따라 자동 결정된다(일반 8/3/8, 목록형 15/10/15). 질문별 관측값은 아래 상세표에 기록한다.")

    # 워밍업 (콜드스타트 제거)
    if args.warmup is None:
        add("- 워밍업: **미수행** (`--no-warmup`). 1회차에 ko-reranker 모델 로딩 시간이 포함될 수 있다.")
    elif "error" in args.warmup:
        add(
            f"- 워밍업: **실패** — 질문 `{args.warmup['question']}` / {args.warmup['error']}. "
            "1회차에 모델 로딩 시간이 포함될 수 있다."
        )
    else:
        add(
            f"- 워밍업: 본 측정 전 1회 수행하고 **집계에서 제외**했다. "
            f"질문 `{args.warmup['question']}`, 워밍업 total_ms = {fmt(args.warmup['total_ms'])} "
            f"(참고용, 아래 어떤 평균에도 포함되지 않음)"
        )

    if args.only:
        add(f"- **주의**: `--only {args.only}`로 일부 문항만 실행했다. 고정 질문셋 전체 비교에는 사용할 수 없다.")

    if args.note:
        add(f"- 비고: {args.note}")

    add("")
    add("### 실제 실행 명령어")
    add("")
    add("```powershell")
    add(args.command_line)
    add("```")
    add("")
    add("---")
    add("")

    # ---- 오류
    add("## 오류 / 특이사항")
    add("")

    if errors:
        for record in errors:
            add(f"- `{record['question_id']}` run {record['run']}: {record['error']}")
    else:
        add("- 없음")

    add("")
    add("---")
    add("")

    # ---- 정확도
    def stage_stats(records, stage_key):
        usable = [
            r for r in records
            if r[stage_key]["available"] and r[stage_key]["hit"] is not None
        ]
        hit_records = [r for r in usable if r[stage_key]["hit"]]

        return usable, hit_records

    oos = [r for r in ok_first if r["out_of_scope"]]
    refused = [r for r in oos if r["auto_refused"]]
    mq_used = [r for r in ok_first if r["multi_query_used"]]

    add("## 정확도 지표 (1회차, 전체 문항)")
    add("")
    add("정답 chunk 추적은 **두 단계로 나누어** 집계한다.")
    add("")
    add(
        "- **검색 단계**: `retrieval_candidates` (server.py가 Re-ranking 전에 확보한 "
        "중복 제거 후 전체 후보). K는 질문별 실제 후보 수이므로 고정값이 아니다."
    )
    add(
        "- **Re-ranking 단계**: `retrieved_docs` (Cross Encoder 이후 최종 Top-K). "
        "K = `rerank_top_k` (일반 3 / 목록형 10)."
    )
    add("")
    add("검색 단계에서 Hit인데 Re-ranking 단계에서 Miss면 Re-ranking이 정답을 떨어뜨린 것이고, 검색 단계부터 Miss면 검색 자체가 실패한 것이다.")
    add("")
    add("| 지표 | 값 |")
    add("|---|---|")
    add(f"| 정상 응답 문항 수 | {len(ok_first)} / {len(first_runs)} |")

    retrieval_usable, retrieval_hits = stage_stats(ok_first, "auto_retrieval_stage")
    rerank_usable, rerank_hits = stage_stats(ok_first, "auto_rerank_stage")

    if retrieval_usable:
        rate = round(len(retrieval_hits) / len(retrieval_usable) * 100, 1)
        add(
            f"| **검색 단계** Hit@검색후보수 (범위 내 {len(retrieval_usable)}문항) | "
            f"{len(retrieval_hits)} / {len(retrieval_usable)} ({rate}%) |"
        )
        add(
            f"| **검색 단계** 정답 chunk 평균 순위 (Hit 문항) | "
            f"{fmt_dash(mean([r['auto_retrieval_stage']['best_rank'] for r in retrieval_hits]))} |"
        )
        add(
            f"| **검색 단계** 평균 후보 수 | "
            f"{fmt(mean([r['auto_retrieval_stage']['k'] for r in ok_first]))} |"
        )
    else:
        add("| **검색 단계** Hit@검색후보수 | 미측정 (응답에 `retrieval_candidates` 없음) |")
        add("| **검색 단계** 정답 chunk 평균 순위 | 미측정 |")
        add("| **검색 단계** 평균 후보 수 | 미측정 |")

    if rerank_usable:
        rate = round(len(rerank_hits) / len(rerank_usable) * 100, 1)
        add(
            f"| **Re-ranking 단계** Hit@rerank_top_k (범위 내 {len(rerank_usable)}문항) | "
            f"{len(rerank_hits)} / {len(rerank_usable)} ({rate}%) |"
        )
        add(
            f"| **Re-ranking 단계** 정답 chunk 평균 순위 (Hit 문항) | "
            f"{fmt_dash(mean([r['auto_rerank_stage']['best_rank'] for r in rerank_hits]))} |"
        )
    else:
        add("| **Re-ranking 단계** Hit@rerank_top_k | 미측정 |")
        add("| **Re-ranking 단계** 정답 chunk 평균 순위 | 미측정 |")

    # 검색은 성공했는데 Re-ranking에서 탈락한 문항
    dropped = [
        r for r in ok_first
        if r["auto_retrieval_stage"]["hit"] and r["auto_rerank_stage"]["hit"] is False
    ]

    if retrieval_usable:
        add(f"| Re-ranking에서 정답 chunk 탈락 | {len(dropped)}문항 |")

    if ok_first:
        mq_rate = round(len(mq_used) / len(ok_first) * 100, 1)
        add(f"| Multi Query 실행 비율 | {len(mq_used)} / {len(ok_first)} ({mq_rate}%) |")
    else:
        add("| Multi Query 실행 비율 | 미측정 |")

    if oos:
        add(f"| 문서 범위 밖 질문 거절 (문자열 자동 판정) | {len(refused)} / {len(oos)} |")
    else:
        add("| 문서 범위 밖 질문 거절 | 미측정 |")

    add("")

    if dropped:
        add("Re-ranking에서 정답 chunk가 탈락한 문항: " + ", ".join(
            f"`{r['question_id']}`(검색 {r['auto_retrieval_stage']['best_rank']}위)"
            for r in dropped
        ))
        add("")

    # 유형별
    add("### 유형별 집계 (1회차)")
    add("")
    add("| 유형 | 문항 수 | 검색 Hit | 검색 순위 | 재랭킹 Hit | 재랭킹 순위 | Multi Query 실행 | 평균 total_ms |")
    add("|---|---|---|---|---|---|---|---|")

    seen_types = []
    for record in ok_first:
        if record["type"] not in seen_types:
            seen_types.append(record["type"])

    for type_name in seen_types:
        group = [r for r in ok_first if r["type"] == type_name]
        cells = []

        for stage_key in ("auto_retrieval_stage", "auto_rerank_stage"):
            usable, hit_records = stage_stats(group, stage_key)
            cells.append(f"{len(hit_records)} / {len(usable)}" if usable else "해당 없음")
            cells.append(fmt_dash(mean([r[stage_key]["best_rank"] for r in hit_records])))

        add(
            f"| {type_name} | {len(group)} | " + " | ".join(cells) + " | "
            f"{len([r for r in group if r['multi_query_used']])} / {len(group)} | "
            f"{fmt(mean([r['total_ms'] for r in group]))} |"
        )

    add("")
    add("---")
    add("")

    # ---- 시간 지표
    add(f"## 시간 지표 (대표 {len(timing_ids)}문항 × {args.repeat}회)")
    add("")
    add("| 질문 ID | 지표 | " + " | ".join(f"{i}회차" for i in range(1, args.repeat + 1)) + " | 평균 |")
    add("|---" * (args.repeat + 3) + "|")

    metric_keys = [
        ("retrieval_ms", "retrieval_ms"),
        ("reranking_ms", "reranking_ms"),
        ("gpt_ms", "gpt_ms"),
        ("total_ms", "total_ms"),
    ]

    for question_id in timing_ids:
        id_runs = sorted(
            [r for r in runs if r["question_id"] == question_id and "error" not in r],
            key=lambda r: r["run"]
        )
        by_run = {r["run"]: r for r in id_runs}

        for key, label in metric_keys:
            cells = []
            for run_index in range(1, args.repeat + 1):
                record = by_run.get(run_index)
                cells.append(fmt(record.get(key) if record else None))
            average = mean([by_run[i].get(key) for i in by_run])
            add(f"| `{question_id}` | {label} | " + " | ".join(cells) + f" | **{fmt(average)}** |")

    add("")
    add("### 대표 문항 평균 (회차 전체 기준)")
    add("")
    add("| 지표 | 평균 |")
    add("|---|---|")

    timing_runs = [r for r in runs if r["question_id"] in timing_ids and "error" not in r]

    for key, label in metric_keys:
        add(f"| 평균 {label} | {fmt(mean([r.get(key) for r in timing_runs]))} |")

    add(f"| 평균 multi_query_ms | {fmt(mean([r.get('multi_query_ms') for r in timing_runs]))} |")
    add("")
    add(
        "> 목록형 문항은 `retrieval_top_k=15 / rerank_top_k=10`, 그 외는 `8 / 3`이므로 "
        "**유형 간 시간 비교는 하지 않는다.** 비교는 항상 동일 질문 ID × 방식 간으로만 수행한다."
    )
    add("")
    add("### 참고 — 1회차 전체 문항 평균")
    add("")
    add("| 지표 | 평균 |")
    add("|---|---|")

    for key, label in metric_keys:
        add(f"| 평균 {label} | {fmt(mean([r.get(key) for r in ok_first]))} |")

    add("")
    add("---")
    add("")

    # ---- 질문별 상세
    def hit_cell(stage):
        if not stage["available"]:
            return "미측정"

        if stage["hit"] is None:
            return "해당 없음"

        return "O" if stage["hit"] else "X"

    def rank_cell(stage):
        if not stage["available"]:
            return "미측정"

        return fmt_dash(stage["best_rank"])

    add("## 질문별 단계별 정답 chunk 추적 (1회차)")
    add("")
    add(
        "| ID | 유형 | 검색 후보 수 | 검색 Hit | 검색 순위 | 재랭킹 후보 수 | "
        "최종 Top-K | 재랭킹 Hit | 재랭킹 순위 |"
    )
    add("|---" * 9 + "|")

    for record in first_runs:
        if "error" in record:
            add(f"| `{record['question_id']}` | {record['type']} | 오류 |" + " |" * 6)
            continue

        retrieval_stage = record["auto_retrieval_stage"]
        rerank_stage = record["auto_rerank_stage"]

        add(
            f"| `{record['question_id']}` | {record['type']} | "
            f"{fmt(record['retrieval_candidate_count'])} | "
            f"{hit_cell(retrieval_stage)} | {rank_cell(retrieval_stage)} | "
            f"{fmt(record['rerank_candidate_count'])} | "
            f"{fmt(record['final_context_count'])} | "
            f"{hit_cell(rerank_stage)} | {rank_cell(rerank_stage)} |"
        )

    add("")
    add("---")
    add("")

    add("## 질문별 실행 조건 및 시간 (1회차)")
    add("")
    add(
        "| ID | 선택 Collection | top_k | MQ | 기대 항목 | 누락 항목 | "
        "retrieval_ms | rerank_ms | gpt_ms | total_ms |"
    )
    add("|---" * 10 + "|")

    for record in first_runs:
        if "error" in record:
            add(f"| `{record['question_id']}` | 오류 |" + " |" * 8)
            continue

        items = record["auto_items"]

        if items["total"] is None:
            items_cell = "-"
        else:
            items_cell = f"{items['matched']} / {items['total']}"

        add(
            f"| `{record['question_id']}` | "
            f"{md_escape(record['selected_collections'])} | "
            f"{fmt(record['retrieval_top_k'])} | "
            f"{'O' if record['multi_query_used'] else 'X'} | {items_cell} | "
            f"{md_escape(', '.join(items['missing'])) or '-'} | "
            f"{fmt(record['retrieval_ms'])} | {fmt(record['reranking_ms'])} | "
            f"{fmt(record['gpt_ms'])} | {fmt(record['total_ms'])} |"
        )

    add("")
    add(
        "> `기대 항목` / `누락 항목`은 questions.json의 `expected_items` 문자열 포함 검사 결과이며 "
        "**자동 보조 지표**이다. 최종 정답 여부와 정보 누락은 아래 수동 판정표에서 사람이 확정한다."
    )
    add("")
    add("---")
    add("")

    # ---- 검색 근거
    candidate_preview = 10

    add("## 검색 근거 (1회차)")
    add("")
    add(
        f"검색 단계는 상위 {candidate_preview}건과 정답 chunk에 해당하는 건만 표시한다"
        f"(전체는 raw.json의 `retrieval_candidates`)."
    )
    add("")

    for record in first_runs:
        if "error" in record:
            continue

        add(f"### `{record['question_id']}` {md_escape(record['question'])}")
        add("")

        expected_keys = build_expected_keys(questions.get(record["question_id"], {}))
        candidates = record["retrieval_candidates"]

        add(f"**검색 단계 (Re-ranking 전, 후보 {fmt(record['retrieval_candidate_count'])}건)**")
        add("")

        if not candidates:
            add("- 미측정 (응답에 `retrieval_candidates` 없음)")
        else:
            add("| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |")
            add("|---|---|---|---|---|---|")

            shown = 0
            skipped = 0

            for doc in candidates:
                is_expected = (doc["collection"], doc["chunk_index"]) in expected_keys

                if doc["rank"] > candidate_preview and not is_expected:
                    skipped += 1
                    continue

                add(
                    f"| {doc['rank']} | {doc['collection']} | {doc['chunk_index']} | "
                    f"{fmt(doc['score'])} | {'O' if doc['passed_to_reranker'] else 'X'} | "
                    f"{'O' if is_expected else ''} |"
                )
                shown += 1

            if skipped:
                add(f"| ... | 이하 {skipped}건 생략 | | | | |")

        add("")
        add(f"**Re-ranking 단계 (최종 Top-{fmt(record['final_context_count'])})**")
        add("")
        add("| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |")
        add("|---|---|---|---|---|---|")

        for doc in record["retrieved_docs"]:
            is_expected = (doc["collection"], doc["chunk_index"]) in expected_keys
            add(
                f"| {doc['rank']} | {doc['collection']} | {doc['chunk_index']} | "
                f"{fmt(doc['retriever_score'])} | {fmt(doc['rerank_score'])} | "
                f"{'O' if is_expected else ''} |"
            )

        add("")

    add("---")
    add("")

    # ---- 답변 전문
    add("## 답변 전문 (1회차)")
    add("")

    for record in first_runs:
        question = questions.get(record["question_id"], {})
        add(f"### `{record['question_id']}` ({record['type']})")
        add("")
        add(f"- 질문: {record['question']}")
        add(f"- 기대 답변 요지: {question.get('expected_summary', '')}")

        if "error" in record:
            add(f"- 결과: 오류 — {record['error']}")
            add("")
            continue

        add(f"- 출처(source): {', '.join(record['source']) if record['source'] else '없음'}")
        add(f"- Multi Query: {'실행' if record['multi_query_used'] else '미실행'}")

        if record["multi_queries"]:
            add(f"- 생성된 추가 질문: {' / '.join(md_escape(q) for q in record['multi_queries'])}")

        if record["out_of_scope"]:
            add(f"- 거절 여부(문자열 자동 판정): {'거절' if record['auto_refused'] else '거절 안 함'}")

        add("- 답변:")
        add("")
        add("```text")
        add(record["answer"])
        add("```")
        add("")

    add("---")
    add("")

    # ---- 수동 판정표
    add("## 수동 판정표 (사람이 채운다)")
    add("")
    add("자동 집계로 대체할 수 없는 항목이다. 위 답변 전문을 보고 직접 채운다.")
    add("")
    add("| ID | 정답 여부 | 정보 누락 | Hallucination | 출처 정확성 | 비고 |")
    add("|---|---|---|---|---|---|")

    for record in first_runs:
        add(f"| `{record['question_id']}` | | | | | |")

    add("")
    add(f"- raw 데이터: `{Path(args.out_dir).name}/{args.config}_raw.json`")
    add("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------- main


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="RAG 고정 질문셋 평가 러너 (server.py /chat 호출)"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="결과 파일 이름에 쓰이는 설정 이름 (예: baseline, routing, hybrid)"
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="시간 지표 대표 문항의 총 실행 횟수 (기본 1). 전체 문항은 항상 1회만 실행한다."
    )
    parser.add_argument(
        "--questions-file",
        default=str(DEFAULT_QUESTIONS),
        help=f"질문셋 JSON 경로 (기본 {DEFAULT_QUESTIONS})"
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help=f"결과 저장 디렉터리 (기본 {DEFAULT_OUT_DIR})"
    )
    parser.add_argument(
        "--api-base",
        # .env를 읽지 않고 os.environ만 참조한다.
        default=os.environ.get("EVAL_API_BASE", "http://127.0.0.1:8000"),
        help="FastAPI 주소 (기본 http://127.0.0.1:8000, 환경변수 EVAL_API_BASE로 변경 가능)"
    )
    parser.add_argument("--endpoint", default="/chat", help="호출 엔드포인트 (기본 /chat)")
    parser.add_argument("--timeout", type=int, default=180, help="요청 timeout 초 (기본 180)")
    parser.add_argument("--sleep", type=float, default=0.0, help="요청 간 대기 초 (기본 0)")
    parser.add_argument(
        "--only",
        default="",
        help="특정 질문 ID만 실행 (쉼표 구분). 지정하면 전체 문항 1회 실행 대상이 이 목록으로 제한된다."
    )
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help=(
            "본 측정 전 워밍업 호출을 생략한다. 기본값은 워밍업 1회 수행이며, "
            "그 결과는 집계에서 제외된다(ko-reranker 모델 로딩·첫 임베딩 호출로 1회차가 이상치가 되는 것을 막기 위함)."
        )
    )
    parser.add_argument(
        "--reranker",
        default="Dongjin-kr/ko-reranker (Cross Encoder, llm/reranker.py)",
        help="테스트 조건에 기록할 Re-ranker 설명"
    )
    parser.add_argument("--note", default="", help="테스트 조건에 함께 기록할 비고 한 줄")

    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)

    if args.repeat < 1:
        print("[ERROR] --repeat은 1 이상이어야 합니다.")
        return 1

    args.command_line = "python " + " ".join(
        ["scripts/eval_run.py"] + [quote_arg(a) for a in argv]
    )

    data = load_questions(args.questions_file)

    questions = data["questions"]

    if args.only:
        wanted = [q.strip() for q in args.only.split(",") if q.strip()]
        questions = [q for q in questions if q["id"] in wanted]

        if not questions:
            print(f"[ERROR] --only에 해당하는 질문이 없습니다 : {args.only}")
            return 1

    timing_ids = [
        question_id
        for question_id in data.get("timing_question_ids", [])
        if any(q["id"] == question_id for q in questions)
    ]

    args.timing_ids = timing_ids

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    runs = []

    total_calls = len(questions) + len(timing_ids) * (args.repeat - 1)
    call_index = 0

    print("=" * 80)
    print(f"config       : {args.config}")
    print(f"api          : {args.api_base.rstrip('/')}{args.endpoint}")
    print(f"질문 수      : {len(questions)} (1회 실행)")
    print(f"시간 대표    : {len(timing_ids)}문항 × {args.repeat}회")
    print(f"워밍업       : {'미수행 (--no-warmup)' if args.no_warmup else '1회 (집계 제외)'}")
    print(f"총 호출 횟수 : {total_calls}{'' if args.no_warmup else ' + 워밍업 1회'}")
    print("=" * 80)

    # 워밍업 : ko-reranker 모델 로딩과 첫 임베딩 호출을 본 측정에서 제외한다.
    warmup = None

    if not args.no_warmup:
        warmup_question = data.get("warmup_question")

        if not warmup_question:
            print("[WARN] questions.json에 warmup_question이 없어 워밍업을 생략합니다.")
        else:
            print(f"[워밍업] {warmup_question} ...", flush=True)
            warmup = run_once(
                {
                    "id": "__warmup__",
                    "type": "워밍업",
                    "question": warmup_question,
                    "expected": []
                },
                0,
                args.api_base,
                args.endpoint,
                args.timeout,
                data
            )

            if "error" in warmup:
                print(f"    ERROR: {warmup['error']}")
            else:
                print(f"    total_ms={warmup['total_ms']} (집계 제외)")

            print("-" * 80)

    args.warmup = warmup

    # 1회차 : 전체 문항
    for question in questions:
        call_index += 1
        print(f"[{call_index}/{total_calls}] run 1  {question['id']} ...", flush=True)
        record = run_once(question, 1, args.api_base, args.endpoint, args.timeout, data)
        runs.append(record)

        if "error" in record:
            print(f"    ERROR: {record['error']}")
        else:
            print(f"    total_ms={record['total_ms']}  MQ={record['multi_query_used']}")

        if args.sleep:
            time.sleep(args.sleep)

    # 2회차 이후 : 시간 지표 대표 문항만
    by_id = {q["id"]: q for q in questions}

    for run_index in range(2, args.repeat + 1):
        for question_id in timing_ids:
            call_index += 1
            question = by_id[question_id]
            print(f"[{call_index}/{total_calls}] run {run_index}  {question_id} ...", flush=True)
            record = run_once(
                question, run_index, args.api_base, args.endpoint, args.timeout, data
            )
            runs.append(record)

            if "error" in record:
                print(f"    ERROR: {record['error']}")
            else:
                print(f"    total_ms={record['total_ms']}")

            if args.sleep:
                time.sleep(args.sleep)

    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    raw_path = out_dir / f"{args.config}_raw.json"
    summary_path = out_dir / f"{args.config}_summary.md"

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": args.config,
                "started_at": started_at,
                "finished_at": finished_at,
                "command_line": args.command_line,
                "api_base": args.api_base,
                "endpoint": args.endpoint,
                "repeat": args.repeat,
                "questions_file": args.questions_file,
                "questions_version": data.get("version"),
                "question_count": len(questions),
                "timing_question_ids": timing_ids,
                "reranker": args.reranker,
                "note": args.note,
                # 워밍업은 집계에서 제외하기 위해 runs와 분리해 저장한다.
                "warmup": args.warmup,
                "runs": runs,
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    write_summary(summary_path, data, runs, args, started_at, finished_at)

    error_count = len([r for r in runs if "error" in r])

    print("=" * 80)
    print(f"raw     : {raw_path}")
    print(f"summary : {summary_path}")
    print(f"오류    : {error_count}건")
    print("=" * 80)

    return 1 if error_count == len(runs) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
