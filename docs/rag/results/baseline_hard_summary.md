# 평가 결과 요약 — `baseline_hard`

`scripts/eval_run.py`가 자동 생성한 파일이다. 수동 편집 시 재실행하면 덮어써진다.

---

## 테스트 조건

- config: `baseline_hard`
- 실행 시각: 2026-09-22 16:04:05 ~ 2026-09-22 16:05:53
- 실행 환경: Conda `rag_env` / Qdrant `6333` / FastAPI
- 호출 대상: `POST http://127.0.0.1:8001/chat` (server.py)
- 질문셋: `docs/rag/questions.json` (v1.1, 30문항)
- Re-ranker: Dongjin-kr/ko-reranker (Cross Encoder, llm/reranker.py)
- 평가 횟수
  - 정확도 지표(Hit@K, 정답 여부, 정보 누락, Hallucination): **7문항 × 1회**
  - 시간 지표(retrieval / reranking / gpt / total): **대표 0문항 × 1회 평균, 회차별 값 병기**
  - 시간 지표 대표 문항: 
- top_k / 후보 수는 `vectorstore/retriever.py`의 질문 유형 판단에 따라 자동 결정된다(일반 8/3/8, 목록형 15/10/15). 질문별 관측값은 아래 상세표에 기록한다.
- 워밍업: 본 측정 전 1회 수행하고 **집계에서 제외**했다. 질문 `이즈파크는 어떤 회사인가요?`, 워밍업 total_ms = 12530.26 (참고용, 아래 어떤 평균에도 포함되지 않음)
- **주의**: `--only H-01,H-02,H-03,H-04,H-05,H-06,H-07`로 일부 문항만 실행했다. 고정 질문셋 전체 비교에는 사용할 수 없다.
- 비고: v1.1 hard 문항 7개. 커밋 7940974 동일 인덱스(10/13/9), 재인덱싱 없음. 시간 측정 대상 아님(repeat 1).

### 실제 실행 명령어

```powershell
python scripts/eval_run.py --config baseline_hard --only H-01,H-02,H-03,H-04,H-05,H-06,H-07 --note "v1.1 hard 문항 7개. 커밋 7940974 동일 인덱스(10/13/9), 재인덱싱 없음. 시간 측정 대상 아님(repeat 1)."
```

---

## 오류 / 특이사항

- 없음

---

## 정확도 지표 (1회차, 전체 문항)

정답 chunk 추적은 **두 단계로 나누어** 집계한다.

- **검색 단계**: `retrieval_candidates` (server.py가 Re-ranking 전에 확보한 중복 제거 후 전체 후보). K는 질문별 실제 후보 수이므로 고정값이 아니다.
- **Re-ranking 단계**: `retrieved_docs` (Cross Encoder 이후 최종 Top-K). K = `rerank_top_k` (일반 3 / 목록형 10).

검색 단계에서 Hit인데 Re-ranking 단계에서 Miss면 Re-ranking이 정답을 떨어뜨린 것이고, 검색 단계부터 Miss면 검색 자체가 실패한 것이다.

| 지표 | 값 |
|---|---|
| 정상 응답 문항 수 | 7 / 7 |
| **검색 단계** Hit@검색후보수 (범위 내 7문항) | 7 / 7 (100.0%) |
| **검색 단계** 정답 chunk 평균 순위 (Hit 문항) | 1.71 |
| **검색 단계** 평균 후보 수 | 26.29 |
| **Re-ranking 단계** Hit@rerank_top_k (범위 내 7문항) | 7 / 7 (100.0%) |
| **Re-ranking 단계** 정답 chunk 평균 순위 (Hit 문항) | 1.14 |
| Re-ranking에서 정답 chunk 탈락 | 0문항 |
| Multi Query 실행 비율 | 6 / 7 (85.7%) |
| 문서 범위 밖 질문 거절 | 미측정 |

### 유형별 집계 (1회차)

| 유형 | 문항 수 | 검색 Hit | 검색 순위 | 재랭킹 Hit | 재랭킹 순위 | Multi Query 실행 | 평균 total_ms |
|---|---|---|---|---|---|---|---|
| 의미 기반 질문 | 3 | 3 / 3 | 1.33 | 3 / 3 | 1.33 | 2 / 3 | 12071.08 |
| 정확한 키워드/코드형 | 4 | 4 / 4 | 2.0 | 4 / 4 | 1.0 | 4 / 4 | 14917.34 |

---

## 시간 지표 (대표 0문항 × 1회)

| 질문 ID | 지표 | 1회차 | 평균 |
|---|---|---|---|

