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

def generate_telemetry():
    events = []
    for device in devices:
        for i in range(5):
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 60))
            events.append({
                "device_id": device["id"],
                "location": device["location"],
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "throughput_mbps": round(random.uniform(0.5, 100.0), 2),
                "latency_ms": random.randint(10, 500),
                "packet_loss_pct": round(random.uniform(0, 15), 2),
                "transport": random.choice(["cellular", "wifi", "satcom"]),
                "failover_event": random.choice([True, False, False, False]),
                "status": device["status"],
            })
    return events

telemetry_data = generate_telemetry()

def build_knowledge_base():
    text = "Hoplynk HAVEN Edge Network Telemetry Report\n\n"
    for e in telemetry_data:
        text += (
            f"Device {e['device_id']} at {e['location']} recorded at {e['timestamp']}: "
            f"throughput={e['throughput_mbps']}Mbps, latency={e['latency_ms']}ms, "
            f"packet_loss={e['packet_loss_pct']}%, transport={e['transport']}, "
            f"status={e['status']}, failover={'yes' if e['failover_event'] else 'no'}.\n"
        )
    return text

knowledge_text = build_knowledge_base()
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.create_documents([knowledge_text])
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)
llm = ChatOpenAI(model="gpt-3.5-turbo")

prompt = ChatPromptTemplate.from_template(
    """You are Argus, an intelligent operator assistant for Hoplynk edge networks.
Use the following telemetry context to answer the operator's question.
Be specific about device IDs, locations, and metrics when relevant.

Context:
{context}

Question: {question}"""
)

chain = prompt | llm

class Query(BaseModel):
    question: str

@app.get("/devices")
def get_devices():
    return devices

@app.get("/telemetry")
def get_telemetry():
    return telemetry_data

@app.post("/ask")
def ask(query: Query):
    retriever = vectorstore.as_retriever()
    retrieved_docs = retriever.invoke(query.question)
    context = "\n".join([doc.page_content for doc in retrieved_docs])
    response = chain.invoke({"context": context, "question": query.question})
    return {"question": query.question, "answer": response.content}

@app.websocket("/ws/ask")
async def websocket_ask(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            question = await websocket.receive_text()
            retrieved_docs = vectorstore.similarity_search(question, k=3)
            context = "\n".join([doc.page_content for doc in retrieved_docs])
            full_prompt = f"""You are Argus, an intelligent operator assistant for Hoplynk edge networks.
Use the following telemetry context to answer the operator's question.
Be specific about device IDs, locations, and metrics when relevant.

Context:
{context}

Question: {question}"""
            client = AsyncOpenAI()
            stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": full_prompt}],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    await websocket.send_text(delta)
            await websocket.send_text("[DONE]")
    except Exception as e:
        await websocket.close()

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            fresh = generate_telemetry()
            await websocket.send_text(json.dumps(fresh))
            await asyncio.sleep(5)
    except Exception:
        await websocket.close()