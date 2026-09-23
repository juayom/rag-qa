# 평가 결과 요약 — `routing`

`scripts/eval_run.py`가 자동 생성한 파일이다. 수동 편집 시 재실행하면 덮어써진다.

---

## 테스트 조건

- config: `routing`
- 실행 시각: 2026-09-23 13:04:41 ~ 2026-09-23 13:15:20
- 실행 환경: Conda `rag_env` / Qdrant `6333` / FastAPI
- 호출 대상: `POST http://127.0.0.1:8001/chat` (server.py)
- 질문셋: `docs/rag/questions.json` (v1.2, 30문항)
- Re-ranker: Dongjin-kr/ko-reranker (Cross Encoder, llm/reranker.py)
- 평가 횟수
  - 정확도 지표(Hit@K, 정답 여부, 정보 누락, Hallucination): **30문항 × 1회**
  - 시간 지표(retrieval / reranking / gpt / total): **대표 7문항 × 3회 평균, 회차별 값 병기**
  - 시간 지표 대표 문항: `F-01`, `L-01`, `K-01`, `S-02`, `A-01`, `C-01`, `O-02`
- top_k / 후보 수는 `vectorstore/retriever.py`의 질문 유형 판단에 따라 자동 결정된다(일반 8/3/8, 목록형 15/10/15). 질문별 관측값은 아래 상세표에 기록한다.
- 워밍업: 본 측정 전 1회 수행하고 **집계에서 제외**했다. 질문 `이즈파크는 어떤 회사인가요?`, 워밍업 total_ms = 10212.34 (참고용, 아래 어떤 평균에도 포함되지 않음)
- 비고: Collection Routing 적용 (REL 0.65 / ABS 0.18, named 설명문). 인덱스는 dedup 과 동일(10/7/9), 재인덱싱 없음. 질문셋 v1.2.

### 실제 실행 명령어

