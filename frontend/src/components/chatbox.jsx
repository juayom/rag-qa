import { useState } from "react";
import api from "../services/api";

// 화면에 붙일 짧은 원인 표시
function describeError(err) {
  if (err?.response) {
    return err.response.status;
  }

  // 응답 자체가 없는 경우
  if (err?.code === "ECONNABORTED") {
    return "응답 시간 초과";
  }

  if (err?.code === "ERR_NETWORK") {
    return "서버에 연결할 수 없음 / CORS 차단";
  }

  return err?.code || "알 수 없는 오류";
}

function ChatBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openRetriever, setOpenRetriever] = useState({});

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("질문을 입력해주세요.");
      return;
    }

    const userQuestion = question;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const res = await api.post("/chat", {
        question: userQuestion,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.data.answer,
          queries: res.data.queries,

          sources: res.data.sources,
          retrieved_docs: res.data.retrieved_docs,
          refused: res.data.refused,

          retrieved_count: res.data.retrieved_count,
          response_time: res.data.response_time_ms,
          top_similarity: res.data.top_rerank_score,


        },
      ]);
    } catch (err) {
      // 원인 파악용 전체 오류는 콘솔에만 남김
      console.error("[/chat] 요청 실패", err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `오류가 발생했습니다 (${describeError(err)})`,
          sources: [],
        },
      ]);
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  return (
    <div className="container">
      <h1>📄 RAG Document QA</h1>

      <div className="chat-window">
        {messages.length === 0 && (
          <div className="welcome">
            질문을 입력하면 RAG가 문서를 검색하여 답변합니다.
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={
              msg.role === "user"
                ? "message user"
                : "message assistant"
            }
          >
            <div className="role">
              {msg.role === "user"
                ? "🙂 질문"
                : "🤖 답변"}
            </div>
            {msg.role === "assistant" &&
              msg.queries &&
              msg.queries.length > 0 && (

                <div className="multiquery-box">

                  <div className="multiquery-title">
                    🔍 Multi Query Generation
                  </div>

                  <ul className="multiquery-list">

                    {msg.queries.map((q, idx) => (

                      <li key={idx}>
                        {q}
                      </li>

                    ))}

                  </ul>

                </div>

              )}
            <div className="text">
              {msg.text}
            </div>
            {msg.role === "assistant" && (
              <div className="result-info">

                <span>
                  📄 검색 Chunk :
                  {msg.retrieved_count}
                </span>

                <span>
                  ⏱ {msg.response_time} ms
                </span>

                <span>
                  🎯 Similarity :
                  {msg.top_similarity}
                </span>

              </div>
            )}

            {msg.sources && msg.sources.length > 0 && (
              <>
                <div className="source-title">
                  📄 출처
                </div>

                <ul className="source-list">
                  {msg.sources.map((source, i) => (
                    <li key={i}>
                      {source}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {msg.retrieved_docs && (
              <>
                <button
                  className="toggle-btn"
                  onClick={() =>
                    setOpenRetriever((prev) => ({
                      ...prev,
                      [index]: !prev[index],
                    }))
                  }
                >
                  {openRetriever[index]
                    ? "📂 Search Process 결과 숨기기"
                    : msg.refused
                      ? "📂 참고: 검색 결과 보기 (답변 근거 아님)"
                      : "📂 Search Process 결과 보기"}
                </button>

                {openRetriever[index] && (
                  <div className="retriever-box">

                    {msg.refused && (
                      <p className="retriever-note">
                        참고: 검색된 문서이나 최종 답변의 근거로 채택되지 않음
                      </p>
                    )}

                    {msg.retrieved_docs.map((doc) => (
                      <div
                        key={doc.rank}
                        className="retriever-card"
                      >
                        <h4>
                          🔎 Retrieved Document #{doc.rank}
                        </h4>

                        <p>
                          <b>파일</b> : {doc.file}
                        </p>

                        <p>
                          <b>Chunk</b> : {doc.chunk}
                        </p>

                        <p>
                          <b>Similarity</b>

                          <span
                            className={
                              doc.rerank_score >= 0.5
                                ? "score-good"
                                : doc.rerank_score >= 0.1
                                  ? "score-mid"
                                  : "score-bad"
                            }
                          >

                            {doc.rerank_score}

                          </span>

                          <span className="retriever-score">
                            (retriever {doc.retriever_score})
                          </span>
                        </p>

                        <pre>
                          {doc.text}
                        </pre>

                      </div>
                    ))}

                  </div>
                )}
              </>
            )}

          </div>
        ))}

        {loading && (
          <div className="loading">
            🔍 문서를 검색하는 중...
          </div>
        )}
      </div>

      <textarea
        placeholder="질문을 입력하세요."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
      />

      <button onClick={askQuestion}>
        질문하기
      </button>
    </div>
  );
}

export default ChatBox;