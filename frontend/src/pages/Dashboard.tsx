import type { CSSProperties } from "react";

const STATUS_COLORS: Record<string, string> = {
  online: "#22c55e",
  degraded: "#f59e0b",
  offline: "#ef4444",
};

interface Device {
  id: string;
  location: string;
  status: string;
  latest?: Telemetry;
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

interface Props {
  devices: Device[];
  telemetry: Telemetry[];
}

export default function Dashboard({ devices, telemetry }: Props) {
  const latestByDevice = devices.map((device) => {
    const events = telemetry.filter((t) => t.device_id === device.id);
    const latest = events[events.length - 1];
    return { ...device, latest };
  });

  return (
  <div>
    {devices.length > 0 && (
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>DEVICE STATUS</h2>
        <div style={styles.grid}>
          {latestByDevice.map((device) => (
            <div key={device.id} style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.deviceId}>{device.id}</span>
                <span style={{ ...styles.statusBadge, background: STATUS_COLORS[device.status] }}>
                  {device.status.toUpperCase()}
                </span>
              </div>
              <p style={styles.location}>📍 {device.location}</p>
              {device.latest && (
                <div style={styles.metrics}>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Throughput</span>
                    <span style={styles.metricValue}>{device.latest.throughput_mbps} Mbps</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Latency</span>
                    <span style={styles.metricValue}>{device.latest.latency_ms} ms</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Packet Loss</span>
                    <span style={styles.metricValue}>{device.latest.packet_loss_pct}%</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Transport</span>
                    <span style={styles.metricValue}>{device.latest.transport}</span>
                  </div>
                  {device.latest.failover_event && (
                    <div style={styles.failoverAlert}>⚠ FAILOVER EVENT DETECTED</div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )}

    {telemetry.length > 0 && devices.length === 0 && (
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>LIVE TELEMETRY FEED</h2>
        <div style={styles.tableWrapper}>
          <table style={styles.table}>
            <thead>
              <tr>
                {["Device", "Location", "Time", "Throughput", "Latency", "Loss", "Transport", "Failover"].map((h) => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {telemetry.slice(0, 10).map((t, i) => (
                <tr key={i} style={{ background: t.failover_event ? "#2d1a1a" : "transparent" }}>
                  <td style={styles.td}>{t.device_id}</td>
                  <td style={styles.td}>{t.location}</td>
                  <td style={styles.td}>{t.timestamp}</td>
                  <td style={styles.td}>{t.throughput_mbps} Mbps</td>
                  <td style={styles.td}>{t.latency_ms} ms</td>
                  <td style={styles.td}>{t.packet_loss_pct}%</td>
                  <td style={styles.td}>{t.transport}</td>
                  <td style={{ ...styles.td, color: t.failover_event ? "#ef4444" : "#22c55e" }}>
                    {t.failover_event ? "⚠ YES" : "NO"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}
  </div>
);
}

const styles: Record<string, CSSProperties> = {
  section: { marginBottom: "40px" },
  sectionTitle: { color: "#38bdf8", fontSize: "12px", letterSpacing: "3px", marginBottom: "16px", borderBottom: "1px solid #1e3a5f", paddingBottom: "8px" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" },
  card: { background: "#0f1f35", border: "1px solid #1e3a5f", borderRadius: "8px", padding: "16px" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" },
  deviceId: { color: "#38bdf8", fontWeight: "bold", fontSize: "14px" },
  statusBadge: { fontSize: "10px", padding: "2px 8px", borderRadius: "4px", color: "#000", fontWeight: "bold" },
  location: { color: "#94a3b8", fontSize: "12px", margin: "0 0 12px" },
  metrics: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" },
  metric: { background: "#0a0f1a", padding: "8px", borderRadius: "4px" },
  metricLabel: { display: "block", color: "#64748b", fontSize: "10px", letterSpacing: "1px" },
  metricValue: { display: "block", color: "#e2e8f0", fontSize: "13px", fontWeight: "bold", marginTop: "2px" },
  failoverAlert: { gridColumn: "span 2", background: "#7f1d1d", color: "#fca5a5", padding: "6px", borderRadius: "4px", fontSize: "11px", textAlign: "center" },
  tableWrapper: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: "12px" },
  th: { color: "#64748b", textAlign: "left", padding: "8px 12px", borderBottom: "1px solid #1e3a5f", letterSpacing: "1px" },
  td: { padding: "8px 12px", borderBottom: "1px solid #0f1f35", color: "#94a3b8" },
};