```powershell
python scripts/eval_run.py --config routing --repeat 3 --note "Collection Routing 적용 (REL 0.65 / ABS 0.18, named 설명문). 인덱스는 dedup 과 동일(10/7/9), 재인덱싱 없음. 질문셋 v1.2."
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
| 정상 응답 문항 수 | 30 / 30 |
| **검색 단계** Hit@검색후보수 (범위 내 27문항) | 27 / 27 (100.0%) |
| **검색 단계** 정답 chunk 평균 순위 (Hit 문항) | 1.41 |
| **검색 단계** 평균 후보 수 | 12.9 |
| **Re-ranking 단계** Hit@rerank_top_k (범위 내 27문항) | 27 / 27 (100.0%) |
| **Re-ranking 단계** 정답 chunk 평균 순위 (Hit 문항) | 1.11 |
| Re-ranking에서 정답 chunk 탈락 | 0문항 |
| Multi Query 실행 비율 | 29 / 30 (96.7%) |
| 문서 범위 밖 질문 거절 (문자열 자동 판정) | 3 / 3 |

### 유형별 집계 (1회차)

| 유형 | 문항 수 | 검색 Hit | 검색 순위 | 재랭킹 Hit | 재랭킹 순위 | Multi Query 실행 | 평균 total_ms |
|---|---|---|---|---|---|---|---|
| 일반 사실형 | 3 | 3 / 3 | 1.0 | 3 / 3 | 1.0 | 3 / 3 | 11269.86 |
| 전체/목록형 | 4 | 4 / 4 | 1.75 | 4 / 4 | 1.25 | 4 / 4 | 15227.07 |
| 정확한 키워드/코드형 | 8 | 8 / 8 | 1.62 | 8 / 8 | 1.0 | 8 / 8 | 13709.78 |
| 의미 기반 질문 | 6 | 6 / 6 | 1.17 | 6 / 6 | 1.17 | 5 / 6 | 13851.69 |
| 짧고 모호한 질문 | 3 | 3 / 3 | 1.0 | 3 / 3 | 1.0 | 3 / 3 | 13153.37 |
| 복합 질문 | 3 | 3 / 3 | 1.67 | 3 / 3 | 1.33 | 3 / 3 | 12857.13 |
| 문서 범위 밖 질문 | 3 | 해당 없음 | - | 해당 없음 | - | 3 / 3 | 12972.83 |

---

## 시간 지표 (대표 7문항 × 3회)

| 질문 ID | 지표 | 1회차 | 2회차 | 3회차 | 평균 |
|---|---|---|---|---|---|
| `F-01` | retrieval_ms | 739.29 | 699.69 | 637.46 | **692.15** |
| `F-01` | reranking_ms | 7135.81 | 7951.74 | 8329.55 | **7805.7** |
| `F-01` | gpt_ms | 1253.87 | 970.29 | 1016.32 | **1080.16** |
| `F-01` | total_ms | 11059.51 | 10763.42 | 11192.92 | **11005.28** |
| `L-01` | retrieval_ms | 1418.06 | 1469.41 | 1751.63 | **1546.37** |
| `L-01` | reranking_ms | 16180.91 | 23437.37 | 21042.39 | **20220.22** |
| `L-01` | gpt_ms | 1957.57 | 2037.42 | 2348.43 | **2114.47** |
| `L-01` | total_ms | 20849.16 | 27994.78 | 26461.26 | **25101.73** |
| `K-01` | retrieval_ms | 751.6 | 711.97 | 722.32 | **728.63** |
| `K-01` | reranking_ms | 9623.5 | 11322.74 | 10951.63 | **10632.62** |
| `K-01` | gpt_ms | 1819.88 | 1743.25 | 1331.45 | **1631.53** |
| `K-01` | total_ms | 13309.77 | 14875.14 | 15135.53 | **14440.15** |
| `S-02` | retrieval_ms | 1503.26 | 1588.15 | 1470.99 | **1520.8** |
| `S-02` | reranking_ms | 10483.13 | 16294.56 | 11039.88 | **12605.86** |
| `S-02` | gpt_ms | 1190.66 | 1257.66 | 1262.31 | **1236.88** |
| `S-02` | total_ms | 14686.49 | 20977.16 | 15658.27 | **17107.31** |
| `A-01` | retrieval_ms | 1557.73 | 1423.43 | 1415.2 | **1465.45** |
| `A-01` | reranking_ms | 7569.53 | 10688.58 | 7674.16 | **8644.09** |
| `A-01` | gpt_ms | 1859.71 | 1586.87 | 1417.06 | **1621.21** |
| `A-01` | total_ms | 12484.63 | 14742.53 | 11566.58 | **12931.25** |
| `C-01` | retrieval_ms | 819.86 | 736.46 | 684.68 | **747.0** |
| `C-01` | reranking_ms | 10016.25 | 14222.38 | 10560.11 | **11599.58** |
| `C-01` | gpt_ms | 2009.55 | 1745.62 | 1974.56 | **1909.91** |
| `C-01` | total_ms | 14400.24 | 18360.31 | 14630.62 | **15797.06** |
| `O-02` | retrieval_ms | 821.44 | 657.65 | 781.68 | **753.59** |
| `O-02` | reranking_ms | 8047.63 | 8273.69 | 7782.62 | **8034.65** |
| `O-02` | gpt_ms | 1107.72 | 790.99 | 957.11 | **951.94** |
| `O-02` | total_ms | 11427.98 | 11125.36 | 10998.52 | **11183.95** |

### 대표 문항 평균 (회차 전체 기준)

| 지표 | 평균 |
|---|---|
| 평균 retrieval_ms | 1064.86 |
| 평균 reranking_ms | 11363.25 |
| 평균 gpt_ms | 1506.59 |
| 평균 total_ms | 15366.68 |
| 평균 multi_query_ms | 1166.68 |

> 목록형 문항은 `retrieval_top_k=15 / rerank_top_k=10`, 그 외는 `8 / 3`이므로 **유형 간 시간 비교는 하지 않는다.** 비교는 항상 동일 질문 ID × 방식 간으로만 수행한다.

### 참고 — 1회차 전체 문항 평균

| 지표 | 평균 |
|---|---|
| 평균 retrieval_ms | 1175.43 |
| 평균 reranking_ms | 9509.64 |
| 평균 gpt_ms | 1401.71 |
| 평균 total_ms | 13481.88 |

---

## 질문별 단계별 정답 chunk 추적 (1회차)

| ID | 유형 | 검색 후보 수 | 검색 Hit | 검색 순위 | 재랭킹 후보 수 | 최종 Top-K | 재랭킹 Hit | 재랭킹 순위 |
|---|---|---|---|---|---|---|---|---|
| `F-01` | 일반 사실형 | 9 | O | 1 | 8 | 3 | O | 1 |
| `F-02` | 일반 사실형 | 7 | O | 1 | 7 | 3 | O | 1 |
| `F-03` | 일반 사실형 | 8 | O | 1 | 8 | 3 | O | 1 |
| `L-01` | 전체/목록형 | 16 | O | 1 | 15 | 10 | O | 1 |
| `L-02` | 전체/목록형 | 10 | O | 2 | 10 | 10 | O | 2 |
| `L-03` | 전체/목록형 | 9 | O | 3 | 9 | 9 | O | 1 |
| `L-04` | 전체/목록형 | 10 | O | 1 | 10 | 10 | O | 1 |
| `K-01` | 정확한 키워드/코드형 | 8 | O | 2 | 8 | 3 | O | 1 |
| `K-02` | 정확한 키워드/코드형 | 16 | O | 1 | 8 | 3 | O | 1 |
| `K-03` | 정확한 키워드/코드형 | 25 | O | 1 | 8 | 3 | O | 1 |
| `K-04` | 정확한 키워드/코드형 | 8 | O | 1 | 8 | 3 | O | 1 |
| `S-01` | 의미 기반 질문 | 15 | O | 1 | 8 | 3 | O | 1 |
| `S-02` | 의미 기반 질문 | 16 | O | 1 | 8 | 3 | O | 1 |
| `S-03` | 의미 기반 질문 | 8 | O | 1 | 8 | 3 | O | 1 |
| `A-01` | 짧고 모호한 질문 | 16 | O | 1 | 8 | 3 | O | 1 |
| `A-02` | 짧고 모호한 질문 | 15 | O | 1 | 8 | 3 | O | 1 |
| `A-03` | 짧고 모호한 질문 | 8 | O | 1 | 8 | 3 | O | 1 |
| `C-01` | 복합 질문 | 8 | O | 3 | 8 | 3 | O | 1 |
| `C-02` | 복합 질문 | 7 | O | 1 | 7 | 3 | O | 1 |
| `C-03` | 복합 질문 | 23 | O | 1 | 8 | 3 | O | 2 |
| `O-01` | 문서 범위 밖 질문 | 24 | 해당 없음 | - | 8 | 3 | 해당 없음 | - |
| `O-02` | 문서 범위 밖 질문 | 9 | 해당 없음 | - | 8 | 3 | 해당 없음 | - |
| `O-03` | 문서 범위 밖 질문 | 10 | 해당 없음 | - | 8 | 3 | 해당 없음 | - |
| `H-01` | 의미 기반 질문 | 8 | O | 2 | 8 | 3 | O | 2 |
| `H-02` | 정확한 키워드/코드형 | 8 | O | 5 | 8 | 3 | O | 1 |
| `H-03` | 정확한 키워드/코드형 | 8 | O | 1 | 8 | 3 | O | 1 |
| `H-04` | 정확한 키워드/코드형 | 16 | O | 1 | 8 | 3 | O | 1 |
| `H-05` | 정확한 키워드/코드형 | 23 | O | 1 | 8 | 3 | O | 1 |
| `H-06` | 의미 기반 질문 | 15 | O | 1 | 8 | 3 | O | 1 |
| `H-07` | 의미 기반 질문 | 24 | O | 1 | 8 | 3 | O | 1 |

---

## 질문별 실행 조건 및 시간 (1회차)

| ID | 선택 Collection | top_k | MQ | 기대 항목 | 누락 항목 | retrieval_ms | rerank_ms | gpt_ms | total_ms |
|---|---|---|---|---|---|---|---|---|---|
| `F-01` | ['ispark_company_profile'] | 8 | O | 2 / 2 | - | 739.29 | 7135.81 | 1253.87 | 11059.51 |
| `F-02` | ['credit_management_guide'] | 8 | O | 1 / 1 | - | 793.43 | 6767.42 | 1210.57 | 10456.41 |
| `F-03` | ['due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 787.93 | 8928.05 | 1330.48 | 12293.67 |
| `L-01` | ['credit_management_guide', 'due_diligence_reason_codes'] | 15 | O | 10 / 10 | - | 1418.06 | 16180.91 | 1957.57 | 20849.16 |
| `L-02` | ['ispark_company_profile'] | 15 | O | 3 / 3 | - | 744.88 | 8783.75 | 2724.81 | 13416.31 |
| `L-03` | ['due_diligence_reason_codes'] | 15 | O | 8 / 8 | - | 784.76 | 9895.17 | 1648.18 | 14205.86 |
| `L-04` | ['ispark_company_profile'] | 15 | O | 3 / 3 | - | 890.99 | 8893.44 | 1369.07 | 12436.95 |
| `K-01` | ['due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 751.6 | 9623.5 | 1819.88 | 13309.77 |
| `K-02` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 1452.23 | 9457.23 | 1080.87 | 13361.96 |
| `K-03` | ['ispark_company_profile', 'credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 4 / 4 | - | 2275.48 | 8901.63 | 1134.85 | 13643.62 |
| `K-04` | ['due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 745.32 | 10200.96 | 1328.4 | 13398.4 |
| `S-01` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 1564.04 | 10261.85 | 1580.17 | 14702.24 |
| `S-02` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 1503.26 | 10483.13 | 1190.66 | 14686.49 |
| `S-03` | ['ispark_company_profile'] | 8 | O | 2 / 2 | - | 722.54 | 9523.38 | 1060.89 | 12654.04 |
| `A-01` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 1557.73 | 7569.53 | 1859.71 | 12484.63 |
| `A-02` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 1441.92 | 10835.46 | 1992.46 | 15648.14 |
| `A-03` | ['ispark_company_profile'] | 8 | O | 1 / 1 | - | 703.58 | 8011.51 | 1303.2 | 11327.35 |
| `C-01` | ['due_diligence_reason_codes'] | 8 | O | 3 / 3 | - | 819.86 | 10016.25 | 2009.55 | 14400.24 |
| `C-02` | ['credit_management_guide'] | 8 | O | 2 / 2 | - | 714.14 | 7426.17 | 1130.2 | 10907.39 |
| `C-03` | ['ispark_company_profile', 'credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 2304.35 | 8379.52 | 1126.9 | 13263.77 |
| `O-01` | ['ispark_company_profile', 'credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | - | - | 2299.03 | 11255.34 | 1118.83 | 16010.23 |
| `O-02` | ['ispark_company_profile'] | 8 | O | - | - | 821.44 | 8047.63 | 1107.72 | 11427.98 |
| `O-03` | ['ispark_company_profile'] | 8 | O | - | - | 756.87 | 8743.39 | 798.92 | 11480.29 |
| `H-01` | ['due_diligence_reason_codes'] | 8 | X | 1 / 1 | - | 177.31 | 12258.48 | 1602.31 | 14223.94 |
| `H-02` | ['due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 766.92 | 10391.26 | 2173.94 | 14819.17 |
| `H-03` | ['due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 757.97 | 11758.47 | 1146.08 | 15515.23 |
| `H-04` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 1437.99 | 8940.71 | 920.07 | 13126.6 |
| `H-05` | ['ispark_company_profile', 'credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 2001.02 | 8203.43 | 842.06 | 12503.5 |
| `H-06` | ['credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 2 / 2 | - | 1475.67 | 10691.37 | 1111.45 | 14548.26 |
| `H-07` | ['ispark_company_profile', 'credit_management_guide', 'due_diligence_reason_codes'] | 8 | O | 1 / 1 | - | 2053.43 | 7724.37 | 1117.75 | 12295.17 |

> `기대 항목` / `누락 항목`은 questions.json의 `expected_items` 문자열 포함 검사 결과이며 **자동 보조 지표**이다. 최종 정답 여부와 정보 누락은 아래 수동 판정표에서 사람이 확정한다.

---

## 검색 근거 (1회차)

검색 단계는 상위 10건과 정답 chunk에 해당하는 건만 표시한다(전체는 raw.json의 `retrieval_candidates`).

### `F-01` 이즈파크의 대표이사와 설립일은 언제인가요?

**검색 단계 (Re-ranking 전, 후보 9건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5161 | O | O |
| 2 | ispark_company_profile | 4 | 0.461 | O |  |
| 3 | ispark_company_profile | 3 | 0.4484 | O |  |
| 4 | ispark_company_profile | 5 | 0.3868 | O |  |
| 5 | ispark_company_profile | 9 | 0.3848 | O |  |
| 6 | ispark_company_profile | 10 | 0.383 | O |  |
| 7 | ispark_company_profile | 6 | 0.3339 | O |  |
| 8 | ispark_company_profile | 7 | 0.3248 | O |  |
| 9 | ispark_company_profile | 2 | 0.3196 | X |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5161 | 0.9686 | O |
| 2 | ispark_company_profile | 4 | 0.461 | 0.0198 |  |
| 3 | ispark_company_profile | 3 | 0.4484 | 0.0019 |  |

### `F-02` 10만원 이상의 금액을 며칠 이상 연체하면 신용등급이 하락하나요?

**검색 단계 (Re-ranking 전, 후보 7건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.5235 | O | O |
| 2 | credit_management_guide | 2 | 0.4756 | O | O |
| 3 | credit_management_guide | 6 | 0.4359 | O |  |
| 4 | credit_management_guide | 4 | 0.4182 | O |  |
| 5 | credit_management_guide | 1 | 0.4026 | O |  |
| 6 | credit_management_guide | 5 | 0.3671 | O |  |
| 7 | credit_management_guide | 7 | 0.3072 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.5235 | 0.9999 | O |
| 2 | credit_management_guide | 2 | 0.4756 | 0.0874 | O |
| 3 | credit_management_guide | 6 | 0.4359 | 0.0446 |  |

### `F-03` 피보험자격 상실신고서는 언제까지 어디에 제출해야 하나요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 9 | 0.5466 | O | O |
| 2 | due_diligence_reason_codes | 8 | 0.5319 | O |  |
| 3 | due_diligence_reason_codes | 7 | 0.4286 | O |  |
| 4 | due_diligence_reason_codes | 5 | 0.407 | O |  |
| 5 | due_diligence_reason_codes | 4 | 0.3546 | O |  |
| 6 | due_diligence_reason_codes | 3 | 0.3522 | O |  |
| 7 | due_diligence_reason_codes | 6 | 0.3415 | O |  |
| 8 | due_diligence_reason_codes | 2 | 0.2901 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 9 | 0.5466 | 0.9897 | O |
| 2 | due_diligence_reason_codes | 8 | 0.5319 | 0.0307 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4286 | 0.0019 |  |

### `L-01` 현명한 신용관리 요령 10가지를 모두 알려주세요.

**검색 단계 (Re-ranking 전, 후보 16건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 7 | 0.5537 | O | O |
| 2 | credit_management_guide | 1 | 0.5067 | O |  |
| 3 | credit_management_guide | 2 | 0.4774 | O |  |
| 4 | credit_management_guide | 3 | 0.4504 | O | O |
| 5 | credit_management_guide | 6 | 0.405 | O | O |
| 6 | credit_management_guide | 5 | 0.3884 | O | O |
| 7 | due_diligence_reason_codes | 4 | 0.3627 | O |  |
| 8 | credit_management_guide | 4 | 0.3441 | O | O |
| 9 | due_diligence_reason_codes | 8 | 0.3423 | O |  |
| 10 | due_diligence_reason_codes | 5 | 0.3258 | O |  |
| ... | 이하 6건 생략 | | | | |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.4504 | 0.9908 | O |
| 2 | credit_management_guide | 7 | 0.5537 | 0.6623 | O |
| 3 | credit_management_guide | 2 | 0.4774 | 0.3866 |  |
| 4 | credit_management_guide | 1 | 0.5067 | 0.1603 |  |
| 5 | credit_management_guide | 6 | 0.405 | 0.059 | O |
| 6 | credit_management_guide | 4 | 0.3441 | 0.0387 | O |
| 7 | credit_management_guide | 5 | 0.3884 | 0.004 | O |
| 8 | due_diligence_reason_codes | 8 | 0.3423 | 0.0005 |  |
| 9 | due_diligence_reason_codes | 7 | 0.3176 | 0.0002 |  |
| 10 | due_diligence_reason_codes | 2 | 0.2954 | 0.0002 |  |

### `L-02` 이즈파크의 주요 사업 영역을 모두 알려주세요.

**검색 단계 (Re-ranking 전, 후보 10건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 5 | 0.5821 | O |  |
| 2 | ispark_company_profile | 1 | 0.554 | O | O |
| 3 | ispark_company_profile | 3 | 0.541 | O |  |
| 4 | ispark_company_profile | 9 | 0.533 | O |  |
| 5 | ispark_company_profile | 7 | 0.5033 | O |  |
| 6 | ispark_company_profile | 2 | 0.4642 | O | O |
| 7 | ispark_company_profile | 10 | 0.457 | O |  |
| 8 | ispark_company_profile | 6 | 0.4538 | O |  |
| 9 | ispark_company_profile | 4 | 0.4473 | O |  |
| 10 | ispark_company_profile | 8 | 0.3784 | O |  |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 5 | 0.5821 | 0.9854 |  |
| 2 | ispark_company_profile | 1 | 0.554 | 0.9743 | O |
| 3 | ispark_company_profile | 4 | 0.4473 | 0.4827 |  |
| 4 | ispark_company_profile | 7 | 0.5033 | 0.3904 |  |
| 5 | ispark_company_profile | 3 | 0.541 | 0.1972 |  |
| 6 | ispark_company_profile | 9 | 0.533 | 0.1411 |  |
| 7 | ispark_company_profile | 10 | 0.457 | 0.017 |  |
| 8 | ispark_company_profile | 8 | 0.3784 | 0.0094 |  |
| 9 | ispark_company_profile | 6 | 0.4538 | 0.0046 |  |
| 10 | ispark_company_profile | 2 | 0.4642 | 0.0002 | O |

### `L-03` 변경 후 상실사유 중분류 코드 8개를 모두 나열해주세요.

**검색 단계 (Re-ranking 전, 후보 9건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.5488 | O |  |
| 2 | due_diligence_reason_codes | 1 | 0.5411 | O |  |
| 3 | due_diligence_reason_codes | 2 | 0.4857 | O | O |
| 4 | due_diligence_reason_codes | 4 | 0.4596 | O | O |
| 5 | due_diligence_reason_codes | 8 | 0.4506 | O |  |
| 6 | due_diligence_reason_codes | 7 | 0.4481 | O |  |
| 7 | due_diligence_reason_codes | 3 | 0.4074 | O | O |
| 8 | due_diligence_reason_codes | 6 | 0.4008 | O |  |
| 9 | due_diligence_reason_codes | 9 | 0.3625 | O |  |

**Re-ranking 단계 (최종 Top-9)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 2 | 0.4857 | 0.741 | O |
| 2 | due_diligence_reason_codes | 5 | 0.5488 | 0.0969 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4481 | 0.0092 |  |
| 4 | due_diligence_reason_codes | 1 | 0.5411 | 0.0074 |  |
| 5 | due_diligence_reason_codes | 6 | 0.4008 | 0.0044 |  |
| 6 | due_diligence_reason_codes | 3 | 0.4074 | 0.0019 | O |
| 7 | due_diligence_reason_codes | 8 | 0.4506 | 0.0008 |  |
| 8 | due_diligence_reason_codes | 4 | 0.4596 | 0.0001 | O |
| 9 | due_diligence_reason_codes | 9 | 0.3625 | 0.0001 |  |

### `L-04` 이즈파크의 핵심 가치 3가지를 모두 알려주세요.

**검색 단계 (Re-ranking 전, 후보 10건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 3 | 0.5531 | O | O |
| 2 | ispark_company_profile | 1 | 0.5178 | O |  |
| 3 | ispark_company_profile | 5 | 0.5113 | O |  |
| 4 | ispark_company_profile | 9 | 0.4586 | O |  |
| 5 | ispark_company_profile | 7 | 0.4583 | O |  |
| 6 | ispark_company_profile | 6 | 0.4368 | O |  |
| 7 | ispark_company_profile | 2 | 0.4218 | O |  |
| 8 | ispark_company_profile | 4 | 0.4206 | O | O |
| 9 | ispark_company_profile | 10 | 0.4147 | O |  |
| 10 | ispark_company_profile | 8 | 0.3542 | O |  |

**Re-ranking 단계 (최종 Top-10)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 3 | 0.5531 | 0.9975 | O |
| 2 | ispark_company_profile | 5 | 0.5113 | 0.7969 |  |
| 3 | ispark_company_profile | 4 | 0.4206 | 0.6551 | O |
| 4 | ispark_company_profile | 1 | 0.5178 | 0.3406 |  |
| 5 | ispark_company_profile | 7 | 0.4583 | 0.1338 |  |
| 6 | ispark_company_profile | 10 | 0.4147 | 0.0866 |  |
| 7 | ispark_company_profile | 6 | 0.4368 | 0.0353 |  |
| 8 | ispark_company_profile | 9 | 0.4586 | 0.0267 |  |
| 9 | ispark_company_profile | 8 | 0.3542 | 0.0003 |  |
| 10 | ispark_company_profile | 2 | 0.4218 | 0.0001 |  |

### `K-01` 코드 26은 어떤 경우에 적용되나요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.4631 | O |  |
| 2 | due_diligence_reason_codes | 7 | 0.4377 | O | O |
| 3 | due_diligence_reason_codes | 4 | 0.4292 | O |  |
| 4 | due_diligence_reason_codes | 6 | 0.4288 | O |  |
| 5 | due_diligence_reason_codes | 1 | 0.4069 | O |  |
| 6 | due_diligence_reason_codes | 3 | 0.3943 | O |  |
| 7 | due_diligence_reason_codes | 2 | 0.3921 | O |  |
| 8 | due_diligence_reason_codes | 8 | 0.3658 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.4377 | 0.9099 | O |
| 2 | due_diligence_reason_codes | 5 | 0.4631 | 0.5321 |  |
| 3 | due_diligence_reason_codes | 3 | 0.3943 | 0.0345 |  |

### `K-02` 자진퇴사를 권고사직으로 허위 신고하면 과태료가 얼마인가요?

**검색 단계 (Re-ranking 전, 후보 16건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 8 | 0.4899 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.4649 | O |  |
| 3 | due_diligence_reason_codes | 9 | 0.4352 | O |  |
| 4 | due_diligence_reason_codes | 6 | 0.4211 | O |  |
| 5 | credit_management_guide | 3 | 0.393 | O |  |
| 6 | due_diligence_reason_codes | 5 | 0.3883 | O |  |
| 7 | due_diligence_reason_codes | 2 | 0.3725 | O |  |
| 8 | due_diligence_reason_codes | 3 | 0.3593 | O |  |
| 9 | credit_management_guide | 5 | 0.3218 | X |  |
| 10 | credit_management_guide | 6 | 0.3213 | X |  |
| ... | 이하 6건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 8 | 0.4899 | 0.9982 | O |
| 2 | due_diligence_reason_codes | 9 | 0.4352 | 0.0345 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4649 | 0.0091 |  |

### `K-03` 3DEXPERIENCE 플랫폼에 통합된 핵심 어플리케이션 이름을 알려주세요.

**검색 단계 (Re-ranking 전, 후보 25건)**

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
| 10 | credit_management_guide | 7 | 0.2256 | X |  |
| ... | 이하 15건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5285 | 0.9983 | O |
| 2 | ispark_company_profile | 2 | 0.4742 | 0.0513 |  |
| 3 | ispark_company_profile | 8 | 0.3031 | 0.0002 |  |

### `K-04` 코드 32는 무엇인가요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.3723 | O | O |
| 2 | due_diligence_reason_codes | 4 | 0.3647 | O |  |
| 3 | due_diligence_reason_codes | 1 | 0.3607 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.3558 | O |  |
| 5 | due_diligence_reason_codes | 3 | 0.3335 | O | O |
| 6 | due_diligence_reason_codes | 6 | 0.3166 | O |  |
| 7 | due_diligence_reason_codes | 7 | 0.2936 | O |  |
| 8 | due_diligence_reason_codes | 8 | 0.2614 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.3723 | 0.1442 | O |
| 2 | due_diligence_reason_codes | 3 | 0.3335 | 0.0346 | O |
| 3 | due_diligence_reason_codes | 2 | 0.3558 | 0.0007 |  |

### `S-01` 빚을 갚지 못하고 계속 밀리면 어떤 불이익이 생기나요?

**검색 단계 (Re-ranking 전, 후보 15건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.3525 | O | O |
| 2 | due_diligence_reason_codes | 3 | 0.3411 | O |  |
| 3 | due_diligence_reason_codes | 7 | 0.3404 | O |  |
| 4 | credit_management_guide | 4 | 0.3397 | O | O |
| 5 | due_diligence_reason_codes | 8 | 0.3379 | O |  |
| 6 | credit_management_guide | 2 | 0.3359 | O | O |
| 7 | credit_management_guide | 6 | 0.3331 | O |  |
| 8 | due_diligence_reason_codes | 2 | 0.3001 | O |  |
| 9 | due_diligence_reason_codes | 5 | 0.2938 | X |  |
| 10 | due_diligence_reason_codes | 9 | 0.2826 | X |  |
| ... | 이하 5건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 4 | 0.3397 | 0.0768 | O |
| 2 | credit_management_guide | 3 | 0.3525 | 0.0688 | O |
| 3 | credit_management_guide | 6 | 0.3331 | 0.0315 |  |

### `S-02` 회사가 멀리 이전해서 출퇴근이 너무 힘들어져 그만두면 실업급여를 받을 수 있나요?

**검색 단계 (Re-ranking 전, 후보 16건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.5949 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.5294 | O |  |
| 3 | due_diligence_reason_codes | 3 | 0.4722 | O |  |
| 4 | due_diligence_reason_codes | 5 | 0.4342 | O |  |
| 5 | due_diligence_reason_codes | 2 | 0.4313 | O |  |
| 6 | due_diligence_reason_codes | 9 | 0.4114 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.4095 | O |  |
| 8 | credit_management_guide | 6 | 0.3615 | O |  |
| 9 | credit_management_guide | 2 | 0.326 | X |  |
| 10 | credit_management_guide | 3 | 0.3087 | X |  |
| ... | 이하 6건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.5949 | 0.7142 | O |
| 2 | due_diligence_reason_codes | 7 | 0.5294 | 0.0847 |  |
| 3 | due_diligence_reason_codes | 5 | 0.4342 | 0.0383 |  |

### `S-03` 이즈파크는 환경 보호에 어떤 기여를 하고 있나요?

**검색 단계 (Re-ranking 전, 후보 8건)**

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

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 10 | 0.4516 | 0.9721 | O |
| 2 | ispark_company_profile | 9 | 0.5104 | 0.1188 | O |
| 3 | ispark_company_profile | 7 | 0.4074 | 0.0606 |  |

### `A-01` 신용등급?

**검색 단계 (Re-ranking 전, 후보 16건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.4536 | O | O |
| 2 | credit_management_guide | 6 | 0.4315 | O |  |
| 3 | credit_management_guide | 2 | 0.3722 | O |  |
| 4 | credit_management_guide | 5 | 0.3643 | O |  |
| 5 | credit_management_guide | 1 | 0.3618 | O |  |
| 6 | credit_management_guide | 4 | 0.3419 | O |  |
| 7 | due_diligence_reason_codes | 7 | 0.3324 | O |  |
| 8 | credit_management_guide | 7 | 0.3267 | O |  |
| 9 | due_diligence_reason_codes | 8 | 0.3259 | X |  |
| 10 | due_diligence_reason_codes | 3 | 0.3207 | X |  |
| ... | 이하 6건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 3 | 0.4536 | 0.1904 | O |
| 2 | credit_management_guide | 5 | 0.3643 | 0.1301 |  |
| 3 | credit_management_guide | 2 | 0.3722 | 0.0619 |  |

### `A-02` 권고사직

**검색 단계 (Re-ranking 전, 후보 15건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 8 | 0.3945 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.3499 | O | O |
| 3 | due_diligence_reason_codes | 3 | 0.3493 | O | O |
| 4 | due_diligence_reason_codes | 2 | 0.3047 | O |  |
| 5 | due_diligence_reason_codes | 9 | 0.2828 | O |  |
| 6 | due_diligence_reason_codes | 6 | 0.262 | O |  |
| 7 | due_diligence_reason_codes | 5 | 0.2564 | O |  |
| 8 | due_diligence_reason_codes | 4 | 0.2336 | O |  |
| 9 | credit_management_guide | 6 | 0.2239 | X |  |
| 10 | credit_management_guide | 1 | 0.206 | X |  |
| ... | 이하 5건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.3499 | 0.1248 | O |
| 2 | due_diligence_reason_codes | 8 | 0.3945 | 0.0657 | O |
| 3 | due_diligence_reason_codes | 3 | 0.3493 | 0.0161 | O |

### `A-03` 이즈파크

**검색 단계 (Re-ranking 전, 후보 8건)**

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

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.5672 | 0.9995 | O |
| 2 | ispark_company_profile | 3 | 0.5102 | 0.9596 |  |
| 3 | ispark_company_profile | 10 | 0.4446 | 0.9571 |  |

### `C-01` 코드 23과 코드 26의 실업급여 수급 차이는 무엇이고, 각각 어떤 경우에 적용되나요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.5216 | O |  |
| 2 | due_diligence_reason_codes | 5 | 0.5039 | O |  |
| 3 | due_diligence_reason_codes | 7 | 0.4817 | O | O |
| 4 | due_diligence_reason_codes | 3 | 0.4683 | O |  |
| 5 | due_diligence_reason_codes | 2 | 0.4513 | O |  |
| 6 | due_diligence_reason_codes | 4 | 0.4305 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.4087 | O |  |
| 8 | due_diligence_reason_codes | 1 | 0.3945 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.4817 | 0.9994 | O |
| 2 | due_diligence_reason_codes | 6 | 0.5216 | 0.7931 |  |
| 3 | due_diligence_reason_codes | 3 | 0.4683 | 0.0407 |  |

### `C-02` 신용등급을 관리하려면 카드는 어떻게 쓰고, 연체가 이미 생겼을 때는 어떤 순서로 갚아야 하나요?

**검색 단계 (Re-ranking 전, 후보 7건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 4 | 0.6314 | O | O |
| 2 | credit_management_guide | 5 | 0.5046 | O |  |
| 3 | credit_management_guide | 2 | 0.4491 | O |  |
| 4 | credit_management_guide | 6 | 0.408 | O |  |
| 5 | credit_management_guide | 7 | 0.3832 | O |  |
| 6 | credit_management_guide | 3 | 0.3712 | O |  |
| 7 | credit_management_guide | 1 | 0.3338 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 4 | 0.6314 | 0.7791 | O |
| 2 | credit_management_guide | 3 | 0.3712 | 0.0731 |  |
| 3 | credit_management_guide | 5 | 0.5046 | 0.0658 |  |

### `C-03` 이즈파크의 설립 연도와, 타인을 위한 보증이 신용등급에 미치는 영향을 함께 알려주세요.

**검색 단계 (Re-ranking 전, 후보 23건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 1 | 0.4665 | O | O |
| 2 | ispark_company_profile | 9 | 0.4233 | O |  |
| 3 | ispark_company_profile | 3 | 0.4181 | O |  |
| 4 | ispark_company_profile | 10 | 0.41 | O |  |
| 5 | credit_management_guide | 6 | 0.4041 | O | O |
| 6 | ispark_company_profile | 7 | 0.3915 | O |  |
| 7 | ispark_company_profile | 4 | 0.389 | O |  |
| 8 | ispark_company_profile | 5 | 0.3803 | O |  |
| 9 | ispark_company_profile | 6 | 0.3725 | X |  |
| 10 | credit_management_guide | 7 | 0.3338 | X |  |
| ... | 이하 13건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 4 | 0.389 | 0.0428 |  |
| 2 | credit_management_guide | 6 | 0.4041 | 0.0386 | O |
| 3 | ispark_company_profile | 1 | 0.4665 | 0.0038 | O |

### `O-01` 양자역학의 불확정성 원리를 설명해주세요.

**검색 단계 (Re-ranking 전, 후보 24건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 2 | 0.2658 | O |  |
| 2 | due_diligence_reason_codes | 7 | 0.2618 | O |  |
| 3 | due_diligence_reason_codes | 3 | 0.2464 | O |  |
| 4 | due_diligence_reason_codes | 6 | 0.2381 | O |  |
| 5 | credit_management_guide | 3 | 0.2334 | O |  |
| 6 | due_diligence_reason_codes | 5 | 0.2301 | O |  |
| 7 | credit_management_guide | 6 | 0.2279 | O |  |
| 8 | due_diligence_reason_codes | 1 | 0.2183 | O |  |
| 9 | credit_management_guide | 4 | 0.206 | X |  |
| 10 | due_diligence_reason_codes | 8 | 0.2054 | X |  |
| ... | 이하 14건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 6 | 0.2279 | 0.0001 |  |
| 2 | due_diligence_reason_codes | 6 | 0.2381 | 0.0001 |  |
| 3 | credit_management_guide | 3 | 0.2334 | 0.0001 |  |

### `O-02` 이즈파크의 2025년 연매출과 영업이익을 알려주세요.

**검색 단계 (Re-ranking 전, 후보 9건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 9 | 0.4736 | O |  |
| 2 | ispark_company_profile | 1 | 0.4699 | O |  |
| 3 | ispark_company_profile | 5 | 0.4626 | O |  |
| 4 | ispark_company_profile | 3 | 0.4568 | O |  |
| 5 | ispark_company_profile | 10 | 0.4478 | O |  |
| 6 | ispark_company_profile | 4 | 0.4337 | O |  |
| 7 | ispark_company_profile | 7 | 0.4304 | O |  |
| 8 | ispark_company_profile | 6 | 0.4174 | O |  |
| 9 | ispark_company_profile | 2 | 0.3702 | X |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 4 | 0.4337 | 0.0027 |  |
| 2 | ispark_company_profile | 10 | 0.4478 | 0.0024 |  |
| 3 | ispark_company_profile | 3 | 0.4568 | 0.0023 |  |

### `O-03` 이즈파크의 임직원 수와 평균 연봉은 얼마인가요?

**검색 단계 (Re-ranking 전, 후보 10건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 10 | 0.4008 | O |  |
| 2 | ispark_company_profile | 6 | 0.3936 | O |  |
| 3 | ispark_company_profile | 7 | 0.3914 | O |  |
| 4 | ispark_company_profile | 3 | 0.3801 | O |  |
| 5 | ispark_company_profile | 1 | 0.3663 | O |  |
| 6 | ispark_company_profile | 5 | 0.3613 | O |  |
| 7 | ispark_company_profile | 9 | 0.3613 | O |  |
| 8 | ispark_company_profile | 2 | 0.3502 | O |  |
| 9 | ispark_company_profile | 8 | 0.3184 | X |  |
| 10 | ispark_company_profile | 4 | 0.3162 | X |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 10 | 0.4008 | 0.0022 |  |
| 2 | ispark_company_profile | 3 | 0.3801 | 0.0018 |  |
| 3 | ispark_company_profile | 5 | 0.3613 | 0.0012 |  |

### `H-01` 직원이 회사 돈에 손을 대서 내보냈습니다. 어떤 사유 코드로 신고해야 하나요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 3 | 0.5362 | O |  |
| 2 | due_diligence_reason_codes | 7 | 0.5168 | O | O |
| 3 | due_diligence_reason_codes | 6 | 0.5081 | O |  |
| 4 | due_diligence_reason_codes | 8 | 0.5074 | O |  |
| 5 | due_diligence_reason_codes | 5 | 0.5032 | O |  |
| 6 | due_diligence_reason_codes | 2 | 0.4902 | O |  |
| 7 | due_diligence_reason_codes | 9 | 0.4786 | O |  |
| 8 | due_diligence_reason_codes | 4 | 0.3065 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.5032 | 0.0426 |  |
| 2 | due_diligence_reason_codes | 7 | 0.5168 | 0.0231 | O |
| 3 | due_diligence_reason_codes | 6 | 0.5081 | 0.0137 |  |

### `H-02` 26번 코드와 23번 코드는 어떻게 다른가요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 1 | 0.4982 | O |  |
| 2 | due_diligence_reason_codes | 5 | 0.4314 | O |  |
| 3 | due_diligence_reason_codes | 4 | 0.4233 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.4095 | O |  |
| 5 | due_diligence_reason_codes | 7 | 0.3689 | O | O |
| 6 | due_diligence_reason_codes | 3 | 0.3624 | O |  |
| 7 | due_diligence_reason_codes | 6 | 0.3472 | O |  |
| 8 | due_diligence_reason_codes | 8 | 0.2806 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 7 | 0.3689 | 0.9931 | O |
| 2 | due_diligence_reason_codes | 6 | 0.3472 | 0.0843 |  |
| 3 | due_diligence_reason_codes | 8 | 0.2806 | 0.0372 |  |

### `H-03` 사업장 이전으로 출퇴근이 왕복 몇 시간 이상 걸리게 되면 자진퇴사해도 실업급여를 받을 수 있나요?

**검색 단계 (Re-ranking 전, 후보 8건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.565 | O | O |
| 2 | due_diligence_reason_codes | 7 | 0.4842 | O |  |
| 3 | due_diligence_reason_codes | 3 | 0.4611 | O |  |
| 4 | due_diligence_reason_codes | 2 | 0.4361 | O |  |
| 5 | due_diligence_reason_codes | 5 | 0.4158 | O |  |
| 6 | due_diligence_reason_codes | 9 | 0.3897 | O |  |
| 7 | due_diligence_reason_codes | 8 | 0.3724 | O |  |
| 8 | due_diligence_reason_codes | 4 | 0.2439 | O |  |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 6 | 0.565 | 0.9993 | O |
| 2 | due_diligence_reason_codes | 5 | 0.4158 | 0.0167 |  |
| 3 | due_diligence_reason_codes | 7 | 0.4842 | 0.014 |  |

### `H-04` 고용보험 비적용과 이중고용은 변경 후 몇 번 코드로 통합되었나요?

**검색 단계 (Re-ranking 전, 후보 16건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 4 | 0.5942 | O | O |
| 2 | due_diligence_reason_codes | 5 | 0.4822 | O | O |
| 3 | credit_management_guide | 7 | 0.4308 | O |  |
| 4 | due_diligence_reason_codes | 8 | 0.4116 | O |  |
| 5 | due_diligence_reason_codes | 3 | 0.4035 | O |  |
| 6 | due_diligence_reason_codes | 7 | 0.3994 | O |  |
| 7 | credit_management_guide | 5 | 0.3953 | O |  |
| 8 | credit_management_guide | 6 | 0.3908 | O |  |
| 9 | due_diligence_reason_codes | 6 | 0.3765 | X |  |
| 10 | due_diligence_reason_codes | 9 | 0.3739 | X |  |
| ... | 이하 6건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | due_diligence_reason_codes | 5 | 0.4822 | 0.9893 | O |
| 2 | due_diligence_reason_codes | 4 | 0.5942 | 0.0367 | O |
| 3 | due_diligence_reason_codes | 3 | 0.4035 | 0.0033 |  |

### `H-05` 금융감독원이 개설하기로 한 금융소비자정보 포털사이트의 이름은 무엇인가요?

**검색 단계 (Re-ranking 전, 후보 23건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 1 | 0.5208 | O | O |
| 2 | ispark_company_profile | 9 | 0.3109 | O |  |
| 3 | credit_management_guide | 6 | 0.3021 | O |  |
| 4 | credit_management_guide | 5 | 0.2969 | O |  |
| 5 | ispark_company_profile | 1 | 0.2887 | O |  |
| 6 | due_diligence_reason_codes | 8 | 0.2717 | O |  |
| 7 | credit_management_guide | 2 | 0.2702 | O |  |
| 8 | ispark_company_profile | 5 | 0.2653 | O |  |
| 9 | credit_management_guide | 7 | 0.2607 | X |  |
| 10 | ispark_company_profile | 3 | 0.2586 | X |  |
| ... | 이하 13건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 1 | 0.5208 | 0.9916 | O |
| 2 | credit_management_guide | 5 | 0.2969 | 0.0001 |  |
| 3 | credit_management_guide | 6 | 0.3021 | 0.0001 |  |

### `H-06` 다른 사람 빚보증을 서주면 내 신용에 문제가 생기나요?

**검색 단계 (Re-ranking 전, 후보 15건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 6 | 0.4901 | O | O |
| 2 | due_diligence_reason_codes | 8 | 0.447 | O |  |
| 3 | credit_management_guide | 2 | 0.433 | O |  |
| 4 | due_diligence_reason_codes | 3 | 0.4247 | O |  |
| 5 | due_diligence_reason_codes | 5 | 0.4056 | O |  |
| 6 | credit_management_guide | 3 | 0.4024 | O |  |
| 7 | due_diligence_reason_codes | 2 | 0.3845 | O |  |
| 8 | due_diligence_reason_codes | 6 | 0.3804 | O |  |
| 9 | due_diligence_reason_codes | 9 | 0.3793 | X |  |
| 10 | due_diligence_reason_codes | 4 | 0.3787 | X |  |
| ... | 이하 5건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | credit_management_guide | 6 | 0.4901 | 0.8942 | O |
| 2 | credit_management_guide | 3 | 0.4024 | 0.003 |  |
| 3 | credit_management_guide | 2 | 0.433 | 0.0015 |  |

### `H-07` 3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 무엇인가요?

**검색 단계 (Re-ranking 전, 후보 24건)**

| rank | collection | chunk | retriever_score | 재랭커 전달 | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5997 | O | O |
| 2 | ispark_company_profile | 2 | 0.4833 | O |  |
| 3 | ispark_company_profile | 8 | 0.3576 | O |  |
| 4 | ispark_company_profile | 7 | 0.3474 | O |  |
| 5 | ispark_company_profile | 4 | 0.3452 | O |  |
| 6 | ispark_company_profile | 10 | 0.3308 | O |  |
| 7 | ispark_company_profile | 5 | 0.304 | O |  |
| 8 | ispark_company_profile | 9 | 0.2742 | O |  |
| 9 | ispark_company_profile | 1 | 0.2563 | X |  |
| 10 | credit_management_guide | 7 | 0.1958 | X |  |
| ... | 이하 14건 생략 | | | | |

**Re-ranking 단계 (최종 Top-3)**

| rank | collection | chunk | retriever_score | rerank_score | 정답 chunk |
|---|---|---|---|---|---|
| 1 | ispark_company_profile | 6 | 0.5997 | 0.9069 | O |
| 2 | ispark_company_profile | 2 | 0.4833 | 0.0149 |  |
| 3 | ispark_company_profile | 8 | 0.3576 | 0.0007 |  |

---

## 답변 전문 (1회차)

### `F-01` (일반 사실형)

- 질문: 이즈파크의 대표이사와 설립일은 언제인가요?
- 기대 답변 요지: 대표이사는 김갑산, 설립일은 2009년.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 CEO와 설립일은 언제입니까? / 이즈파크 회사의 대표이사 이름과 설립 날짜를 알려주세요. / 이즈파크의 대표 임원과 설립 시기는 어떻게 되나요?
- 답변:

```text
이즈파크의 대표이사는 김갑산이며, 설립일은 2009년입니다. 본사는 서울특별시 금천구 가산디지털2로 43-14, 한화비즈메트로2차 803~820호에 위치해 있습니다.
```

### `F-02` (일반 사실형)

- 질문: 10만원 이상의 금액을 며칠 이상 연체하면 신용등급이 하락하나요?
- 기대 답변 요지: 10만원 이상의 금액을 5영업일 이상 연체하면 신용평점이나 신용등급이 하락한다.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 10만원 이상 연체 시 며칠 후에 신용등급이 떨어지나요? / 10만원 넘는 금액을 며칠 이상 연체하면 신용점수가 하락하나요? / 10만원 이상 연체 기간이 며칠 이상일 때 신용등급이 낮아지나요?
- 답변:

```text
10만원 이상의 금액을 5영업일 이상 연체하면 신용평점이나 신용등급이 하락합니다. 연체정보는 신용등급 평가에 부정적인 영향을 미치는 가장 중요한 요인으로, 소액이라도 연체는 절대 피해야 좋은 신용등급을 받을 수 있습니다.
```

### `F-03` (일반 사실형)

- 질문: 피보험자격 상실신고서는 언제까지 어디에 제출해야 하나요?
- 기대 답변 요지: 퇴사일이 속하는 달의 다음 달 15일까지 관할 근로복지공단에 제출.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 피보험자격 상실신고서는 제출 기한과 제출 장소가 어떻게 되나요? / 피보험자격 상실신고서는 언제, 어디에 제출해야 합니까? / 피보험자격 상실신고서 제출 마감일과 제출처는 어디인가요?
- 답변:

```text
피보험자격 상실신고서는 근로자가 퇴사한 날이 속하는 달의 다음 달 15일까지 관할 근로복지공단에 제출해야 합니다. 예를 들어, 4월 20일 퇴사자의 경우 5월 15일까지 신고해야 합니다. 신고 기한을 엄수하지 않으면 사업장에 과태료가 부과될 수 있으므로 주의가 필요합니다.
```

### `L-01` (전체/목록형)

- 질문: 현명한 신용관리 요령 10가지를 모두 알려주세요.
- 기대 답변 요지: 신용관리 요령 10개 항목 전부.
- 출처(source): 현명한 신용관리 요령.pdf, 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 신용 관리를 잘하는 10가지 방법을 알려주세요. / 신용 점수를 높이기 위한 10가지 팁을 모두 설명해 주세요. / 효과적인 신용 관리 비법 10가지를 알려주실 수 있나요?
- 답변:

```text
현명한 신용관리 요령 10가지는 다음과 같습니다. ① 평소 자기 신용등급에 관심 기울이기, ② 소액이라도 절대 연체하지 않기, ③ 신용카드보다는 체크카드 사용하기, ④ 연체는 오래된 것부터 상환하기, ⑤ 과도한 빚은 피하기, ⑥ 주거래 금융회사 및 자동이체 이용하기, ⑦ 타인을 위한 보증은 가급적 피하기, ⑧ 대출 금융회사 신중하게 결정하기, ⑨ 신용평가 가점제 적극 활용하기, ⑩ 신용관리체험단 활용하기입니다.
```

### `L-02` (전체/목록형)

- 질문: 이즈파크의 주요 사업 영역을 모두 알려주세요.
- 기대 답변 요지: 스마트 제조 솔루션 / 디지털 트윈 및 XR(메타버스) / AI 및 클라우드 서비스 3개 영역.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 핵심 사업 분야를 전부 알려주세요. / 이즈파크가 진행하는 주요 사업 영역을 자세히 설명해 주세요. / 이즈파크의 모든 주요 비즈니스 분야를 알려 주실 수 있나요?
- 답변:

```text
이즈파크의 주요 사업 영역은 스마트 제조 솔루션(PLM, CAD/CAM/CAE, MES, QMS 등 스마트 팩토리 구현), 디지털 트윈 및 XR(AR/VR/MR 기반 산업용 XR 콘텐츠, 디지털 트윈 기술 활용 가상 시뮬레이션 및 모니터링, 메타버스 플랫폼 서비스), AI 및 클라우드 서비스(빅데이터 분석, AI 기반 최적화, 클라우드 SaaS 협업 시스템, 디지털 경영 관리 및 RPA 도입 지원) 등입니다. 또한, 3D CAD/CAM 및 PLM 비즈니스를 기반으로 제조 산업 설계 및 생산 효율성 향상, 메타버스/XR 기술, AI 기반 스마트 예지보전 및 빅데이터 최적화 등 다양한 ICT 솔루션을 제공합니다.
```

### `L-03` (전체/목록형)

- 질문: 변경 후 상실사유 중분류 코드 8개를 모두 나열해주세요.
- 기대 답변 요지: 11 / 12 / 22 / 23 / 26 / 31 / 32 / 41 총 8개 코드.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 변경 후 상실사유 중분류 코드 8가지를 모두 알려주세요. / 변경된 상실사유 중분류 코드 8개를 전부 나열해 주세요. / 변경 후 상실사유 중분류 코드 8개 목록을 모두 보여주세요.
- 답변:

```text
변경 후 상실사유 중분류 코드 8개는 다음과 같습니다.  
11. 개인사정으로 인한 자진퇴사  
12. 사업장 이전, 근로조건변동, 임금체불 등으로 자진퇴사  
22. 폐업 도산  
23. 경영상 필요 및 회사불황으로 인원감축 등에 의한 퇴사(해고 권고사직 명예퇴직 포함)  
26. 근로자의 귀책사유에 의한 징계해고 권고사직  
31. 정년  
32. 계약만료, 공사종료  
41. 고용보험 비적용, 이중 고용
```

### `L-04` (전체/목록형)

- 질문: 이즈파크의 핵심 가치 3가지를 모두 알려주세요.
- 기대 답변 요지: 고객 중심 / 지속적인 혁신 / 신뢰와 상생 파트너십.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크의 주요 가치 세 가지를 모두 설명해 주세요. / 이즈파크가 중요하게 여기는 핵심 가치 3가지를 알려 주세요. / 이즈파크의 3가지 핵심 가치를 모두 알려 주세요.
- 답변:

```text
이즈파크의 핵심 가치는 첫째 고객 중심(Customer Centric), 둘째 지속적인 혁신(Continuous Innovation), 셋째 신뢰와 상생 파트너십(Trust & Partnership)입니다. 고객의 비즈니스 환경을 정확히 분석해 맞춤형 솔루션을 제공하고, 4차 산업혁명 시대에 맞춰 신기술에 대한 R&D 투자를 지속하며, 투명한 소통을 통해 장기적 동반 성장을 추구합니다.
```

### `K-01` (정확한 키워드/코드형)

- 질문: 코드 26은 어떤 경우에 적용되나요?
- 기대 답변 요지: 근로자의 중대한 귀책사유로 인한 징계해고·권고사직. 실업급여 수급이 제한될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 코드 26이 적용되는 상황은 무엇인가요? / 코드 26은 언제 사용되나요? / 코드 26의 적용 조건은 무엇인가요?
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
3DEXPERIENCE 플랫폼에 통합된 핵심 어플리케이션은 설계(CATIA), 엔지니어링 및 해석(SIMULIA), 프로젝트 및 데이터 관리(ENOVIA), 디지털 제조 및 생산 계획(DELMIA)입니다. 이들 어플리케이션이 하나의 플랫폼에 통합되어 실시간 협업 환경을 제공합니다.
```

