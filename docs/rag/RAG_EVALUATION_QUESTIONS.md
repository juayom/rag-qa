# RAG 고정 평가 질문셋

## 1. 목적

`RAG_ADVANCEMENT_PLAN.md` 7항과 `RAG_EVALUATION_GUIDE.md` 3항에 따라, 모든 비교 실험(Baseline / Collection Routing / Semantic·Keyword·Hybrid / Re-ranking / 최종 평가)에서 **동일하게 사용할 고정 질문셋**을 정의한다.

비교 도중에는 질문을 추가·수정·삭제하지 않는다. 질문을 바꿔야 할 사유가 발생하면 변경 이력을 9항에 기록하고, 변경 이후의 결과는 이전 결과와 직접 비교하지 않는다.

---

## 2. 대상 문서 및 Collection

질문은 아래 3개 문서에 실제로 존재하는 내용만을 근거로 작성했다.

| Collection | 원본 파일 | Loader | Splitter | Chunk 수 |
|---|---|---|---|---|
| `ispark_company_profile` | `data/txt/이즈파크 회사 소개서.txt` | `load_txt` | `SentenceSplitter` | 10 |
| `credit_management_guide` | `data/pdf/현명한 신용관리 요령.pdf` | `load_pdf` (pdfplumber) | `StructuredSplitter` | 7 |
| `due_diligence_reason_codes` | `data/docx/실사유 코드.docx` | `load_docx` (python-docx) | `StructuredSplitter` | 9 |
| **합계** | | | | **26** |

### 위 Chunk 수를 측정한 실제 실행 명령어

Qdrant 컨테이너가 기동되어 있지 않아 Qdrant Point 수는 조회할 수 없었으므로, `index_documents.py`와 동일한 로더·클리너·청커 조합을 로컬에서 직접 실행해 Chunk 수와 Chunk 본문을 확인했다.

```powershell
& "C:\Users\User\.conda\envs\rag_env\python.exe" -c @'
import sys
sys.path.insert(0,".")
from pathlib import Path
from preprocessing.document_loader import load_document
from preprocessing.cleaner import clean_markdown
from preprocessing.chunkers import sentence_split, structured_split

DOCS = {
    Path("data/txt/이즈파크 회사 소개서.txt"): "ispark_company_profile",
    Path("data/pdf/현명한 신용관리 요령.pdf"): "credit_management_guide",
    Path("data/docx/실사유 코드.docx"): "due_diligence_reason_codes",
}
for p, c in DOCS.items():
    text = clean_markdown(load_document(str(p)))
    if p.suffix.lower() in (".pdf", ".docx"):
        nodes = structured_split(text)
    else:
        nodes = sentence_split(text)
    print(c, "| chunks:", len(nodes))
    for i, n in enumerate(nodes):
        print(f"  [{i+1}] len={len(n.text)} :: {n.text[:110]}")
'@
```

- 실행 결과: `ispark_company_profile` 10개, `credit_management_guide` 7개, `due_diligence_reason_codes` 9개 (PDF 중복 chunk 제거(안 B) 적용 후 기준. 적용 전에는 `credit_management_guide`가 13개였다.)
- Qdrant Collection별 실제 Point 수: **미측정** (Qdrant 미기동. Baseline 측정 시 `docker compose up -d qdrant` → `python index_documents.py` 후 함께 기록한다.)

### 재인덱싱 멱등성 (코드 확인 결과)

`index_documents.py`는 문서마다 아래 순서로 동작하므로 **누적 적재되지 않고 매번 덮어쓴다.**

1. `reset_collection(collection_name)` → `client.delete_collection()` (존재하면 삭제)
2. `get_index(...)` → `QdrantVectorStore.__init__`이 `_collection_initialized = _collection_exists(...)`를 평가 → 직전에 삭제했으므로 `False`
3. `save_nodes(...)` → `index.insert_nodes()` → `QdrantVectorStore.add()`가 `_collection_initialized`가 False이므로 `_create_collection()` 후 `upload_points()`

따라서 `index_documents.py`를 몇 번 실행해도 **points_count는 Chunk 수와 같아야 한다.**

