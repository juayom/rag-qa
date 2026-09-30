from pathlib import Path

from preprocessing.document_loader import load_document
from preprocessing.cleaner import clean_markdown
from preprocessing.chunkers import (
    sentence_split,
    structured_split,
    structured_split_v2,
)

from vectorstore.embedding import get_embedding_model
from vectorstore.qdrant_store import get_index, reset_collection, save_nodes

# Embedding Model
embed_model = get_embedding_model()

DOCUMENT_COLLECTIONS = {
    Path("data/txt/이즈파크 회사 소개서.txt"): "ispark_company_profile",
    Path("data/pdf/현명한 신용관리 요령.pdf"): "credit_management_guide",
    Path("data/docx/실사유 코드.docx"): "due_diligence_reason_codes",
}

print("=" * 80)
print(f"총 {len(DOCUMENT_COLLECTIONS)}개의 문서를 발견했습니다.")
print("=" * 80)

for file_path, collection_name in DOCUMENT_COLLECTIONS.items():

    print(f"\n처리 중 : {file_path.name}")

    try:

        text = load_document(str(file_path))

        text = clean_markdown(text)

        # PDF/DOCX 는 구조 기반 v2 를 쓴다.
        if file_path.suffix.lower() in (".pdf", ".docx"):
            nodes = structured_split_v2(text)
            splitter_name = "StructuredSplitterV2"
        else:
            nodes = sentence_split(text)
            splitter_name = "SentenceSplitter"

        print(f"Chunk 개수 : {len(nodes)}")

        reset_collection(collection_name)
        index = get_index(embed_model, collection_name)

        save_nodes(
            index=index,
            nodes=nodes,
            file_name=file_path.name,
            splitter_name=splitter_name,
            collection_name=collection_name,
            source_type=file_path.suffix.lower().lstrip(".")
        )

        print("저장 완료")

    except Exception as e:

        print(e)

print("\n모든 문서 저장 완료")
