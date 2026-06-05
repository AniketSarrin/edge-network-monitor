import { useState, useEffect, useRef } from "react";
import type { CSSProperties } from "react";
import axios from "axios";
import Dashboard from "./pages/Dashboard";
import Assistant from "./pages/Assistant";

interface Device {
  id: string;
  location: string;
  status: string;
}

interface Telemetry {
  device_id: string;
  location: string;
  timestamp: string;
  throughput_mbps: number;
  latency_ms: number;
  packet_loss_pct: number;
  transport: string;
  failover_event?: boolean;
}

export default function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry[]>([]);
  const [activeTab, setActiveTab] = useState<"dashboard" | "assistant">("dashboard");
  const wsTelemetryRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    axios.get("http://localhost:8000/devices").then((res) => setDevices(res.data));
  }, []);

  useEffect(() => {
    wsTelemetryRef.current = new WebSocket("ws://localhost:8000/ws/telemetry");
    wsTelemetryRef.current.onmessage = (event) => {
      setTelemetry(JSON.parse(event.data));
    };
    return () => wsTelemetryRef.current?.close();
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>EDGE NETWORK MONITOR</h1>
        <p style={styles.subtitle}>AI-Powered Network Operations Dashboard</p>
      </div>

      <div style={styles.tabs}>
        <button
          style={{ ...styles.tab, ...(activeTab === "dashboard" ? styles.tabActive : {}) }}
          onClick={() => setActiveTab("dashboard")}
        >
          📡 Device Status
        </button>
        <button
          style={{ ...styles.tab, ...(activeTab === "assistant" ? styles.tabActive : {}) }}
          onClick={() => setActiveTab("assistant")}
        >
          🤖 Live Feed & AI
        </button>
      </div>

      {activeTab === "dashboard" ? (
  <Dashboard devices={devices} telemetry={telemetry} />
) : (
  <>
    <Assistant />
    <Dashboard devices={[]} telemetry={telemetry} />
  </>
)}
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  container: { background: "#0a0f1a", minHeight: "100vh", color: "#e2e8f0", fontFamily: "monospace", padding: "24px" },
  header: { borderBottom: "1px solid #1e3a5f", paddingBottom: "16px", marginBottom: "24px" },
  title: { color: "#38bdf8", fontSize: "24px", letterSpacing: "4px", margin: 0 },
  subtitle: { color: "#64748b", margin: "4px 0 0", fontSize: "12px", letterSpacing: "2px" },
  tabs: { display: "flex", gap: "8px", marginBottom: "32px", borderBottom: "1px solid #1e3a5f" },
  tab: { background: "transparent", border: "none", color: "#64748b", padding: "10px 20px", cursor: "pointer", fontSize: "13px", fontFamily: "monospace", borderBottom: "2px solid transparent", marginBottom: "-1px" },
  tabActive: { color: "#38bdf8", borderBottom: "2px solid #38bdf8" },
};