| Collection | 기대 points_count |
|---|---|
| `ispark_company_profile` | 10 |
| `credit_management_guide` | 7 |
| `due_diligence_reason_codes` | 9 |

값이 위와 다르면 정상이 아니다. 특히 **10/7/9의 배수**라면 삭제가 동작하지 않고 누적된 것이고, **0이거나 Collection이 없으면** 임베딩 호출 등에서 예외가 발생해 삭제만 되고 적재가 실패한 것이다(`index_documents.py`의 `except`가 예외를 출력만 하고 넘어가므로 실행 로그를 함께 확인해야 한다).

> 아래 표의 `기대 근거 chunk_index`는 위 실행 결과 기준값이다. Chunking 로직이나 문서가 변경되면 값이 달라질 수 있으므로, Chunking 비교 단계에서는 chunk_index 대신 **근거 본문 내용**을 기준으로 정답 여부를 판정한다.

---

## 3. 질문 유형 구성

PLAN 7항의 7가지 유형을 모두 포함하며, Baseline 질문 **23개**와 v1.1에서 추가한 hard 문항 **7개**를 합쳐 총 **30개** 질문으로 구성한다.

| 유형 | ID Prefix | 질문 수 |
|---|---|---|
| 일반 사실형 | `F` | 3 |
| 전체/목록형 | `L` | 4 |
| 정확한 키워드/코드형 | `K` | 4 |
| 의미 기반 질문 | `S` | 3 |
| 짧고 모호한 질문 | `A` | 3 |
| 복합 질문 | `C` | 3 |
| 문서 범위 밖 질문 | `O` | 3 |
| hard 문항 (v1.1 추가 — 키워드/코드형 4, 의미 기반 3) | `H` | 7 |

hard 문항(`H`)은 검색 방식 비교의 변별력 확보를 위해 추가한 질문이며, 유형은 기존 7가지 중 `정확한 키워드/코드형`과 `의미 기반 질문`에 속한다. 해당 유형 절(6항 / 7항)에 함께 기재한다. Baseline 23문항의 측정 결과는 재측정하지 않고 그대로 유지한다.

---

## 4. 유형 1 — 일반 사실형

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| F-01 | 이즈파크의 대표이사와 설립일은 언제인가요? | `ispark_company_profile` | 1 | 대표이사는 김갑산, 설립일은 2009년. 회사명은 (주)이즈파크(ISPark Co., Ltd.). |
| F-02 | 10만원 이상의 금액을 며칠 이상 연체하면 신용등급이 하락하나요? | `credit_management_guide` | 2, 3 | 10만원 이상의 금액을 **5영업일 이상** 연체하면 신용평점이나 신용등급이 하락한다. |
| F-03 | 피보험자격 상실신고서는 언제까지 어디에 제출해야 하나요? | `due_diligence_reason_codes` | 9 | 퇴사일(상실일)이 속하는 달의 **다음 달 15일까지** 관할 **근로복지공단**에 제출. (예: 4월 20일 퇴사 → 5월 15일까지) |

---

## 5. 유형 2 — 전체/목록형

