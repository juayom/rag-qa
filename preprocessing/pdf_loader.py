import pdfplumber


def load_pdf(file_path):
    blocks = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""

            # 줄 경계를 문단 경계로 보존한다.
            for line in page_text.splitlines():
                line = line.strip()
                if line:
                    blocks.append(line)

            # 표 추출
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue

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
