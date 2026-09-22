# RAG 챗봇 고도화 작업 계획

## 1. 목적

기존 RAG 프로젝트를 기반으로 검색 정확도, 답변 품질, 응답속도를 개선하고  
4주차 과제인 **검색·답변 성능 평가 및 RAG 챗봇 고도화**를 진행한다.

이번 작업은 기존 구조를 최대한 유지하면서 필요한 기능만 단계적으로 추가한다.  
불필요한 대규모 리팩토링이나 과도한 추상화는 하지 않는다.

---

## 2. 현재 구현 상태

### 완료된 항목

- VectorDB를 ChromaDB에서 **Qdrant**로 전환
- Docker에서 Qdrant `6333` 포트 사용
- 문서별 Qdrant Collection 분리
  - `ispark_company_profile`
  - `credit_management_guide`
  - `due_diligence_reason_codes`
- PDF / DOCX / TXT 문서별 Chunking 개선
- Adaptive Multi Query 적용
  - 원본 질문으로 1차 검색
  - 검색 결과가 부족할 때만 Multi Query 실행
- Dynamic top-k 적용
  - 일반 질문과 전체/목록 질문의 검색 개수 구분
- Cross Encoder Re-ranking 적용
- Re-ranker 입력 후보 수 제한
- 단계별 처리시간 측정
  - Multi Query
  - Retrieval
  - Re-ranking
  - GPT
  - Total
- 웹 화면에서 답변 근거와 출처 확인 가능
  - 근거는 Re-ranking 결과(`rerank_top_k`) 전체가 렌더링된다.
  - 일반 질문은 3건, 전체/목록형 질문은 10건이 표시된다.

### 현재 검색 흐름

```text
사용자 질문
→ 질문 유형 판단
→ Dynamic top-k
→ 모든 Collection 검색
→ 검색 결과 충분 여부 판단
→ 부족한 경우 Multi Query
→ 검색 결과 병합 및 중복 제거
→ Re-ranker 후보 제한
→ Cross Encoder Re-ranking
→ GPT 답변 생성
→ 근거 및 출처 표시
```

---

## 3. 이번 고도화에서 새로 진행할 항목

### 3.1 Qdrant Metadata / Payload 보완

각 Chunk에 검색 및 출처 확인에 필요한 metadata를 명확히 저장한다.

권장 항목:

```text
source
source_path
collection
chunk_index
splitter
section_title
page
```

문서 형식상 값이 없는 항목은 생략 가능하며, 현재 코드 구조에서 필요한 수준만 적용한다.

---

### 3.2 Collection Routing 적용

현재는 질문마다 3개 Collection을 모두 검색하고 있으므로  
Collection별 설명을 추가하고 질문과 가장 관련 있는 Collection을 먼저 선택하도록 개선한다.

예시:

```text
ispark_company_profile
- 이즈파크 회사 소개, 비전, 사업 영역, 핵심 가치, 솔루션, 연혁, ESG

credit_management_guide
- 신용등급, 신용점수, 연체, 카드, 대출, 보증, 신용관리 요령

due_diligence_reason_codes
- 퇴사, 이직, 상실사유, 실사유 코드, 권고사직, 계약만료, 실업급여
```

기본 방향:

```text
사용자 질문
→ Collection 설명과 질문 비교
→ 관련 Collection 선택
→ 선택된 Collection에서 검색
→ 판단이 애매하면 전체 Collection 검색 fallback
```

가능하면 현재 Embedding을 활용한 Semantic Similarity 방식으로 단순하게 구현한다.  
Routing을 위해 별도의 LLM 호출은 우선 사용하지 않는다.

---

### 3.3 Semantic / Keyword / Hybrid Search 적용 및 비교

현재 검색은 Qdrant Vector Search 기반의 Semantic Search이다.

추가할 검색 방식:

```text
1. Semantic Search
2. Keyword Search
3. Hybrid Search
```

Hybrid Search 기본 흐름:

```text
Semantic Search
        +
Keyword Search
        ↓
검색 결과 병합
        ↓
중복 제거
        ↓
Cross Encoder Re-ranking
```

처음부터 복잡한 점수 정규화 로직을 만들기보다  
Semantic / Keyword 후보를 병합한 뒤 기존 Cross Encoder가 최종 순위를 판단하도록 구성한다.

동일한 평가 질문셋으로 세 방식을 비교하고 최종 방식을 선택한다.

---

### 3.4 Query 처리 방식 보완

현재 Adaptive Multi Query는 유지한다.

```text
원본 질문
→ 1차 검색
→ 결과 충분
   ├─ YES: 다음 단계
   └─ NO: Multi Query 생성 후 추가 검색
```

과제에 포함된 Query Rewrite / Decomposition은 모두 무조건 구현하지 않는다.

- 현재 Multi Query와 특징을 비교
- 실제 테스트에서 필요성이 확인되는 경우에만 추가
- 단순 질문에서는 불필요한 LLM 호출을 늘리지 않는다

---

### 3.5 Re-ranking 방식 비교

현재 방식:

```text
Cross Encoder
→ Dongjin-kr/ko-reranker
```

이미 후보 수 제한을 적용해 응답시간을 개선한 상태이므로  
현재 방식을 무조건 교체하지 않는다.

다른 Re-ranking 방식 1개 이상을 조사하고 동일한 질문셋으로 비교한다.

비교 기준:

```text
- 정답 Chunk 순위
- 검색 품질
- 답변 품질
- Re-ranking 처리시간
- 전체 응답시간
```

비교 결과 현재 방식이 더 적합하면 유지한다.  
변경 또는 유지 여부와 판단 근거를 기록한다.

---

### 3.6 System Prompt / Context 구성 개선