전체/목록형은 **항목 누락 여부**를 핵심 판정 기준으로 삼는다. 기대 항목 중 몇 개가 답변에 포함되었는지를 `포함 항목 수 / 전체 항목 수` 형태로 기록한다.

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| L-01 | 현명한 신용관리 요령 10가지를 모두 알려주세요. | `credit_management_guide` | 3, 4, 5, 6, 7 | 10개 항목 전부: ① 평소 자기 신용등급에 관심 기울이기 ② 소액이라도 절대 연체하지 않기 ③ 신용카드보다는 체크카드 사용하기 ④ 연체는 오래된 것부터 상환하기 ⑤ 과도한 빚은 고통의 시작임을 명심하기 ⑥ 주거래 금융회사 및 자동이체 이용하기 ⑦ 타인을 위한 보증은 가급적 피하기 ⑧ 대출 금융회사 신중하게 결정하기 ⑨ 신용평가 가점제 적극 활용하기 ⑩ 신용관리체험단 활용하기 |
| L-02 | 이즈파크의 주요 사업 영역을 모두 알려주세요. | `ispark_company_profile` | 1, 2 | 3개 영역: (1) 스마트 제조 솔루션(PLM, CAD/CAM/CAE, MES, QMS) (2) 디지털 트윈 및 XR(메타버스) (3) AI 및 클라우드 서비스 |
| L-03 | 변경 후 상실사유 중분류 코드 8개를 모두 나열해주세요. | `due_diligence_reason_codes` | 2, 3, 4 | 8개 코드: 11(개인사정으로 인한 자진퇴사), 12(사업장 이전·근로조건 변동·임금체불 등으로 자진퇴사), 22(폐업·도산), 23(경영상 필요 및 회사불황으로 인원감축 등에 의한 퇴사), 26(근로자 귀책사유에 의한 징계해고·권고사직), 31(정년), 32(계약만료·공사종료), 41(고용보험 비적용·이중고용) |
| L-04 | 이즈파크의 핵심 가치 3가지를 모두 알려주세요. | `ispark_company_profile` | 3, 4 | 3가지: 고객 중심(Customer Centric), 지속적인 혁신(Continuous Innovation), 신뢰와 상생 파트너십(Trust & Partnership) |

---

## 6. 유형 3 — 정확한 키워드/코드형

문서에 있는 코드 번호·고유명사·금액을 그대로 사용하는 질문이다. Keyword Search 및 Hybrid Search 비교의 주요 판정 대상이다.

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| K-01 | 코드 26은 어떤 경우에 적용되나요? | `due_diligence_reason_codes` | 7 | 근로자의 중대한 귀책사유(공금 횡령, 장기 무단결근, 기밀 누설 등)로 징계해고되거나, 해고를 피하기 위해 권고사직 형태로 퇴사하는 경우. 23번과 달리 실업급여 수급이 제한될 수 있고, 적법한 징계위원회 기록이 필요하다. |
| K-02 | 자진퇴사를 권고사직으로 허위 신고하면 과태료가 얼마인가요? | `due_diligence_reason_codes` | 8 | 사업장에 **최대 300만 원 이하**의 과태료가 부과될 수 있고, 사업주와 근로자 모두 부정수급 공범으로 처벌받을 수 있다. |
| K-03 | 3DEXPERIENCE 플랫폼에 통합된 핵심 어플리케이션 이름을 알려주세요. | `ispark_company_profile` | 6 | 설계 **CATIA**, 엔지니어링·해석 **SIMULIA**, 프로젝트·데이터 관리 **ENOVIA**, 디지털 제조·생산 계획 **DELMIA** |
| K-04 | 코드 32는 무엇인가요? | `due_diligence_reason_codes` | 3, 5 | 32번은 **계약만료, 공사종료**. 기존에 분리되어 있던 계약만료(32)와 공사종료(33)가 32번으로 통합되었다. |

### v1.1 추가 — hard 문항

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| H-02 | 26번 코드와 23번 코드는 어떻게 다른가요? | `due_diligence_reason_codes` | 7 | 23번은 경영상 필요·인원 감축에 의한 퇴사, 26번은 근로자 귀책사유에 의한 징계해고·권고사직. 26번은 실업급여 수급이 제한될 수 있다. |
| H-03 | 사업장 이전으로 출퇴근이 왕복 몇 시간 이상 걸리게 되면 자진퇴사해도 실업급여를 받을 수 있나요? | `due_diligence_reason_codes` | 6 | 왕복 **3시간 이상**. |
| H-04 | 고용보험 비적용과 이중고용은 변경 후 몇 번 코드로 통합되었나요? | `due_diligence_reason_codes` | 4, 5 | **41번** 단일 코드로 병합. |
| H-05 | 금융감독원이 개설하기로 한 금융소비자정보 포털사이트의 이름은 무엇인가요? | `credit_management_guide` | 1 | **파인(FINE)**. |

---

## 7. 유형 4 — 의미 기반 질문