### `K-04` (정확한 키워드/코드형)

- 질문: 코드 32는 무엇인가요?
- 기대 답변 요지: 32번은 계약만료, 공사종료.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 코드 32의 의미가 무엇인가요? / 코드 32가 뜻하는 바는 무엇인가요? / 코드 32에 대해 설명해 주세요.
- 답변:

```text
코드 32는 '계약만료, 공사종료'를 의미하며, 정년 등 기간만료에 의한 이직에 해당합니다. 계약만료와 공사종료가 32번 코드로 통합되어 실무자의 코드 선택 부담을 줄였습니다.
```

### `S-01` (의미 기반 질문)

- 질문: 빚을 갚지 못하고 계속 밀리면 어떤 불이익이 생기나요?
- 기대 답변 요지: 연체는 신용등급 평가에 가장 부정적인 요인이며, 대출 거절이나 높은 금리로 이어진다.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 빚을 제때 갚지 못하면 어떤 불이익이 발생하나요? / 채무를 연체하면 어떤 불이익이 따르나요? / 빚을 계속 연체할 경우 어떤 불이익이 있나요?
- 답변:

```text
빚을 갚지 못하고 연체가 계속되면 연체 기간이 길어질수록 신용등급에 불리하게 작용하여 신용평점이나 신용등급이 하락합니다. 과도한 채무는 가계운영과 개인의 삶을 어렵게 할 뿐만 아니라 연체 가능성이 높다고 평가되어 신용등급에 부정적인 영향을 줍니다. 또한, 연체정보는 신용등급 평가에 가장 부정적인 요인이므로 소액이라도 연체하지 않는 것이 중요합니다.
```