### 대표 문항 평균 (회차 전체 기준)

| 지표 | 평균 |
|---|---|
| 평균 retrieval_ms | 미측정 |
| 평균 reranking_ms | 미측정 |
| 평균 gpt_ms | 미측정 |
| 평균 total_ms | 미측정 |
| 평균 multi_query_ms | 미측정 |

> 목록형 문항은 `retrieval_top_k=15 / rerank_top_k=10`, 그 외는 `8 / 3`이므로 **유형 간 시간 비교는 하지 않는다.** 비교는 항상 동일 질문 ID × 방식 간으로만 수행한다.

### 참고 — 1회차 전체 문항 평균

| 지표 | 평균 |
|---|---|
| 평균 retrieval_ms | 2187.33 |
| 평균 reranking_ms | 8370.87 |
| 평균 gpt_ms | 1712.59 |
| 평균 total_ms | 13697.51 |

---

## 질문별 단계별 정답 chunk 추적 (1회차)

| ID | 유형 | 검색 후보 수 | 검색 Hit | 검색 순위 | 재랭킹 후보 수 | 최종 Top-K | 재랭킹 Hit | 재랭킹 순위 |
|---|---|---|---|---|---|---|---|---|
| `H-01` | 의미 기반 질문 | 24 | O | 2 | 8 | 3 | O | 2 |
| `H-02` | 정확한 키워드/코드형 | 26 | O | 5 | 8 | 3 | O | 1 |
| `H-03` | 정확한 키워드/코드형 | 25 | O | 1 | 8 | 3 | O | 1 |
| `H-04` | 정확한 키워드/코드형 | 27 | O | 1 | 8 | 3 | O | 1 |
| `H-05` | 정확한 키워드/코드형 | 26 | O | 1 | 8 | 3 | O | 1 |
| `H-06` | 의미 기반 질문 | 28 | O | 1 | 8 | 3 | O | 1 |
| `H-07` | 의미 기반 질문 | 28 | O | 1 | 8 | 3 | O | 1 |

---

## 질문별 실행 조건 및 시간 (1회차)

| ID | 선택 Collection | top_k | MQ | 기대 항목 | 누락 항목 | retrieval_ms | rerank_ms | gpt_ms | total_ms |
|---|---|---|---|---|---|---|---|---|---|
| `H-01` | ALL(3) - Routing 미적용 | 8 | X | 1 / 1 | - | 1263.64 | 8679.13 | 2452.81 | 12396.05 |
| `H-02` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2324.83 | 8634.5 | 2596.31 | 15068.18 |
| `H-03` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2208.53 | 12293.94 | 1744.84 | 18403.98 |
| `H-04` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2515.46 | 8375.67 | 1150.48 | 13580.86 |
| `H-05` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2340.93 | 7143.93 | 1652.71 | 12616.34 |
| `H-06` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2378.23 | 6730.71 | 1182.56 | 11933.74 |
| `H-07` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2279.66 | 6738.18 | 1208.41 | 11883.44 |

> `기대 항목` / `누락 항목`은 questions.json의 `expected_items` 문자열 포함 검사 결과이며 **자동 보조 지표**이다. 최종 정답 여부와 정보 누락은 아래 수동 판정표에서 사람이 확정한다.

---

## 검색 근거 (1회차)

검색 단계는 상위 10건과 정답 chunk에 해당하는 건만 표시한다(전체는 raw.json의 `retrieval_candidates`).

### `H-01` 직원이 회사 돈에 손을 대서 내보냈습니다. 어떤 사유 코드로 신고해야 하나요?

