from openai import OpenAI
from dotenv import load_dotenv
import os

from vectorstore.retriever import is_retrieval_sufficient, is_retrieval_sufficient_v2

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)



MULTI_QUERY_MODE = os.environ.get("RAG_MULTI_QUERY", "adaptive_v2")

VALID_MULTI_QUERY_MODES = ("adaptive", "adaptive_v2", "off", "on")


# 잘못된 환경변수는 기동 시점에 바로 실패시킨다.
# 요청 처리 중에 터지면 측정이 절반쯤 진행된 뒤에야 알게 된다.
if MULTI_QUERY_MODE not in VALID_MULTI_QUERY_MODES:
    raise ValueError(
        f"RAG_MULTI_QUERY 값이 올바르지 않다: {MULTI_QUERY_MODE!r} "
        f"(가능한 값: {', '.join(VALID_MULTI_QUERY_MODES)})"
    )


def should_run_multi_query(nodes, required_count):
    """Multi Query를 실행할지 판정한다.

    adaptive에서는 기존과 똑같이 `not is_retrieval_sufficient(...)`를 그대로 쓴다.
    판정 기준(`MIN_RELEVANT_SCORE`, `required_count`)은 손대지 않는다.
    """
    if MULTI_QUERY_MODE == "off":
        return False

    if MULTI_QUERY_MODE == "on":
        return True

    if MULTI_QUERY_MODE == "adaptive_v2":
        return not is_retrieval_sufficient_v2(nodes)

    return not is_retrieval_sufficient(nodes, required_count)


def generate_multi_queries(question):

    prompt = f"""
당신은 RAG 시스템의 Multi Query Generator입니다.

사용자의 질문을 다양한 표현으로 다시 작성하여
Vector Database 검색 Recall을 높이는 것이 목표입니다.

규칙

1. 질문의 의미는 절대 변경하지 않는다.

2. 검색될 가능성이 높은 다양한 표현을 생성한다.

3. 동의어, 공식 용어, 구어체 등을 적절히 활용한다.

4. 동일한 의미의 질문만 생성한다.

5. 원본 질문과 중복되지 않는 추가 질문을 최대 3개 생성한다.

6. 질문만 출력한다.
한 줄에 하나씩 출력한다.

Question
---------
{question}

Multi Queries
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    queries = [
        q.strip()
        for q in response.choices[0].message.content.split("\n")
        if q.strip()
    ][:3]

    return queries
