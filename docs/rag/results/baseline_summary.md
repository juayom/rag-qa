# 평가 결과 요약 — `baseline`

`scripts/eval_run.py`가 자동 생성한 파일이다. 수동 편집 시 재실행하면 덮어써진다.

---

## 테스트 조건

- config: `baseline`
- 실행 시각: 2026-09-22 14:43:15 ~ 2026-09-22 14:53:06
- 실행 환경: Conda `rag_env` / Qdrant `6333` / FastAPI
- 호출 대상: `POST http://127.0.0.1:8001/chat` (server.py)
- 질문셋: `docs/rag/questions.json` (v1.0, 23문항)
- Re-ranker: Dongjin-kr/ko-reranker (Cross Encoder, llm/reranker.py)
- 평가 횟수
  - 정확도 지표(Hit@K, 정답 여부, 정보 누락, Hallucination): **23문항 × 1회**
  - 시간 지표(retrieval / reranking / gpt / total): **대표 7문항 × 3회 평균, 회차별 값 병기**
  - 시간 지표 대표 문항: `F-01`, `L-01`, `K-01`, `S-02`, `A-01`, `C-01`, `O-02`
- top_k / 후보 수는 `vectorstore/retriever.py`의 질문 유형 판단에 따라 자동 결정된다(일반 8/3/8, 목록형 15/10/15). 질문별 관측값은 아래 상세표에 기록한다.
- 워밍업: 본 측정 전 1회 수행하고 **집계에서 제외**했다. 질문 `이즈파크는 어떤 회사인가요?`, 워밍업 total_ms = 9541.79 (참고용, 아래 어떤 평균에도 포함되지 않음)

### 실제 실행 명령어

