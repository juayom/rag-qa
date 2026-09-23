# Chunking 비교 — PDF 중복 chunk 제거 (안 B)

GUIDE 9항(Chunking 비교) / 13항(작업 기록 규칙) 형식으로 기록한다.
비교 대상은 **baseline(중복 포함, `credit_management_guide` 13 chunk)** 과
**dedup(안 B 적용, 7 chunk)** 이다.

---

## 변경 내용

- `preprocessing/pdf_loader.py`에 **페이지 텍스트 / 표 중복 적재 제거 로직(안 B)** 을 추가했다.
  - `현명한 신용관리 요령.pdf`는 본문 전체가 테두리 박스(표) 안에 들어 있어
    `page.extract_text()`가 표 안의 글자까지 그대로 반환한다.
    그 상태에서 `page.extract_tables()` 결과를 markdown으로 또 추가하면 같은 내용이 두 번 적재된다.
  - `_normalize()`로 공백을 모두 제거해 줄바꿈 위치 차이를 무시하고 비교한다.
  - `_is_duplicated_line()`은 **정규화 길이 10자 이상**인 줄은 표 전체 텍스트에 포함되기만 하면 중복으로 보고,
    그보다 짧은 줄은 우연한 부분 문자열 일치를 피하기 위해 **표 셀의 한 줄과 완전히 같을 때만** 중복으로 본다.
  - 판정된 줄만 본문 blocks에서 제외하고, 표 markdown 블록은 그대로 유지한다.
- 그 결과 `credit_management_guide` chunk 수가 **13 → 7**, 전체 chunk 수가 **32 → 26**이 되었다.
- `docs/rag/questions.json` / `RAG_EVALUATION_QUESTIONS.md`의 기대 근거 chunk 번호를
  새 chunk 구성에 맞춰 재매핑했다(질문셋 **v1.2**, 질문 문구·`expected_items`는 변경 없음).
- 다른 Collection(`ispark_company_profile` 10, `due_diligence_reason_codes` 9)과
  `server.py` / `retriever.py` / `reranker.py`는 변경하지 않았다.

---

## 실제 실행 명령어

baseline (중복 포함 인덱스, 커밋 `7940974`):

```powershell
conda activate rag_env
docker compose up -d qdrant
python index_documents.py
python scripts/eval_run.py --config baseline --repeat 3
python scripts/eval_run.py --config baseline_hard --only H-01,H-02,H-03,H-04,H-05,H-06,H-07 --note "v1.1 hard 문항 7개. 커밋 7940974 동일 인덱스(10/13/9), 재인덱싱 없음. 시간 측정 대상 아님(repeat 1)."
```

dedup (안 B 적용 후 재인덱싱):

```powershell
conda activate rag_env
docker compose up -d qdrant
python index_documents.py
python scripts/eval_run.py --config dedup --repeat 3 --note "PDF 중복 chunk 제거(안 B) 후 재인덱싱. points_count 10/7/9. 질문셋 v1.2. baseline 과 동일 조건."
```

---

## 테스트 조건

| 항목 | 값 |
|---|---|
| 질문 수 | 30문항 (`docs/rag/questions.json` v1.2) |
| 검색 방식 | Semantic (Qdrant) + Multi Query, Collection Routing 미적용(ALL 3 Collection 조회) |
| top_k | 일반 `retrieval_top_k=8` / 목록형 `15` (`vectorstore/retriever.py`가 질문 유형으로 자동 결정) |
| Re-ranker | `Dongjin-kr/ko-reranker` (Cross Encoder, `llm/reranker.py`) |
| 후보 수 | 재랭커 입력 `rerank_candidate_limit` 일반 8 / 목록형 15, 최종 `rerank_top_k` 일반 3 / 목록형 10 |
| 실행 환경 | Conda `rag_env` / Qdrant `6333` / FastAPI, `POST http://127.0.0.1:8001/chat` |
| 정확도 측정 | 30문항 × 1회 |
| 시간 측정 | 대표 7문항(`F-01`, `L-01`, `K-01`, `S-02`, `A-01`, `C-01`, `O-02`) × 3회 평균 |
| 워밍업 | 본 측정 전 1회 수행 후 집계에서 제외 |
| dedup 실행 시각 | 2026-09-23 10:57:21 ~ 11:08:35 |