문서와 표현이 다르지만 의미가 같은 질문이다. Semantic Search의 강점 확인용이다.

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| S-01 | 빚을 갚지 못하고 계속 밀리면 어떤 불이익이 생기나요? | `credit_management_guide` | 2, 3, 4 | 연체정보는 신용등급 평가에서 가장 부정적인 영향을 미치는 요인이며, 연체 기간이 길수록 불리하다. 신용등급이 하락하면 대출이 거절되거나 더 높은 대출금리를 부담하게 된다. |
| S-02 | 회사가 멀리 이전해서 출퇴근이 너무 힘들어져 그만두면 실업급여를 받을 수 있나요? | `due_diligence_reason_codes` | 6 | 코드 12에 해당한다. 회사 이전으로 출퇴근이 **왕복 3시간 이상** 소요되면, 형식상 자진퇴사여도 원인 제공이 회사에 있으므로 실업급여를 받을 수 있다. 출퇴근 기록 등 증빙 보관이 필요하다. |
| S-03 | 이즈파크는 환경 보호에 어떤 기여를 하고 있나요? | `ispark_company_profile` | 9, 10 | ESG 경영을 실천하고 있으며, 디지털 트윈과 3D 시뮬레이션 기술로 물리적 시제품 제작(Prototyping) 횟수를 줄여 산업 현장의 폐기물 감소와 탄소 배출 절감에 기여한다. |

### v1.1 추가 — hard 문항

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| H-01 | 직원이 회사 돈에 손을 대서 내보냈습니다. 어떤 사유 코드로 신고해야 하나요? | `due_diligence_reason_codes` | 7 | **코드 26** (근로자 귀책사유에 의한 징계해고·권고사직). |
| H-06 | 다른 사람 빚보증을 서주면 내 신용에 문제가 생기나요? | `credit_management_guide` | 6 | 보증내역이 신용조회회사에 보내져 신용등급 산정에 반영되고, 채무자가 연체하지 않아도 보증인의 신용등급이 **하락**할 수 있다. |
| H-07 | 3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 무엇인가요? | `ispark_company_profile` | 6 | **CATIA**. |

> H-06 비고 — 이 문항은 원래 중복 chunk 쌍 `10, 12`를 근거로 삼는 문항이었다. v1.2의 PDF 중복 제거로 두 chunk가 하나로 합쳐져 기대 근거가 `6` 하나가 되었으므로, **Baseline에서 관찰된 "최종 Top-3의 2칸을 같은 내용이 차지하는" 현상은 더 이상 재현되지 않는다.**

---

## 8. 유형 5 — 짧고 모호한 질문

Collection Routing의 fallback 동작과 Adaptive Multi Query 실행 여부를 확인하는 질문이다. 정답 판정은 "관련 Collection의 내용을 근거로 답변했는가 / 관련 없는 Collection 문서를 출처로 표시하지 않았는가"로 한다.

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| A-01 | 신용등급? | `credit_management_guide` | 3 | 신용등급은 금융거래의 신분증과 같으며 대출 가능여부·한도·금리를 결정하는 기본지표라는 취지로 답변. |
| A-02 | 권고사직 | `due_diligence_reason_codes` | 3, 7, 8 | 권고사직은 코드 23(경영상 필요·인원감축 등) 또는 코드 26(근로자 귀책사유)에 해당할 수 있다는 취지로 답변. |
| A-03 | 이즈파크 | `ispark_company_profile` | 1 | 2009년 설립된 ICT 솔루션 전문기업이라는 취지의 회사 개요로 답변. |

---

## 9. 유형 6 — 복합 질문

하나의 질문에 2개 이상의 요구가 포함된다. 요구 항목별로 답변이 모두 포함되었는지 확인한다.

