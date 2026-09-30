"""Re-ranking 방식 스위치 (PLAN 3.5 / GUIDE 8항)

비교 대상은 셋이다.
  current : Dongjin-kr/ko-reranker (현행, 0.6B)
  alt     : Alibaba-NLP/gte-multilingual-reranker-base (306M)
  none    : 재랭킹 없음. Retriever 점수 순서 그대로 Top-K를 자른다.

alt2(dragonkue/bge-reranker-v2-m3-ko, 0.6B)는 코드 경로만 만들어 둔다.
alt가 current보다 품질이 명확히 나쁘게 나오면, 그 원인이 "모델이 작아서"인지
"한국어에 약해서"인지 가르기 위해 그때 측정한다. alt2는 current와 같은 0.6B이면서
한국어에 최적화된 모델이므로, alt2가 current 수준이면 원인은 크기가 아니라 한국어다.
"""

import os

import torch
from sentence_transformers import CrossEncoder



RERANKER_MODE = os.environ.get("RAG_RERANKER", "current")


RERANKER_MODELS = {
    "current": "Dongjin-kr/ko-reranker",
    "alt": "Alibaba-NLP/gte-multilingual-reranker-base",
    "alt2": "dragonkue/bge-reranker-v2-m3-ko",
    "none": None,
}

VALID_RERANKER_MODES = tuple(RERANKER_MODELS)


TRUST_REMOTE_CODE_MODES = {"alt"}


if RERANKER_MODE not in RERANKER_MODELS:
    raise ValueError(
        f"RAG_RERANKER 값이 올바르지 않다: {RERANKER_MODE!r} "
        f"(가능한 값: {', '.join(VALID_RERANKER_MODES)})"
    )


RERANKER_MODEL_NAME = RERANKER_MODELS[RERANKER_MODE]


def _repair_position_ids(cross_encoder):
    """망가진 `position_ids` 버퍼를 복구한다.

    `Alibaba-NLP/gte-multilingual-reranker-base`의 원격 코드는 `position_ids`를
    `persistent=False` 버퍼로 등록한다. 이런 버퍼는 체크포인트에 들어 있지 않아
    최신 transformers의 로딩 경로에서 초기화되지 않은 메모리로 남고,
    forward의 `rope_cos[position_ids]`에서 IndexError가 난다.

    버퍼가 `arange`가 아닌 모듈만 골라 다시 등록한다.
    정상인 모델에서는 아무것도 바꾸지 않으므로 current / alt2에는 영향이 없다.
    """
    repaired = []

    for name, module in cross_encoder.model.named_modules():
        buffer = getattr(module, "position_ids", None)

        if buffer is None or buffer.dim() != 1:
            continue

        expected = torch.arange(buffer.size(0), device=buffer.device)

        if torch.equal(buffer, expected):
            continue

        module.register_buffer("position_ids", expected, persistent=False)
        repaired.append(name)

    return repaired


def load_reranker():
    """서버 기동 시 1회 호출한다. none 모드에서는 모델을 내려받지 않는다."""
    if RERANKER_MODEL_NAME is None:
        return None

    cross_encoder = CrossEncoder(
        RERANKER_MODEL_NAME,
        trust_remote_code=RERANKER_MODE in TRUST_REMOTE_CODE_MODES
    )

    repaired = _repair_position_ids(cross_encoder)

    if repaired:
        print(f"[INFO] position_ids 버퍼 복구 : {', '.join(repaired)}")

    return cross_encoder


# 한국어 Cross Encoder
model = load_reranker()


def rerank(question, candidates, top_k=3):
    """
    candidates 예시
    [
        {
            "document": "...",
            "metadata": {...},
            "score": retrieval_score
        }
    ]
    """
    if model is None:
        passthrough = []

        for item in candidates:
            retriever_score = item.get("score")

            passthrough.append({
                "document": item["document"],
                "metadata": item["metadata"],
                "retriever_score": retriever_score,

                "score": float(retriever_score) if retriever_score is not None else 0.0
            })

        passthrough.sort(key=lambda x: x["score"], reverse=True)

        return passthrough[:top_k]

    # CrossEncoder 입력 생성
    pairs = [
        (question, item["document"])
        for item in candidates
    ]
    # Relevance Score 계산
    scores = model.predict(pairs)

    reranked = []

    for item, score in zip(candidates, scores):

        reranked.append({

            # 기존 정보 유지
            "document": item["document"],
            "metadata": item["metadata"],

            # Retriever 점수(디버깅용)
            "retriever_score": item.get("score"),

            # CrossEncoder 점수
            "score": float(score)

        })
    # CrossEncoder 점수 내림차순
    reranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )
    return reranked[:top_k]
