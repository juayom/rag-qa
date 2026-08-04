from docx import Document


def load_docx(file_path: str) -> str:
    """
    DOCX 문서를 Markdown 형태의 문자열로 변환한다.
    표(Table)는 Markdown Table 형태로 변환한다.
    """

    doc = Document(file_path)

    markdown = []

    # 일반 문단
    for para in doc.paragraphs:
        if para.text.strip():
            markdown.append(para.text)

    # 표 처리
    for table in doc.tables:

        rows = []

        for row in table.rows:
            rows.append([cell.text.strip() for cell in row.cells])

        if not rows:
            continue

        # Header
        markdown.append("| " + " | ".join(rows[0]) + " |")
        markdown.append("|" + "|".join(["---"] * len(rows[0])) + "|")

        # Body
        for row in rows[1:]:
            markdown.append("| " + " | ".join(row) + " |")

        markdown.append("")

    return "\n".join(markdown)