| ID | 질문 | 기대 근거 Collection | 기대 근거 chunk_index | 기대 답변 요지 |
|---|---|---|---|---|
| C-01 | 코드 23과 코드 26의 실업급여 수급 차이는 무엇이고, 각각 어떤 경우에 적용되나요? | `due_diligence_reason_codes` | 7 | 23번은 경영 악화·부서 폐지·직제 개편에 따른 희망퇴직·명예퇴직·권고사직에 적용되고, 회사가 정부 지원금 혜택에 제한을 받을 수 있다. 26번은 근로자의 중대한 귀책사유에 의한 징계해고·권고사직으로, 23번과 달리 실업급여 수급이 제한될 수 있다. |
| C-02 | 신용등급을 관리하려면 카드는 어떻게 쓰고, 연체가 이미 생겼을 때는 어떤 순서로 갚아야 하나요? | `credit_management_guide` | 4 | 카드는 신용카드보다 체크카드를 사용해 상환능력을 벗어난 사용을 자제하고, 이미 발생한 연체는 **가장 오래된 연체 건부터** 상환해야 불이익이 최소화된다. |
| C-03 | 이즈파크의 설립 연도와, 타인을 위한 보증이 신용등급에 미치는 영향을 함께 알려주세요. | `ispark_company_profile` + `credit_management_guide` (2개) | ispark 1 / credit 6 | 이즈파크는 2009년 설립. 타인을 위해 보증을 서면 보증내역이 신용조회회사에 전달되어 신용등급 산정에 반영되며, 채무자가 연체하지 않아도 보증인의 신용등급이 하락할 수 있다. |

> C-03은 서로 다른 2개 Collection의 근거를 동시에 요구한다. Collection Routing 적용 시 **단일 Collection만 선택해 한쪽 근거를 놓치는지**를 확인하는 질문이므로, Routing 비교(GUIDE 5항)에서 반드시 확인한다.

---

## 10. 유형 7 — 문서 범위 밖 질문

Hallucination 방지 평가(GUIDE 10항) 대상이다. **성공 기준**은 다음 세 가지를 모두 만족하는 것이다.

1. 문서에 없는 내용을 임의로 생성하지 않는다.
2. "제공된 문서에서는 해당 정보를 찾을 수 없습니다." 형태로 응답한다.
3. 관련 없는 문서를 출처로 표시하지 않는다.

| ID | 질문 | 기대 근거 Collection | 기대 답변 요지 |
|---|---|---|---|
| O-01 | 양자역학의 불확정성 원리를 설명해주세요. | 없음 (3개 문서 모두 무관) | 문서에서 찾을 수 없다고 응답해야 한다. |
| O-02 | 이즈파크의 2025년 연매출과 영업이익을 알려주세요. | 없음 (`ispark_company_profile`에 재무 정보 없음) | 문서에서 찾을 수 없다고 응답해야 한다. 회사 소개 내용으로 수치를 추정해 답하면 실패로 판정한다. |
| O-03 | 이즈파크의 임직원 수와 평균 연봉은 얼마인가요? | 없음 (`ispark_company_profile`에 인원·급여 정보 없음) | 문서에서 찾을 수 없다고 응답해야 한다. |

---

## 11. 질문 ID 전체 목록 (실행 순서)

측정 스크립트/수동 실행 모두 아래 순서를 고정해서 사용한다.

```text
F-01, F-02, F-03,
L-01, L-02, L-03, L-04,
K-01, K-02, K-03, K-04,
S-01, S-02, S-03,
A-01, A-02, A-03,
C-01, C-02, C-03,
O-01, O-02, O-03,
H-01, H-02, H-03, H-04, H-05, H-06, H-07
```

hard 문항(`H-01`~`H-07`)은 v1.1에서 Baseline 23문항 **뒤에 추가**했다. 앞 23문항의 순서와 문구는 그대로 두었으므로, Baseline 측정 결과와 ID 대응이 유지된다.

---

## 12. 측정 시 기록 항목

GUIDE 4항에 따라 질문별로 아래 항목을 기록한다. 값을 얻지 못한 항목은 `미측정`으로 적는다.

```text
question_id
question
selected_collection(s)
retrieval_top_k
retrieval_candidate_count
retrieval_candidates (rank / collection / chunk_index / score / passed_to_reranker)
retrieved_docs (source / chunk_index / rank / retriever_score / rerank_score)
multi_query_used
rerank_candidate_count
final_context_count
retrieval_ms
multi_query_ms
reranking_ms
gpt_ms
total_ms
answer
source
정답 여부
정보 누락 여부 (목록형은 포함 항목 수 / 전체 항목 수)
Hallucination 여부
```

### 평가 횟수 (모든 비교 문서의 "테스트 조건"에 동일하게 명시한다)

