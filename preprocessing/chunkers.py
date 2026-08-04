from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter


def sentence_split(text):
    document = Document(text=text)

    splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )

    return splitter.get_nodes_from_documents([document])

