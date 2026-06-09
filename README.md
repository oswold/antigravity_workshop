# Antigravity Vibe coded Application Demo - Newsletter Generator

This repository contains a **complete end‑to‑end demo** of the **Agentic AI 101** pipeline built with:

- **FastAPI** backend (`pipeline/`)
- **React + Vite** dashboard (`frontend/`)
- **WhatsApp Bridge** (Node.js Baileys) (`whatsapp-bridge/`)
- **Google Antigravity SDK** demo scripts (`antigravity-demo/`)

The **root** README provides instructions for deploying the full stack, while the `antigravity-demo/README.md` focuses solely on the individual demo scripts.

---

## 📦 Prerequisites

1. **Docker Desktop** (or Docker Engine) – required for the containerised deployment.
2. **Node.js ≥ 18** – for the WhatsApp bridge (only needed in native mode).
3. **Python ≥ 3.9** – for the FastAPI backend.
4. **Ollama** (optional) – to run the local Gemma model used by some demo scripts.
5. **Gemini API key** – create a `.env` file at the repo root:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

---

## 🚀 Deploy the Pipeline (Root Application)

The repository ships a **PowerShell helper** (`deploy.ps1`) that can launch the entire stack either via **Docker‑Compose** or **Native mode**.

### 1️⃣ Docker‑Compose (recommended)
```powershell
# From the repository root
depower.ps1   # alias for the script, or run directly:
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```
When the interactive menu appears, select **`1`**:
- Validates the workspace layout and injects `REPO_PATH` into `.env`.
- Stops any stray processes on ports 8000, 5173, 3002.
- Builds and starts three containers: `ai_backend`, `ai_frontend`, `whatsapp_bridge`.
- Shows URLs for the dashboard, API, and bridge.
- Prompts to verify/start local Gemma via Ollama (answer `y` if you have Ollama running).

### 2️⃣ Native Mode (no Docker)
Select **`2`** from the menu. The script will:
- Open three separate console windows:
  - FastAPI backend (`uvicorn pipeline.main:app --reload`)
  - React dashboard (`npm run dev`)
  - WhatsApp bridge (`node bridge.js`)
- Install missing `node_modules` or create a Python virtual environment on first run.
- Prompt for Ollama verification (same as Docker mode).
- Useful on machines without Docker or when you need direct process access.

### 3️⃣ Stopping & Cleaning Up
- **Docker mode** – preserve the WhatsApp session volume:
  ```powershell
  docker-compose down
  ```
- To wipe the session (force QR‑code re‑scan):
  ```powershell
  docker-compose down -v
  ```
- **Native mode** – close the three console windows or choose option **`3`** from the script menu.

---

## 📁 Repository Layout
```
antigravity-sdk-demo-scripts/
│   README.md            # <‑‑ (this file) – full app deployment guide
│   deploy.ps1            # PowerShell deploy helper
│
├─ antigravity-demo/      # Demo scripts – see its own README
│   README.md            # script‑focused documentation
│   *.py                 # 12 Python demo files
│
├─ pipeline/              # FastAPI backend with LangGraph state graph
│   main.py, stategraph.py, …
│
├─ frontend/              # React + Vite dashboard
│   src/, public/, vite.config.ts
│
└─ whatsapp-bridge/       # Node.js Baileys bridge
    bridge.js, package.json
```

---

## 🛠️ Additional Resources
- **SDK docs**: <https://github.com/google-antigravity/antigravity-sdk-python>
- **LangGraph examples**: <https://github.com/langgraph/langgraph>
- **MCP integrations**: see `.agents/skills/` for WhatsApp, YouTube, and Fetch MCPs.
- **Troubleshooting**:
  - Ensure Docker daemon is reachable (`docker info`).
  - If the bridge fails to authenticate, run `docker attach whatsapp_bridge` to scan the QR code, then detach with `Ctrl+X`.

---

*Happy hacking!*
