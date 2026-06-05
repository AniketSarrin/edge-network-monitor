# Edge Network Monitor

An AI-powered full-stack network monitoring dashboard built with FastAPI, React, TypeScript, WebSockets, and a RAG pipeline.

## Overview

This project simulates a real-time edge network operations dashboard where operators can monitor device health and query network telemetry using natural language.

### Tab 1 — Device Status
- Live device status cards showing online, degraded, and offline states
- Real-time metrics per device: throughput, latency, packet loss, and transport type
- Automatic failover event alerts

### Tab 2 — Live Feed & AI Assistant
- AI assistant powered by a RAG pipeline — ask natural language questions about network health
- Responses stream token by token via WebSockets
- Live telemetry feed updating every 5 seconds

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Frontend | React, TypeScript, Vite |
| Real-time | WebSockets |
| AI | RAG pipeline, LangChain, OpenAI GPT-3.5 |
| Vector Store | FAISS |
| HTTP Client | Axios |

## Architecture

```
React Frontend (TypeScript)
        │
        ├── REST API ──────────► GET /devices
        │                        GET /telemetry
        │
        ├── WebSocket ─────────► ws://localhost:8000/ws/telemetry
        │                        (live telemetry every 5s)
        │
        └── WebSocket ─────────► ws://localhost:8000/ws/ask
                                 (streaming RAG responses)

FastAPI Backend (Python)
        │
        ├── Telemetry Generator (simulated HAVEN devices)
        │
        └── RAG Pipeline
                │
                ├── FAISS Vector Store
                ├── LangChain + OpenAI Embeddings
                └── GPT-3.5 Streaming
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key

### Backend Setup
```bash
cd rag_pipeline
pip install fastapi uvicorn langchain langchain-openai langchain-community langchain-text-splitters faiss-cpu python-dotenv openai
```

Create a `.env` file:
```
OPENAI_API_KEY=your_key_here
```

Run the backend:
```bash
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## Example Queries

- *"Which devices have had failover events?"*
- *"What is the average latency across all devices?"*
- *"Which device has the highest packet loss?"*
- *"Show me the status of all offline devices"*

## Project Structure

```
edge-network-monitor/
├── main.py                 # FastAPI backend
├── .env                    # API keys (not committed)
├── .gitignore
└── frontend/
    ├── src/
    │   ├── App.tsx          # Root component + tab navigation
    │   └── pages/
    │       ├── Dashboard.tsx    # Device status + telemetry table
    │       └── Assistant.tsx    # AI chat interface
    ├── package.json
    └── vite.config.ts
```

## Inspiration

Built after thinking about the overlap between aircraft telemetry pipelines (Honeywell Aerospace) and edge network operations. Same core problem: high-volume real-time data that needs to be ingested, normalized, and made actionable for operators. This project explores adding an AI layer on top of that.