두 측정의 질문 문구·순서·평가 횟수·top_k 규칙은 동일하며, **인덱스만 다르다.**

---

## 결과

| 지표 | baseline (30문항) | dedup (30문항) | 차이 |
|---|---|---|---|
| `credit_management_guide` chunk 수 | 13 | **7** | -6 |
| 전체 chunk 수 | 32 | **26** | -6 |
| 평균 검색 후보 수 | 27.80 | 24.53 | -3.27 |
| 검색 단계 Hit | 27 / 27 (100%) | 27 / 27 (100%) | 동일 |
| 검색 단계 평균 순위 | 1.48 | 1.52 | +0.04 (악화) |
| 검색 단계 MRR | 0.841 | 0.835 | -0.006 (악화) |
| 재랭킹 단계 Hit | 27 / 27 (100%) | 27 / 27 (100%) | 동일 |
| 재랭킹 단계 평균 순위 | 1.18 | **1.11** | -0.07 (개선) |
| 재랭킹 단계 MRR | 0.920 | **0.944** | +0.024 (개선) |
| 대표 7문항 평균 total_ms | 15310.58 | 15359.96 | +49.38 (+0.3%) |
| 대표 7문항 평균 reranking_ms | 10182.84 | 10050.28 | -132.56 (-1.3%) |
| 오류 / 특이사항 | — | **없음** | — |

> baseline의 MRR과 평균 순위는 `baseline`(23문항) 결과와 `baseline_hard`(7문항) 결과를 합산해,
> 각 summary에 기록된 정답 chunk 순위로 계산한 값이다.
> Hit 판정 대상은 문서 범위 밖 질문 3문항을 제외한 27문항이다.

---

## 비교 결과

### a. H-06 — 중복 chunk가 Top-3를 차지하던 문제가 해소됐다

질문: *다른 사람 빚보증을 서주면 내 신용에 문제가 생기나요?*

| | 1위 | 2위 |
|---|---|---|
| baseline | `credit_management_guide` chunk 10 (rerank 0.9218) | chunk 12 (rerank 0.8942) — **1위와 동일 내용** |
| dedup | `credit_management_guide` chunk 6 (rerank 0.8942) | chunk 3 (rerank 0.003) — **다른 내용** |

baseline은 Top-3의 1·2위를 같은 내용의 중복 chunk가 차지해 실질 근거가 1건뿐이었다.
dedup은 1위가 정답 chunk이고 2위부터는 서로 다른 내용이 들어온다.
**최종 Top-K에 담기는 정보량이 늘었다**는 뜻이다.

### b. L-02 — 목록 항목 누락이 2개에서 1개로 줄었다

질문: *이즈파크의 주요 사업 영역을 모두 알려주세요.*

| | 누락 항목 |
|---|---|
| baseline | "스마트 제조", "클라우드" (2개) |
| dedup | "스마트 제조" (1개) |

정답 chunk가 `ispark_company_profile`(변경 없는 Collection)인 질문인데도 누락이 줄었다.
중복 chunk가 빠지면서 재랭킹 Top-10에 들어가는 서로 다른 내용의 chunk 수가 늘어난 효과다.

### c. 응답시간 — 전체 평균은 변화 없고, 목록형 L-01을 빼면 감소했다

| 구분 | baseline | dedup | 차이 |
|---|---|---|---|
| 대표 7문항 평균 total_ms | 15310.58 | 15359.96 | **+0.3%** |
| L-01 제외 6문항 평균 total_ms | 14494.47 | **13405.44** | **-7.5%** |
| `L-01` 단독 total_ms | 20207.24 | 27087.04 | +34.0% |