| 지표 구분 | 대상 | 실행 횟수 |
|---|---|---|
| 정확도 지표 (정답 chunk 순위, MRR, Hit@K, 정답 여부, 정보 누락, Hallucination) | **30문항 전체** | **1회** |
| 시간 지표 (retrieval_ms / reranking_ms / gpt_ms / total_ms) | 유형별 대표 7문항 | **3회 평균, 회차별 값 병기** |

- Baseline의 정확도 지표는 기측정 23문항(`baseline`) 결과와 hard 7문항(`baseline_hard`) 결과를 **합산**한다. 23문항은 재측정하지 않는다.
- hard 7문항은 **재인덱싱 없이 동일 인덱스**(커밋 `7940974`, 10 / 13 / 9)에서 측정했다.
- 시간 지표는 대표 7문항 × 3회로 **변경 없다**(`timing_question_ids` 유지). **hard 문항은 시간 측정 대상이 아니다.**

### 주 평가 지표

전체 chunk는 26개(`ispark_company_profile` 10 / `credit_management_guide` 7 / `due_diligence_reason_codes` 9)인데, 질문당 검색 후보 수가 dedup 실측 평균 24.53개로 **코퍼스의 94.3%**(24.53 / 26)를 차지한다. 이 조건에서는 정답 chunk가 후보에 포함되지 않기가 어렵고, 실제로 Hit@K는 Baseline 23문항·hard 7문항·dedup 30문항 모두 100%로 포화됐다. 중복 chunk 제거 전(전체 32개)의 비율은 86.9%(27.80 / 32)였으므로, 포화는 오히려 심해졌다.

따라서 검색 방식 비교(GUIDE 6항)와 Re-ranking 비교(GUIDE 8항)의 **주 지표는 Hit@K가 아니라 정답 chunk 순위와 MRR**로 한다.

| 지표 | 구분 | 정의 |
|---|---|---|
| 정답 chunk 순위 | **주 지표** | 검색 단계 / Re-ranking 단계 각각에서 기대 근거 chunk의 가장 높은 rank |
| MRR | **주 지표** | `mean(1/rank)`. 검색 단계 / Re-ranking 단계를 나누어 계산한다. 정답 chunk가 없는 문서 범위 밖 질문(`O`)은 제외한다. |
| Hit@K | 보조 지표 | 포화 상태이므로 방식 간 변별에 사용하지 않고 기록만 한다. |

### 시간 지표 대표 7문항

유형별로 1문항씩 선정했다. 정확도 지표 실행(23문항 × 1회)의 1회차 결과를 시간 지표 1회차로 함께 사용하고, 대표 7문항만 2회차·3회차를 추가 실행한다.

| 유형 | 질문 ID | 근거 Collection |
|---|---|---|
| 일반 사실형 | `F-01` | `ispark_company_profile` |
| 전체/목록형 | `L-01` | `credit_management_guide` |
| 정확한 키워드/코드형 | `K-01` | `due_diligence_reason_codes` |
| 의미 기반 질문 | `S-02` | `due_diligence_reason_codes` |
| 짧고 모호한 질문 | `A-01` | `credit_management_guide` |
| 복합 질문 | `C-01` | `due_diligence_reason_codes` |
| 문서 범위 밖 질문 | `O-02` | 없음 |

- 대표 7문항은 3개 Collection과 "근거 없음" 케이스를 모두 포함한다.
- 목록형(`L-01`)은 `retrieval_top_k=15` / `rerank_top_k=10`, 나머지 6문항은 `8 / 3` 조건이므로 **유형 간 시간 비교는 하지 않는다.** 시간 비교는 항상 `동일 질문 ID × 방식 간`으로만 수행한다.

### 콜드스타트 제거 (워밍업)

`llm/reranker.py`는 import 시점에 `Dongjin-kr/ko-reranker`를 로드하고, 첫 임베딩 호출에도 초기화 비용이 있어 1회차 시간이 이상치가 된다.

