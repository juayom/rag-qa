from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


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
