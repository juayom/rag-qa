from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time

from vectorstore.chroma_store import get_index
from vectorstore.retriever import get_retriever
from vectorstore.embedding import get_embedding_model
from llm.multi_query import generate_multi_queries
from llm.reranker import rerank
from llm.openai_llm import generate_answer


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedding Model, Index, Retriever는 서버 시작 시 한 번만 생성
embed_model = get_embedding_model()
index = get_index(embed_model)
retriever = get_retriever(index, top_k=8)


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "RAG Server Running"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    start_time = time.perf_counter()
    question = request.question.strip()

    if question == "":
        return {
            "answer": "질문을 입력해주세요."
        }

    # Multi Query 생성
    queries = generate_multi_queries(question)

    print("=" * 80)
    print("Multi Query")
    print("=" * 80)

    for q in queries:
        print(q)

    # Retrieval
    all_results = []

    for q in queries:

        results = retriever.retrieve(q)

        for node in results:
            all_results.append({
                "document": node.text,
                "metadata": node.metadata,
                "score": node.score
            })

    # 중복 제거
    unique_results = {}

    for item in all_results:

        key = (
            item["metadata"]["source"],
            item["metadata"]["chunk_index"]
        )

        if key not in unique_results:
            unique_results[key] = item

        elif item["score"] > unique_results[key]["score"]:
            unique_results[key] = item


    # Reranker
    top_results = rerank(
        question,
        list(unique_results.values()),
        top_k=3
    )

    # 결과 정리
    documents = []
    metadatas = []
    rerank_scores = []

    for item in top_results:
        documents.append(item["document"])
        metadatas.append(item["metadata"])
        rerank_scores.append(item["score"])

    # Retriever 결과
    retrieved_docs = []

    for i, item in enumerate(top_results):
        retrieved_docs.append({
            "rank": i + 1,
            "file": item["metadata"]["source"],
            "splitter": item["metadata"]["splitter"],
            "chunk": item["metadata"]["chunk_index"],

            # Retriever 점수
            "retriever_score": round(
                item["retriever_score"],
                4
            ) if item["retriever_score"] is not None else None,

            # CrossEncoder 점수
            "rerank_score": round(
                item["score"],
                4
            ),

            "text": item["document"]
        })

    # GPT
    answer = generate_answer(
        question,
        documents
    )

    response_time = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    # 출처
    sources = []

    for meta in metadatas:
        if meta["source"] not in sources:
            sources.append(meta["source"])


    return {
        "question": question,
        "queries": queries,
        "answer": answer,
        "sources": sources,
        "retrieved_docs": retrieved_docs,
        "retrieved_count": len(retrieved_docs),
        "response_time_ms": response_time,
        "top_rerank_score":
            round(rerank_scores[0], 4)
            if rerank_scores else None

    }