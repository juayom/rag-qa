import chromadb

from chromadb.config import Settings

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode


# Chroma Collection 생성

def get_chroma_collection():
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(
            anonymized_telemetry=False
        )
    )
    collection = client.get_or_create_collection(
        "rag_collection"
    )

    return collection


# Chroma Collection -> LlamaIndex VectorStoreIndex 생성

def get_index(embed_model):
    collection = get_chroma_collection()
    vector_store = ChromaVectorStore(
        chroma_collection=collection
    )
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    index = VectorStoreIndex(
        [],
        storage_context=storage_context,
        embed_model=embed_model
    )

    return index


# Node 저장

def save_nodes(index, nodes, file_name, splitter_name):

    collection = get_chroma_collection()

    # 기존 데이터 삭제
    try:

        collection.delete(
            where={
                "$and": [
                    {
                        "source": file_name
                    },
                    {
                        "splitter": splitter_name
                    }
                ]
            }
        )

        print(f"[INFO] 기존 데이터 삭제 : {file_name}")

    except Exception:

        print(f"[INFO] 기존 데이터 없음 : {file_name}")

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

    # LlamaIndex Framework 이용 저장
    index.insert_nodes(insert_nodes)

    print(f"[INFO] 저장 완료 : {file_name}")
