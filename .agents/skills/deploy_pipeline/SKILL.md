---
name: Deploy Pipeline
description: Automates environment checks and launches the AI Pulse application stack (FastAPI backend, React frontend, and WhatsApp Bridge) in Docker Compose or Local Dev mode.
---

# Deploy Pipeline Skill

This skill teaches the agent how to deploy and manage the full AI Pulse stack (consisting of the FastAPI backend, React + Vite dashboard, and Node.js WhatsApp bridge). The skill ensures environment safety, manages port conflicts, configures dynamic project paths, and manages service lifecycle either in containerized (Docker Compose) or local development mode.

## Core Capabilities
- **Environment Autoconfig**: Automatically replicates `.env` between workspace root and the backend, dynamically updating the absolute `REPO_PATH` parameter.
- **Port Conflict Resolver**: Proactively identifies processes using ports `8000`, `5173`, or `3002` and terminates them to prevent collision errors.
- **Multi-Environment Runner**: Supports isolated containerized setups (Docker Compose) or native multi-process spawning for rapid local debugging.

## How to Execute the Deployment

Whenever you are asked to deploy, start, restart, or troubleshoot the application stack, follow these steps:

### 1. Verification Phase
- **Check Workspace Path**: Verify you are in the workspace root. Ensure `agent-pipeline` and the deployment scripts exist.
- **Verify Environment Files**: Use the files `deploy.ps1` (Windows/PowerShell) or `deploy.sh` (macOS/Linux) which automate copying `.env.example` to `.env` if none exists.
- **Verify Gemini API Key**: Check the `.env` file for a valid `GEMINI_API_KEY`. If it contains `gemini_api_key_from_ai_studio` or is empty, alert the user immediately.

### 2. Launch Stack (Windows PowerShell)
To launch the deployment menu on Windows (the user's OS), run:
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```
*Tip: If you want to automatically start in a specific mode without the menu, the script can be modified, or you can invoke specific parts or commands as detailed below.*

### 3. Launch Stack (macOS / Linux Bash)
To launch the deployment menu on Unix systems, run:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🛠️ Deployment Modes Reference

### Mode A: Docker Compose (Recommended for isolated runs)
This mode runs all three services inside Docker containers. It is clean and isolated.
1. Run command:
   ```bash
   docker-compose up -d --build
   ```
2. **Scan WhatsApp QR Code**: The WhatsApp bridge requires one-time authentication. Since the terminal is in the background, you must attach to the WhatsApp bridge to view and scan the QR code:
   ```bash
   docker attach whatsapp_bridge
   ```
   *Note: After scanning, detach safely by pressing `Ctrl+P, Ctrl+Q` (DO NOT press `Ctrl+C`, which kills the bridge).*

### Mode B: Local Native Processes (Recommended for active coding and live console inspection)
This mode runs the processes directly on the host system.
- **On Windows**: The PowerShell script uses `Start-Process` to spawn three separate, labeled Command Prompt consoles side-by-side:
  - `WhatsApp Bridge (Port 3002)`
  - `FastAPI Backend (Port 8000)`
  - `React Dashboard (Port 5173)`
  This gives instant visual feedback of the QR code and any runtime errors.
- **On Unix/macOS/Linux**: The Bash script runs them in the background and streams their outputs to the `logs/` directory:
  - WhatsApp Bridge: `tail -f logs/whatsapp.log`
  - Python Backend: `tail -f logs/backend.log`
  - React Frontend: `tail -f logs/frontend.log`

---

## 🛑 Stop & Cleanup Instructions

To gracefully stop all services and free up ports:
- **Docker Compose**:
  ```bash
  docker-compose down -v
  ```
- **PowerShell (Local)**:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000, 5173, 3002 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  ```
- **Bash (Local)**:
  ```bash
  lsof -i :8000,5173,3002 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
  ```

---

## 🔍 Troubleshooting & Verification

### Port Verification
Always check if ports are busy before reporting successful start:
- **Windows**: `Get-NetTCPConnection -LocalPort 8000, 5173, 3002 -ErrorAction SilentlyContinue`
- **Unix**: `lsof -i :8000`

### Checking Logs
If a service is misbehaving:
- **Docker logs**:
  - Backend: `docker logs ai_backend`
  - Frontend: `docker logs ai_frontend`
  - WhatsApp Bridge: `docker logs whatsapp_bridge`
- **Local logs (Unix)**:
  - Read files under the `logs/` folder.
