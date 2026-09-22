# RAG 고도화 비교·평가 실행 가이드

## 1. 목적

RAG 고도화 과정에서 어떤 방식을 선택했는지 **실행 명령어, 테스트 결과, 비교 지표, 선택 근거**를 남기기 위한 가이드이다.

Codex는 기능을 구현할 때마다 아래 내용을 기록한다.

- 실제 실행한 명령어
- 테스트 환경
- 비교 대상
- 동일 질문셋 기준 결과
- 응답시간 및 검색 결과
- 장단점
- 최종 선택 방식
- 선택 근거

비교 결과는 기능을 바꾼 뒤 기억에 의존해 작성하지 않고, **실제로 실행한 결과를 기준으로 기록**한다.

---

## 2. 기본 실행 환경

작업 환경:

```text
Conda: rag_env
VectorDB: Qdrant
Qdrant Port: 6333
Backend: FastAPI
```

기본 실행 명령:

```powershell
conda activate rag_env
docker compose up -d qdrant
docker compose ps
python index_documents.py
uvicorn server:app --reload
```

Qdrant 확인:

```text
http://localhost:6333/dashboard
```

기본 API 테스트 예시:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/chat `
  -ContentType "application/json" `
  -Body '{"question":"이즈파크의 핵심 가치는 무엇인가요?"}' |
  ConvertTo-Json -Depth 10
```

> 실제 프로젝트의 API 입력 형식이 변경된 경우 현재 코드에 맞는 명령어를 사용하고, 실행한 명령어를 그대로 기록한다.

---

## 3. 평가 질문셋

모든 비교는 가능한 한 **동일한 고정 질문셋**으로 수행한다.

질문 유형:

```text
- 일반 사실형
- 전체/목록형
- 정확한 키워드/코드형
- 의미 기반 질문
- 짧고 모호한 질문
- 복합 질문
- 문서 범위 밖 질문
```

비교 중 질문을 임의로 바꾸지 않는다.

---

## 4. Baseline 측정

고도화 전 현재 버전을 먼저 측정한다.

기록 항목:

```text
question
selected_collection(s)
retrieval_top_k
retrieved_docs
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
```

최소 3회 이상 반복 실행하여 평균 시간을 계산한다.

### Baseline 결과에 반드시 남길 것

- 평균 전체 응답시간
- 평균 Retrieval 시간
- 평균 Re-ranking 시간
- Multi Query 실행 비율
- 정답 Chunk 포함 여부
- 답변 누락 여부
- 문서 밖 질문 거절 여부

---

## 5. Collection Routing 비교

### 비교 대상

```text
A. 모든 Collection 검색
B. Collection Routing 적용
```

### 확인 항목

- 올바른 Collection을 선택했는가
- 애매한 질문에서 전체 검색 fallback이 정상 동작하는가
- Retrieval 후보 수가 줄었는가
- 평균 Retrieval 시간이 줄었는가
- 최종 답변 품질이 유지되는가

### 선택 기준

```text
1. Collection 선택 정확도
2. 검색 후보 감소
3. Retrieval 시간 감소
4. 답변 품질 유지 여부
```

Routing 때문에 정답 문서를 놓치는 경우에는 threshold 또는 fallback 기준을 조정하고 근거를 기록한다.

---

## 6. Semantic / Keyword / Hybrid Search 비교

### 비교 대상

```text
A. Semantic Search
B. Keyword Search
C. Hybrid Search
```

### 질문 유형별 확인

Semantic에 유리한 질문:
- 표현이 문서와 다르지만 의미가 같은 질문
- 자연어 설명형 질문

Keyword에 유리한 질문:
- 실사유 코드
- 숫자
- 제품/솔루션명
- 정확한 고유명사
- 문서에 있는 특정 표현

Hybrid:
- Semantic과 Keyword의 장점을 모두 유지하는지 확인

### 비교 지표

```text
- 정답 Chunk가 Top-K 안에 포함됐는지
- 정답 Chunk의 순위
- 검색 실패 건수
- 평균 Retrieval 시간
- 최종 답변 정확성
```

가능하면 다음을 집계한다.

```text
Hit@K = 정답 Chunk가 Top-K 안에 포함된 질문 비율
MRR = 정답 Chunk가 얼마나 상위에 검색되는지 평가
```

MRR 계산이 현재 구조에 과도한 작업이면 Hit@K와 정답 Chunk 순위만 기록해도 된다.

---

## 7. Query 처리 방식 비교

현재 기준 방식:

```text
Adaptive Multi Query
```

확인 항목:

```text
- 일반 질문에서는 Multi Query가 불필요하게 실행되지 않는가
- 1차 검색이 부족한 질문에서만 실행되는가
- Multi Query 후 정답 Chunk가 새로 검색되는가
- 추가 응답시간이 어느 정도 발생하는가
```

필요성이 확인되는 경우에만 아래 방식을 비교한다.

```text
A. 원본 Query만 사용
B. Adaptive Multi Query
C. Query Rewrite
D. Decomposition
```

판단 기준:

- 검색 성공률 향상
- 정답 Chunk 순위
- 추가 LLM 호출 횟수
- 평균 응답시간
- 구현 복잡도

성능 차이가 작다면 더 단순한 방식을 우선한다.

---

## 8. Re-ranking 방식 비교

현재 기준:

```text
Dongjin-kr/ko-reranker
Cross Encoder
```

현재 Cross Encoder와 다른 Re-ranking 방식 최소 1개를 비교한다.

Codex는 비교 후보를 조사한 뒤 다음 내용을 기록한다.

```text
- 방식/모델명
- 동작 방식
- 로컬 실행/API 여부
- 한국어 지원 여부
- 예상 장점
- 예상 단점
```

비교 시 조건을 동일하게 맞춘다.

```text
- 동일 질문
- 동일 Retrieval 결과
- 동일 후보 수
- 동일 최종 Top-K
```

비교 지표:

```text
- 정답 Chunk의 Re-ranking 순위
- Top-3 정답 포함 여부
- Re-ranking 시간
- 전체 응답시간
- 답변 품질
- 모델 크기 / 실행 환경 부담
```

실제 결과를 근거로 변경 또는 유지 이유를 작성한다.

---

## 9. Chunking 비교

### 비교 대상

```text
기존:
SentenceSplitter 기반 공통 Chunking

