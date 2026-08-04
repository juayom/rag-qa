from pathlib import Path

from preprocessing.document_loader import load_document
from preprocessing.cleaner import clean_markdown
from preprocessing.chunkers import sentence_split

from vectorstore.embedding import get_embedding_model
from vectorstore.chroma_store import get_index, save_nodes

# Embedding Model
embed_model = get_embedding_model()

# LlamaIndex 생성
index = get_index(embed_model)

DATA_DIR = Path("data")

files = []

for ext in ("*.pdf", "*.docx", "*.txt"):
    files.extend(DATA_DIR.rglob(ext))

print("=" * 80)
print(f"총 {len(files)}개의 문서를 발견했습니다.")
print("=" * 80)

for file_path in files:

    print(f"\n처리 중 : {file_path.name}")

    try:

        text = load_document(str(file_path))

        text = clean_markdown(text)

        nodes = sentence_split(text)

        print(f"Chunk 개수 : {len(nodes)}")

        save_nodes(
            index=index,
            nodes=nodes,
            file_name=file_path.name,
            splitter_name="SentenceSplitter"
        )

        print("저장 완료")

    except Exception as e:

        print(e)

print("\n모든 문서 저장 완료")