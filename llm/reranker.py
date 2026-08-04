from sentence_transformers import CrossEncoder

# 한국어 Cross Encoder
model = CrossEncoder(
    "Dongjin-kr/ko-reranker"
)


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