개선:
PDF / DOCX 구조 기반 Chunking
TXT SentenceSplitter 유지
```

### 판단 기준

```text
- 정답 내용이 하나의 Chunk 안에 잘 보존되는가
- 목록 항목 누락이 감소하는가
- 제목과 본문의 관계가 유지되는가
- 불필요한 중복 Chunk가 증가하지 않는가
- 전체 Chunk 수가 지나치게 증가하지 않는가
```

재인덱싱 후 Collection별 Point 수도 함께 기록한다.

Qdrant 확인 예시:

```powershell
Invoke-RestMethod http://localhost:6333/collections |
  ConvertTo-Json -Depth 10
```

---

## 10. Hallucination 방지 평가

문서에 존재하지 않는 질문을 최소 2~3개 포함한다.

예:

```text
양자역학의 불확정성 원리를 설명해주세요.
이즈파크의 2025년 연매출과 영업이익을 알려주세요.
```

### 비교 대상

```text
A. 기존 Prompt
B. 개선된 System Prompt + 검색 결과 검증
```

### 성공 기준

- 문서에 없는 내용을 임의로 생성하지 않음
- "제공된 문서에서 관련 정보를 찾을 수 없습니다." 형태로 응답
- 잘못된 출처를 표시하지 않음

---

## 11. 근거 및 출처 평가

현재 웹 화면의 Top-3 근거와 출처가 실제 답변과 일치하는지 확인한다.

확인 항목:

```text
- 답변 내용과 근거 Chunk가 일치하는가
- 출처 문서가 올바른가
- 다른 Collection의 관련 없는 문서가 표시되지 않는가
- 전체 목록 답변에서 필요한 근거가 충분히 포함되는가
```

---

## 12. 최종 Baseline vs 고도화 RAG 비교

마지막에는 동일 질문셋으로 전체 평가를 다시 수행한다.

### 최종 비교 지표

```text
- 검색 성공률
- 전체/목록 답변 완전성
- Collection Routing 정확도
- Hallucination 방지 성공률
- 평균 Retrieval 시간
- 평균 Re-ranking 시간
- 평균 전체 응답시간
```

추가로 다음 내용을 서술한다.

```text
- 어떤 검색 방식을 최종 선택했는가
- 어떤 Re-ranking 방식을 선택했는가
- Query 처리 방식은 무엇을 유지했는가
- 선택하지 않은 방식은 왜 제외했는가
- 최종 RAG의 남은 한계는 무엇인가
```

---

## 13. Codex 작업 기록 규칙

Codex는 각 기능 구현 또는 비교가 끝날 때마다 아래 형식으로 결과를 남긴다.

```text
## 작업명

### 변경 내용
- ...

### 실제 실행 명령어
실제로 실행한 명령어를 기록

### 테스트 조건
- 질문 수:
- 검색 방식:
- top_k:
- Re-ranker:
- 후보 수:

### 결과
- 검색 정확도:
- 평균 Retrieval:
- 평균 Re-ranking:
- 평균 Total:
- 오류/특이사항:

### 비교 결과
- 기존:
- 비교 방식:
- 차이:

### 최종 판단
- 선택:
- 선택 근거:
```

실행하지 않은 명령어나 측정하지 않은 수치는 작성하지 않는다.

---

## 14. 권장 문서 구조

비교 결과와 근거는 `docs/rag/` 아래에 남긴다.

```text
docs/rag/
├─ RAG_ADVANCEMENT_PLAN.md
├─ RAG_EVALUATION_GUIDE.md
├─ RAG_EVALUATION_QUESTIONS.md
├─ questions.json
├─ RAG_BASELINE_RESULT.md
├─ RAG_CHUNKING_COMPARISON.md
├─ RAG_SEARCH_COMPARISON.md
├─ RAG_RERANK_COMPARISON.md
├─ RAG_FINAL_EVALUATION.md
└─ results/
   ├─ <config>_raw.json
   └─ <config>_summary.md
```

파일 역할:

```text
RAG_ADVANCEMENT_PLAN.md
→ 전체 고도화 계획

RAG_EVALUATION_GUIDE.md
→ 실행 명령어와 비교 기준

RAG_EVALUATION_QUESTIONS.md
→ 고정 평가 질문셋 및 기대 답변

questions.json
→ RAG_EVALUATION_QUESTIONS.md와 동일한 질문셋의 기계 판독용 사본
   (scripts/eval_run.py가 읽는다. 두 파일은 항상 함께 수정한다)

RAG_BASELINE_RESULT.md
→ 고도화 전 결과

RAG_CHUNKING_COMPARISON.md
→ Chunking 비교 및 PDF 중복 chunk 제거 전후 결과

results/
→ scripts/eval_run.py가 생성하는 측정 원본(raw.json)과 집계(summary.md)

RAG_SEARCH_COMPARISON.md
→ Semantic / Keyword / Hybrid 비교

RAG_RERANK_COMPARISON.md
→ Re-ranking 방식 비교 및 선택 근거

RAG_FINAL_EVALUATION.md
→ 최종 고도화 전후 비교 결과
```
