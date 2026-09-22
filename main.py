import time

from llm.openai_llm import generate_answer
from llm.multi_query import generate_multi_queries

from vectorstore.qdrant_store import COLLECTION_NAMES, get_index

from vectorstore.retriever import (
    get_dynamic_top_k,
    get_rerank_candidate_limit,
    get_rerank_top_k,
    get_retriever,
    is_retrieval_sufficient,
)
from llm.reranker import rerank
from vectorstore.embedding import get_embedding_model

# Index는 프로그램 시작 시 한 번만 생성

embed_model = get_embedding_model()
indexes = [
    get_index(embed_model, collection_name)
    for collection_name in COLLECTION_NAMES
]

print("=" * 80)
print("Retriever 테스트")
print("exit 입력 시 종료")
print("=" * 80)

while True:

    query = input("\n질문 : ").strip()

    if query.lower() == "exit":
        break

    if query == "":
        continue

    start_time = time.perf_counter()
    retrieval_top_k = get_dynamic_top_k(query)
    rerank_top_k = get_rerank_top_k(query)
    rerank_candidate_limit = get_rerank_candidate_limit(query)
    retrievers = [
        get_retriever(index, top_k=retrieval_top_k)
        for index in indexes
    ]

    # 원본 질문으로 1차 검색
    retrieval_start = time.perf_counter()
    all_nodes = []

    for retriever in retrievers:
        all_nodes.extend(retriever.retrieve(query))

    retrieval_time = time.perf_counter() - retrieval_start
    additional_queries = []
    multi_query_time = 0
    multi_query_used = False

    # 검색 결과가 부족할 때만 추가 검색어를 생성한다.
    if not is_retrieval_sufficient(all_nodes, rerank_top_k):
        multi_query_used = True
        multi_query_start = time.perf_counter()
        generated_queries = generate_multi_queries(query)
        multi_query_time = time.perf_counter() - multi_query_start

        for generated_query in generated_queries:
            if generated_query != query and generated_query not in additional_queries:
                additional_queries.append(generated_query)

        additional_retrieval_start = time.perf_counter()
        for generated_query in additional_queries:
            for retriever in retrievers:
                all_nodes.extend(retriever.retrieve(generated_query))
        retrieval_time += time.perf_counter() - additional_retrieval_start

    print("\n" + "=" * 80)
    print(f"Adaptive Multi Query: {'실행' if multi_query_used else '미실행'}")
    print("=" * 80)

    for generated_query in additional_queries:
        print(generated_query)

    # 중복 제거

    unique_nodes = {}

    for node in all_nodes:
        meta = node.metadata
        key = (
            meta["source"],
            meta["chunk_index"]
        )

        score = getattr(node, "score", 0)

        if key not in unique_nodes:
            unique_nodes[key] = node

        elif score > getattr(unique_nodes[key], "score", 0):
            unique_nodes[key] = node

    unique_nodes = list(unique_nodes.values())

    # Reranker 입력 변환 (NodeWithScore -> dict)

    candidates = []

    for node in unique_nodes:

        candidates.append({
            "document": node.text,
            "metadata": node.metadata,
            "score": getattr(node, "score", 0)
        })

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )
    candidates = candidates[:rerank_candidate_limit]

    # Reranker

    rerank_start = time.perf_counter()
    reranked_nodes = rerank(
        query,
        candidates,
        top_k=rerank_top_k
    )
    rerank_time = time.perf_counter() - rerank_start

    # 출력용 데이터

    documents = []
    metadatas = []
    scores = []

    for node in reranked_nodes:

        documents.append(node["document"])
        metadatas.append(node["metadata"])
        scores.append(node["score"])

    print()

    for i in range(len(documents)):

        print("=" * 80)
        print(f"TOP {i+1}")
        print("=" * 80)

        print(f"출처      : {metadatas[i]['source']}")
        print(f"Splitter  : {metadatas[i]['splitter']}")
        print(f"Chunk     : {metadatas[i]['chunk_index']}")
        print(f"Score     : {round(scores[i], 4)}")

        print("-" * 80)
        print(documents[i])
        print()

    # GPT Answer

    gpt_start = time.perf_counter()
    answer = generate_answer(
        query,
        documents
    )
    gpt_time = time.perf_counter() - gpt_start
    total_time = time.perf_counter() - start_time

    print("=" * 80)
    print("최종 답변")
    print("=" * 80)
    print(answer)

    print("\n" + "=" * 80)
    print("응답시간")
    print("=" * 80)
    print(f"Multi Query : {multi_query_time * 1000:.2f} ms")
    print(f"Retrieval   : {retrieval_time * 1000:.2f} ms")
    print(f"Reranking   : {rerank_time * 1000:.2f} ms")
    print(f"GPT         : {gpt_time * 1000:.2f} ms")
    print(f"Total       : {total_time * 1000:.2f} ms")
