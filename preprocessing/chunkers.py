import re

from llama_index.core import Document
from llama_index.core.schema import TextNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.utils import get_tokenizer


def sentence_split(text):
    document = Document(text=text)

    splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )

    return splitter.get_nodes_from_documents([document])


def structured_split(text, chunk_size=512, chunk_overlap=50):
    """문단·제목·표 경계를 우선 보존하여 PDF/DOCX를 분할한다."""
    tokenizer = get_tokenizer()
    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", text)
        if block.strip()
    ]
    chunks = []
    current_blocks = []

    def token_length(value):
        return len(tokenizer(value))

    def append_current():
        if current_blocks:
            chunks.append("\n\n".join(current_blocks))

    for block in blocks:
        if token_length(block) > chunk_size:
            append_current()
            current_blocks = []
            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            long_nodes = splitter.get_nodes_from_documents([Document(text=block)])
            chunks.extend(node.text for node in long_nodes)
            continue

        candidate = "\n\n".join(current_blocks + [block])

        if current_blocks and token_length(candidate) > chunk_size:
            append_current()

            overlap_blocks = []
            overlap_tokens = 0
            for previous_block in reversed(current_blocks):
                previous_tokens = token_length(previous_block)
                if overlap_tokens + previous_tokens > chunk_overlap:
                    break
                overlap_blocks.insert(0, previous_block)
                overlap_tokens += previous_tokens

            current_blocks = overlap_blocks

        current_blocks.append(block)

    append_current()

    return [TextNode(text=chunk) for chunk in chunks]

