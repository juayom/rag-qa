import re

from llama_index.core import Document
from llama_index.core.schema import TextNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.utils import get_tokenizer


def sentence_split(text):
    document = Document(text=text)

    splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )

    return splitter.get_nodes_from_documents([document])


def structured_split(text, chunk_size=512, chunk_overlap=50):
    """문단·제목·표 경계를 우선 보존하여 PDF/DOCX를 분할한다."""
    tokenizer = get_tokenizer()
    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", text)
        if block.strip()
    ]
    chunks = []
    current_blocks = []

    def token_length(value):
        return len(tokenizer(value))

    def append_current():
        if current_blocks:
            chunks.append("\n\n".join(current_blocks))

    for block in blocks:
        if token_length(block) > chunk_size:
            append_current()
            current_blocks = []
            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            long_nodes = splitter.get_nodes_from_documents([Document(text=block)])
            chunks.extend(node.text for node in long_nodes)
            continue

        candidate = "\n\n".join(current_blocks + [block])

        if current_blocks and token_length(candidate) > chunk_size:
            append_current()

            overlap_blocks = []
            overlap_tokens = 0
            for previous_block in reversed(current_blocks):
                previous_tokens = token_length(previous_block)
                if overlap_tokens + previous_tokens > chunk_overlap:
                    break
                overlap_blocks.insert(0, previous_block)
                overlap_tokens += previous_tokens

            current_blocks = overlap_blocks

        current_blocks.append(block)

    append_current()

    return [TextNode(text=chunk) for chunk in chunks]



# 의미 단위의 시작을 알리는 마커.
#   `## 제목`     DOCX 로더가 Heading/Title 스타일에 붙인 표시
#   `[코드 11]`   DOCX 본문의 코드 제목
#   `①`~`⑳`      PDF 목록 항목

UNIT_MARKER = re.compile(r"^(#{1,6}\s+|\[코드\s*\d+\]|[①-⑳])")


TITLE_ONLY_MAX_LENGTH = 60


def _is_table_block(block):
    return block.lstrip().startswith("|")


def _logical_rows(block):
    """마크다운 표를 논리 행 단위로 끊는다.

    셀 안에 줄바꿈이 들어간 표(PDF 유사 표)가 있어 한 줄 = 한 행이 아니다.
    `|` 로 시작한 행은 `|` 로 끝나는 줄까지를 한 행으로 묶는다.
    """
    rows = []
    current = []

    for line in block.splitlines():
        stripped = line.strip()

        if not current:
            if stripped.startswith("|"):
                current = [line]

                if stripped.endswith("|") and len(stripped) > 1:
                    rows.append("\n".join(current))
                    current = []
            else:
                # 표 앞뒤에 섞여 들어온 비표 줄
                rows.append(line)

            continue

        current.append(line)

        if stripped.endswith("|"):
            rows.append("\n".join(current))
            current = []

    if current:
        rows.append("\n".join(current))

    return [row for row in rows if row.strip()]


def _split_by_marker(segment):
    """세그먼트 안에 목록/제목 마커가 있으면 마커 시작점마다 끊는다.

    마커 줄과 그 뒤 본문이 항상 같은 조각에 남는다.
    """
    units = []
    current = []

    for line in segment.splitlines():
        if current and UNIT_MARKER.match(line.strip()):
            units.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        units.append("\n".join(current))

    return [unit for unit in units if unit.strip()]


def _is_title_only(text):
    lines = [line for line in text.strip().splitlines() if line.strip()]

    return (
        len(lines) == 1
        and len(lines[0].strip()) <= TITLE_ONLY_MAX_LENGTH
        and bool(UNIT_MARKER.match(lines[0].strip()))
    )


def _is_separator_row(text):
    """`|---|---|` 처럼 구분선만 있는 표 행."""
    stripped = text.strip()

    return bool(stripped) and set(stripped) <= set("|-: \t")


