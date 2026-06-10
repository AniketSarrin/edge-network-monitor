import { useState, useRef, useEffect } from "react";
import type { CSSProperties } from "react";

interface Alert {
  id: string;
  type: string;
  device_id: string;
  message: string;
  timestamp: string;
  severity: string;
}

export default function Assistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const wsAskRef = useRef<WebSocket | null>(null);
  const wsAlertsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to alerts WebSocket
    wsAlertsRef.current = new WebSocket("ws://localhost:8000/ws/alerts");
    const ws = wsAlertsRef.current;

    ws.onmessage = (event) => {
      try {
        const alert = JSON.parse(event.data);
        setAlerts((prev) => [alert, ...prev].slice(0, 20)); // Keep last 20 alerts
      } catch (e) {
        // Ignore non-JSON messages
      }
    };

    ws.onerror = () => {
      console.error("Alert WebSocket error");
    };

    return () => {
      ws.close();
    };
  }, []);

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

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "#ef4444";
      case "medium":
        return "#f59e0b";
      case "low":
        return "#eab308";
      default:
        return "#64748b";
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>AI NETWORK ASSISTANT</h2>
        <p style={styles.subtitle}>Ask natural language questions about your network</p>
        <div style={styles.inputRow}>
          <input
            style={styles.input}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && askQuestion()}
            placeholder="e.g. Which devices have had failover events in the last 5 minutes?"
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
            <p style={styles.answerLabel}>AI RESPONSE (AGENTIC)</p>
            <p style={styles.answerText}>
              {answer}
              {isStreaming && <span style={styles.cursor}>▋</span>}
            </p>
          </div>
        )}
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>
          🚨 PROACTIVE ALERTS
          <span style={styles.alertCount}>{alerts.length}</span>
        </h2>
        <p style={styles.subtitle}>Real-time anomaly detection and notifications</p>
        
        {alerts.length === 0 ? (
          <div style={styles.noAlertsBox}>
            <p style={styles.noAlertsText}>✅ All systems nominal. No active alerts.</p>
          </div>
        ) : (
          <div style={styles.alertsList}>
            {alerts.map((alert) => (
              <div
                key={alert.id}
                style={{
                  ...styles.alertItem,
                  borderLeft: `4px solid ${getSeverityColor(alert.severity)}`,
                }}
              >
                <div style={styles.alertHeader}>
                  <span style={styles.alertMessage}>{alert.message}</span>
                  <button
                    style={styles.dismissButton}
                    onClick={() => dismissAlert(alert.id)}
                  >
                    ✕
                  </button>
                </div>
                <p style={styles.alertMeta}>
                  Device {alert.device_id} • {alert.timestamp} • {alert.type.toUpperCase()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  container: { marginBottom: "40px" },
  section: { marginBottom: "40px" },
  sectionTitle: {
    color: "#38bdf8",
    fontSize: "12px",
    letterSpacing: "3px",
    marginBottom: "16px",
    borderBottom: "1px solid #1e3a5f",
    paddingBottom: "8px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  alertCount: {
    background: "#ef4444",
    color: "#fff",
    borderRadius: "50%",
    width: "24px",
    height: "24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "10px",
    fontWeight: "bold",
  },
  subtitle: { color: "#64748b", fontSize: "12px", marginBottom: "16px" },
  inputRow: { display: "flex", gap: "12px" },
  input: {
    flex: 1,
    background: "#0f1f35",
    border: "1px solid #1e3a5f",
    borderRadius: "6px",
    padding: "12px 16px",
    color: "#e2e8f0",
    fontSize: "14px",
    fontFamily: "monospace",
    outline: "none",
  } as CSSProperties,
  button: {
    background: "#0369a1",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    padding: "12px 24px",
    cursor: "pointer",
    fontSize: "14px",
    fontFamily: "monospace",
    letterSpacing: "1px",
  } as CSSProperties,
  answerBox: {
    marginTop: "16px",
    background: "#0f1f35",
    border: "1px solid #1e3a5f",
    borderRadius: "8px",
    padding: "16px",
  },
  answerLabel: { color: "#38bdf8", fontSize: "10px", letterSpacing: "2px", margin: "0 0 8px" },
  answerText: { color: "#e2e8f0", fontSize: "14px", lineHeight: "1.6", margin: 0 },
  cursor: { animation: "blink 1s infinite" },
  alertsList: { display: "flex", flexDirection: "column" as const, gap: "12px" },
  alertItem: {
    background: "#0f1f35",
    border: "1px solid #1e3a5f",
    borderRadius: "6px",
    padding: "12px",
  },
  alertHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "12px",
  },
  alertMessage: { color: "#e2e8f0", fontSize: "13px", fontWeight: "500" as const },
  dismissButton: {
    background: "transparent",
    border: "none",
    color: "#64748b",
    cursor: "pointer",
    fontSize: "16px",
    padding: "0",
    minWidth: "24px",
  },
  alertMeta: { color: "#64748b", fontSize: "11px", margin: "8px 0 0" },
  noAlertsBox: { background: "#0f1f35", border: "1px solid #1e3a5f", borderRadius: "8px", padding: "16px" },
  noAlertsText: { color: "#22c55e", fontSize: "14px", margin: 0 },
};