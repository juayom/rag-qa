from llm.openai_llm import generate_answer
from llm.multi_query import generate_multi_queries

from vectorstore.chroma_store import get_index

from vectorstore.retriever import get_retriever
from llm.reranker import rerank
from vectorstore.embedding import get_embedding_model

# Index, Retriever는 프로그램 시작 시 한 번만 생성

embed_model = get_embedding_model()
index = get_index(embed_model)
retriever = get_retriever(index, top_k=8)

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

    # Multi Query 생성
    queries = generate_multi_queries(query)

    print("\n" + "=" * 80)
    print("Multi Query")
    print("=" * 80)

    for q in queries:
        print(q)

    # Retrieval

    all_nodes = []

    for q in queries:
        nodes = retriever.retrieve(q)
        all_nodes.extend(nodes)

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

    # Reranker

    reranked_nodes = rerank(
        query,
        candidates,
        top_k=3
    )

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

    answer = generate_answer(
        query,
        documents
    )

    print("=" * 80)
    print("최종 답변")
    print("=" * 80)
    print(answer)