def _build_units(text):
    """본문을 의미 단위 리스트로 만든다. 각 단위는 더 쪼개지 않는 것이 원칙이다.

    DOCX 는 `[코드 11]` 제목과 `적용 대상:` / `주의사항:` 본문이 서로 다른 문단이므로,
    마커로 시작한 단위가 다음 마커를 만날 때까지 뒤따르는 문단을 흡수해야 한다.
    그렇게 해야 제목과 본문이 같은 chunk 에 남는다.
    """
    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", text)
        if block.strip()
    ]

    # (표 행 여부, 마커 시작 여부, 본문)
    pieces = []

    for block in blocks:
        if _is_table_block(block):
            for row in _logical_rows(block):
                for unit in _split_by_marker(row):
                    head = unit.strip().splitlines()[0].strip()
                    pieces.append((True, bool(UNIT_MARKER.match(head)), unit))
        else:
            for unit in _split_by_marker(block):
                head = unit.strip().splitlines()[0].strip()
                pieces.append((False, bool(UNIT_MARKER.match(head)), unit))

    units = []
    absorbing = False

    for is_row, is_marker, unit in pieces:
        # 구분선만 있는 행은 직전 단위에 붙인다. 단독 조각으로 남기지 않는다.
        if _is_separator_row(unit) and units:
            units[-1] = units[-1] + "\n" + unit
            continue

        if is_marker:
            units.append(unit)
            absorbing = not is_row
            continue

        # 마커 단위 뒤에 오는 일반 문단은 그 단위에 흡수시킨다.
        if absorbing and not is_row and units:
            units[-1] = units[-1] + "\n\n" + unit
            continue

        units.append(unit)
        absorbing = False

    # 그래도 제목만 남은 단위가 있으면 다음 단위와 합친다.
    merged = []

    for unit in units:
        if merged and _is_title_only(merged[-1]):
            merged[-1] = merged[-1] + "\n" + unit
        else:
            merged.append(unit)

    return merged


def structured_split_v2(text, chunk_size=512, chunk_overlap=50):
    """제목·목록·표 구조를 인식해 분할한다.

    - 제목(`##`, `[코드 N]`)과 목록 항목(`①`~`⑳`)은 본문과 같은 chunk 에 남는다.
    - 마크다운 표는 논리 행 경계에서만 끊는다. 행 중간에서 자르지 않는다.
    - 일반 문단은 문단 단위로 유지하고, 한 단위가 chunk_size 를 넘을 때만 보조 분할한다.
    - 제목 단독 조각은 만들지 않는다. overlap 도 단위 경계에서만 적용한다.

    기존 `structured_split` 은 비교용으로 그대로 남겨 둔다.
    """
    tokenizer = get_tokenizer()

    def token_length(value):
        return len(tokenizer(value))

    chunks = []
    current = []

    def flush():
        if current:
            chunks.append("\n\n".join(current))

    for unit in _build_units(text):
        # 한 단위가 상한을 넘으면 그 단위 안에서만 보조 분할한다.
        if token_length(unit) > chunk_size:
            flush()
            current = []

            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            pieces = [
                node.text
                for node in splitter.get_nodes_from_documents([Document(text=unit)])
            ]

            # 마커 줄이 첫 조각에 남도록 보정한다.
            head = unit.splitlines()[0].strip()

            if pieces and UNIT_MARKER.match(head) and head not in pieces[0]:
                pieces[0] = head + "\n" + pieces[0]

            chunks.extend(pieces)
            continue

        candidate = "\n\n".join(current + [unit])

        if current and token_length(candidate) > chunk_size:
            flush()

            # overlap 은 단위 경계에서만 잡고, 제목 단독 단위는 넘기지 않는다.
            overlap_units = []
            overlap_tokens = 0

            for previous in reversed(current):
                if _is_title_only(previous):
                    continue

                previous_tokens = token_length(previous)

                if overlap_tokens + previous_tokens > chunk_overlap:
                    break

                overlap_units.insert(0, previous)
                overlap_tokens += previous_tokens

            current = overlap_units

        current.append(unit)

    flush()

    return [TextNode(text=chunk) for chunk in chunks]

