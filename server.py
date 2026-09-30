from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time

from vectorstore.qdrant_store import COLLECTION_NAMES, get_index, get_qdrant_client
from vectorstore.retriever import (
    get_dynamic_top_k,
    get_rerank_candidate_limit,
    get_rerank_top_k,
    get_retriever,
)
from vectorstore.embedding import get_embedding_model
from vectorstore.routing import (
    build_collection_vectors,
    select_collections,
)
from vectorstore.keyword import (
    SEARCH_MODE,
    build_keyword_index,
    merge_candidates,
)
from llm.multi_query import (
    MULTI_QUERY_MODE,
    generate_multi_queries,
    should_run_multi_query,
)
from llm.reranker import RERANKER_MODE, RERANKER_MODEL_NAME, rerank
from llm.openai_llm import generate_answer, is_refusal


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedding Model, Index는 서버 시작 시 한 번만 생성
embed_model = get_embedding_model()
indexes = {
    collection_name: get_index(embed_model, collection_name)
    for collection_name in COLLECTION_NAMES
}

# Collection Routing용 설명문 임베딩도 서버 시작 시 한 번만 생성한다.
collection_vectors = build_collection_vectors(embed_model)

# Keyword Search용 BM25 색인. 기존 dense 인덱스는 건드리지 않고 본문만 읽어 만든다.
keyword_index = build_keyword_index(get_qdrant_client(), SEARCH_MODE)

print(f"[INFO] Multi Query : MULTI_QUERY_MODE={MULTI_QUERY_MODE}")
print(
    f"[INFO] Re-ranker : RERANKER_MODE={RERANKER_MODE} / "
    f"model={RERANKER_MODEL_NAME or '없음 (Retriever 점수 순서 그대로)'}"
)

if keyword_index is None:
    print(f"[INFO] Keyword 색인 미구축 (SEARCH_MODE={SEARCH_MODE})")
else:
    print(
        f"[INFO] Keyword 색인 구축 완료 : chunk {len(keyword_index.chunks)}개 / "
        f"SEARCH_MODE={SEARCH_MODE} / tokenizer={keyword_index.tokenizer_name}"
    )


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

    # Collection Routing
    routing_start = time.perf_counter()
    selected_collections, routing_scores, routing_fallback = select_collections(
        question,
        embed_model,
        collection_vectors
    )
    routing_time = time.perf_counter() - routing_start

    retrievers = [
        get_retriever(indexes[collection_name], top_k=retrieval_top_k)
        for collection_name in selected_collections
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

    # Multi Query 실행 여부.
    # adaptive(기본값)는 기존과 같이 1차 검색 결과가 부족한 경우에만 수행
    if should_run_multi_query(initial_nodes, rerank_top_k):
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

    # Keyword Search (BM25)
    # dense가 생성 질의까지 검색하므로 Keyword도 원 질문 + 생성 질의를 함께 씀
    keyword_start = time.perf_counter()
    keyword_hits = []

    if keyword_index is not None:
        keyword_hits = keyword_index.search(
            [question] + additional_queries,
            selected_collections
        )

    keyword_time = time.perf_counter() - keyword_start

    print("=" * 80)
    print(f"Re-ranker: {RERANKER_MODE} ({RERANKER_MODEL_NAME or '미사용'})")
    print(f"Search Mode: {SEARCH_MODE}", end="")
    print(f" (tokenizer={keyword_index.tokenizer_name})" if keyword_index else "")
    print(f"Collection Routing: {', '.join(selected_collections)}")
    if routing_fallback:
        print(f"  fallback: {routing_fallback}")
    print(f"  scores: {routing_scores}")
    print(
        f"Multi Query [{MULTI_QUERY_MODE}]: "
        f"{'실행' if multi_query_used else '미실행'}"
    )
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


    # 검색 방식에 따라 후보와 순서를 정함
    # SEARCH_MODE="semantic"이면 Retriever 점수 내림차순으로, 기존과 동일
    retrieval_candidates = merge_candidates(
        list(unique_results.values()),
        keyword_hits,
        SEARCH_MODE
    )

    # 점수가 높은 후보만 Cross Encoder에 전달
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

            # Keyword Search(BM25) 결과 (semantic 모드에서는 None)
            "keyword_rank": item.get("keyword_rank"),
            "keyword_score": item.get("keyword_score"),

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
    refused = is_refusal(answer)
    sources = []

    if not refused:
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
        "multi_query_mode": MULTI_QUERY_MODE,
        "multi_query_used": multi_query_used,
        "reranker_mode": RERANKER_MODE,
        "reranker_model": RERANKER_MODEL_NAME,
        "search_mode": SEARCH_MODE,
        "bm25_tokenizer": (
            keyword_index.tokenizer_name if keyword_index is not None else None
        ),
        "keyword_candidate_count": len(keyword_hits),
        "selected_collections": selected_collections,
        "routing_scores": routing_scores,
        "routing_fallback": routing_fallback,
        "retrieval_top_k": retrieval_top_k,
        "retrieval_candidate_count": len(retrieval_candidates),
        "retrieval_candidates": retrieval_candidate_docs,
        "rerank_candidate_count": len(rerank_candidates),
        "answer": answer,
        "refused": refused,
        "sources": sources,
        "retrieved_docs": retrieved_docs,
        "retrieved_count": len(retrieved_docs),
        "response_time_ms": response_time,
        "timings_ms": {
            "routing": round(routing_time * 1000, 2),
            "keyword": round(keyword_time * 1000, 2),
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