```powershell
python scripts/eval_run.py --config baseline --repeat 3
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
| 정상 응답 문항 수 | 23 / 23 |
| **검색 단계** Hit@검색후보수 (범위 내 20문항) | 20 / 20 (100.0%) |
| **검색 단계** 정답 chunk 평균 순위 (Hit 문항) | 1.4 |
| **검색 단계** 평균 후보 수 | 28.26 |
| **Re-ranking 단계** Hit@rerank_top_k (범위 내 20문항) | 20 / 20 (100.0%) |
| **Re-ranking 단계** 정답 chunk 평균 순위 (Hit 문항) | 1.2 |
| Re-ranking에서 정답 chunk 탈락 | 0문항 |
| Multi Query 실행 비율 | 22 / 23 (95.7%) |
| 문서 범위 밖 질문 거절 (문자열 자동 판정) | 3 / 3 |

### 유형별 집계 (1회차)

| 유형 | 문항 수 | 검색 Hit | 검색 순위 | 재랭킹 Hit | 재랭킹 순위 | Multi Query 실행 | 평균 total_ms |
|---|---|---|---|---|---|---|---|
| 일반 사실형 | 3 | 3 / 3 | 1.0 | 3 / 3 | 1.0 | 2 / 3 | 12732.66 |
| 전체/목록형 | 4 | 4 / 4 | 1.75 | 4 / 4 | 1.25 | 4 / 4 | 21352.67 |
| 정확한 키워드/코드형 | 4 | 4 / 4 | 1.25 | 4 / 4 | 1.0 | 4 / 4 | 16576.47 |
| 의미 기반 질문 | 3 | 3 / 3 | 1.67 | 3 / 3 | 1.67 | 3 / 3 | 16139.55 |
| 짧고 모호한 질문 | 3 | 3 / 3 | 1.0 | 3 / 3 | 1.0 | 3 / 3 | 15317.41 |
| 복합 질문 | 3 | 3 / 3 | 1.67 | 3 / 3 | 1.33 | 3 / 3 | 15004.89 |
| 문서 범위 밖 질문 | 3 | 해당 없음 | - | 해당 없음 | - | 3 / 3 | 13113.34 |

---

## 시간 지표 (대표 7문항 × 3회)

| 질문 ID | 지표 | 1회차 | 2회차 | 3회차 | 평균 |
|---|---|---|---|---|---|
| `F-01` | retrieval_ms | 2176.78 | 2247.37 | 2456.3 | **2293.48** |
| `F-01` | reranking_ms | 7409.81 | 7854.15 | 7586.65 | **7616.87** |
| `F-01` | gpt_ms | 923.35 | 1042.73 | 1033.71 | **999.93** |
| `F-01` | total_ms | 11449.81 | 12314.57 | 12328.24 | **12030.87** |
| `L-01` | retrieval_ms | 2324.69 | 2403.41 | 2408.18 | **2378.76** |
| `L-01` | reranking_ms | 13148.56 | 15726.67 | 14610.57 | **14495.27** |
| `L-01` | gpt_ms | 2310.67 | 2100.81 | 2025.0 | **2145.49** |
| `L-01` | total_ms | 18977.26 | 21211.96 | 20432.49 | **20207.24** |
| `K-01` | retrieval_ms | 2475.76 | 2826.45 | 2273.11 | **2525.11** |
| `K-01` | reranking_ms | 11891.49 | 9535.77 | 9794.55 | **10407.27** |
| `K-01` | gpt_ms | 1787.48 | 1841.95 | 1577.0 | **1735.48** |
| `K-01` | total_ms | 17341.84 | 15200.65 | 14628.78 | **15723.76** |
| `S-02` | retrieval_ms | 2272.51 | 2278.86 | 2229.9 | **2260.42** |
| `S-02` | reranking_ms | 11719.64 | 10083.91 | 10304.05 | **10702.53** |
| `S-02` | gpt_ms | 1254.35 | 1421.77 | 1991.52 | **1555.88** |
| `S-02` | total_ms | 16643.76 | 15224.93 | 15902.5 | **15923.73** |
| `A-01` | retrieval_ms | 2171.23 | 2204.75 | 2336.52 | **2237.5** |
| `A-01` | reranking_ms | 9043.59 | 9230.53 | 8461.82 | **8911.98** |
| `A-01` | gpt_ms | 1753.88 | 1584.32 | 1877.56 | **1738.59** |
| `A-01` | total_ms | 14104.3 | 13852.37 | 13978.17 | **13978.28** |
| `C-01` | retrieval_ms | 2373.28 | 2241.35 | 2472.85 | **2362.49** |
| `C-01` | reranking_ms | 11955.8 | 11359.03 | 10106.94 | **11140.59** |
| `C-01` | gpt_ms | 2086.54 | 2486.24 | 1873.41 | **2148.73** |
| `C-01` | total_ms | 17724.45 | 17209.76 | 15717.22 | **16883.81** |
| `O-02` | retrieval_ms | 2269.25 | 2093.17 | 2161.42 | **2174.61** |
| `O-02` | reranking_ms | 7549.42 | 8111.69 | 8354.99 | **8005.37** |
| `O-02` | gpt_ms | 1084.36 | 908.7 | 1012.83 | **1001.96** |
| `O-02` | total_ms | 12236.25 | 12392.22 | 12650.61 | **12426.36** |

### 대표 문항 평균 (회차 전체 기준)

| 지표 | 평균 |
|---|---|
| 평균 retrieval_ms | 2318.91 |
| 평균 reranking_ms | 10182.84 |
| 평균 gpt_ms | 1618.01 |
| 평균 total_ms | 15310.58 |
| 평균 multi_query_ms | 1190.0 |

> 목록형 문항은 `retrieval_top_k=15 / rerank_top_k=10`, 그 외는 `8 / 3`이므로 **유형 간 시간 비교는 하지 않는다.** 비교는 항상 동일 질문 ID × 방식 간으로만 수행한다.

### 참고 — 1회차 전체 문항 평균

| 지표 | 평균 |
|---|---|
| 평균 retrieval_ms | 2240.48 |
| 평균 reranking_ms | 11043.03 |
| 평균 gpt_ms | 1520.85 |
| 평균 total_ms | 16027.83 |

---

## 질문별 단계별 정답 chunk 추적 (1회차)

| ID | 유형 | 검색 후보 수 | 검색 Hit | 검색 순위 | 재랭킹 후보 수 | 최종 Top-K | 재랭킹 Hit | 재랭킹 순위 |
|---|---|---|---|---|---|---|---|---|
| `F-01` | 일반 사실형 | 28 | O | 1 | 8 | 3 | O | 1 |
| `F-02` | 일반 사실형 | 24 | O | 1 | 8 | 3 | O | 1 |
| `F-03` | 일반 사실형 | 25 | O | 1 | 8 | 3 | O | 1 |
| `L-01` | 전체/목록형 | 32 | O | 1 | 15 | 10 | O | 1 |
| `L-02` | 전체/목록형 | 32 | O | 2 | 15 | 10 | O | 2 |
| `L-03` | 전체/목록형 | 32 | O | 3 | 15 | 10 | O | 1 |
| `L-04` | 전체/목록형 | 32 | O | 1 | 15 | 10 | O | 1 |
| `K-01` | 정확한 키워드/코드형 | 27 | O | 2 | 8 | 3 | O | 1 |
| `K-02` | 정확한 키워드/코드형 | 29 | O | 1 | 8 | 3 | O | 1 |
| `K-03` | 정확한 키워드/코드형 | 28 | O | 1 | 8 | 3 | O | 1 |
| `K-04` | 정확한 키워드/코드형 | 26 | O | 1 | 8 | 3 | O | 1 |
| `S-01` | 의미 기반 질문 | 26 | O | 3 | 8 | 3 | O | 3 |
| `S-02` | 의미 기반 질문 | 27 | O | 1 | 8 | 3 | O | 1 |
| `S-03` | 의미 기반 질문 | 27 | O | 1 | 8 | 3 | O | 1 |
| `A-01` | 짧고 모호한 질문 | 31 | O | 1 | 8 | 3 | O | 1 |
| `A-02` | 짧고 모호한 질문 | 27 | O | 1 | 8 | 3 | O | 1 |
| `A-03` | 짧고 모호한 질문 | 27 | O | 1 | 8 | 3 | O | 1 |
| `C-01` | 복합 질문 | 28 | O | 3 | 8 | 3 | O | 1 |
| `C-02` | 복합 질문 | 32 | O | 1 | 8 | 3 | O | 1 |
| `C-03` | 복합 질문 | 27 | O | 1 | 8 | 3 | O | 2 |
| `O-01` | 문서 범위 밖 질문 | 28 | 해당 없음 | - | 8 | 3 | 해당 없음 | - |
| `O-02` | 문서 범위 밖 질문 | 26 | 해당 없음 | - | 8 | 3 | 해당 없음 | - |
| `O-03` | 문서 범위 밖 질문 | 29 | 해당 없음 | - | 8 | 3 | 해당 없음 | - |

---

## 질문별 실행 조건 및 시간 (1회차)

| ID | 선택 Collection | top_k | MQ | 기대 항목 | 누락 항목 | retrieval_ms | rerank_ms | gpt_ms | total_ms |
|---|---|---|---|---|---|---|---|---|---|
| `F-01` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2176.78 | 7409.81 | 923.35 | 11449.81 |
| `F-02` | ALL(3) - Routing 미적용 | 8 | X | 1 / 1 | - | 652.65 | 8164.8 | 1602.77 | 10420.74 |
| `F-03` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2272.95 | 9664.65 | 1163.6 | 16327.43 |
| `L-01` | ALL(3) - Routing 미적용 | 15 | O | 10 / 10 | - | 2324.69 | 13148.56 | 2310.67 | 18977.26 |
| `L-02` | ALL(3) - Routing 미적용 | 15 | O | 1 / 3 | 스마트 제조, 클라우드 | 2544.29 | 16619.15 | 2066.02 | 22375.84 |
| `L-03` | ALL(3) - Routing 미적용 | 15 | O | 8 / 8 | - | 2228.02 | 18870.43 | 1767.04 | 23964.15 |
| `L-04` | ALL(3) - Routing 미적용 | 15 | O | 3 / 3 | - | 2172.58 | 15231.29 | 1583.41 | 20093.42 |
| `K-01` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2475.76 | 11891.49 | 1787.48 | 17341.84 |
| `K-02` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2375.12 | 12101.2 | 1863.12 | 17710.71 |
| `K-03` | ALL(3) - Routing 미적용 | 8 | O | 4 / 4 | - | 2078.74 | 10725.73 | 1124.54 | 15117.74 |
| `K-04` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2123.15 | 11934.37 | 1093.54 | 16135.57 |
| `S-01` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2472.48 | 11999.67 | 1573.37 | 17287.85 |
| `S-02` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2272.51 | 11719.64 | 1254.35 | 16643.76 |
| `S-03` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2373.57 | 9504.53 | 1323.82 | 14487.05 |
| `A-01` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2171.23 | 9043.59 | 1753.88 | 14104.3 |
| `A-02` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2034.39 | 11611.75 | 3025.03 | 17728.66 |
| `A-03` | ALL(3) - Routing 미적용 | 8 | O | 1 / 1 | - | 2645.36 | 8679.08 | 1613.13 | 14119.28 |
| `C-01` | ALL(3) - Routing 미적용 | 8 | O | 3 / 3 | - | 2373.28 | 11955.8 | 2086.54 | 17724.45 |
| `C-02` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2658.74 | 9739.35 | 1155.37 | 14686.46 |
| `C-03` | ALL(3) - Routing 미적용 | 8 | O | 2 / 2 | - | 2446.82 | 7703.5 | 1194.57 | 12603.77 |
| `O-01` | ALL(3) - Routing 미적용 | 8 | O | - | - | 2068.72 | 9200.76 | 852.41 | 13300.25 |
| `O-02` | ALL(3) - Routing 미적용 | 8 | O | - | - | 2269.25 | 7549.42 | 1084.36 | 12236.25 |
| `O-03` | ALL(3) - Routing 미적용 | 8 | O | - | - | 2319.92 | 9521.23 | 777.16 | 13803.53 |

> `기대 항목` / `누락 항목`은 questions.json의 `expected_items` 문자열 포함 검사 결과이며 **자동 보조 지표**이다. 최종 정답 여부와 정보 누락은 아래 수동 판정표에서 사람이 확정한다.

---

## 검색 근거 (1회차)

검색 단계는 상위 10건과 정답 chunk에 해당하는 건만 표시한다(전체는 raw.json의 `retrieval_candidates`).

### `F-01` 이즈파크의 대표이사와 설립일은 언제인가요?

**검색 단계 (Re-ranking 전, 후보 28건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5161 | O | O |
| 2 | ispark_company_profile | 4 | 0.461 | O |  |
| 3 | ispark_company_profile | 3 | 0.4484 | O |  |
| 4 | ispark_company_profile | 10 | 0.4114 | O |  |
| 5 | ispark_company_profile | 5 | 0.4049 | O |  |
| 6 | ispark_company_profile | 9 | 0.3848 | O |  |
| 7 | ispark_company_profile | 6 | 0.3537 | O |  |
| 8 | ispark_company_profile | 2 | 0.3309 | O |  |
| 9 | ispark_company_profile | 7 | 0.3248 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.2185 | X |  |
| ... | 이하 18건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5161 | 0.9686 | O |
| 2 | ispark_company_profile | 4 | 0.461 | 0.0198 |  |
| 3 | ispark_company_profile | 3 | 0.4484 | 0.0019 |  |

### `F-02` 10만원 이상의 금액을 며칠 이상 연체하면 신용등급이 하락하나요?

**검색 단계 (Re-ranking 전, 후보 24건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.5268 | O | O |
| 2 | credit_management_guide | 5 | 0.5251 | O |  |
| 3 | credit_management_guide | 2 | 0.5024 | O |  |
| 4 | credit_management_guide | 1 | 0.4807 | O |  |
| 5 | credit_management_guide | 4 | 0.4752 | O | O |
| 6 | credit_management_guide | 10 | 0.4418 | O |  |
| 7 | credit_management_guide | 12 | 0.4362 | O |  |
| 8 | credit_management_guide | 8 | 0.419 | O |  |
| 9 | due_diligence_reason_codes | 9 | 0.3158 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.3101 | X |  |
| ... | 이하 14건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.5268 | 0.9999 | O |
| 2 | credit_management_guide | 5 | 0.5251 | 0.9999 |  |
| 3 | credit_management_guide | 1 | 0.4807 | 0.1695 |  |

### `F-03` 피보험자격 상실신고서는 언제까지 어디에 제출해야 하나요?

**검색 단계 (Re-ranking 전, 후보 25건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 9 | 0.5465 | O | O |
| 2 | due_diligence_reason_codes | 8 | 0.5318 | O |  |
| 3 | due_diligence_reason_codes | 7 | 0.4282 | O |  |
| 4 | due_diligence_reason_codes | 5 | 0.407 | O |  |
| 5 | credit_management_guide | 12 | 0.3616 | O |  |
| 6 | credit_management_guide | 10 | 0.3576 | O |  |
| 7 | due_diligence_reason_codes | 4 | 0.354 | O |  |
| 8 | due_diligence_reason_codes | 3 | 0.352 | O |  |
| 9 | credit_management_guide | 13 | 0.3461 | X |  |
| 10 | due_diligence_reason_codes | 6 | 0.3416 | X |  |
| ... | 이하 15건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 9 | 0.5465 | 0.9897 | O |
| 2 | due_diligence_reason_codes | 8 | 0.5318 | 0.0307 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4282 | 0.0019 |  |

### `L-01` 현명한 신용관리 요령 10가지를 모두 알려주세요.

**검색 단계 (Re-ranking 전, 후보 32건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 13 | 0.5545 | O | O |
| 2 | credit_management_guide | 11 | 0.5289 | O | O |
| 3 | credit_management_guide | 4 | 0.4774 | O |  |
| 4 | credit_management_guide | 1 | 0.454 | O |  |
| 5 | credit_management_guide | 5 | 0.4531 | O | O |
| 6 | credit_management_guide | 2 | 0.4446 | O |  |
| 7 | credit_management_guide | 3 | 0.4227 | O | O |
| 8 | credit_management_guide | 10 | 0.4131 | O | O |
| 9 | credit_management_guide | 7 | 0.4111 | O | O |
| 10 | credit_management_guide | 12 | 0.4052 | O | O |
| 14 | credit_management_guide | 6 | 0.3563 | O | O |
| 17 | credit_management_guide | 8 | 0.3449 | X | O |
| ... | 이하 20건 생략 | | | | |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 5 | 0.4531 | 0.9908 | O |
| 2 | credit_management_guide | 2 | 0.4446 | 0.9595 |  |
| 3 | credit_management_guide | 11 | 0.5289 | 0.6691 | O |
| 4 | credit_management_guide | 13 | 0.5545 | 0.6623 | O |
| 5 | credit_management_guide | 4 | 0.4774 | 0.3866 |  |
| 6 | credit_management_guide | 1 | 0.454 | 0.2217 |  |
| 7 | credit_management_guide | 3 | 0.4227 | 0.1455 | O |
| 8 | credit_management_guide | 12 | 0.4052 | 0.059 | O |
| 9 | credit_management_guide | 10 | 0.4131 | 0.0556 | O |
| 10 | credit_management_guide | 6 | 0.3563 | 0.0432 | O |

### `L-02` 이즈파크의 주요 사업 영역을 모두 알려주세요.

**검색 단계 (Re-ranking 전, 후보 32건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 5 | 0.6202 | O |  |
| 2 | ispark_company_profile | 1 | 0.5601 | O | O |
| 3 | ispark_company_profile | 3 | 0.5456 | O |  |
| 4 | ispark_company_profile | 9 | 0.5375 | O |  |
| 5 | ispark_company_profile | 7 | 0.5225 | O |  |
| 6 | ispark_company_profile | 2 | 0.4973 | O | O |
| 7 | ispark_company_profile | 6 | 0.4831 | O |  |
| 8 | ispark_company_profile | 4 | 0.4792 | O |  |
| 9 | ispark_company_profile | 10 | 0.4714 | O |  |
| 10 | ispark_company_profile | 8 | 0.382 | O |  |
| ... | 이하 22건 생략 | | | | |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 5 | 0.6202 | 0.9854 |  |
| 2 | ispark_company_profile | 1 | 0.5601 | 0.9743 | O |
| 3 | ispark_company_profile | 4 | 0.4792 | 0.4827 |  |
| 4 | ispark_company_profile | 7 | 0.5225 | 0.3904 |  |
| 5 | ispark_company_profile | 3 | 0.5456 | 0.1972 |  |
| 6 | ispark_company_profile | 9 | 0.5375 | 0.1411 |  |
| 7 | ispark_company_profile | 10 | 0.4714 | 0.017 |  |
| 8 | ispark_company_profile | 8 | 0.382 | 0.0094 |  |
| 9 | ispark_company_profile | 6 | 0.4831 | 0.0046 |  |
| 10 | credit_management_guide | 10 | 0.279 | 0.0004 |  |

### `L-03` 변경 후 상실사유 중분류 코드 8개를 모두 나열해주세요.

**검색 단계 (Re-ranking 전, 후보 32건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.5488 | O |  |
| 2 | due_diligence_reason_codes | 1 | 0.5411 | O |  |
| 3 | due_diligence_reason_codes | 2 | 0.4859 | O | O |
| 4 | due_diligence_reason_codes | 4 | 0.4596 | O | O |
| 5 | due_diligence_reason_codes | 8 | 0.4529 | O |  |
| 6 | due_diligence_reason_codes | 7 | 0.4477 | O |  |
| 7 | due_diligence_reason_codes | 3 | 0.4127 | O | O |
| 8 | due_diligence_reason_codes | 6 | 0.4008 | O |  |
| 9 | due_diligence_reason_codes | 9 | 0.3633 | O |  |
| 10 | credit_management_guide | 9 | 0.3323 | O |  |
| ... | 이하 22건 생략 | | | | |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 2 | 0.4859 | 0.741 | O |
| 2 | due_diligence_reason_codes | 5 | 0.5488 | 0.0969 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4477 | 0.0092 |  |
| 4 | due_diligence_reason_codes | 1 | 0.5411 | 0.0074 |  |
| 5 | due_diligence_reason_codes | 6 | 0.4008 | 0.0044 |  |
| 6 | due_diligence_reason_codes | 3 | 0.4127 | 0.0019 | O |
| 7 | due_diligence_reason_codes | 8 | 0.4529 | 0.0008 |  |
| 8 | credit_management_guide | 10 | 0.3028 | 0.0003 |  |
| 9 | due_diligence_reason_codes | 4 | 0.4596 | 0.0001 | O |
| 10 | credit_management_guide | 4 | 0.3229 | 0.0001 |  |

### `L-04` 이즈파크의 핵심 가치 3가지를 모두 알려주세요.

**검색 단계 (Re-ranking 전, 후보 32건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 3 | 0.5728 | O | O |
| 2 | ispark_company_profile | 1 | 0.5178 | O |  |
| 3 | ispark_company_profile | 5 | 0.5113 | O |  |
| 4 | ispark_company_profile | 9 | 0.4735 | O |  |
| 5 | ispark_company_profile | 7 | 0.4583 | O |  |
| 6 | ispark_company_profile | 6 | 0.4368 | O |  |
| 7 | ispark_company_profile | 2 | 0.4218 | O |  |
| 8 | ispark_company_profile | 4 | 0.4206 | O | O |
| 9 | ispark_company_profile | 10 | 0.4147 | O |  |
| 10 | ispark_company_profile | 8 | 0.3542 | O |  |
| ... | 이하 22건 생략 | | | | |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 3 | 0.5728 | 0.9975 | O |
| 2 | ispark_company_profile | 5 | 0.5113 | 0.7969 |  |
| 3 | ispark_company_profile | 4 | 0.4206 | 0.6551 | O |
| 4 | ispark_company_profile | 1 | 0.5178 | 0.3406 |  |
| 5 | ispark_company_profile | 7 | 0.4583 | 0.1338 |  |
| 6 | ispark_company_profile | 10 | 0.4147 | 0.0866 |  |
| 7 | ispark_company_profile | 6 | 0.4368 | 0.0353 |  |
| 8 | ispark_company_profile | 9 | 0.4735 | 0.0267 |  |
| 9 | credit_management_guide | 12 | 0.2617 | 0.0004 |  |
| 10 | ispark_company_profile | 8 | 0.3542 | 0.0003 |  |

### `K-01` 코드 26은 어떤 경우에 적용되나요?

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.4631 | O |  |
| 2 | due_diligence_reason_codes | 7 | 0.4375 | O | O |
| 3 | due_diligence_reason_codes | 4 | 0.4292 | O |  |
| 4 | due_diligence_reason_codes | 6 | 0.4289 | O |  |
| 5 | due_diligence_reason_codes | 1 | 0.4069 | O |  |
| 6 | due_diligence_reason_codes | 3 | 0.3943 | O |  |
| 7 | due_diligence_reason_codes | 2 | 0.3923 | O |  |
| 8 | credit_management_guide | 7 | 0.3789 | O |  |
| 9 | credit_management_guide | 11 | 0.377 | X |  |
| 10 | credit_management_guide | 9 | 0.37 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.4375 | 0.9099 | O |
| 2 | due_diligence_reason_codes | 5 | 0.4631 | 0.5321 |  |
| 3 | due_diligence_reason_codes | 3 | 0.3943 | 0.0345 |  |

### `K-02` 자진퇴사를 권고사직으로 허위 신고하면 과태료가 얼마인가요?

**검색 단계 (Re-ranking 전, 후보 29건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 8 | 0.4904 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.4651 | O |  |
| 3 | due_diligence_reason_codes | 9 | 0.4359 | O |  |
| 4 | due_diligence_reason_codes | 6 | 0.4212 | O |  |
| 5 | credit_management_guide | 5 | 0.3891 | O |  |
| 6 | due_diligence_reason_codes | 5 | 0.3883 | O |  |
| 7 | due_diligence_reason_codes | 2 | 0.3723 | O |  |
| 8 | credit_management_guide | 3 | 0.3721 | O |  |
| 9 | due_diligence_reason_codes | 3 | 0.3593 | X |  |
| 10 | credit_management_guide | 2 | 0.3465 | X |  |
| ... | 이하 19건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 8 | 0.4904 | 0.9982 | O |
| 2 | due_diligence_reason_codes | 9 | 0.4359 | 0.0345 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4651 | 0.0091 |  |

### `K-03` 3DEXPERIENCE 플랫폼에 통합된 핵심 어플리케이션 이름을 알려주세요.

**검색 단계 (Re-ranking 전, 후보 28건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5285 | O | O |
| 2 | ispark_company_profile | 2 | 0.4742 | O |  |
| 3 | ispark_company_profile | 7 | 0.3533 | O |  |
| 4 | ispark_company_profile | 5 | 0.333 | O |  |
| 5 | ispark_company_profile | 4 | 0.3222 | O |  |
| 6 | ispark_company_profile | 1 | 0.3171 | O |  |
| 7 | ispark_company_profile | 10 | 0.3081 | O |  |
| 8 | ispark_company_profile | 8 | 0.3031 | O |  |
| 9 | ispark_company_profile | 3 | 0.2938 | X |  |
| 10 | credit_management_guide | 11 | 0.2264 | X |  |
| ... | 이하 18건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5285 | 0.9983 | O |
| 2 | ispark_company_profile | 2 | 0.4742 | 0.0513 |  |
| 3 | ispark_company_profile | 8 | 0.3031 | 0.0002 |  |

### `K-04` 코드 32는 무엇인가요?

**검색 단계 (Re-ranking 전, 후보 26건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.3723 | O | O |
| 2 | due_diligence_reason_codes | 4 | 0.3647 | O |  |
| 3 | due_diligence_reason_codes | 1 | 0.3608 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.3562 | O |  |
| 5 | due_diligence_reason_codes | 3 | 0.3335 | O | O |
| 6 | due_diligence_reason_codes | 6 | 0.3167 | O |  |
| 7 | credit_management_guide | 7 | 0.2996 | O |  |
| 8 | credit_management_guide | 11 | 0.2974 | O |  |
| 9 | due_diligence_reason_codes | 7 | 0.2934 | X |  |
| 10 | credit_management_guide | 9 | 0.2913 | X |  |
| ... | 이하 16건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.3723 | 0.1442 | O |
| 2 | due_diligence_reason_codes | 3 | 0.3335 | 0.0346 | O |
| 3 | due_diligence_reason_codes | 2 | 0.3562 | 0.0007 |  |

### `S-01` 빚을 갚지 못하고 계속 밀리면 어떤 불이익이 생기나요?

**검색 단계 (Re-ranking 전, 후보 26건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 3 | 0.3916 | O |  |
| 2 | credit_management_guide | 2 | 0.3624 | O |  |
| 3 | credit_management_guide | 4 | 0.3616 | O | O |
| 4 | due_diligence_reason_codes | 2 | 0.3528 | O |  |
| 5 | credit_management_guide | 5 | 0.3498 | O |  |
| 6 | due_diligence_reason_codes | 7 | 0.3482 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.3468 | O |  |
| 8 | credit_management_guide | 10 | 0.3435 | O |  |
| 9 | credit_management_guide | 8 | 0.3417 | X | O |
| 10 | credit_management_guide | 12 | 0.3409 | X |  |
| 12 | credit_management_guide | 3 | 0.3294 | X | O |
| 13 | credit_management_guide | 6 | 0.3178 | X | O |
| ... | 이하 14건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 5 | 0.3498 | 0.0688 |  |
| 2 | credit_management_guide | 10 | 0.3435 | 0.0379 |  |
| 3 | credit_management_guide | 4 | 0.3616 | 0.0113 | O |

### `S-02` 회사가 멀리 이전해서 출퇴근이 너무 힘들어져 그만두면 실업급여를 받을 수 있나요?

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.6061 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.5438 | O |  |
| 3 | due_diligence_reason_codes | 3 | 0.4892 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.4556 | O |  |
| 5 | due_diligence_reason_codes | 5 | 0.4347 | O |  |
| 6 | due_diligence_reason_codes | 8 | 0.4151 | O |  |
| 7 | due_diligence_reason_codes | 9 | 0.3909 | O |  |
| 8 | credit_management_guide | 2 | 0.3795 | O |  |
| 9 | credit_management_guide | 12 | 0.3544 | X |  |
| 10 | credit_management_guide | 10 | 0.3465 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.6061 | 0.7142 | O |
| 2 | due_diligence_reason_codes | 7 | 0.5438 | 0.0847 |  |
| 3 | due_diligence_reason_codes | 5 | 0.4347 | 0.0383 |  |

### `S-03` 이즈파크는 환경 보호에 어떤 기여를 하고 있나요?

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 9 | 0.5104 | O | O |
| 2 | ispark_company_profile | 3 | 0.4574 | O |  |
| 3 | ispark_company_profile | 10 | 0.4516 | O | O |
| 4 | ispark_company_profile | 1 | 0.446 | O |  |
| 5 | ispark_company_profile | 6 | 0.4253 | O |  |
| 6 | ispark_company_profile | 5 | 0.4224 | O |  |
| 7 | ispark_company_profile | 7 | 0.4074 | O |  |
| 8 | ispark_company_profile | 4 | 0.376 | O |  |
| 9 | due_diligence_reason_codes | 3 | 0.2624 | X |  |
| 10 | due_diligence_reason_codes | 8 | 0.2447 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 10 | 0.4516 | 0.9721 | O |
| 2 | ispark_company_profile | 9 | 0.5104 | 0.1188 | O |
| 3 | ispark_company_profile | 7 | 0.4074 | 0.0606 |  |

### `A-01` 신용등급?

**검색 단계 (Re-ranking 전, 후보 31건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 5 | 0.4209 | O | O |
| 2 | credit_management_guide | 3 | 0.3936 | O | O |
| 3 | credit_management_guide | 1 | 0.3617 | O |  |
| 4 | credit_management_guide | 10 | 0.3543 | O |  |
| 5 | credit_management_guide | 12 | 0.3536 | O |  |
| 6 | credit_management_guide | 9 | 0.3381 | O |  |
| 7 | credit_management_guide | 4 | 0.3332 | O |  |
| 8 | credit_management_guide | 7 | 0.33 | O |  |
| 9 | credit_management_guide | 6 | 0.3299 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.3206 | X |  |
| ... | 이하 21건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 5 | 0.4209 | 0.1904 | O |
| 2 | credit_management_guide | 9 | 0.3381 | 0.1301 |  |
| 3 | credit_management_guide | 4 | 0.3332 | 0.0619 |  |

### `A-02` 권고사직

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 8 | 0.3952 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.3502 | O | O |
| 3 | due_diligence_reason_codes | 3 | 0.3493 | O | O |
| 4 | due_diligence_reason_codes | 2 | 0.3048 | O |  |
| 5 | due_diligence_reason_codes | 9 | 0.2828 | O |  |
| 6 | due_diligence_reason_codes | 6 | 0.2621 | O |  |
| 7 | due_diligence_reason_codes | 5 | 0.2564 | O |  |
| 8 | credit_management_guide | 10 | 0.2339 | O |  |
| 9 | due_diligence_reason_codes | 4 | 0.2337 | X |  |
| 10 | credit_management_guide | 12 | 0.2241 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.3502 | 0.1248 | O |
| 2 | due_diligence_reason_codes | 8 | 0.3952 | 0.0657 | O |
| 3 | due_diligence_reason_codes | 3 | 0.3493 | 0.0161 | O |

### `A-03` 이즈파크

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5672 | O | O |
| 2 | ispark_company_profile | 3 | 0.5102 | O |  |
| 3 | ispark_company_profile | 5 | 0.4972 | O |  |
| 4 | ispark_company_profile | 6 | 0.4832 | O |  |
| 5 | ispark_company_profile | 9 | 0.4739 | O |  |
| 6 | ispark_company_profile | 7 | 0.4533 | O |  |
| 7 | ispark_company_profile | 10 | 0.4446 | O |  |
| 8 | ispark_company_profile | 2 | 0.4445 | O |  |
| 9 | due_diligence_reason_codes | 5 | 0.2574 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.257 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5672 | 0.9995 | O |
| 2 | ispark_company_profile | 3 | 0.5102 | 0.9596 |  |
| 3 | ispark_company_profile | 10 | 0.4446 | 0.9571 |  |

### `C-01` 코드 23과 코드 26의 실업급여 수급 차이는 무엇이고, 각각 어떤 경우에 적용되나요?

**검색 단계 (Re-ranking 전, 후보 28건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.5216 | O |  |
| 2 | due_diligence_reason_codes | 5 | 0.5193 | O |  |
| 3 | due_diligence_reason_codes | 7 | 0.4906 | O | O |
| 4 | due_diligence_reason_codes | 3 | 0.4768 | O |  |
| 5 | due_diligence_reason_codes | 2 | 0.4671 | O |  |
| 6 | due_diligence_reason_codes | 4 | 0.4305 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.4248 | O |  |
| 8 | due_diligence_reason_codes | 1 | 0.4153 | O |  |
| 9 | credit_management_guide | 9 | 0.3835 | X |  |
| 10 | credit_management_guide | 10 | 0.3699 | X |  |
| ... | 이하 18건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.4906 | 0.9994 | O |
| 2 | due_diligence_reason_codes | 6 | 0.5216 | 0.7931 |  |
| 3 | due_diligence_reason_codes | 3 | 0.4768 | 0.0407 |  |

### `C-02` 신용등급을 관리하려면 카드는 어떻게 쓰고, 연체가 이미 생겼을 때는 어떤 순서로 갚아야 하나요?

**검색 단계 (Re-ranking 전, 후보 32건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 8 | 0.6109 | O | O |
| 2 | credit_management_guide | 6 | 0.5987 | O | O |
| 3 | credit_management_guide | 7 | 0.507 | O |  |
| 4 | credit_management_guide | 9 | 0.5049 | O |  |
| 5 | credit_management_guide | 4 | 0.4479 | O |  |
| 6 | credit_management_guide | 3 | 0.4142 | O |  |
| 7 | credit_management_guide | 1 | 0.4114 | O |  |
| 8 | credit_management_guide | 11 | 0.4108 | O |  |
| 9 | credit_management_guide | 2 | 0.3975 | X |  |
| 10 | credit_management_guide | 12 | 0.396 | X |  |
| ... | 이하 22건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 8 | 0.6109 | 0.7791 | O |
| 2 | credit_management_guide | 6 | 0.5987 | 0.6562 | O |
| 3 | credit_management_guide | 9 | 0.5049 | 0.0658 |  |

### `C-03` 이즈파크의 설립 연도와, 타인을 위한 보증이 신용등급에 미치는 영향을 함께 알려주세요.

**검색 단계 (Re-ranking 전, 후보 27건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.4727 | O | O |
| 2 | ispark_company_profile | 3 | 0.4234 | O |  |
| 3 | ispark_company_profile | 9 | 0.4191 | O |  |
| 4 | credit_management_guide | 10 | 0.4174 | O | O |
| 5 | ispark_company_profile | 10 | 0.4155 | O |  |
| 6 | credit_management_guide | 12 | 0.4033 | O | O |
| 7 | ispark_company_profile | 4 | 0.4007 | O |  |
| 8 | ispark_company_profile | 5 | 0.3836 | O |  |
| 9 | ispark_company_profile | 7 | 0.3791 | X |  |
| 10 | ispark_company_profile | 6 | 0.3561 | X |  |
| ... | 이하 17건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 4 | 0.4007 | 0.0428 |  |
| 2 | credit_management_guide | 12 | 0.4033 | 0.0386 | O |
| 3 | credit_management_guide | 10 | 0.4174 | 0.0091 | O |

### `O-01` 양자역학의 불확정성 원리를 설명해주세요.

**검색 단계 (Re-ranking 전, 후보 28건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.2848 | O |  |
| 2 | due_diligence_reason_codes | 2 | 0.2695 | O |  |
| 3 | due_diligence_reason_codes | 5 | 0.2644 | O |  |
| 4 | due_diligence_reason_codes | 3 | 0.2553 | O |  |
| 5 | due_diligence_reason_codes | 6 | 0.247 | O |  |
| 6 | credit_management_guide | 10 | 0.2384 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.2356 | O |  |
| 8 | credit_management_guide | 2 | 0.232 | O |  |
| 9 | credit_management_guide | 5 | 0.2315 | X |  |
| 10 | credit_management_guide | 12 | 0.2298 | X |  |
| ... | 이하 18건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 2 | 0.232 | 0.0001 |  |
| 2 | credit_management_guide | 10 | 0.2384 | 0.0001 |  |
| 3 | due_diligence_reason_codes | 6 | 0.247 | 0.0001 |  |

### `O-02` 이즈파크의 2025년 연매출과 영업이익을 알려주세요.

**검색 단계 (Re-ranking 전, 후보 26건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.4535 | O |  |
| 2 | ispark_company_profile | 9 | 0.4506 | O |  |
| 3 | ispark_company_profile | 5 | 0.4453 | O |  |
| 4 | ispark_company_profile | 3 | 0.4372 | O |  |
| 5 | ispark_company_profile | 10 | 0.4294 | O |  |
| 6 | ispark_company_profile | 7 | 0.4154 | O |  |
| 7 | ispark_company_profile | 4 | 0.413 | O |  |
| 8 | ispark_company_profile | 6 | 0.4055 | O |  |
| 9 | ispark_company_profile | 2 | 0.3702 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.3466 | X |  |
| ... | 이하 16건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 4 | 0.413 | 0.0027 |  |
| 2 | ispark_company_profile | 10 | 0.4294 | 0.0024 |  |
| 3 | ispark_company_profile | 3 | 0.4372 | 0.0023 |  |

### `O-03` 이즈파크의 임직원 수와 평균 연봉은 얼마인가요?

**검색 단계 (Re-ranking 전, 후보 29건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 3 | 0.438 | O |  |
| 2 | ispark_company_profile | 10 | 0.4187 | O |  |
| 3 | due_diligence_reason_codes | 2 | 0.4085 | O |  |
| 4 | due_diligence_reason_codes | 6 | 0.4055 | O |  |
| 5 | due_diligence_reason_codes | 5 | 0.3974 | O |  |
| 6 | due_diligence_reason_codes | 8 | 0.3726 | O |  |
| 7 | ispark_company_profile | 3 | 0.3682 | O |  |
| 8 | due_diligence_reason_codes | 7 | 0.3672 | O |  |
| 9 | ispark_company_profile | 1 | 0.3644 | X |  |
| 10 | ispark_company_profile | 5 | 0.3628 | X |  |
| ... | 이하 19건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 10 | 0.4187 | 0.0022 |  |
| 2 | ispark_company_profile | 3 | 0.3682 | 0.0018 |  |
| 3 | due_diligence_reason_codes | 6 | 0.4055 | 0.0001 |  |

---

## 답변 전문 (1회차)

### `F-01` (일반 사실형)

- 질문: 이즈파크의 대표이사와 설립일은 언제인가요?
- 기대 답변 요지: 대표이사는 김갑산, 설립일은 2009년.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 CEO와 설립일은 언제입니까? / 이즈파크의 대표 임원과 회사 설립일자가 어떻게 되나요? / 이즈파크의 사장과 설립 날짜를 알려주세요.
- 답변:

```text
이즈파크의 대표이사는 김갑산이며, 설립일은 2009년입니다. 이 정보는 기업 개요 섹션에 명시되어 있습니다.
```

### `F-02` (일반 사실형)

- 질문: 10만원 이상의 금액을 며칠 이상 연체하면 신용등급이 하락하나요?
- 기대 답변 요지: 10만원 이상의 금액을 5영업일 이상 연체하면 신용평점이나 신용등급이 하락한다.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 미실행
- 답변:

```text
10만원 이상의 금액을 5영업일 이상 연체하면 신용평점이나 신용등급이 하락합니다. 따라서 좋은 신용등급을 유지하기 위해서는 소액이라도 연체를 절대 피해야 합니다.
```

### `F-03` (일반 사실형)

- 질문: 피보험자격 상실신고서는 언제까지 어디에 제출해야 하나요?
- 기대 답변 요지: 퇴사일이 속하는 달의 다음 달 15일까지 관할 근로복지공단에 제출.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 피보험자격 상실신고서는 제출 기한과 제출 장소가 어떻게 되나요? / 피보험자격 상실신고서 제출 마감일과 제출처는 어디인가요? / 피보험자격 상실신고서는 언제까지 어디에 내야 하나요?
- 답변:

```text
피보험자격 상실신고서는 근로자가 퇴사한 날이 속하는 달의 다음 달 15일까지 관할 근로복지공단에 제출해야 합니다. 예를 들어, 4월 20일 퇴사자의 경우 5월 15일까지 신고해야 합니다. 신고 기한을 엄수하지 않으면 사업장에 과태료가 부과될 수 있으므로 주의가 필요합니다.
```

### `L-01` (전체/목록형)

- 질문: 현명한 신용관리 요령 10가지를 모두 알려주세요.
- 기대 답변 요지: 신용관리 요령 10개 항목 전부.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 신용 관리를 잘하는 10가지 방법을 알려주세요. / 신용 점수를 높이기 위한 10가지 팁을 모두 설명해 주세요. / 효과적인 신용 관리 비법 10가지를 알려주세요.
- 답변:

```text
현명한 신용관리 요령 10가지는 다음과 같습니다. ① 평소 자기 신용등급에 관심 기울이기, ② 소액이라도 절대 연체하지 않기, ③ 신용카드 보다는 체크카드 사용하기, ④ 연체는 오래된 것부터 상환하기, ⑤ 과도한 빚은 고통의 시작임을 명심하기, ⑥ 주거래 금융회사 및 자동이체 이용하기, ⑦ 타인을 위한 보증은 가급적 피하기, ⑧ 대출 금융회사 신중하게 결정하기, ⑨ 신용평가 가점제 적극 활용하기, ⑩ 신용관리체험단 활용하기입니다.
```

### `L-02` (전체/목록형)

- 질문: 이즈파크의 주요 사업 영역을 모두 알려주세요.
- 기대 답변 요지: 스마트 제조 솔루션 / 디지털 트윈 및 XR(메타버스) / AI 및 클라우드 서비스 3개 영역.
- 출처(source): 이즈파크 회사 소개서.txt, 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 핵심 사업 분야를 전부 알려주세요. / 이즈파크가 주력하는 사업 영역을 모두 설명해 주세요. / 이즈파크의 주요 비즈니스 분야를 모두 알려줄 수 있나요?
- 답변:

```text
이즈파크의 주요 사업 영역은 제조업 혁신을 돕는 솔루션부터 최신 메타버스 및 XR 기술까지 폭넓게 포함합니다. 구체적으로 스마트 팩토리 구축, MES·QMS 고도화, AI 기반 스마트 예지보전 및 빅데이터 최적화, 3D CAD/CAM 및 PLM 비즈니스, 디지털 트윈과 메타버스, XR 기반 산업 안전 교육 및 설비 유지보수 매뉴얼 개발 등이 있습니다. 또한 항공우주, 자동차 부품, 하이테크, 산업 기계 등 다양한 핵심 산업군에 맞춤형 IT 컨설팅과 솔루션을 제공합니다.
```

### `L-03` (전체/목록형)

- 질문: 변경 후 상실사유 중분류 코드 8개를 모두 나열해주세요.
- 기대 답변 요지: 11 / 12 / 22 / 23 / 26 / 31 / 32 / 41 총 8개 코드.
- 출처(source): 실사유 코드.docx, 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 변경 후 상실사유 중분류 코드 8가지를 모두 알려주세요. / 변경된 상실사유 중분류 코드 8개를 전부 나열해 주세요. / 변경 후 상실사유 중분류 코드 8종을 모두 보여주세요.
- 답변:

```text
변경 후 상실사유 중분류 코드는 총 8개이며 다음과 같습니다. 11. 개인사정으로 인한 자진퇴사, 12. 사업장 이전, 근로조건변동, 임금체불 등으로 자진퇴사, 22. 폐업 도산, 23. 경영상 필요 및 회사불황으로 인원감축 등에 의한 퇴사(해고 권고사직 명예퇴직 포함), 26. 근로자의 귀책사유에 의한 징계해고 권고사직, 31. 정년, 32. 계약만료, 공사종료, 41. 고용보험 비적용, 이중 고용입니다.
```

### `L-04` (전체/목록형)

- 질문: 이즈파크의 핵심 가치 3가지를 모두 알려주세요.
- 기대 답변 요지: 고객 중심 / 지속적인 혁신 / 신뢰와 상생 파트너십.
- 출처(source): 이즈파크 회사 소개서.txt, 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 주요 가치 세 가지를 모두 설명해 주세요. / 이즈파크가 중요하게 여기는 핵심 가치 3가지를 알려 주세요. / 이즈파크의 3가지 핵심 가치를 모두 알려 주실 수 있나요?
- 답변:

```text
이즈파크의 핵심 가치는 첫째 고객 중심(Customer Centric), 둘째 지속적인 혁신(Continuous Innovation), 셋째 신뢰와 상생 파트너십(Trust & Partnership)입니다. 고객의 비즈니스 환경을 정확히 분석해 맞춤형 솔루션을 제공하고, 4차 산업혁명 시대에 맞춰 신기술에 대한 R&D 투자를 지속하며, 투명한 소통을 통해 장기적 동반 성장을 추구합니다.
```

### `K-01` (정확한 키워드/코드형)

- 질문: 코드 26은 어떤 경우에 적용되나요?
- 기대 답변 요지: 근로자의 중대한 귀책사유로 인한 징계해고·권고사직. 실업급여 수급이 제한될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 코드 26이 적용되는 상황은 무엇인가요? / 코드 26의 적용 조건은 어떻게 되나요? / 코드 26은 언제 사용되나요?
- 답변:

```text
코드 26은 근로자의 중대한 귀책사유(공금 횡령, 장기 무단결근, 기밀 누설 등)로 인해 징계해고를 당하거나, 해고를 피하기 위해 권고사직의 형태로 퇴사하는 경우에 적용됩니다. 이 경우 근로자에게 전적으로 중대한 잘못이 있어 실업급여 수급이 제한될 수 있으며, 적법한 징계위원회를 거친 기록이 있어야 안전합니다.
```

### `K-02` (정확한 키워드/코드형)

- 질문: 자진퇴사를 권고사직으로 허위 신고하면 과태료가 얼마인가요?
- 기대 답변 요지: 사업장에 최대 300만 원 이하의 과태료가 부과될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 자진퇴사를 권고사직으로 거짓 신고할 경우 부과되는 과태료는 얼마인가요? / 자발적 퇴사를 강제 퇴사로 허위 신고하면 과태료 금액이 어떻게 되나요? / 스스로 그만둔 것을 권고사직으로 잘못 신고했을 때 과태료는 얼마인가요?
- 답변:

```text
자진퇴사를 권고사직으로 허위 신고할 경우, 사업장에는 최대 300만 원 이하의 과태료가 부과됩니다. 또한 사업주와 근로자 모두 부정수급 공범으로 처벌받을 수 있으므로 주의가 필요합니다.
```

### `K-03` (정확한 키워드/코드형)

- 질문: 3DEXPERIENCE 플랫폼에 통합된 핵심 어플리케이션 이름을 알려주세요.
- 기대 답변 요지: CATIA, SIMULIA, ENOVIA, DELMIA.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 3DEXPERIENCE 플랫폼에 포함된 주요 애플리케이션 명칭은 무엇인가요? / 3DEXPERIENCE 시스템에 통합된 핵심 소프트웨어 이름을 알려주세요. / 3DEXPERIENCE 플랫폼에서 제공하는 핵심 앱 이름이 무엇인지 알려주세요.
- 답변:

```text
3DEXPERIENCE 플랫폼에 통합된 핵심 어플리케이션은 설계(CATIA), 엔지니어링 및 해석(SIMULIA), 프로젝트 및 데이터 관리(ENOVIA), 디지털 제조 및 생산 계획(DELMIA)입니다. 이들 어플리케이션을 하나의 플랫폼에 통합하여 실시간 협업 환경을 제공합니다.
```

### `K-04` (정확한 키워드/코드형)

- 질문: 코드 32는 무엇인가요?
- 기대 답변 요지: 32번은 계약만료, 공사종료.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 코드 32의 의미가 무엇인가요? / 코드 32가 뜻하는 바는 무엇인가요? / 코드 32에 대해 설명해 주세요.
- 답변:

```text
코드 32는 '계약만료, 공사종료'를 의미하며, 정년 등 기간만료에 의한 이직에 해당합니다. 기존에는 계약만료와 공사종료가 별도로 분류되었으나, 이번 개편으로 32번 코드로 통합되었습니다.
```

### `S-01` (의미 기반 질문)

- 질문: 빚을 갚지 못하고 계속 밀리면 어떤 불이익이 생기나요?
- 기대 답변 요지: 연체는 신용등급 평가에 가장 부정적인 요인이며, 대출 거절이나 높은 금리로 이어진다.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 빚을 제때 갚지 못하면 어떤 불이익이 있나요? / 채무를 연체하면 어떤 불이익이 발생하나요? / 대출금을 계속 연체하면 어떤 불이익을 받게 되나요?
- 답변:

```text
빚을 갚지 못하고 연체하면 신용등급이 하락하는 부정적인 영향을 받습니다. 특히 10만원 이상의 금액을 5영업일 이상 연체하면 신용평점이나 신용등급이 떨어지며, 이는 대출 거절이나 높은 대출금리 부담으로 이어질 수 있습니다. 따라서 소액이라도 연체는 절대 피하는 것이 중요합니다.
```

### `S-02` (의미 기반 질문)

- 질문: 회사가 멀리 이전해서 출퇴근이 너무 힘들어져 그만두면 실업급여를 받을 수 있나요?
- 기대 답변 요지: 코드 12. 왕복 3시간 이상이면 자진퇴사 형태여도 실업급여 수급이 가능하다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 회사가 먼 곳으로 이전해서 출퇴근이 어려워졌을 때 퇴사하면 실업급여를 받을 수 있나요? / 회사 이전으로 출퇴근이 힘들어 퇴사할 경우 실업급여 수급 자격이 있나요? / 출퇴근 거리 증가로 인해 퇴사하면 실업급여를 신청할 수 있나요?
- 답변:

```text
회사가 이전하여 출퇴근 시간이 왕복 3시간 이상 소요되어 퇴사하는 경우는 [코드 12] 사업장 이전, 근로조건 변동 등으로 인한 자진퇴사에 해당합니다. 이 경우 회사 측 원인 제공이 있으므로 근로자는 실업급여를 받을 수 있습니다. 다만 관련 증빙 자료(출퇴근 기록 등)를 철저히 보관해야 합니다.
```

### `S-03` (의미 기반 질문)

- 질문: 이즈파크는 환경 보호에 어떤 기여를 하고 있나요?
- 기대 답변 요지: ESG 경영. 디지털 트윈·3D 시뮬레이션으로 시제품 제작을 줄여 폐기물 감소와 탄소 배출 절감에 기여.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크가 환경 보호를 위해 하는 활동은 무엇인가요? / 이즈파크의 환경 보호 기여 내용이 궁금합니다. / 이즈파크는 환경 보호에 어떻게 참여하고 있나요?
- 답변:

```text
이즈파크는 디지털 트윈과 3D 시뮬레이션 기술을 통해 물리적 시제품 제작 횟수를 획기적으로 줄여 산업 현장의 폐기물 감소와 탄소 배출 절감에 직접 기여하고 있습니다. 또한 친환경(Environment) 중심의 ESG 경영을 적극 실천하며 환경 보호에 힘쓰고 있습니다.
```

### `A-01` (짧고 모호한 질문)

- 질문: 신용등급?
- 기대 답변 요지: 신용등급은 금융거래의 신분증과 같으며 대출 가능여부·한도·금리를 결정하는 기본지표.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 신용 점수란 무엇인가요? / 신용 등급이란 무엇을 의미하나요? / 신용 평가 기준이 어떻게 되나요?
- 답변:

```text
신용등급은 금융거래에서 신분증과 같은 역할을 하며, 대출 가능 여부, 대출 한도, 대출 금리를 결정하는 기본 지표입니다. 신용등급은 신용조회회사(CB)에서 산정한 것을 바탕으로 각 금융회사가 거래실적 등을 반영해 다시 산정하여 적용합니다. 연체 정보는 신용등급 평가에 부정적인 영향을 미치며, 소액이라도 연체하지 않는 것이 중요합니다.
```

### `A-02` (짧고 모호한 질문)

- 질문: 권고사직
- 기대 답변 요지: 권고사직은 코드 23 또는 코드 26에 해당할 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 권고사직이란 무엇인가요? / 권고사직의 의미와 정의는 무엇인가요? / 권고사직에 대해 설명해 주세요.
- 답변:

```text
권고사직은 경영상 필요 및 인원 감축 등에 의한 퇴사(코드 23)와 근로자 귀책사유에 의한 징계해고·권고사직(코드 26) 두 가지 경우가 있다. 코드 23은 경영 악화, 부서 폐지, 직제 개편 등에 따른 희망퇴직, 명예퇴직, 권고사직 등이며, 이 경우 회사는 정부 지원금 혜택에 제한이 생길 수 있다. 코드 26은 근로자의 중대한 귀책사유로 징계해고를 당하거나 해고를 피하기 위해 권고사직하는 경우로, 실업급여 수급이 제한될 수 있고 적법한 징계위원회 기록이 필요하다. 권고사직 시에는 사직서나 합의서를 반드시 확보하여 구체적 사유를 명시하는 것이 중요하다.
```

### `A-03` (짧고 모호한 질문)

- 질문: 이즈파크
- 기대 답변 요지: 2009년 설립된 ICT 솔루션 전문기업.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크란 무엇인가요? / 이즈파크에 대해 알려주세요. / 이즈파크의 정의가 궁금합니다.
- 답변:

```text
이즈파크는 2009년 창업한 4차산업혁명 핵심 ICT 솔루션 전문기업으로, 고객 맞춤형 솔루션과 혁신 기술 서비스를 통해 산업 발전에 기여하고 있습니다. 서울 금천구에 본사를 두고 있으며, 제조업 혁신부터 메타버스/XR 기술까지 폭넓은 사업 영역을 보유하고 있습니다. ‘고객 중심’, ‘지속적인 혁신’ 등 핵심 가치를 바탕으로 디지털 트윈과 3D 시뮬레이션 기술을 통해 환경 보호와 사회적 책임을 실천하는 기업입니다.
```

### `C-01` (복합 질문)

- 질문: 코드 23과 코드 26의 실업급여 수급 차이는 무엇이고, 각각 어떤 경우에 적용되나요?
- 기대 답변 요지: 23번은 경영상 필요·인원감축, 26번은 근로자 귀책사유. 26번은 23번과 달리 실업급여 수급이 제한될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 코드 23과 코드 26의 실업급여 수급 조건과 차이점은 무엇인가요? / 실업급여에서 코드 23과 코드 26이 적용되는 상황과 그 차이는 어떻게 되나요? / 코드 23과 코드 26이 각각 어떤 경우에 실업급여 수급에 영향을 미치며, 두 코드 간 차이는 무엇인가요?
- 답변:

```text
코드 23은 경영상 필요, 인원 감축, 부서 폐지 등 회사 사정에 의한 퇴사로, 실업급여 수급이 가능하나 회사는 일정 기간 정부 지원금 혜택에 제한을 받을 수 있습니다. 코드 26은 근로자의 중대한 귀책사유(공금 횡령, 장기 무단결근 등)로 인한 징계해고 또는 권고사직으로, 실업급여 수급이 제한될 수 있으며 적법한 징계위원회 기록이 필요합니다. 즉, 코드 23은 회사 사정에 의한 퇴사, 코드 26은 근로자 귀책사유에 의한 퇴사에 적용됩니다.
```

### `C-02` (복합 질문)

- 질문: 신용등급을 관리하려면 카드는 어떻게 쓰고, 연체가 이미 생겼을 때는 어떤 순서로 갚아야 하나요?
- 기대 답변 요지: 체크카드 사용 권장, 이미 발생한 연체는 가장 오래된 건부터 상환.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 신용등급 관리를 위해 카드를 어떻게 사용해야 하나요? / 연체가 발생했을 때 빚을 갚는 최적의 순서는 무엇인가요? / 신용점수를 유지하려면 카드 사용법과 연체 상환 방법은 어떻게 되나요?
- 답변:

```text
신용등급 관리를 위해서는 자신의 상환능력을 벗어난 카드 사용을 자제하고, 신용카드보다는 체크카드를 사용하는 것이 안전합니다. 이미 연체가 발생했다면 가장 오래된 연체 건부터 상환해야 연체로 인한 불이익을 최소화할 수 있습니다.
```

### `C-03` (복합 질문)

- 질문: 이즈파크의 설립 연도와, 타인을 위한 보증이 신용등급에 미치는 영향을 함께 알려주세요.
- 기대 답변 요지: 2009년 설립. 보증내역은 신용조회회사에 전달되어 신용등급 산정에 반영되고, 채무자가 연체하지 않아도 보증인의 신용등급이 하락할 수 있다.
- 출처(source): 이즈파크 회사 소개서.txt, 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크가 설립된 연도와 타인 보증이 신용등급에 끼치는 영향에 대해 알려주세요. / 이즈파크 설립 시기와 남을 위한 보증이 신용등급에 미치는 효과를 설명해 주세요. / 이즈파크의 창립 연도와 타인 보증이 신용 등급에 어떤 영향을 주는지 알려주세요.
- 답변:

```text
이즈파크는 2009년에 설립되었습니다. 타인을 위한 보증을 서면, 그 보증내역이 신용조회회사에 전달되어 신용등급 산정 시 반영되며, 채무자가 연체하지 않아도 보증인의 신용등급이 하락할 수 있으므로 보증은 가급적 피하는 것이 좋습니다.
```

### `O-01` (문서 범위 밖 질문)

- 질문: 양자역학의 불확정성 원리를 설명해주세요.
- 기대 답변 요지: 문서에서 찾을 수 없다고 응답해야 한다.
- 출처(source): 현명한 신용관리 요령.pdf, 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 양자역학에서 불확정성 원리가 무엇인지 설명해 주세요. / 양자물리학의 하이젠베르크 불확정성 원리에 대해 알려주세요. / 불확정성 원리란 양자역학에서 어떤 의미를 가지는지 설명해 주세요.
- 거절 여부(문자열 자동 판정): 거절
- 답변:

```text
제공된 문서에서는 양자역학의 불확정성 원리에 대한 정보를 찾을 수 없습니다.
```

### `O-02` (문서 범위 밖 질문)

- 질문: 이즈파크의 2025년 연매출과 영업이익을 알려주세요.
- 기대 답변 요지: 문서에서 찾을 수 없다고 응답해야 한다. 수치를 추정해 답하면 실패.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 2025년 예상 매출액과 영업이익은 얼마인가요? / 2025년 이즈파크의 연간 매출과 영업이익 규모를 알려주세요. / 이즈파크가 2025년에 기록할 연매출과 영업이익 수치를 알려주실 수 있나요?
- 거절 여부(문자열 자동 판정): 거절
- 답변:

```text
제공된 문서에서는 이즈파크의 2025년 연매출과 영업이익에 관한 정보를 찾을 수 없습니다.
```

### `O-03` (문서 범위 밖 질문)

- 질문: 이즈파크의 임직원 수와 평균 연봉은 얼마인가요?
- 기대 답변 요지: 문서에서 찾을 수 없다고 응답해야 한다.
- 출처(source): 이즈파크 회사 소개서.txt, 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크 직원 수와 평균 급여는 어떻게 되나요? / 이즈파크 회사의 임직원 규모와 평균 연봉 정보를 알려주세요. / 이즈파크의 전체 직원 수와 평균 연봉 수준이 궁금합니다.
- 거절 여부(문자열 자동 판정): 거절
- 답변:

```text
제공된 문서에서는 이즈파크의 임직원 수와 평균 연봉에 관한 정보를 찾을 수 없습니다.
```

---

## 수동 판정표 (사람이 채운다)

자동 집계로 대체할 수 없는 항목이다. 위 답변 전문을 보고 직접 채운다.

| ID | 정답 여부 | 정보 누락 | Hallucination | 출처 정확성 | 비고 |
|---|---|---|---|---|---|
| `F-01` | | | | | |
| `F-02` | | | | | |
| `F-03` | | | | | |
| `L-01` | | | | | |
| `L-02` | | | | | |
| `L-03` | | | | | |
| `L-04` | | | | | |
| `K-01` | | | | | |
| `K-02` | | | | | |
| `K-03` | | | | | |
| `K-04` | | | | | |
| `S-01` | | | | | |
| `S-02` | | | | | |
| `S-03` | | | | | |
| `A-01` | | | | | |
| `A-02` | | | | | |
| `A-03` | | | | | |
| `C-01` | | | | | |
| `C-02` | | | | | |
| `C-03` | | | | | |
| `O-01` | | | | | |
| `O-02` | | | | | |
| `O-03` | | | | | |

- raw 데이터: `results/baseline_raw.json`

