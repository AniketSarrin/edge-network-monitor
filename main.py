from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import asyncio
import json
import random
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from collections import deque
import statistics
from typing import List

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

devices = [
    {"id": "1", "location": "Forward Base Alpha", "status": "online"},
    {"id": "2", "location": "Checkpoint Bravo", "status": "degraded"},
    {"id": "3", "location": "Outpost Charlie", "status": "offline"},
    {"id": "4", "location": "Command Delta", "status": "online"},
]

# ==================== PHASE 1: LIVE RAG ====================
# In-memory telemetry buffer (keeps last ~300 events = ~15 min at 1 event/3sec per device)
telemetry_buffer = deque(maxlen=300)
vectorstore = None
embeddings = None
splitter = None
last_vectorstore_rebuild = datetime.now()

def generate_telemetry():
    """Generate fresh telemetry and add to buffer"""
    events = []
    for device in devices:
        for i in range(5):
            timestamp = datetime.now() - timedelta(minutes=random.randint(0, 5))
            event = {
                "device_id": device["id"],
                "location": device["location"],
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_obj": timestamp,
                "throughput_mbps": round(random.uniform(0.5, 100.0), 2),
                "latency_ms": random.randint(10, 500),
                "packet_loss_pct": round(random.uniform(0, 15), 2),
                "transport": random.choice(["cellular", "wifi", "satcom"]),
                "failover_event": random.choice([True, False, False, False]),
                "status": device["status"],
            }
            events.append(event)
            telemetry_buffer.append(event)
    return events

def build_knowledge_base_from_buffer():
    """Build knowledge base from current buffer (for live RAG)"""
    text = "Hoplynk HAVEN Edge Network Telemetry Report\n\n"
    for e in telemetry_buffer:
        text += (
            f"Device {e['device_id']} at {e['location']} recorded at {e['timestamp']}: "
            f"throughput={e['throughput_mbps']}Mbps, latency={e['latency_ms']}ms, "
            f"packet_loss={e['packet_loss_pct']}%, transport={e['transport']}, "
            f"status={e['status']}, failover={'yes' if e['failover_event'] else 'no'}.\n"
        )
    return text

def rebuild_vectorstore():
    """Rebuild FAISS vectorstore from current buffer (live RAG update)"""
    global vectorstore, last_vectorstore_rebuild
    if len(telemetry_buffer) == 0:
        return
    
    knowledge_text = build_knowledge_base_from_buffer()
    docs = splitter.create_documents([knowledge_text])
    
    # Add metadata to each doc (timestamp, device_id for filtering)
    for i, doc in enumerate(docs):
        event_idx = i % len(telemetry_buffer) if telemetry_buffer else 0
        if event_idx < len(telemetry_buffer):
            event = list(telemetry_buffer)[event_idx]
            doc.metadata = {
                "timestamp": event["timestamp"],
                "device_id": event["device_id"],
                "timestamp_obj": event["timestamp_obj"]
            }
    
    vectorstore = FAISS.from_documents(docs, embeddings)
    last_vectorstore_rebuild = datetime.now()

# Initialize once at startup
embeddings = OpenAIEmbeddings()
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
generate_telemetry()  # Populate buffer
rebuild_vectorstore()

llm = ChatOpenAI(model="gpt-3.5-turbo")

# ==================== PHASE 2: AGENTIC TOOLS ====================
# ==================== PHASE 2: AGENTIC TOOLS ====================
def get_device_failures(time_minutes: int = 5) -> str:
    """Get all devices that had failover events in the last N minutes"""
    cutoff_time = datetime.now() - timedelta(minutes=time_minutes)
    failures = [
        e for e in telemetry_buffer
        if e["failover_event"] and e["timestamp_obj"] >= cutoff_time
    ]
    
    if not failures:
        return f"No failover events detected in the last {time_minutes} minutes."
    
    result = f"Found {len(failures)} failover events in the last {time_minutes} minutes:\n"
    for f in failures:
        result += f"  - Device {f['device_id']} at {f['location']} at {f['timestamp']}\n"
    return result

def analyze_latency(device_id: str = None, threshold_ms: int = 300) -> str:
    """Analyze latency for a specific device, flag if exceeds threshold"""
    if device_id is None:
        # If no device specified, show all devices with high latency
        result = "Device Latency Analysis:\n"
        for d_id in [dev["id"] for dev in devices]:
            device_events = [e for e in telemetry_buffer if e["device_id"] == d_id]
            if device_events:
                latencies = [e["latency_ms"] for e in device_events]
                avg_latency = statistics.mean(latencies)
                max_latency = max(latencies)
                status = "⚠️ HIGH" if avg_latency > threshold_ms else "✓ NORMAL"
                result += f"  Device {d_id}: Avg {avg_latency:.0f}ms, Max {max_latency}ms [{status}]\n"
        return result
    
    device_events = [
        e for e in telemetry_buffer
        if e["device_id"] == device_id
    ]
    
    if not device_events:
        return f"No data found for device {device_id}."
    
    latencies = [e["latency_ms"] for e in device_events]
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    
    anomalies = [e for e in device_events if e["latency_ms"] > threshold_ms]
    anomaly_msg = f"\n  ⚠️ {len(anomalies)} readings exceed {threshold_ms}ms threshold" if anomalies else ""
    
    return (
        f"Device {device_id} ({device_events[0]['location']}):\n"
        f"  Avg Latency: {avg_latency:.1f}ms\n"
        f"  Max Latency: {max_latency}ms\n"
        f"  Min Latency: {min_latency}ms{anomaly_msg}"
    )

