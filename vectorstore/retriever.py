from llama_index.core.indices.vector_store import VectorIndexRetriever


def get_retriever(index, top_k=3):

    retriever = index.as_retriever(
        similarity_top_k=top_k
    )

    return retriever