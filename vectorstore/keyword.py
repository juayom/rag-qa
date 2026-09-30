"""Keyword Search(BM25)와 Semantic / Keyword / Hybrid 병합 (PLAN 3.3)

기존 Qdrant dense 인덱스는 그대로 두고, chunk 본문만 기동 시 한 번 읽어
메모리에 BM25 색인을 만든다. **재인덱싱은 하지 않는다.**

Qdrant의 sparse vector(server-side hybrid)는 collection 생성 시점에만 설정할 수 있어
`recreate_collection`이 불가피하므로 채택하지 않았다. 재인덱싱을 하면
baseline / dedup / routing 측정과의 비교 가능성이 깨진다.
"""

import json
import math
import os
import re
from collections import Counter

from vectorstore.qdrant_store import COLLECTION_NAMES

SEARCH_MODE = os.environ.get("RAG_SEARCH_MODE", "semantic")
VALID_SEARCH_MODES = ("semantic", "keyword", "hybrid")


BM25_TOKENIZER = os.environ.get("RAG_BM25_TOKENIZER", "cjk")


# Reciprocal Rank Fusion 상수.
#
# RRF 점수는 sum(1 / (RRF_K + rank))이다. 60은 RRF를 제안한 논문
# (Cormack et al., 2009)의 기본값이며 이후 사실상 표준으로 쓰인다.
# 값이 클수록 상위 rank의 우위가 완만해져 두 방식의 기여가 고르게 섞이고,
# 작을수록 각 방식의 1위가 강하게 반영된다.
RRF_K = 60


# BM25 표준 파라미터.
BM25_K1 = 1.5
BM25_B = 0.75


_TOKEN_RE = re.compile(r"[가-힣]+|[a-zA-Z]+|[0-9]+")


def _ngrams(text, size):
    if len(text) < size:
        return [text] if text else []

    return [text[i:i + size] for i in range(len(text) - size + 1)]


def _tokenize_cjk(text):
    """영문·숫자는 통째로 남기고 한글만 2-gram으로 쪼갠다.

    Elasticsearch의 cjk_bigram analyzer와 같은 발상이다.
    한국어는 조사가 붙어 공백 분리로는 "신용등급?"처럼 매칭이 전혀 되지 않는데,
    2-gram은 조사 경계를 몰라도 어간을 공유하게 해준다.
    """
    tokens = []

    for match in _TOKEN_RE.findall(text.lower()):
        if re.fullmatch(r"[가-힣]+", match):
            tokens.extend(_ngrams(match, 2) if len(match) >= 2 else [match])
        else:
            tokens.append(match)

    return tokens


def _tokenize_ngram23(text):
    """공백을 모두 지운 문자열의 2-gram과 3-gram을 합쳐 쓴다.

    "코드 26" -> "코드26"이 되어 경계를 넘는 gram("드2", "코드2")이 생기므로
    숫자와 한글이 붙은 표현을 잘 잡는다. 대신 어떤 gram이 걸렸는지 설명하기 어렵다.
    """
    normalized = re.sub(r"\s+", "", text.lower())

    return _ngrams(normalized, 2) + _ngrams(normalized, 3)


TOKENIZERS = {
    "cjk": _tokenize_cjk,
    "ngram23": _tokenize_ngram23,
}


if SEARCH_MODE not in VALID_SEARCH_MODES:
    raise ValueError(
        f"RAG_SEARCH_MODE 값이 올바르지 않다: {SEARCH_MODE!r} "
        f"(가능한 값: {', '.join(VALID_SEARCH_MODES)})"
    )

if BM25_TOKENIZER not in TOKENIZERS:
    raise ValueError(
        f"RAG_BM25_TOKENIZER 값이 올바르지 않다: {BM25_TOKENIZER!r} "
        f"(가능한 값: {', '.join(TOKENIZERS)})"
    )


def get_tokenizer():
    return TOKENIZERS[BM25_TOKENIZER]


