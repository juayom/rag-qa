"""Collection Routing (PLAN 3.2)

질문과 Collection 설명문의 임베딩 코사인 유사도로 검색할 Collection을 고른다.
Routing을 위한 별도 LLM 호출은 하지 않는다.

단일 선택이 아니라 다중 선택이다. C-03처럼 두 Collection의 근거를 동시에
요구하는 질문은 단일 선택이면 반드시 실패하기 때문이다.
"""

import math

from vectorstore.qdrant_store import COLLECTION_NAMES


# Routing on/off 스위치.
# False면 항상 COLLECTION_NAMES 전체를 원래 순서 그대로 반환하므로
# Routing 미적용 기준선(현재 동작)이 그대로 재현된다. 비교 측정용이다.
ROUTING_ENABLED = True


# 최고 점수 대비 이 비율 이상인 Collection을 모두 선택한다.
#
# 기본값 0.65는 질문셋 v1.2 30문항 × 3 Collection의 실제 코사인 유사도로 정했다.
#   - 상한을 정하는 것은 C-03(이즈파크 복지 제도 + 타인 빚보증의 신용 영향)이다.
#     이 질문은 ispark + credit 두 Collection의 근거를 동시에 요구하는데,
#     credit / 최고점 비율이 0.7117이라 0.712를 넘기면 credit이 탈락해 반드시 실패한다.
#   - 0.712 이하 구간에서는 정답 Collection 포함률이 27/27로 모두 같고,
#     평균 선택 Collection 수만 달라진다(0.60 -> 1.67개, 0.65 -> 1.59개, 0.70 -> 1.52개).
#   - 0.70은 평균 선택 수가 가장 적지만 C-03 여유가 1.7%뿐이라 질문 문구가 조금만
#     바뀌어도 깨진다. 0.65는 여유 8.8%를 확보하면서 평균 선택 수는 0.07개만 손해다.
#
# 0.72 이상으로 올리면 C-03이 깨진다. 값을 바꾸려면 먼저 재측정할 것.
RELATIVE_THRESHOLD = 0.65


# 최고 점수가 이 값 미만이면 라우터가 판단을 포기하고 전체 Collection을 검색한다.
#
# 이 상수는 "문서 범위 밖 질문 걸러내기"가 아니라 "라우터가 자신 없을 때의 안전장치"다.
# 임베딩 유사도는 주제를 볼 뿐 내용의 존재 여부를 보지 못하므로 범위 밖 판정에 쓸 수 없다.
# 실제로 범위 밖 질문 O-02(0.399) / O-03(0.303)은 주제가 이즈파크라서 정상 문항
# 다수보다 오히려 높게 나온다. 범위 밖 판정은 기존대로 Re-ranking과 GPT 프롬프트가 맡는다.
#
# 기본값 0.18은 명백히 무관한 O-01(0.160, "양자역학의 불확정성 원리")과
# 정상 문항 최저값 H-07(0.177) 사이에 오도록 잡았다.
# fallback은 현재 동작(전체 3개 검색)과 같아 정확도 손실이 없고 속도 이득만 포기하므로,
# 경계에서는 fallback 쪽으로 기우는 값을 택했다.
#
# 주의: 두 threshold 모두 text-embedding-3-small의 코사인 점수 분포에 종속된다.
#       임베딩 모델을 바꾸면 ABSOLUTE_THRESHOLD는 반드시 재측정해야 한다.
#       RELATIVE_THRESHOLD는 비율이라 상대적으로 둔감하지만 함께 확인하는 편이 좋다.
ABSOLUTE_THRESHOLD = 0.18


# 설명문은 PLAN 3.2의 예시를 그대로 사용한다.
COLLECTION_DESCRIPTIONS = {
    "ispark_company_profile":
        "이즈파크 회사 소개, 비전, 사업 영역, 핵심 가치, 솔루션, 연혁, ESG",
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

    # 최고 점수 Collection은 항상 조건을 만족하므로 정상적으로는 비지 않는다.
    # 방어적으로 전체 검색 fallback을 둔다.
    if not selected:
        return list(COLLECTION_NAMES), scores, "no_collection_selected"

    return selected, scores, None