L-01이 느려진 원인은 **후보 구성**이다.
목록형의 `rerank_candidate_limit`은 15로 고정인데 `credit_management_guide`가 13 → 7 chunk로 줄어,
부족분이 `due_diligence_reason_codes`의 **긴 chunk**로 채워졌다.
실제로 dedup L-01의 재랭킹 Top-10에는 `due_diligence_reason_codes` chunk 6·7·8이 들어가 있다
(rerank_score 0.0005 / 0.0005 / 0.0002 — 내용상 무관하지만 Cross Encoder는 이미 처리한 뒤다).
Cross Encoder 처리시간은 입력 길이에 비례하므로 `reranking_ms`가 늘어난다.

또한 L-01의 3회차 `reranking_ms`가 **27618.07** 로,
1·2회차(17606.06 / 17699.91) 대비 명확한 이상치이며 이 값이 평균을 끌어올렸다.
회차별 `total_ms`는 24190.15 / 23113.59 / 33957.38 이다.

### d. Hit@K 포화가 더 심해졌다 — 주 지표를 순위·MRR로 쓰는 근거가 강화됐다

| | 평균 검색 후보 수 / 전체 chunk 수 | 비율 |
|---|---|---|
| baseline | 27.80 / 32 | 86.9% |
| dedup | 24.53 / 26 | **94.3%** |

코퍼스 축소 폭이 후보 수 감소 폭보다 커서, 질문 하나가 **전체 chunk의 94.3%** 를 후보로 본다.
이 조건에서 Hit@K는 구조적으로 100%가 나오므로 방식 간 변별력이 없다.
따라서 이후 비교(GUIDE 6항 검색 방식, 8항 Re-ranking)에서도
**정답 chunk 순위와 MRR을 주 지표, Hit@K를 보조 지표**로 유지한다.

---

## 최종 판단

- **선택: 안 B(PDF 페이지 텍스트 / 표 중복 제거) 채택.**
- 선택 근거
  1. **재랭킹 품질이 개선됐다.** 재랭킹 MRR 0.920 → 0.944, 평균 순위 1.18 → 1.11.
     최종 Top-K는 LLM에 그대로 전달되는 구간이므로 이 개선이 답변 품질에 직접 연결된다.
  2. **중복이 실제로 해소됐다.** H-06에서 Top-3의 1·2위를 차지하던 동일 내용 chunk가 사라지고,
     서로 다른 내용의 근거가 들어왔다. L-02의 항목 누락도 2개 → 1개로 줄었다.
  3. **응답시간은 목록형을 제외하면 감소했다.** 6문항 평균 -7.5%, 평균 `reranking_ms` -1.3%.
  4. 검색 단계 MRR이 0.841 → 0.835로 미세하게 낮아졌으나,
     후보 비율이 94.3%로 포화된 구간의 0.006 차이이고 재랭킹 단계에서 역전된다. 채택을 막을 근거가 아니다.
  5. 목록형 L-01의 시간 증가는 **Collection Routing 미적용 상태에서 후보 15개를 억지로 채우느라
     무관한 Collection의 긴 chunk가 들어온 결과**이며, Chunking 자체의 문제가 아니다.
     GUIDE 5항 Collection Routing 적용 시 재확인한다.

### 후속 확인 과제

- Collection Routing 적용 후 L-01의 `reranking_ms` 재측정.
- L-01 3회차 이상치(27618.07)가 재현되는지 확인.
- L-02에 남은 누락 항목 "스마트 제조"는 `ispark_company_profile` 쪽 과제로,
  본 변경 범위 밖이다.

---

## 참고 원본

- `docs/rag/results/dedup_summary.md` / `dedup_raw.json`
- `docs/rag/results/baseline_summary.md` / `baseline_hard_summary.md`
- `docs/rag/RAG_BASELINE_RESULT.md`