GPT에 전달하는 Context와 Prompt를 다음 원칙으로 정리한다.

```text
- 검색된 Context를 근거로 답변한다.
- Context에 없는 내용은 추측하지 않는다.
- 관련 정보가 없으면 문서에서 찾을 수 없다고 답변한다.
- 답변에 사용된 근거와 출처를 함께 제공한다.
- 불필요하게 많은 Chunk를 Context에 넣지 않는다.
```

현재 `temperature=0` 설정은 유지할 수 있으나  
Hallucination 방지는 Prompt 및 검색 결과 검증 로직을 함께 사용한다.

---

### 3.7 Hallucination 방지

최소한 다음 방식으로 보완한다.

```text
검색 결과가 충분함
→ Context 기반 답변 생성

검색 결과가 부족함
→ Multi Query 등 추가 검색

추가 검색 후에도 관련 정보 없음
→ "제공된 문서에서 관련 정보를 찾을 수 없습니다." 응답
```

문서 범위 밖 질문에서 외부 지식을 임의로 생성하지 않는지 평가한다.

---

## 4. 최종 목표 흐름

```text
문서 적재
→ 문서 구조별 Chunking
→ Embedding
→ Qdrant Collection별 저장
→ Metadata Payload 저장


사용자 질문
→ 질문 유형 판단
→ Collection Routing
→ Dynamic top-k 결정
→ Semantic / Keyword Search
→ Hybrid 결과 병합
→ 검색 결과 충분 여부 판단
   ├─ 충분: 계속 진행
   └─ 부족: Adaptive Multi Query → 추가 검색
→ 중복 제거
→ Re-ranker 후보 제한
→ Cross Encoder Re-ranking
→ 최적 Context 구성
→ GPT 답변 생성
→ 근거 Top-3 및 출처 표시
```

---

## 5. 개발 순서

1. 현재 버전을 Baseline으로 저장
2. Qdrant Metadata / Payload 정리
3. Collection Routing 적용
4. Keyword Search 추가
5. Semantic / Keyword / Hybrid Search 비교
6. Adaptive Multi Query와 Hybrid Search 연결
7. System Prompt 및 Hallucination 방지 보완
8. 다른 Re-ranking 방식 조사 및 비교
9. 동일 평가 질문셋으로 최종 성능 평가

기존에 완료된 Chunking, Dynamic top-k, Adaptive Multi Query, 응답시간 측정, Re-ranker 후보 제한은  
새로 구현하지 않고 현재 코드를 최대한 재사용한다.

---

## 6. 비교 및 평가가 필요한 항목

### 반드시 비교

| 비교 항목 | 비교 대상 | 주요 판단 기준 |
|---|---|---|
| 검색 방식 | Semantic / Keyword / Hybrid | 정답 검색 여부, 검색 품질, 응답시간 |
| Re-ranking | 현재 Cross Encoder / 비교 방식 | 정답 Chunk 순위, 품질, 처리시간 |
| Chunking | 기존 SentenceSplitter / 개선 Chunking | 정보 누락, 구조 보존, 검색 품질 |
| 전체 RAG | Baseline / 최종 고도화 버전 | 답변 품질, 출처 정확성, Hallucination, 응답시간 |

### 필요 시 비교

- Multi Query vs Query Rewrite
- Multi Query vs Decomposition

Query Rewrite / Decomposition은 테스트 결과 필요성이 확인될 때만 실제 적용한다.

---

## 7. 평가 질문셋

동일한 질문셋을 모든 비교 실험에서 사용한다.

질문 유형은 다음을 포함한다.

```text
- 일반 사실형 질문
- 전체/목록형 질문
- 정확한 키워드 / 코드 질문
- 의미 기반 질문
- 짧고 모호한 질문
- 복합 질문
- 문서 범위 밖 질문
```

평가 시 다음 항목을 기록한다.

```text
- 질문
- 검색 방식
- 선택된 Collection
- 검색된 Chunk
- Multi Query 실행 여부
- Re-ranking 결과
- 최종 답변
- 출처
- 정답 여부
- 정보 누락 여부
- Hallucination 여부
- Retrieval 시간
- Re-ranking 시간
- GPT 시간
- 전체 응답시간
```

---

## 8. 구현 원칙

- Conda 환경은 `rag_env` 사용
- 고도화 대상은 웹 화면이 사용하는 `server.py` 하나로 한정하고, CLI 테스트 스크립트인 `main.py`는 현 상태로 동결한다(수정 금지). `main.py`는 `Dockerfile.backend`(`uvicorn server:app`), GUIDE 실행 명령, 프론트엔드 API 호출 어디에서도 참조되지 않는 독립 스크립트이므로 동결해도 서비스 동작에 영향이 없다.
- 기존 정상 동작 코드 구조를 최대한 유지
- 기존 함수 및 모듈을 재사용
- 불필요한 Repository / Service / 추상화 계층 추가 금지
- 과도한 리팩토링 금지
- 한 기능씩 적용 후 동일 질문셋으로 검증
- 기능 추가 전후 결과를 비교할 수 있도록 유지
- 테스트 과정에서 발견된 문제는 원인과 수정 근거를 기록
- 계획에 없는 기능을 임의로 추가하지 않음

---

## 9. 최종 산출물

작업 완료 후 다음 내용을 정리한다.

```text
1. 적용한 고도화 기능
2. 검색 방식 비교 결과
3. Re-ranking 방식 비교 결과 및 선택 근거
4. Baseline vs 최종 RAG 성능 비교
5. 평균 응답시간 변화
6. 검색 정확도 / 답변 완전성 결과
7. Hallucination 테스트 결과
8. 최종 RAG 처리 흐름
```
