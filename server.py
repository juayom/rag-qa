from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time

from vectorstore.qdrant_store import COLLECTION_NAMES, get_index
from vectorstore.retriever import (
    get_dynamic_top_k,
    get_rerank_candidate_limit,
    get_rerank_top_k,
    get_retriever,
    is_retrieval_sufficient,
)
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

# Embedding Model, Index는 서버 시작 시 한 번만 생성
embed_model = get_embedding_model()
indexes = [
    get_index(embed_model, collection_name)
    for collection_name in COLLECTION_NAMES
]


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

    retrieval_top_k = get_dynamic_top_k(question)
    rerank_top_k = get_rerank_top_k(question)
    rerank_candidate_limit = get_rerank_candidate_limit(question)
    retrievers = [
        get_retriever(index, top_k=retrieval_top_k)
        for index in indexes
    ]

    # 원본 질문으로 1차 Retrieval
    retrieval_start = time.perf_counter()
    all_results = []

    initial_nodes = []
    for retriever in retrievers:
        initial_nodes.extend(retriever.retrieve(question))

    retrieval_time = time.perf_counter() - retrieval_start
    additional_queries = []
    multi_query_time = 0
    multi_query_used = False

    # 1차 검색 결과가 부족한 경우에만 Multi Query를 수행한다.
    if not is_retrieval_sufficient(initial_nodes, rerank_top_k):
        multi_query_used = True
        multi_query_start = time.perf_counter()
        generated_queries = generate_multi_queries(question)
        multi_query_time = time.perf_counter() - multi_query_start

        for query in generated_queries:
            if query != question and query not in additional_queries:
                additional_queries.append(query)

        additional_retrieval_start = time.perf_counter()
        for query in additional_queries:
            for retriever in retrievers:
                initial_nodes.extend(retriever.retrieve(query))
        retrieval_time += time.perf_counter() - additional_retrieval_start

    print("=" * 80)
    print(f"Adaptive Multi Query: {'실행' if multi_query_used else '미실행'}")
    print("=" * 80)

    for query in additional_queries:
        print(query)

    for node in initial_nodes:
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


    # Retriever 점수가 높은 후보만 Cross Encoder에 전달한다.
    retrieval_candidates = sorted(
        unique_results.values(),
        key=lambda item: item["score"],
        reverse=True
    )
    rerank_candidates = retrieval_candidates[:rerank_candidate_limit]

    # Reranker
    rerank_start = time.perf_counter()
    top_results = rerank(
        question,
        rerank_candidates,
        top_k=rerank_top_k
    )
    rerank_time = time.perf_counter() - rerank_start

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

    # Re-ranking 전 검색 후보 (평가용 디버그 필드)
    # 검색 성능과 Re-ranking 성능을 분리해 측정하기 위해 중간 결과를 그대로 내보낸다.
    # 파이프라인 동작에는 사용하지 않으며 프론트엔드도 사용하지 않는다.
    retrieval_candidate_docs = []

    for i, item in enumerate(retrieval_candidates):
        retrieval_candidate_docs.append({
            "rank": i + 1,
            "file": item["metadata"]["source"],
            "splitter": item["metadata"]["splitter"],
            "chunk": item["metadata"]["chunk_index"],

            # Retriever 점수
            "score": round(
                item["score"],
                4
            ) if item["score"] is not None else None,

            # Cross Encoder까지 전달된 후보인지 여부
            "passed_to_reranker": i < rerank_candidate_limit,

            "text": item["document"][:200]
        })

    # GPT
    gpt_start = time.perf_counter()
    answer = generate_answer(
        question,
        documents
    )
    gpt_time = time.perf_counter() - gpt_start

    # 출처
    sources = []

    for meta in metadatas:
        if meta["source"] not in sources:
            sources.append(meta["source"])

    response_time = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    return {
        "question": question,
        "queries": additional_queries,
        "multi_query_used": multi_query_used,
        "retrieval_top_k": retrieval_top_k,
        "retrieval_candidate_count": len(retrieval_candidates),
        "retrieval_candidates": retrieval_candidate_docs,
        "rerank_candidate_count": len(rerank_candidates),
        "answer": answer,
        "sources": sources,
        "retrieved_docs": retrieved_docs,
        "retrieved_count": len(retrieved_docs),
        "response_time_ms": response_time,
        "timings_ms": {
            "multi_query": round(multi_query_time * 1000, 2),
            "retrieval": round(retrieval_time * 1000, 2),
            "reranking": round(rerank_time * 1000, 2),
            "gpt": round(gpt_time * 1000, 2),
            "total": response_time
        },
        "top_rerank_score":
            round(rerank_scores[0], 4)
            if rerank_scores else None

    }