class BM25:
    """BM25 Okapi. chunk 26개 규모라 외부 라이브러리를 쓰지 않는다."""

    def __init__(self, documents_tokens, k1=BM25_K1, b=BM25_B):
        self.k1 = k1
        self.b = b
        self.documents = [Counter(tokens) for tokens in documents_tokens]
        self.lengths = [len(tokens) for tokens in documents_tokens]
        self.count = len(documents_tokens)
        self.average_length = (
            sum(self.lengths) / self.count if self.count else 0
        )

        document_frequency = Counter()

        for tokens in documents_tokens:
            document_frequency.update(set(tokens))

        self.idf = {
            token: math.log(1 + (self.count - freq + 0.5) / (freq + 0.5))
            for token, freq in document_frequency.items()
        }

    def score(self, query_tokens, index):
        document = self.documents[index]
        length = self.lengths[index]
        total = 0.0

        for token in query_tokens:
            frequency = document.get(token, 0)

            if not frequency:
                continue

            total += self.idf.get(token, 0.0) * frequency * (self.k1 + 1) / (
                frequency
                + self.k1 * (1 - self.b + self.b * length / (self.average_length or 1))
            )

        return total


def load_chunks(client):
    """Qdrant에서 chunk 본문과 메타데이터만 읽는다. 쓰기는 하지 않는다."""
    chunks = []

    for collection_name in COLLECTION_NAMES:
        offset = None

        while True:
            points, offset = client.scroll(
                collection_name,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            for point in points:
                node = json.loads(point.payload["_node_content"])

                chunks.append({
                    "collection": collection_name,
                    "document": node.get("text", ""),
                    "metadata": {
                        "source": point.payload["source"],
                        "splitter": point.payload["splitter"],
                        "chunk_index": point.payload["chunk_index"],
                        "chunk_length": point.payload.get("chunk_length"),
                    },
                })

            if offset is None:
                break

    chunks.sort(
        key=lambda chunk: (
            COLLECTION_NAMES.index(chunk["collection"]),
            chunk["metadata"]["chunk_index"],
        )
    )

    return chunks


class KeywordIndex:
    """선택된 Collection 조합별로 BM25 색인을 만들어 캐시한다.

    IDF는 대상 문서 집합에 따라 달라지므로, Collection Routing이 고른 조합
    안에서만 계산해야 한다. 조합은 최대 7가지뿐이라 요청 중 lazy 생성해도 충분하다.
    """

    def __init__(self, chunks, tokenize, tokenizer_name=BM25_TOKENIZER):
        self.chunks = chunks
        self.tokenize = tokenize

        # 실제로 색인에 쓰인 토크나이저 이름. 응답의 bm25_tokenizer 필드는 이 값을
        # 쓴다. 모듈 전역 대신 색인 자신이 들고 있어야 보고값과 적용값이 갈라지지 않는다.
        self.tokenizer_name = tokenizer_name
        self._cache = {}

    def _index_for(self, collections):
        key = tuple(collections)

        if key not in self._cache:
            pool = [
                chunk for chunk in self.chunks
                if chunk["collection"] in key
            ]
            self._cache[key] = (
                pool,
                BM25([self.tokenize(chunk["document"]) for chunk in pool]),
            )

        return self._cache[key]

    def search(self, queries, collections):
        """BM25 검색 결과를 점수 내림차순으로 돌려준다.

        `queries`에는 원 질문과 Multi Query가 생성한 질의를 함께 넘긴다.
        dense 쪽이 생성 질의까지 검색해 후보를 합치므로, Keyword 쪽만 원 질문으로
        제한하면 비교가 한쪽에 불리해진다. chunk별로 질의 중 최대 점수를 쓴다.
        """
        pool, bm25 = self._index_for(collections)

        if not pool:
            return []

        best = [0.0] * len(pool)

        for query in queries:
            query_tokens = self.tokenize(query)

            for i in range(len(pool)):
                score = bm25.score(query_tokens, i)

                if score > best[i]:
                    best[i] = score

        ordered = sorted(
            range(len(pool)),
            key=lambda i: best[i],
            reverse=True
        )

        hits = []

        for rank, i in enumerate(ordered, start=1):
            chunk = pool[i]
            hits.append({
                "document": chunk["document"],
                "metadata": chunk["metadata"],
                "keyword_rank": rank,
                "keyword_score": round(best[i], 4),
            })

        return hits


def build_keyword_index(client, mode=None):
    """기동 시 1회 호출한다. semantic 모드에서는 만들지 않는다."""
    if (mode or SEARCH_MODE) == "semantic":
        return None

    chunks = load_chunks(client)

    return KeywordIndex(chunks, get_tokenizer(), BM25_TOKENIZER)


def _candidate_key(item):
    return (item["metadata"]["source"], item["metadata"]["chunk_index"])


def merge_candidates(dense_items, keyword_hits, mode=None):
    """검색 방식에 따라 Re-ranking에 넘길 후보와 그 순서를 정한다.

    반환 항목은 dense 경로와 같은 dict 구조({document, metadata, score})에
    디버그용 keyword_rank / keyword_score를 덧붙인 것이다.
    Keyword로만 걸린 후보는 dense 점수가 없으므로 score가 None이다
    (`llm/reranker.py`가 `item.get("score")`로 읽으므로 문제되지 않는다).

    병합에는 점수를 쓰지 않고 rank만 쓰는 RRF를 사용한다.
    PLAN 3.3이 경계한 것은 점수 정규화 로직이며, RRF는 점수를 쓰지 않고
    rank만 사용하는 융합이므로 PLAN 취지에 어긋나지 않는다.
    """
    mode = mode or SEARCH_MODE

    dense_sorted = sorted(
        dense_items,
        key=lambda item: item["score"],
        reverse=True
    )

    # Keyword를 쓰지 않는다. 본 모듈 도입 이전과 완전히 같은 후보와 순서다.
    if mode == "semantic":
        return dense_sorted

    keyword_by_key = {
        _candidate_key(hit): hit
        for hit in keyword_hits
    }

    # 두 방식의 합집합을 만든다. dense가 top_k에서 놓친 chunk도 후보가 된다.
    merged = {}

    for item in dense_sorted:
        key = _candidate_key(item)
        hit = keyword_by_key.get(key)
        merged[key] = dict(
            item,
            keyword_rank=hit["keyword_rank"] if hit else None,
            keyword_score=hit["keyword_score"] if hit else None,
        )

    for hit in keyword_hits:
        key = _candidate_key(hit)

        if key in merged:
            continue

        merged[key] = {
            "document": hit["document"],
            "metadata": hit["metadata"],
            "score": None,
            "keyword_rank": hit["keyword_rank"],
            "keyword_score": hit["keyword_score"],
        }

    dense_rank = {
        _candidate_key(item): rank
        for rank, item in enumerate(dense_sorted, start=1)
    }

    if mode == "keyword":
        # Keyword 단독. BM25 순위만 쓰고, BM25에 걸리지 않은 후보는 뒤로 보낸다.
        return sorted(
            merged.values(),
            key=lambda item: (
                item["keyword_rank"] is None,
                item["keyword_rank"] or 0,
                dense_rank.get(_candidate_key(item), 10 ** 6),
            )
        )

    if mode != "hybrid":
        raise ValueError(f"알 수 없는 SEARCH_MODE: {mode}")

    def rrf_score(item):
        key = _candidate_key(item)
        total = 0.0

        if key in dense_rank:
            total += 1 / (RRF_K + dense_rank[key])

        if item["keyword_rank"] is not None:
            total += 1 / (RRF_K + item["keyword_rank"])

        return total

    # 동점일 때 순서가 흔들리지 않도록 dense 순위를 보조 키로 쓴다.
    return sorted(
        merged.values(),
        key=lambda item: (
            -rrf_score(item),
            dense_rank.get(_candidate_key(item), 10 ** 6),
            item["keyword_rank"] or 10 ** 6,
        )
    )
