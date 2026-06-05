import { useState, useRef } from "react";
import type { CSSProperties } from "react";

export default function Assistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const wsAskRef = useRef<WebSocket | null>(null);

  const askQuestion = () => {
    if (!question.trim()) return;
    setAnswer("");
    setIsStreaming(true);

    wsAskRef.current = new WebSocket("ws://localhost:8000/ws/ask");
    const ws = wsAskRef.current;

    ws.onopen = () => ws.send(question);
    ws.onmessage = (event) => {
      if (event.data === "[DONE]") {
        setIsStreaming(false);
        ws.close();
      } else {
        setAnswer((prev) => prev + event.data);
      }
    };
  };

  return (
    <div style={styles.section}>
      <h2 style={styles.sectionTitle}>AI NETWORK ASSISTANT</h2>
      <p style={styles.subtitle}>Ask natural language questions about your network</p>
      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askQuestion()}
          placeholder="e.g. Which devices have had failover events?"
        />
        <button
          style={{ ...styles.button, opacity: isStreaming ? 0.6 : 1 }}
          onClick={askQuestion}
          disabled={isStreaming}
        >
          {isStreaming ? "Analyzing..." : "Ask AI"}
        </button>
      </div>
      {answer && (
        <div style={styles.answerBox}>
          <p style={styles.answerLabel}>AI RESPONSE</p>
          <p style={styles.answerText}>
            {answer}
            {isStreaming && <span style={styles.cursor}>▋</span>}
          </p>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  section: { marginBottom: "40px" },
  sectionTitle: { color: "#38bdf8", fontSize: "12px", letterSpacing: "3px", marginBottom: "16px", borderBottom: "1px solid #1e3a5f", paddingBottom: "8px" },
  subtitle: { color: "#64748b", fontSize: "12px", marginBottom: "16px" },
  inputRow: { display: "flex", gap: "12px" },
  input: { flex: 1, background: "#0f1f35", border: "1px solid #1e3a5f", borderRadius: "6px", padding: "12px 16px", color: "#e2e8f0", fontSize: "14px", fontFamily: "monospace", outline: "none" },
  button: { background: "#0369a1", color: "#fff", border: "none", borderRadius: "6px", padding: "12px 24px", cursor: "pointer", fontSize: "14px", fontFamily: "monospace", letterSpacing: "1px" },
  answerBox: { marginTop: "16px", background: "#0f1f35", border: "1px solid #1e3a5f", borderRadius: "8px", padding: "16px" },
  answerLabel: { color: "#38bdf8", fontSize: "10px", letterSpacing: "2px", margin: "0 0 8px" },
  answerText: { color: "#e2e8f0", fontSize: "14px", lineHeight: "1.6", margin: 0 },
  cursor: { animation: "blink 1s infinite" },
};