- 본 측정 시작 전에 **워밍업 호출을 1회** 수행하고, 그 결과는 **모든 집계에서 제외**한다.
- 워밍업 질문은 `questions.json`의 `warmup_question`(`"이즈파크는 어떤 회사인가요?"`)을 사용한다. 고정 질문셋에 포함되지 않은 별도 질문이다.
- `scripts/eval_run.py`가 자동으로 수행하며, 워밍업 실시 여부·질문·워밍업 자체의 `total_ms`를 summary.md 테스트 조건에 기록한다. 워밍업 결과는 `raw.json`의 `runs`가 아니라 별도 `warmup` 키에 저장되어 평균 계산에 들어가지 않는다.

---

## 13. 인덱스 운용 정책

비교 실험 간 조건을 동일하게 유지하기 위해 인덱스 변경 시점을 아래와 같이 고정한다.

| 시점 | 인덱스 상태 | 비고 |
|---|---|---|
| Baseline 측정 | **현재 인덱스 그대로** (PDF 중복 chunk 포함) | 중복 chunk를 고치지 않은 상태를 Baseline으로 측정한다. |
| Baseline 직후 | 중복 제거 + 재인덱싱 **1회만** 수행 | 결과는 `RAG_CHUNKING_COMPARISON.md`에 기록한다. |
| 이후 모든 비교 | 재인덱싱 후 인덱스 **고정** | Collection Routing / Semantic·Keyword·Hybrid / Re-ranking 비교는 모두 동일 인덱스에서 실행한다. |

- ~~`credit_management_guide`의 PDF 중복 chunk~~ **해소됨(2026-09-23).** `credit_management_guide`는 PDF 본문 전체가 표 안에 포함된 구조여서, `preprocessing/pdf_loader.py`가 페이지 텍스트와 표를 각각 추가해 같은 내용이 두 번 들어갔었다(13개 chunk 중 4·8·12번이 3·5·6·7·10·11번과 중복). Baseline에서 이 중복 chunk가 실제로 Top-K를 차지하는 것을 `H-06`에서 확인한 뒤(Top-3의 1·2위가 동일 내용) 중복 제거(안 B)를 적용했고, chunk 수가 13 → 7로 줄었다.
- 중복 제거 전후 비교 결과와 최종 판단은 [RAG_CHUNKING_COMPARISON.md](RAG_CHUNKING_COMPARISON.md)에 기록했다. 이후 모든 비교는 중복 제거 후 인덱스(10 / 7 / 9)에서 수행한다.
- 고도화 대상은 웹 화면이 사용하는 `server.py` 하나로 한정하며, CLI 스크립트 `main.py`는 현 상태로 동결한다(수정 금지).

---

## 14. 판정 기준

정답 chunk 추적은 **검색 단계와 Re-ranking 단계를 나누어** 판정한다. 검색 성능과 Re-ranking 성능을 분리하지 않으면 GUIDE 6항(Semantic/Keyword/Hybrid 비교)과 8항(Re-ranking 비교)에서 원인을 구분할 수 없다.

| 항목 | 기준 |
|---|---|
| 정답 여부 | 기대 답변 요지의 핵심 사실이 답변에 포함되고, 문서와 어긋나는 서술이 없으면 정답 |
| **검색 단계** 정답 Chunk 포함 | `/chat` 응답의 `retrieval_candidates`(Re-ranking 전, 중복 제거 후 전체 후보) 안에 기대 근거 chunk가 최소 1개 포함되면 Hit. K는 질문별 실제 후보 수이다. |
| **검색 단계** 정답 Chunk 순위 | `retrieval_candidates` 안에서 기대 근거 chunk의 가장 높은 rank (Retriever 점수 내림차순) |
| **Re-ranking 단계** 정답 Chunk 포함 (Hit@rerank_top_k) | `retrieved_docs`(Cross Encoder 이후 최종 Top-K) 안에 기대 근거 chunk가 최소 1개 포함되면 Hit |
| **Re-ranking 단계** 정답 Chunk 순위 | `retrieved_docs` 안에서 기대 근거 chunk의 가장 높은 rank |
| Re-ranking 탈락 | 검색 단계는 Hit인데 Re-ranking 단계는 Miss인 경우. Re-ranker가 정답을 떨어뜨린 것으로 판정한다. |
| 정보 누락 | 목록형·복합형에서 기대 항목 중 누락된 항목 수 |
| Hallucination | 문서에 없는 사실을 단정적으로 서술하면 발생으로 판정 |
| 출처 정확성 | 표시된 `sources`가 실제 답변 근거 문서와 일치하는지 |

