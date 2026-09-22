from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def table_to_markdown(table):
    rows = [
        [cell.text.strip() for cell in row.cells]
        for row in table.rows
    ]

    if not rows:
        return ""

    markdown = [
        "| " + " | ".join(rows[0]) + " |",
        "|" + "|".join(["---"] * len(rows[0])) + "|"
    ]

    for row in rows[1:]:
        markdown.append("| " + " | ".join(row) + " |")

    return "\n".join(markdown)

def load_docx(file_path: str) -> str:
    """
    DOCX 문서를 Markdown 형태의 문자열로 변환한다.
    표(Table)는 Markdown Table 형태로 변환한다.
    """

    doc = Document(file_path)

    blocks = []

    # 문단과 표의 원래 순서를 유지한다.
    for block in iter_blocks(doc):
        if isinstance(block, Table):
            markdown_table = table_to_markdown(block)
            if markdown_table:
                blocks.append(markdown_table)
            continue

        text = block.text.strip()
        if not text:
            continue

        style_name = block.style.name if block.style else ""

        if style_name.startswith(("Title", "Heading", "제목")):
            text = f"## {text}"
        elif style_name.startswith(("List", "목록")):
            text = f"- {text}"

        blocks.append(text)

    return "\n\n".join(blocks)
