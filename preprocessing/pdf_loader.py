import re

import pdfplumber


MIN_DUPLICATE_LENGTH = 10


def _normalize(value):
    """공백을 모두 지운다. 줄바꿈 위치가 달라도 같은 문장으로 비교하기 위함이다."""
    return re.sub(r"\s+", "", value or "")


def _table_cell_lines(table):
    """표 셀 안의 텍스트를 줄 단위로 펼친다."""
    lines = []

    for row in table:
        for cell in row:
            if not cell:
                continue

            for line in str(cell).splitlines():
                line = line.strip()
                if line:
                    lines.append(line)

    return lines


def _is_duplicated_line(line, table_text, cell_lines):
    """이 줄이 같은 페이지의 표에 이미 들어있는지 판정한다."""
    normalized = _normalize(line)

    if not normalized or not table_text:
        return False

    # 충분히 긴 줄은 표 텍스트 안에 들어있기만 하면 중복으로 본다.
    if len(normalized) >= MIN_DUPLICATE_LENGTH:
        return normalized in table_text

    # 짧은 줄은 우연히 부분 문자열로 걸릴 수 있으므로,
    # 표 셀의 한 줄과 완전히 같을 때만 중복으로 본다.
    return normalized in cell_lines


def load_pdf(file_path):
    blocks = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""

            # 표 추출 (텍스트 중복 판정에 먼저 필요하다)
            tables = [table for table in page.extract_tables() if table]

            # 같은 페이지 표의 셀 텍스트를 줄 단위로 모아둔다.
            cell_lines = {
                _normalize(line)
                for table in tables
                for line in _table_cell_lines(table)
            }
            table_text = "".join(
                _normalize(line)
                for table in tables
                for line in _table_cell_lines(table)
            )

            # 줄 경계를 문단 경계로 보존한다.
            # 단, 표에 이미 있는 줄은 중복이므로 건너뛴다.
            for line in page_text.splitlines():
                line = line.strip()
                if not line:
                    continue

                if _is_duplicated_line(line, table_text, cell_lines):
                    continue

                blocks.append(line)

            for table in tables:

                markdown = []
                header = table[0]
                markdown.append(
                    "| " + " | ".join(header) + " |"
                )
                markdown.append(
                    "|" + "---|" * len(header)
                )
                for row in table[1:]:
                    markdown.append(
                        "| " + " | ".join(
                            cell if cell else ""
                            for cell in row
                        ) + " |"
                    )
                blocks.append("\n".join(markdown))

    return "\n\n".join(blocks)