### `S-02` (의미 기반 질문)

- 질문: 회사가 멀리 이전해서 출퇴근이 너무 힘들어져 그만두면 실업급여를 받을 수 있나요?
- 기대 답변 요지: 코드 12. 왕복 3시간 이상이면 자진퇴사 형태여도 실업급여 수급이 가능하다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 회사가 먼 곳으로 이전해서 출퇴근이 어려워 퇴사하면 실업급여를 받을 수 있나요? / 출퇴근이 힘들어 회사 이전 후 자발적으로 퇴사할 경우 실업급여 신청이 가능한가요? / 회사 위치 변경으로 출퇴근이 불편해져 퇴사할 때 실업급여를 받을 수 있는지 궁금합니다.
- 답변:

```text
회사가 이전하여 출퇴근 시간이 왕복 3시간 이상 소요되어 퇴사하는 경우는 [코드 12] 사업장 이전, 근로조건 변동 등으로 인한 자진퇴사에 해당합니다. 이 경우 회사에 원인 제공이 있으므로 근로자는 실업급여를 받을 수 있습니다. 다만, 관련 증빙 자료(출퇴근 기록 등)를 철저히 보관해야 합니다.
```

### `S-03` (의미 기반 질문)

- 질문: 이즈파크는 환경 보호에 어떤 기여를 하고 있나요?
- 기대 답변 요지: ESG 경영. 디지털 트윈·3D 시뮬레이션으로 시제품 제작을 줄여 폐기물 감소와 탄소 배출 절감에 기여.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크가 환경 보호를 위해 하는 활동은 무엇인가요? / 이즈파크의 환경 보호 기여 내용이 궁금합니다. / 이즈파크는 환경 보호에 어떻게 참여하고 있나요?
- 답변:

```text
이즈파크는 디지털 트윈과 3D 시뮬레이션 기술을 통해 물리적 시제품 제작 횟수를 획기적으로 줄여 산업 현장의 폐기물 감소와 탄소 배출 절감에 직접 기여하고 있습니다. 또한 친환경(Environment)을 포함한 ESG 경영을 적극 실천하며 환경 보호에 힘쓰고 있습니다.
```

### `A-01` (짧고 모호한 질문)

- 질문: 신용등급?
- 기대 답변 요지: 신용등급은 금융거래의 신분증과 같으며 대출 가능여부·한도·금리를 결정하는 기본지표.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 신용 점수란 무엇인가요? / 신용 평가 기준이 어떻게 되나요? / 신용 등급을 확인하는 방법은 무엇인가요?
- 답변:

```text
신용등급은 금융거래에서 신분증과 같은 역할을 하며, 대출 가능 여부, 대출한도, 대출금리를 결정하는 기본지표입니다. 신용등급은 신용조회회사(CB)에서 산정한 것을 바탕으로 각 금융회사가 거래실적 등을 반영해 다시 산정하여 적용합니다. 연체정보는 신용등급에 부정적인 영향을 미치는 가장 중요한 요인으로, 소액이라도 연체하지 않는 것이 중요합니다.
```

