import re


def clean_markdown(text: str) -> str:
    """
    Markdown 문서를 Embedding하기 전에 정리한다.

    - 페이지 번호 제거
    - 연속 공백 제거
    - 연속 빈 줄 제거
    - HTML 태그 제거(<u> 등)
    - 불필요한 기호 제거
    - Markdown 표는 유지
    """

    # HTML 태그 제거
    text = re.sub(r"<.*?>", "", text)

    # 페이지 번호 제거
    text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.MULTILINE)

    # 불필요한 특수문자 제거
    remove_chars = [
        "☞",
        "•"
    ]

    for ch in remove_chars:
        text = text.replace(ch, "")

    cleaned_lines = []

    previous = ""

    for line in text.split("\n"):

        # 양쪽 공백 제거
        line = line.strip()

        # 빈 줄은 하나만 유지
        if line == "":
            if previous == "":
                continue

        cleaned_lines.append(line)
        previous = line

    text = "\n".join(cleaned_lines)

    # 연속 공백 제거
    text = re.sub(r"[ ]{2,}", " ", text)

    return text