def get_device_status(device_id: str) -> str:
    """Get the latest status and metrics for a device"""
    device_events = [e for e in telemetry_buffer if e["device_id"] == device_id]
    
    if not device_events:
        return f"No data found for device {device_id}."
    
    latest = device_events[-1]
    return (
        f"Device {device_id} at {latest['location']}:\n"
        f"  Status: {latest['status']}\n"
        f"  Throughput: {latest['throughput_mbps']} Mbps\n"
        f"  Latency: {latest['latency_ms']} ms\n"
        f"  Packet Loss: {latest['packet_loss_pct']}%\n"
        f"  Transport: {latest['transport']}\n"
        f"  Failover Event: {'Yes' if latest['failover_event'] else 'No'}"
    )

def compute_network_stats(time_window_minutes: int = 10) -> str:
    """Compute aggregated network statistics across all devices"""
    cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
    recent_events = [e for e in telemetry_buffer if e["timestamp_obj"] >= cutoff_time]
    
    if not recent_events:
        return f"No data in the last {time_window_minutes} minutes."
    
    throughputs = [e["throughput_mbps"] for e in recent_events]
    latencies = [e["latency_ms"] for e in recent_events]
    packet_losses = [e["packet_loss_pct"] for e in recent_events]
    
    return (
        f"Network Statistics (last {time_window_minutes} minutes):\n"
        f"  Avg Throughput: {statistics.mean(throughputs):.2f} Mbps\n"
        f"  Avg Latency: {statistics.mean(latencies):.1f} ms\n"
        f"  Avg Packet Loss: {statistics.mean(packet_losses):.2f}%\n"
        f"  Max Latency: {max(latencies)} ms\n"
        f"  Failover Events: {sum(1 for e in recent_events if e['failover_event'])}"
    )

def run_agentic_query(question: str) -> str:
    """
    Route question to appropriate tool(s) based on keywords.
    This is a simple agent that routes queries to tools without complex orchestration.
    """
    question_lower = question.lower()
    
    # Detect intent and call appropriate tools
    if "failover" in question_lower or "failure" in question_lower:
        time_minutes = 5
        # Try to extract time window from question
        if "last" in question_lower:
            import re
            match = re.search(r'last\s+(\d+)\s+(minutes?|mins?)', question_lower)
            if match:
                time_minutes = int(match.group(1))
        return get_device_failures(time_minutes)
    
    elif "latency" in question_lower or "latencies" in question_lower:
        device_id = None
        # Try to extract device ID
        import re
        match = re.search(r'device\s+(\d+)', question_lower)
        if match:
            device_id = match.group(1)
        return analyze_latency(device_id)
    
    elif ("device" in question_lower and "status" in question_lower) or "which devices" in question_lower:
        # Return status for specific device or all
        import re
        match = re.search(r'device\s+(\d+)', question_lower)
        if match:
            device_id = match.group(1)
            return get_device_status(device_id)
        else:
            # Show all device statuses
            result = "Device Status Summary:\n"
            for device_id in [d["id"] for d in devices]:
                device_events = [e for e in telemetry_buffer if e["device_id"] == device_id]
                if device_events:
                    latest = device_events[-1]
                    result += f"  Device {device_id}: {latest['status']} - Latency {latest['latency_ms']}ms, Loss {latest['packet_loss_pct']}%\n"
            return result
    
    elif "network" in question_lower or "stats" in question_lower or "statistics" in question_lower:
        return compute_network_stats()
    
    else:
        # Default: use RAG + LLM for general questions
        return "🤖 Using semantic search to answer your question..."

# ==================== PHASE 3: PROACTIVE ALERTING ====================
alerts_buffer = deque(maxlen=100)
active_alert_clients = set()