### `A-02` (짧고 모호한 질문)

- 질문: 권고사직
- 기대 답변 요지: 권고사직은 코드 23 또는 코드 26에 해당할 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 권고사직이란 무엇인가요? / 권고사직의 의미와 정의는 무엇인가요? / 권고사직에 대해 설명해 주세요.
- 답변:

```text
권고사직은 경영상 필요 및 인원 감축 등에 의한 퇴사(코드 23)와 근로자 귀책사유에 의한 징계해고·권고사직(코드 26) 두 가지 경우가 있다. 코드 23은 경영 악화, 부서 폐지, 직제 개편 등에 따른 희망퇴직, 명예퇴직, 권고사직 등이며, 이 경우 회사는 정부 지원금 혜택에 제한이 생길 수 있다. 코드 26은 근로자의 중대한 귀책사유로 징계해고를 당하거나 해고를 피하기 위해 권고사직하는 경우로, 실업급여 수급이 제한될 수 있고 적법한 징계위원회 기록이 필요하다. 권고사직 시에는 사직서나 합의서에 ‘사직 권고에 따른 합의 퇴사’임을 명시하는 것이 좋다.
```

### `A-03` (짧고 모호한 질문)

- 질문: 이즈파크
- 기대 답변 요지: 2009년 설립된 ICT 솔루션 전문기업.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크란 무엇인가요? / 이즈파크에 대해 알려주세요. / 이즈파크에 관한 정보를 알고 싶습니다.
- 답변:

