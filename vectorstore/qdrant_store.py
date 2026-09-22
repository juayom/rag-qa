import os

from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


load_dotenv()


COLLECTION_NAMES = [
    "ispark_company_profile",
    "credit_management_guide",
    "due_diligence_reason_codes",
]


def get_qdrant_client():
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333")
    )


def reset_collection(collection_name):
    client = get_qdrant_client()

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)


def get_index(embed_model, collection_name):
    vector_store = QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=collection_name
    )

    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model
    )


def save_nodes(index, nodes, file_name, splitter_name):
    insert_nodes = []

    for i, node in enumerate(nodes):
        text_node = TextNode(
            text=node.text,
            metadata={
                "source": file_name,
                "splitter": splitter_name,
                "chunk_index": i + 1,
                "chunk_length": len(node.text)
            }
        )

        insert_nodes.append(text_node)

    index.insert_nodes(insert_nodes)

    print(f"[INFO] 저장 완료 : {file_name}")
