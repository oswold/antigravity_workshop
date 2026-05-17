# AI Pulse — Autonomous Newsletter Agent Pipeline
### WIBD Workshop: Agentic AI 101

A fully working **agentic pipeline** that researches, writes, and publishes a tech newsletter autonomously — with a live dashboard, real MCP integrations, and human-in-the-loop approval.

---

## 🏗️ Project Structure

```
agent-pipeline/
├── python-backend/            # FastAPI + LangGraph pipeline (port 8000)
│   ├── main.py                # Entry point (REST + SSE)
│   ├── state.py               # Shared in-memory state & event queue
│   ├── pipeline/
│   │   ├── graph.py           # LangGraph StateGraph definition
│   │   ├── runner.py          # Async graph execution
│   │   ├── nodes/             # Agent steps (fetch, research, write, review, publish)
│   │   ├── mcps/              # Client wrappers for WhatsApp, YouTube, and Fetch MCPs
│   │   └── guardrails/        # Input policy logic
│   └── scheduler/             # APScheduler cron integration
├── frontend/                  # React + Vite dashboard (port 5173)
│   └── src/
│       ├── App.jsx            # Full dashboard UI with SSE streaming
│       └── App.css            # Dark glassmorphism theme
└── whatsapp-bridge-js/        # Baileys-based WhatsApp HTTP bridge (port 3002)
    └── bridge.js              # Syncs and extracts links from self-messages
```

---

## 🚀 Quick Start

Ensure you have your `GEMINI_API_KEY` (and optionally your GitHub PAT and Gmail App Password) ready. 
Copy `python-backend/.env.example` to `python-backend/.env` and fill it out.

You need three terminal windows to run the stack:

### 1. WhatsApp Bridge
```bash
cd agent-pipeline/whatsapp-bridge-js
npm install
node bridge.js
# → First time only: Scan the QR code with your WhatsApp app
```

### 2. Python Backend
```bash
cd agent-pipeline/python-backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

python -m pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000
```

### 3. Frontend Dashboard
```bash
cd agent-pipeline/frontend
npm install
npm run dev
# → http://localhost:5173
```

## 🐳 Run with Docker (Alternative to Quick Start)

If you have Docker installed, you can run the entire pipeline (frontend, backend, and whatsapp bridge) using Docker Compose.

1. Create an `.env` file in the **root** of the repository (`podcasts/.env`) and add your secrets (you can copy `agent-pipeline/python-backend/.env.example`).
2. Run the following command from the root directory:
```bash
docker-compose up -d --build
```
3. **Important:** The WhatsApp bridge requires you to scan a QR code on its first run. To do this, attach to the whatsapp container's terminal:
```bash
docker attach whatsapp_bridge
# Scan the QR code, then press Ctrl+P, Ctrl+Q to detach (leave it running)
```

The apps will be available at:
- Dashboard: http://localhost:5173
- Backend API: http://localhost:8000

---

## 🔌 Live MCP Integrations

This pipeline relies exclusively on real MCP (Model Context Protocol) subprocess tools — **no mocks**.

| MCP Tool | Execution | Purpose |
|---|---|---|
| **WhatsApp Bridge** | Local HTTP (`:3002`) | Extracts URLs from messages sent to your own number |
| **YouTube Transcript** | `npx @kimtaeyoon83/...` | Fetches full captions for YouTube URLs directly |
| **Fetch** | `uvx mcp-server-fetch` | Scrapes and converts any public webpage into Markdown |

---

## 🛡️ Human-in-the-Loop (HITL) Guardrails

The LangGraph pipeline enforces two hard pauses where the agent waits for your explicit UI input before proceeding:

1. **Link Selection:** Before researching, you check/uncheck which extracted URLs should be processed.
2. **Publish Approval:** Before pushing to GitHub or sending an email, you review the generated newsletter and must explicitly click **Approve & Publish**.

---

## 🦙 Switch to Local Gemma (Offline LLM)

You can run the Writer Agent completely offline on your own hardware:
1. Ensure Ollama is installed and running: `ollama run gemma`
2. In the React dashboard, change the Writer Agent Model dropdown to **🦙 Local Gemma (Ollama)**.
3. The pipeline will automatically route the prompt to `http://localhost:11434` instead of the cloud Gemini API.

---

## 📡 API Reference

The FastAPI backend exposes the following key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/pipeline/run` | Start a new LangGraph run |
| `POST` | `/api/pipeline/cancel/{runId}` | Halt the pipeline immediately |
| `GET` | `/api/pipeline/events/{runId}` | SSE live stream of agent steps/logs |
| `POST` | `/api/pipeline/select-links/{runId}`| Respond to HITL Gate #1 |
| `POST` | `/api/pipeline/approve/{runId}` | Respond to HITL Gate #2 |
| `POST` | `/api/pipeline/cron` | Schedule the pipeline via APScheduler |