def check_for_anomalies() -> List[dict]:
    """Check recent telemetry for anomalies and generate alerts"""
    new_alerts = []
    
    # Check last 5 minutes for anomalies
    cutoff_time = datetime.now() - timedelta(minutes=5)
    recent = [e for e in telemetry_buffer if e["timestamp_obj"] >= cutoff_time]
    
    if not recent:
        return new_alerts
    
    # Check for failover events
    failovers = [e for e in recent if e["failover_event"]]
    if failovers:
        for event in failovers[-3:]:  # Last 3 failovers
            alert = {
                "id": f"failover_{event['device_id']}_{event['timestamp']}",
                "type": "failover",
                "device_id": event["device_id"],
                "message": f"⚠️ FAILOVER EVENT: Device {event['device_id']} at {event['location']}",
                "timestamp": event["timestamp"],
                "severity": "high"
            }
            if alert["id"] not in [a.get("id") for a in alerts_buffer]:
                new_alerts.append(alert)
                alerts_buffer.append(alert)
    
    # Check for high latency
    for device_id in [d["id"] for d in devices]:
        device_events = [e for e in recent if e["device_id"] == device_id]
        if device_events:
            avg_latency = statistics.mean([e["latency_ms"] for e in device_events])
            if avg_latency > 300:
                alert = {
                    "id": f"latency_{device_id}",
                    "type": "latency",
                    "device_id": device_id,
                    "message": f"🔴 HIGH LATENCY: Device {device_id} avg latency {avg_latency:.0f}ms (threshold: 300ms)",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "severity": "medium"
                }
                if alert["id"] not in [a.get("id") for a in alerts_buffer]:
                    new_alerts.append(alert)
                    alerts_buffer.append(alert)
    
    # Check for high packet loss
    for device_id in [d["id"] for d in devices]:
        device_events = [e for e in recent if e["device_id"] == device_id]
        if device_events:
            avg_loss = statistics.mean([e["packet_loss_pct"] for e in device_events])
            if avg_loss > 5:
                alert = {
                    "id": f"packet_loss_{device_id}",
                    "type": "packet_loss",
                    "device_id": device_id,
                    "message": f"🟡 HIGH PACKET LOSS: Device {device_id} packet loss {avg_loss:.1f}% (threshold: 5%)",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "severity": "low"
                }
                if alert["id"] not in [a.get("id") for a in alerts_buffer]:
                    new_alerts.append(alert)
                    alerts_buffer.append(alert)
    
    return new_alerts

async def background_monitor():
    """Background task that periodically checks for anomalies and broadcasts alerts"""
    while True:
        try:
            new_alerts = check_for_anomalies()
            # Broadcast to all connected alert clients
            for client in list(active_alert_clients):
                for alert in new_alerts:
                    try:
                        await client.send_text(json.dumps(alert))
                    except Exception:
                        active_alert_clients.discard(client)
            await asyncio.sleep(10)  # Check every 10 seconds
        except Exception as e:
            await asyncio.sleep(10)

class Query(BaseModel):
    question: str

@app.get("/devices")
def get_devices():
    return devices

@app.get("/telemetry")
def get_telemetry():
    # Return telemetry without timestamp_obj (not JSON serializable)
    return [{k: v for k, v in e.items() if k != 'timestamp_obj'} for e in telemetry_buffer]

@app.get("/alerts")
def get_alerts():
    return list(alerts_buffer)

@app.post("/ask")
def ask(query: Query):
    """Use agentic query routing to answer (Phase 2: Agentic)"""
    response = run_agentic_query(query.question)
    return {"question": query.question, "answer": response}

@app.websocket("/ws/ask")
async def websocket_ask(websocket: WebSocket):
    """WebSocket agent endpoint with live RAG (Phase 1 + 2)"""
    await websocket.accept()
    try:
        while True:
            question = await websocket.receive_text()
            
            # Rebuild vectorstore if needed (every 30 seconds for freshness)
            global last_vectorstore_rebuild
            if (datetime.now() - last_vectorstore_rebuild).total_seconds() > 30:
                rebuild_vectorstore()
            
            # Use agentic query routing
            answer_text = run_agentic_query(question)
            
            # Send response as stream-like chunks
            chunk_size = 20
            for i in range(0, len(answer_text), chunk_size):
                await websocket.send_text(answer_text[i:i+chunk_size])
                await asyncio.sleep(0.01)  # Small delay for effect
            await websocket.send_text("[DONE]")
    except Exception as e:
        await websocket.close()

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Stream fresh telemetry data"""
    await websocket.accept()
    try:
        while True:
            fresh = generate_telemetry()
            # Remove timestamp_obj before sending (not JSON serializable)
            clean_fresh = [{k: v for k, v in e.items() if k != 'timestamp_obj'} for e in fresh]
            await websocket.send_text(json.dumps(clean_fresh))
            await asyncio.sleep(5)
    except Exception:
        await websocket.close()

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Stream proactive alerts to client (Phase 3)"""
    await websocket.accept()
    active_alert_clients.add(websocket)
    try:
        # Send existing alerts to new client
        for alert in list(alerts_buffer)[-10:]:  # Last 10 alerts
            await websocket.send_text(json.dumps(alert))
        
        # Keep connection alive and receive dismiss/clear commands
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except Exception:
        active_alert_clients.discard(websocket)
        await websocket.close()

# Start background monitoring task on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_monitor())