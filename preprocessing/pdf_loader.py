import pdfplumber

def load_pdf(file_path):

    texts = []

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:
            page_text = page.extract_text() or ""
            # 일반 텍스트
            texts.append(page_text)

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
                texts.append("\n".join(markdown))

    return "\n\n".join(texts)