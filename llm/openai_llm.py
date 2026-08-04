from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def generate_answer(question, documents):

    context = "\n\n".join(documents)

    prompt = f"""
당신은 문서 기반 질의응답(RAG) 시스템입니다.

반드시 아래 Context만 이용하여 답변하세요.

=========================
Context
=========================
{context}

=========================
Question
=========================
{question}

=========================
답변 규칙
=========================

1. 반드시 Context 전체를 끝까지 확인한 후 답변하세요.

2. 질문과 가장 관련성이 높은 문장을 먼저 찾으세요.

3. Context 안에 답이 존재하면 반드시 그 내용을 이용하여 답변하세요.

4. Context 여러 곳에 정보가 흩어져 있으면 종합하여 답변하세요.

5. 절대로 외부 지식을 사용하지 마세요.

6. Context에 답이 없는 경우에만
   "제공된 문서에서는 해당 정보를 찾을 수 없습니다."
   라고 답하세요.

7. 답변은 핵심만 2~4문장 정도로 작성하세요.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content":
                "당신은 문서 기반 QA 전문가입니다. "
                "Context에 있는 정보만 이용하여 정확하게 답변하세요."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content