---

## 15. 질문셋 설계 시 확인한 코드 동작 (참고)

Baseline 결과 해석에 영향을 주는 현재 코드 동작을 미리 확인해 둔다. 아래는 코드 확인 결과이며 실행 측정값이 아니다.

- `vectorstore/retriever.py`의 `is_list_question()`은 `전체/모두/모든/전부/목록/리스트/나열/항목/종류` 키워드 또는 정규식 `\d+\s*(가지|개|단계|방법|항목|종류|이유|요령)`으로만 목록형을 판단한다. 따라서 "세 가지"처럼 **한글 수사로 쓴 목록형 질문은 목록형으로 감지되지 않는다.** 본 질문셋의 L-04는 이 영향을 배제하기 위해 "3가지"로 표기했다.
- 목록형으로 판정되면 `retrieval_top_k=15`, `rerank_top_k=10`, `rerank_candidate_limit=15`가 적용되고, 그 외에는 `8 / 3 / 8`이 적용된다. 따라서 L-01~L-04와 F/K/S/A/C/O 질문은 top-k 조건이 다르다. **유형 간 시간 비교는 하지 않고, 동일 질문의 방식 간 비교만 수행한다.**
- `is_retrieval_sufficient()`는 score ≥ 0.5인 노드 수가 `rerank_top_k` 이상인지로 판단한다. 목록형 질문은 기준이 10개이므로 Multi Query가 상대적으로 자주 실행될 수 있다. Multi Query 실행 비율은 유형별로 나누어 집계한다.

---

## 16. 변경 이력

| 날짜 | 변경 내용 | 사유 |
|---|---|---|
| 2026-09-22 | 최초 작성 (23개 질문, 7개 유형) | Baseline 측정 전 고정 질문셋 확정 |
| 2026-09-22 | 질문 변경 없음. 인덱스 운용 정책 / 평가 횟수 / 단계별 판정 기준 / 워밍업 규칙 추가 | Baseline 측정 조건 확정 (질문 문구·개수는 그대로) |
| 2026-09-22 | **v1.1** — hard 문항 7개(`H-01`~`H-07`) 추가 (23문항 → 30문항). 기존 23문항의 문구·순서·기대값은 수정하지 않았고, `timing_question_ids`(시간 대표 7문항)도 변경하지 않았다. | 기존 23문항의 검색 Hit가 100%로 검색 방식 간 변별이 어려워 hard 문항 7개 추가. Baseline 23문항 결과는 재측정하지 않고 유지. |
| 2026-09-22 | 질문 변경 없음. 12항 평가 횟수를 30문항 기준으로 수정(23문항 + hard 7문항 합산)하고, 12항에 "주 평가 지표" 추가 | hard 7문항 측정 결과 Hit@K가 100%로 포화되어, 검색 방식·Re-ranking 비교의 주 지표를 정답 chunk 순위와 MRR로 변경 |
| 2026-09-23 | **v1.2** — `credit_management_guide`를 참조하는 8문항(F-02, L-01, S-01, A-01, C-02, C-03, H-05, H-06)의 기대 근거 chunk 번호 재매핑. 질문 문구·`expected_items`·다른 Collection 참조는 변경 없음 | PDF 중복 chunk 제거(안 B)로 credit_management_guide 가 13 → 7 chunk 로 변경되어 expected chunk 번호를 재매핑. 질문 문구는 변경 없음. |
| 2026-09-23 | 질문 변경 없음. 2항 chunk 수(13 → 7, 합계 32 → 26)와 기대 points_count(10 / 7 / 9), 12항 주 평가 지표의 후보 비율(94.3%), 13항 중복 chunk 서술을 dedup 실측 기준으로 갱신하고 [RAG_CHUNKING_COMPARISON.md](RAG_CHUNKING_COMPARISON.md) 링크 추가 | PDF 중복 chunk 제거(안 B) 적용 및 dedup 측정 완료로 기존 서술이 실제 인덱스와 불일치 |
