from llama_index.core.indices.vector_store import VectorIndexRetriever
import re


DEFAULT_TOP_K = 8
LIST_TOP_K = 15
DEFAULT_RERANK_TOP_K = 3
LIST_RERANK_TOP_K = 10
DEFAULT_RERANK_CANDIDATES = 8
LIST_RERANK_CANDIDATES = 15
MIN_RELEVANT_SCORE = 0.5


def is_list_question(question):
    list_keywords = (
        "전체", "모두", "모든", "전부", "목록", "리스트", "나열", "항목", "종류"
    )
    numbered_list = re.search(
        r"\d+\s*(가지|개|단계|방법|항목|종류|이유|요령)",
        question
    )

    return any(keyword in question for keyword in list_keywords) or bool(numbered_list)


def get_dynamic_top_k(question):
    return LIST_TOP_K if is_list_question(question) else DEFAULT_TOP_K


def get_rerank_top_k(question):
    return LIST_RERANK_TOP_K if is_list_question(question) else DEFAULT_RERANK_TOP_K


def get_rerank_candidate_limit(question):
    return (
        LIST_RERANK_CANDIDATES
        if is_list_question(question)
        else DEFAULT_RERANK_CANDIDATES
    )


def is_retrieval_sufficient(nodes, required_count):
    relevant_count = sum(
        1
        for node in nodes
        if (getattr(node, "score", None) or 0) >= MIN_RELEVANT_SCORE
    )

    return relevant_count >= required_count


def get_retriever(index, top_k=3):

    retriever = index.as_retriever(
        similarity_top_k=top_k
    )

    return retriever
