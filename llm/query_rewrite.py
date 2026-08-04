from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def rewrite_query(question, retrieved_docs):

    context = "\n\n".join(retrieved_docs)

    prompt = f"""
당신은 RAG 시스템의 Query Rewrite 전문가입니다.

목표는 사용자의 질문을
Vector Database에서 관련 문서를 더 정확하게 검색할 수 있도록
검색 친화적인 형태로 다시 작성하는 것입니다.

========================
규칙

1. 질문의 의미는 변경하지 않는다.

2. Retrieved Context를 참고하여 질문의 대상(Entity), 핵심 키워드 또는 도메인을 추론할 수 있다면 질문에 자연스럽게 반영한다.

3. 검색 성능 향상을 위해 구어체, 축약 표현 또는 모호한 표현은 보다 공식적이고 검색 친화적인 표현으로 변경할 수 있다.

4. Retrieved Context에 존재하지 않는 새로운 정보를 추가하거나 추측하지 않는다.

5. Retrieved Context만으로 판단하기 어려우면 질문을 그대로 유지한다.

6. 질문이 이미 검색에 적합한 형태라면 불필요하게 수정하지 않는다.

7. Rewrite된 질문만 출력한다.

========================
Original Question
{question}

========================
Retrieved Context
{context}

========================
Rewrite Query
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

    return response.choices[0].message.content.strip()