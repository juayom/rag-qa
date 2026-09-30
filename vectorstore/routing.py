"""Collection Routing (PLAN 3.2)

질문과 Collection 설명문의 임베딩 코사인 유사도로 검색할 Collection을 고른다.
Routing을 위한 별도 LLM 호출은 하지 않는다.

단일 선택이 아니라 다중 선택이다. C-03처럼 두 Collection의 근거를 동시에
요구하는 질문은 단일 선택이면 반드시 실패하기 때문이다.
"""

import math

from vectorstore.qdrant_store import COLLECTION_NAMES


ROUTING_ENABLED = True


RELATIVE_THRESHOLD = 0.65


ABSOLUTE_THRESHOLD = 0.18


COLLECTION_DESCRIPTIONS = {
    "ispark_company_profile":
        "이즈파크 회사 소개, 대표이사, 설립 연도, 본사 위치, "
        "비전, 사업 영역, 핵심 가치, 솔루션, 연혁, ESG",
    "credit_management_guide":
        "신용등급, 신용점수, 연체, 카드, 대출, 보증, 신용관리 요령",
    "due_diligence_reason_codes":
        "퇴사, 이직, 상실사유, 실사유 코드, 권고사직, 계약만료, 실업급여",
}


def build_description_text(collection_name):
    """임베딩에 넣을 설명문을 만든다.

    PLAN 3.2 예시와 같이 Collection 이름 줄을 포함한다.
    이름을 빼고 키워드 줄만 임베딩하면 30문항 중 S-01 / H-04 / H-05 / C-03의
    최고점 Collection이 기대값과 어긋난다(23/27). 이름 줄을 포함하면 27/27이 된다.
    Collection 이름 자체가 의미를 담고 있어 임베딩에 실질적인 신호를 더하기 때문이다.
    """
    return f"{collection_name}\n- {COLLECTION_DESCRIPTIONS[collection_name]}"


def build_collection_vectors(embed_model):
    """Collection 설명문 임베딩을 서버 기동 시 1회 계산해 캐시한다.

    Routing이 꺼져 있으면 임베딩 호출 자체를 하지 않는다.
    """
    if not ROUTING_ENABLED:
        return {}

    return {
        collection_name: embed_model.get_text_embedding(
            build_description_text(collection_name)
        )
        for collection_name in COLLECTION_NAMES
        if collection_name in COLLECTION_DESCRIPTIONS
    }


def cosine_similarity(left, right):
    dot = sum(x * y for x, y in zip(left, right))
    left_norm = math.sqrt(sum(x * x for x in left))
    right_norm = math.sqrt(sum(y * y for y in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (left_norm * right_norm)


def select_collections(question, embed_model, collection_vectors):
    """검색할 Collection을 고른다.

    반환값: (선택된 Collection 이름 리스트, 점수 dict, fallback 사유 또는 None)

    선택 결과는 항상 COLLECTION_NAMES 순서로 정렬한다.
    후보 정렬이 stable sort이므로 점수가 같을 때 Collection 순서가 최종 결과에
    영향을 준다. 순서를 고정해야 측정이 재현된다.
    """
    if not ROUTING_ENABLED:
        return list(COLLECTION_NAMES), {}, "routing_disabled"

    if not collection_vectors:
        return list(COLLECTION_NAMES), {}, "no_description"

    question_vector = embed_model.get_query_embedding(question)

    scores = {
        collection_name: round(
            cosine_similarity(question_vector, description_vector),
            4
        )
        for collection_name, description_vector in collection_vectors.items()
    }

    max_score = max(scores.values())

    # 라우터가 어느 Collection에도 자신이 없다. 전체 검색으로 넘긴다.
    if max_score < ABSOLUTE_THRESHOLD:
        return list(COLLECTION_NAMES), scores, "below_absolute_threshold"

    selected = [
        collection_name
        for collection_name in COLLECTION_NAMES
        if collection_name in scores
        and scores[collection_name] >= max_score * RELATIVE_THRESHOLD
    ]


    if not selected:
        return list(COLLECTION_NAMES), scores, "no_collection_selected"

    return selected, scores, None