```text
이즈파크는 2009년 창업한 4차산업혁명 핵심 ICT 솔루션 전문기업으로, 고객 맞춤형 솔루션과 혁신 기술 서비스를 통해 산업 발전에 기여하고 있습니다. 서울 금천구에 본사를 두고 있으며, 제조업 혁신부터 메타버스/XR 기술까지 폭넓은 사업 영역을 보유하고 있습니다. ‘고객 중심’, ‘지속적 혁신’, ‘사회적 책임’을 핵심 가치로 삼아 글로벌 IT 리딩 기업으로 성장하고자 노력하고 있습니다.
```

### `C-01` (복합 질문)

- 질문: 코드 23과 코드 26의 실업급여 수급 차이는 무엇이고, 각각 어떤 경우에 적용되나요?
- 기대 답변 요지: 23번은 경영상 필요·인원감축, 26번은 근로자 귀책사유. 26번은 23번과 달리 실업급여 수급이 제한될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 코드 23과 코드 26의 실업급여 수급 조건 차이는 무엇인가요? / 실업급여에서 코드 23과 코드 26이 적용되는 상황은 어떻게 다릅니까? / 코드 23과 코드 26이 실업급여 지급에 미치는 영향과 적용 기준은 무엇인가요?
- 답변:

```text
코드 23은 경영상 필요, 인원 감축, 부서 폐지 등 회사 사정에 의한 퇴사로, 실업급여 수급이 가능하나 회사가 고용유지지원금 등 정부 지원금 혜택을 받는 데 제한이 생길 수 있습니다. 코드 26은 근로자의 중대한 귀책사유(공금 횡령, 장기 무단결근 등)로 인한 징계해고 또는 권고사직으로, 실업급여 수급이 제한될 수 있으며 적법한 징계위원회 기록이 필요합니다. 즉, 코드 23은 회사 사정에 의한 퇴사, 코드 26은 근로자 귀책사유에 의한 퇴사에 적용됩니다.
```

### `C-02` (복합 질문)

- 질문: 신용등급을 관리하려면 카드는 어떻게 쓰고, 연체가 이미 생겼을 때는 어떤 순서로 갚아야 하나요?
- 기대 답변 요지: 체크카드 사용 권장, 이미 발생한 연체는 가장 오래된 건부터 상환.
- 출처(source): 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 신용등급 관리를 위해 카드를 어떻게 사용해야 하나요? / 연체가 발생했을 때 어떤 순서로 빚을 상환하는 것이 좋나요? / 신용점수를 유지하려면 카드 사용법과 연체금 상환 순서는 어떻게 되나요?
- 답변:

