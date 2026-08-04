from pathlib import Path

from preprocessing.pdf_loader import load_pdf
from preprocessing.docx_loader import load_docx
from preprocessing.txt_loader import load_txt


def load_document(file_path: str):

    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return load_pdf(file_path)

    elif suffix == ".docx":
        return load_docx(file_path)

    elif suffix == ".txt":
        return load_txt(file_path)

    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다 : {suffix}")