**검색 단계 (Re-ranking 전, 후보 24건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 3 | 0.5362 | O |  |
| 2 | due_diligence_reason_codes | 7 | 0.5166 | O | O |
| 3 | due_diligence_reason_codes | 6 | 0.5081 | O |  |
| 4 | due_diligence_reason_codes | 8 | 0.5073 | O |  |
| 5 | due_diligence_reason_codes | 5 | 0.5032 | O |  |
| 6 | due_diligence_reason_codes | 2 | 0.4904 | O |  |
| 7 | due_diligence_reason_codes | 9 | 0.4791 | O |  |
| 8 | credit_management_guide | 1 | 0.4176 | O |  |
| 9 | credit_management_guide | 4 | 0.4164 | X |  |
| 10 | credit_management_guide | 12 | 0.4163 | X |  |
| ... | 이하 14건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.5032 | 0.0426 |  |
| 2 | due_diligence_reason_codes | 7 | 0.5166 | 0.0231 | O |
| 3 | due_diligence_reason_codes | 6 | 0.5081 | 0.0137 |  |

### `H-02` 26번 코드와 23번 코드는 어떻게 다른가요?

**검색 단계 (Re-ranking 전, 후보 26건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 1 | 0.4441 | O |  |
| 2 | due_diligence_reason_codes | 5 | 0.4314 | O |  |
| 3 | due_diligence_reason_codes | 4 | 0.3885 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.3862 | O |  |
| 5 | due_diligence_reason_codes | 7 | 0.3398 | O | O |
| 6 | due_diligence_reason_codes | 3 | 0.3359 | O |  |
| 7 | due_diligence_reason_codes | 6 | 0.3302 | O |  |
| 8 | credit_management_guide | 7 | 0.2904 | O |  |
| 9 | credit_management_guide | 9 | 0.2838 | X |  |
| 10 | due_diligence_reason_codes | 8 | 0.2805 | X |  |
| ... | 이하 16건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.3398 | 0.9931 | O |
| 2 | due_diligence_reason_codes | 6 | 0.3302 | 0.0843 |  |
| 3 | due_diligence_reason_codes | 3 | 0.3359 | 0.0254 |  |

### `H-03` 사업장 이전으로 출퇴근이 왕복 몇 시간 이상 걸리게 되면 자진퇴사해도 실업급여를 받을 수 있나요?

**검색 단계 (Re-ranking 전, 후보 25건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.5776 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.4875 | O |  |
| 3 | due_diligence_reason_codes | 3 | 0.452 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.4364 | O |  |
| 5 | due_diligence_reason_codes | 9 | 0.4261 | O |  |
| 6 | due_diligence_reason_codes | 5 | 0.412 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.3772 | O |  |
| 8 | credit_management_guide | 2 | 0.3496 | O |  |
| 9 | credit_management_guide | 5 | 0.3076 | X |  |
| 10 | credit_management_guide | 3 | 0.3072 | X |  |
| ... | 이하 15건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.5776 | 0.9993 | O |
| 2 | due_diligence_reason_codes | 5 | 0.412 | 0.0167 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4875 | 0.014 |  |

### `H-04` 고용보험 비적용과 이중고용은 변경 후 몇 번 코드로 통합되었나요?

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 4 | 0.5841 | O | O |
| 2 | due_diligence_reason_codes | 5 | 0.4764 | O | O |
| 3 | credit_management_guide | 11 | 0.4365 | O |  |
| 4 | due_diligence_reason_codes | 8 | 0.4117 | O |  |
| 5 | credit_management_guide | 13 | 0.4055 | O |  |
| 6 | due_diligence_reason_codes | 3 | 0.4035 | O |  |
| 7 | credit_management_guide | 7 | 0.3874 | O |  |
| 8 | credit_management_guide | 10 | 0.3867 | O |  |
| 9 | credit_management_guide | 12 | 0.3848 | X |  |
| 10 | credit_management_guide | 9 | 0.3786 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.4764 | 0.9893 | O |
| 2 | due_diligence_reason_codes | 4 | 0.5841 | 0.0367 | O |
| 3 | due_diligence_reason_codes | 3 | 0.4035 | 0.0033 |  |

### `H-05` 금융감독원이 개설하기로 한 금융소비자정보 포털사이트의 이름은 무엇인가요?

**검색 단계 (Re-ranking 전, 후보 26건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 1 | 0.4804 | O | O |
| 2 | ispark_company_profile | 9 | 0.3109 | O |  |
| 3 | credit_management_guide | 10 | 0.3052 | O |  |
| 4 | credit_management_guide | 12 | 0.3016 | O |  |
| 5 | credit_management_guide | 9 | 0.2958 | O |  |
| 6 | ispark_company_profile | 1 | 0.2887 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.2718 | O |  |
| 8 | credit_management_guide | 4 | 0.2692 | O |  |
| 9 | ispark_company_profile | 5 | 0.2653 | X |  |
| 10 | credit_management_guide | 13 | 0.259 | X |  |
| ... | 이하 16건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 1 | 0.4804 | 0.9945 | O |
| 2 | credit_management_guide | 9 | 0.2958 | 0.0001 |  |
| 3 | credit_management_guide | 10 | 0.3052 | 0.0001 |  |

### `H-06` 다른 사람 빚보증을 서주면 내 신용에 문제가 생기나요?

**검색 단계 (Re-ranking 전, 후보 28건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 10 | 0.4461 | O | O |
| 2 | credit_management_guide | 12 | 0.4391 | O | O |
| 3 | credit_management_guide | 4 | 0.402 | O |  |
| 4 | credit_management_guide | 5 | 0.3909 | O |  |
| 5 | due_diligence_reason_codes | 8 | 0.3789 | O |  |
| 6 | credit_management_guide | 2 | 0.3774 | O |  |
| 7 | credit_management_guide | 3 | 0.3582 | O |  |
| 8 | credit_management_guide | 1 | 0.3544 | O |  |
| 9 | due_diligence_reason_codes | 5 | 0.3493 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.344 | X |  |
| ... | 이하 18건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 10 | 0.4461 | 0.9218 | O |
| 2 | credit_management_guide | 12 | 0.4391 | 0.8942 | O |
| 3 | credit_management_guide | 1 | 0.3544 | 0.004 |  |

### `H-07` 3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 무엇인가요?

**검색 단계 (Re-ranking 전, 후보 28건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5845 | O | O |
| 2 | ispark_company_profile | 2 | 0.4759 | O |  |
| 3 | ispark_company_profile | 4 | 0.3567 | O |  |
| 4 | ispark_company_profile | 7 | 0.354 | O |  |
| 5 | ispark_company_profile | 8 | 0.3502 | O |  |
| 6 | ispark_company_profile | 10 | 0.3491 | O |  |
| 7 | ispark_company_profile | 5 | 0.3036 | O |  |
| 8 | ispark_company_profile | 9 | 0.2816 | O |  |
| 9 | ispark_company_profile | 1 | 0.267 | X |  |
| 10 | credit_management_guide | 11 | 0.2075 | X |  |
| ... | 이하 18건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5845 | 0.9069 | O |
| 2 | ispark_company_profile | 2 | 0.4759 | 0.0149 |  |
| 3 | ispark_company_profile | 8 | 0.3502 | 0.0007 |  |

---

## 답변 전문 (1회차)

### `H-01` (의미 기반 질문)

- 질문: 직원이 회사 돈에 손을 대서 내보냈습니다. 어떤 사유 코드로 신고해야 하나요?
- 기대 답변 요지: 코드 26 (근로자 귀책사유에 의한 징계해고·권고사직).
- 출처(source): 실사유 코드.docx
- Multi Query: 미실행
- 답변:

```text
직원이 회사 돈에 손을 대어 내보낸 경우는 [코드 26] 근로자 귀책사유에 의한 징계해고·권고사직으로 신고해야 합니다. 이 코드는 근로자의 중대한 귀책사유(공금 횡령 등)로 인해 징계해고를 당하거나 권고사직 형태로 퇴사하는 경우에 적용됩니다. 실업급여 수급이 제한될 수 있으며, 적법한 징계위원회 기록이 있어야 안전합니다.
```

### `H-02` (정확한 키워드/코드형)

- 질문: 26번 코드와 23번 코드는 어떻게 다른가요?
- 기대 답변 요지: 23번은 경영상 필요·인원 감축에 의한 퇴사, 26번은 근로자 귀책사유에 의한 징계해고·권고사직. 26번은 실업급여 수급이 제한될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 26번 코드와 23번 코드의 차이점은 무엇인가요? / 26번 코드와 23번 코드는 어떤 점에서 다릅니까? / 26번 코드와 23번 코드를 비교하면 어떤 차이가 있나요?
- 답변:

```text
26번 코드는 근로자의 중대한 귀책사유(공금 횡령, 장기 무단결근, 기밀 누설 등)로 인한 징계해고 또는 권고사직에 해당하며, 실업급여 수급이 제한될 수 있습니다. 반면 23번 코드는 경영상 필요, 회사 불황, 인원 감축 등 회사 사정에 의한 퇴사(희망퇴직, 명예퇴직, 권고사직 포함)로, 회사가 정부 지원금 혜택을 받는 데 제한이 생길 수 있으나 근로자 귀책사유는 없습니다. 즉, 26번은 근로자 귀책사유에 의한 퇴사이고 23번은 회사 사정에 의한 퇴사입니다.
```

### `H-03` (정확한 키워드/코드형)

- 질문: 사업장 이전으로 출퇴근이 왕복 몇 시간 이상 걸리게 되면 자진퇴사해도 실업급여를 받을 수 있나요?
- 기대 답변 요지: 왕복 3시간 이상.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 사업장 이전으로 출퇴근 시간이 왕복 몇 시간 이상일 때 자진퇴사해도 실업급여를 받을 수 있나요? / 사업장 이전으로 인해 출퇴근 시간이 왕복 몇 시간 이상 걸리면 자발적 퇴사 시 실업급여 수급이 가능한가요? / 출퇴근 시간이 사업장 이전으로 왕복 몇 시간 이상 늘어나면 자진퇴사해도 실업급여를 받을 수 있나요?
- 답변:

```text
사업장 이전으로 출퇴근이 왕복 3시간 이상 소요되게 되어 자진퇴사하는 경우, 회사에 원인이 있으므로 근로자가 실업급여를 받을 수 있는 중요한 코드(코드 12)에 해당합니다. 다만, 관련 증빙 자료(출퇴근 기록 등)를 철저히 보관해야 합니다.
```

### `H-04` (정확한 키워드/코드형)

- 질문: 고용보험 비적용과 이중고용은 변경 후 몇 번 코드로 통합되었나요?
- 기대 답변 요지: 41번 단일 코드로 병합.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 고용보험 비적용과 이중고용이 변경되어 통합된 코드는 몇 번인가요? / 고용보험 비적용 및 이중고용 관련 코드가 변경 후 몇 번으로 합쳐졌나요? / 고용보험 비적용과 이중고용이 변경되어 하나의 코드로 통합된 번호는 무엇인가요?
- 답변:

```text
고용보험 비적용과 이중고용은 변경 후 41번 코드로 통합되었습니다. 이는 중복성 코드 통폐합의 일환으로, 실무자의 코드 선택 부담을 줄이기 위해 이루어졌습니다.
```

### `H-05` (정확한 키워드/코드형)

- 질문: 금융감독원이 개설하기로 한 금융소비자정보 포털사이트의 이름은 무엇인가요?
- 기대 답변 요지: 파인(FINE).
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 금융감독원이 만들 예정인 금융소비자정보 포털사이트 명칭은 무엇인가요? / 금융소비자정보 포털사이트의 공식 명칭은 무엇인가요? / 금융감독원이 개설하는 금융소비자정보 포털사이트 이름이 어떻게 되나요?
- 답변:

```text
금융감독원은 2016년 9월 1일 개설 예정인 금융소비자정보 포털사이트 이름을 "파인(FINE)"이라고 명시하고 있습니다. 이 사이트에는 금융꿀팁 200선이 게시될 예정입니다.
```

### `H-06` (의미 기반 질문)

- 질문: 다른 사람 빚보증을 서주면 내 신용에 문제가 생기나요?
- 기대 답변 요지: 보증내역이 신용조회회사에 보내져 신용등급 산정에 반영되고, 채무자가 연체하지 않아도 보증인의 신용등급이 하락할 수 있다.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 다른 사람의 채무 보증을 서면 내 신용에 영향이 있나요? / 남의 빚 보증을 서면 내 신용등급에 문제가 생기나요? / 타인의 대출 보증을 서주면 내 신용 점수에 영향이 있나요?
- 답변:

```text
다른 사람을 위해 보증을 서면 보증내역이 신용조회회사에 전달되어 신용등급 산정 시 반영됩니다. 이 경우 채무자가 연체하지 않더라도 보증인의 신용등급이 하락할 수 있으므로, 보증을 서는 것은 가급적 피하는 것이 좋습니다.
```

### `H-07` (의미 기반 질문)

- 질문: 3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 무엇인가요?
- 기대 답변 요지: CATIA.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 3DEXPERIENCE 플랫폼에서 설계에 사용되는 애플리케이션은 무엇인가요? / 3DEXPERIENCE에서 설계 작업을 지원하는 소프트웨어는 어떤 것들이 있나요? / 3DEXPERIENCE 플랫폼 내 설계용 애플리케이션 종류는 무엇인가요?
- 답변:

```text
3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 CATIA입니다. 이 플랫폼은 설계(CATIA), 엔지니어링 및 해석(SIMULIA), 프로젝트 및 데이터 관리(ENOVIA), 디지털 제조 및 생산 계획(DELMIA) 등 핵심 애플리케이션을 하나로 통합하여 제공합니다.
```

---

## 수동 판정표 (사람이 채운다)

자동 집계로 대체할 수 없는 항목이다. 위 답변 전문을 보고 직접 채운다.

| ID | 정답 여부 | 정보 누락 | Hallucination | 출처 정확성 | 비고 |
|---|---|---|---|---|---|
| `H-01` | | | | | |
| `H-02` | | | | | |
| `H-03` | | | | | |
| `H-04` | | | | | |
| `H-05` | | | | | |
| `H-06` | | | | | |
| `H-07` | | | | | |

- raw 데이터: `results/baseline_hard_raw.json`