```text
신용등급 관리를 위해서는 자신의 상환능력을 벗어난 카드 사용을 자제하고, 신용카드보다는 체크카드를 사용하는 것이 안전합니다. 연체가 이미 발생했다면 가장 오래된 연체 건부터 상환해야 연체로 인한 불이익을 최소화할 수 있습니다.
```

### `C-03` (복합 질문)

- 질문: 이즈파크의 설립 연도와, 타인을 위한 보증이 신용등급에 미치는 영향을 함께 알려주세요.
- 기대 답변 요지: 2009년 설립. 보증내역은 신용조회회사에 전달되어 신용등급 산정에 반영되고, 채무자가 연체하지 않아도 보증인의 신용등급이 하락할 수 있다.
- 출처(source): 이즈파크 회사 소개서.txt, 현명한 신용관리 요령.pdf
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크가 설립된 연도와 타인 보증이 신용등급에 끼치는 영향에 대해 설명해 주세요. / 이즈파크 설립 시기와 남을 위한 보증이 신용등급에 미치는 효과를 알려 주세요. / 이즈파크의 창립 연도와 타인 보증이 신용 등급에 어떤 영향을 주는지 알려 주세요.
- 답변:

```text
이즈파크는 2009년에 설립되었습니다. 타인을 위한 보증은 보증내역이 신용조회회사에 전달되어 신용등급 산정 시 반영되며, 채무자가 연체하지 않더라도 보증인의 신용등급이 하락할 수 있으므로 가급적 피하는 것이 좋습니다.
```

### `O-01` (문서 범위 밖 질문)

- 질문: 양자역학의 불확정성 원리를 설명해주세요.
- 기대 답변 요지: 문서에서 찾을 수 없다고 응답해야 한다.
- 출처(source): 현명한 신용관리 요령.pdf, 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 양자역학에서 불확정성 원리가 무엇인지 설명해 주세요. / 양자물리학의 하이젠베르크 불확정성 원리에 대해 알려주세요. / 양자역학 불확정성 원리의 개념을 자세히 설명해 주실 수 있나요?
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
- 생성된 추가 질문: 이즈파크의 2025년 예상 매출액과 영업이익은 어떻게 되나요? / 2025년 이즈파크의 연간 매출과 영업이익 수치를 알려주세요. / 이즈파크 2025년 연간 매출과 영업이익 전망을 알려주실 수 있나요?
- 거절 여부(문자열 자동 판정): 거절
- 답변:

```text
제공된 문서에서는 이즈파크의 2025년 연매출과 영업이익에 관한 정보를 찾을 수 없습니다.
```

### `O-03` (문서 범위 밖 질문)

- 질문: 이즈파크의 임직원 수와 평균 연봉은 얼마인가요?
- 기대 답변 요지: 문서에서 찾을 수 없다고 응답해야 한다.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 이즈파크 직원 수와 평균 급여는 어떻게 되나요? / 이즈파크 회사의 임직원 규모와 평균 연봉 정보가 궁금합니다. / 이즈파크에 근무하는 인원 수와 평균 연봉 수준은 얼마인가요?
- 거절 여부(문자열 자동 판정): 거절
- 답변:

```text
제공된 문서에서는 이즈파크의 임직원 수와 평균 연봉에 관한 정보를 찾을 수 없습니다.
```

### `H-01` (의미 기반 질문)

- 질문: 직원이 회사 돈에 손을 대서 내보냈습니다. 어떤 사유 코드로 신고해야 하나요?
- 기대 답변 요지: 코드 26 (근로자 귀책사유에 의한 징계해고·권고사직).
- 출처(source): 실사유 코드.docx
- Multi Query: 미실행
- 답변:

```text
직원이 회사 돈에 손을 대어 징계해고된 경우에는 [코드 26] 근로자 귀책사유에 의한 징계해고·권고사직으로 신고해야 합니다. 이 코드는 근로자의 중대한 귀책사유(공금 횡령 등)로 인해 징계해고를 당하거나 권고사직하는 경우에 적용되며, 실업급여 수급이 제한될 수 있습니다.
```

### `H-02` (정확한 키워드/코드형)

- 질문: 26번 코드와 23번 코드는 어떻게 다른가요?
- 기대 답변 요지: 23번은 경영상 필요·인원 감축에 의한 퇴사, 26번은 근로자 귀책사유에 의한 징계해고·권고사직. 26번은 실업급여 수급이 제한될 수 있다.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 26번 코드와 23번 코드의 차이점은 무엇인가요? / 26번 코드와 23번 코드는 어떤 점에서 다릅니까? / 26번 코드와 23번 코드는 어떻게 구분되나요?
- 답변:

```text
26번 코드는 근로자의 중대한 귀책사유(공금 횡령, 장기 무단결근, 기밀 누설 등)로 인한 징계해고 또는 권고사직에 적용되며, 실업급여 수급이 제한될 수 있습니다. 반면 23번 코드는 경영상 필요, 인원 감축, 부서 폐지 등 회사 사정에 따른 퇴사에 적용되며, 이 경우 회사가 정부 지원금 혜택을 받는 데 제한이 생길 수 있습니다. 또한 23번은 단순 업무 부적응 등 근로자 귀책이 아닌 경영상 이유에 한정되어야 하며, 26번은 근로자의 중대한 잘못이 있을 때 사용됩니다.
```

### `H-03` (정확한 키워드/코드형)

- 질문: 사업장 이전으로 출퇴근이 왕복 몇 시간 이상 걸리게 되면 자진퇴사해도 실업급여를 받을 수 있나요?
- 기대 답변 요지: 왕복 3시간 이상.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 사업장 이전으로 출퇴근 시간이 왕복 몇 시간 이상일 때 자진퇴사해도 실업급여를 받을 수 있나요? / 출퇴근 시간이 왕복 몇 시간 이상 증가하면 자진퇴사 시 실업급여 수급이 가능한가요? / 사업장 이전으로 인해 출퇴근 시간이 많이 늘어나 자진퇴사할 경우 실업급여를 받을 수 있나요?
- 답변:

```text
사업장 이전으로 출퇴근이 왕복 3시간 이상 소요되게 되어 자진퇴사하는 경우, 회사에 원인이 있으므로 근로자가 실업급여를 받을 수 있는 중요한 사유에 해당합니다. 다만, 관련 증빙 자료(출퇴근 기록 등)를 철저히 보관해야 합니다.
```

### `H-04` (정확한 키워드/코드형)

- 질문: 고용보험 비적용과 이중고용은 변경 후 몇 번 코드로 통합되었나요?
- 기대 답변 요지: 41번 단일 코드로 병합.
- 출처(source): 실사유 코드.docx
- Multi Query: 실행
- 생성된 추가 질문: 고용보험 비적용과 이중고용이 변경되어 통합된 코드는 몇 번인가요? / 고용보험 비적용 및 이중고용 관련 코드가 변경 후 몇 번으로 합쳐졌나요? / 변경된 고용보험 비적용과 이중고용 통합 코드는 몇 번인지 알려주세요?
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
- 생성된 추가 질문: 다른 사람의 채무를 보증하면 내 신용등급에 영향이 있나요? / 남의 빚을 대신 갚아주면 내 신용 점수에 문제가 생기나요? / 타인의 대출 보증을 서면 내 신용 기록에 불이익이 있나요?
- 답변:

```text
다른 사람을 위해 보증을 서면 보증내역이 신용조회회사에 보내져 신용등급 산정 시 반영됩니다. 이 경우 채무자가 연체하지 않더라도 보증인의 신용등급이 하락할 수 있으므로, 보증을 서는 것은 가급적 피하는 것이 좋습니다.
```

### `H-07` (의미 기반 질문)

- 질문: 3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 무엇인가요?
- 기대 답변 요지: CATIA.
- 출처(source): 이즈파크 회사 소개서.txt
- Multi Query: 실행
- 생성된 추가 질문: 3DEXPERIENCE 플랫폼에서 설계에 사용되는 애플리케이션은 무엇인가요? / 3DEXPERIENCE에서 디자인 작업을 수행하는 애플리케이션 이름이 무엇인가요? / 3DEXPERIENCE 플랫폼 내 설계용 소프트웨어는 어떤 것이 있나요?
- 답변:

```text
3DEXPERIENCE 플랫폼에서 설계 작업에 쓰이는 애플리케이션은 CATIA입니다. 이 플랫폼은 설계(CATIA), 엔지니어링 및 해석(SIMULIA), 프로젝트 및 데이터 관리(ENOVIA), 디지털 제조 및 생산 계획(DELMIA) 등 핵심 어플리케이션을 하나로 통합하여 제공합니다.
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
| `H-01` | | | | | |
| `H-02` | | | | | |
| `H-03` | | | | | |
| `H-04` | | | | | |
| `H-05` | | | | | |
| `H-06` | | | | | |
| `H-07` | | | | | |

- raw 데이터: `results/routing_raw.json`

