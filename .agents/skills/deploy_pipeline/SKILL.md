---
name: Deploy Pipeline
description: Automates environment checks and launches the AI Pulse application stack (FastAPI backend, React frontend, and WhatsApp Bridge) in Docker Compose or Local Dev mode.
---

# Deploy Pipeline Skill

This skill teaches the agent how to deploy and manage the full AI Pulse stack (FastAPI backend, React + Vite dashboard, Node.js WhatsApp bridge). It covers environment safety, port conflict resolution, Docker Compose orchestration, container teardown, and portability across fresh environments.

---

## ✅ Pre-Flight Checklist (Run Every Time)

### 1. Verify Workspace Root
Ensure the following exist in the workspace root:
- `agent-pipeline/` directory
- `docker-compose.yml`
- `Dockerfile.backend`, `Dockerfile.frontend`, `Dockerfile.whatsapp`
- `deploy.ps1` (Windows) or `deploy.sh` (Unix)

### 2. Verify `.env` File
Check the root `.env` file exists and is populated:
- **`GEMINI_API_KEY`** — must NOT be `gemini_api_key_from_ai_studio` or empty → alert the user immediately if so
- **`GITHUB_PERSONAL_ACCESS_TOKEN`** — required for newsletter publishing
- **`REPO_PATH`** — only used in local-mode error messages; not required in Docker mode
- Other values (`GITHUB_OWNER`, `GITHUB_REPO`, `GMAIL_*`) — optional features

If `.env` does not exist, copy from `.env.example`:
```powershell
# Windows
Copy-Item .env.example .env
```
```bash
# Unix
cp .env.example .env
```

---

## 🚀 Bring Up: Docker Compose (Recommended)

```bash
docker-compose up -d --build
```

Docker will:
1. Build images for all three services (uses cache for unchanged layers — fast on reruns)
2. Start containers: `ai_backend` (`:8000`), `ai_frontend` (`:5173`), `whatsapp_bridge`
3. Mount the named volume `whatsapp_auth → /app/auth_info_baileys` to persist WhatsApp session

**Verify containers are running:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## 📱 WhatsApp Authentication Check

**Always check auth status via logs — do NOT blindly attach:**
```bash
docker logs whatsapp_bridge --tail 30
```

**Interpret the output:**

| Log pattern | Meaning | Action needed |
|---|---|---|
| `"msg":"resyncing regular"` / `"msg":"identity changed"` / Baileys JSON lines | ✅ Already authenticated, session restored from volume | Nothing — skip QR |
| Large ASCII `█ ▄` block or `Connecting...` with no Baileys activity | ⚠️ QR scan required | Run `docker attach` below |

**Only if QR scan IS needed:**

> ⚠️ **Antigravity IDE conflict**: `Ctrl+P` and `Ctrl+Q` are captured by the Antigravity IDE and **cannot** be used to detach from `docker attach` inside the IDE's integrated terminal. Use one of the two solutions below.

**Solution 1 (Recommended) — Custom detach key via `--detach-keys`:**
```bash
docker attach --detach-keys="ctrl-x" whatsapp_bridge
```
Scan the QR code: WhatsApp mobile → Linked Devices → Link a Device.
To detach after scanning, press **`Ctrl+X`** — this key is not bound by Antigravity and safely exits `docker attach` without killing the container.

**Solution 2 — Use an external terminal:**
Open **Windows Terminal**, **PowerShell**, or **Command Prompt** (outside Antigravity) and run:
```bash
docker attach whatsapp_bridge
```
Scan the QR code, then use `Ctrl+P, Ctrl+Q` in the external terminal where those keys are not intercepted.

> ❌ Never press `Ctrl+C` inside `docker attach` — it sends SIGINT and kills the Node.js bridge process. The container will restart (due to `restart: unless-stopped`) but causes a brief outage.

---

## 🦙 Local Gemma (Ollama) Verification

If you choose to run local models (e.g. `gemma` or `gemma3`) instead of Gemini cloud, ensure Ollama is running on the host machine. The backend container communicates with the host machine's Ollama instance via `OLLAMA_BASE_URL=http://host.docker.internal:11434`.

### Verification Steps

1. **Prompted at deploy time**: The `deploy.ps1` and `deploy.sh` scripts will automatically prompt you:
   ```
   Would you like to verify/start local Gemma via Ollama? (y/n)
   ```
2. **If approved, the script will**:
   - Check if the `ollama` command is available in the host PATH.
   - Verify if Ollama is listening on port `11434`. If not, it will ask to start it in the background (`ollama serve`).
   - Check if the `gemma` model is pulled and available locally. If not, it will prompt to pull it (`ollama pull gemma`).

3. **Manual Check command**:
   ```bash
   ollama list
   ```
   Expected output contains `gemma` or `gemma3`.

4. **Verify container communication**:
   Ensure `docker-compose.yml` has the environment variable `OLLAMA_BASE_URL` set to `http://host.docker.internal:11434` and `extra_hosts` mapped for DNS resolution:
   ```yaml
   backend:
     environment:
       - OLLAMA_BASE_URL=http://host.docker.internal:11434
     extra_hosts:
       - "host.docker.internal:host-gateway"
   ```

---

## 🛑 Bring Down: Stopping Containers

Choose based on whether you need to preserve the WhatsApp session:

### Stop containers, preserve WhatsApp session (recommended)
```bash
docker-compose down
```
- Stops and removes containers
- **Named volume `whatsapp_auth` is kept** → no QR re-scan needed on next `up`

### Stop containers AND wipe WhatsApp session (forces re-auth on next start)
```bash
docker-compose down -v
```
- Stops and removes containers
- **Deletes all named volumes including `whatsapp_auth`** → QR re-scan required next time

### Stop without removing containers (fastest resume)
```bash
docker-compose stop
```
- Suspends containers but keeps them; `docker-compose start` resumes instantly

### Summary table

| Command | Containers | WhatsApp session volume | Next start |
|---|---|---|---|
| `docker-compose stop` | Suspended | ✅ Kept | `docker-compose start` (instant) |
| `docker-compose down` | Removed | ✅ Kept | `docker-compose up -d` (fast) |
| `docker-compose down -v` | Removed | ❌ Deleted | `docker-compose up -d` + QR scan |

---

## ♻️ What Happens on Rerun (`docker-compose up -d --build`)

| Scenario | Docker behaviour | WhatsApp session |
|---|---|---|
| Code **unchanged** (fully cached) | Containers left untouched | ✅ Safe |
| Code **changed** → image rebuilt → container recreated | Old container replaced with new | ✅ Safe (volume persists) |
| `docker-compose down -v` was run first | Volumes destroyed | ❌ QR re-scan needed |

---

## 🌍 Portability: Does This Work in Any Fresh Environment?

**Yes — with the following requirements:**

### Hard requirements (stack will not work without these)
| Requirement | Notes |
|---|---|
| **Docker + Docker Compose installed** | `docker --version` and `docker compose version` must succeed |
| **`.env` populated with `GEMINI_API_KEY`** | The LLM writer node will fail without it |
| **All files cloned from the repo** | `docker-compose.yml`, all 3 Dockerfiles, and `agent-pipeline/` must be present |

### Soft requirements (specific features only)
| Requirement | Feature gated |
|---|---|
| `GITHUB_PERSONAL_ACCESS_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` | Newsletter publish to GitHub Pages |
| `GMAIL_USER`, `GMAIL_APP_PASSWORD` | Email delivery to subscribers |

### What is NOT required in Docker mode
- **`REPO_PATH`** — only used in local-mode error messages (the `whatsapp.py` MCP client uses it to print a helpful `cd <path>` hint). In Docker mode, the bridge URL is set via `WHATSAPP_BRIDGE_URL=http://whatsapp:3002` inside `docker-compose.yml`, so `REPO_PATH` is irrelevant.
- **Node.js, Python, npm** installed locally — Docker provides its own runtimes inside containers.
- **Any prior QR scan** — as long as `docker-compose down` (not `-v`) was used, the `whatsapp_auth` volume persists the session across machines only if the volume is explicitly exported/imported. On a **brand new machine**, a QR scan is always required once.

### Steps for a fresh environment
```bash
# 1. Clone the repo
git clone <repo-url>
cd podcasts

# 2. Populate .env
cp .env.example .env
# Edit .env — fill in GEMINI_API_KEY and GitHub tokens

# 3. Deploy
docker-compose up -d --build

# 4. Check WhatsApp auth (expect QR needed on first run)
docker logs whatsapp_bridge --tail 30

# If QR needed — use --detach-keys to avoid IDE key binding conflict:
docker attach --detach-keys="ctrl-x" whatsapp_bridge
# Scan QR → then press Ctrl+X to safely detach (works inside Antigravity IDE)
```

---

## 🚀 Local Native Mode (Windows PowerShell)

For active development — runs services directly on the host:
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```
Spawns three labeled Command Prompt windows: `WhatsApp Bridge (3002)`, `FastAPI Backend (8000)`, `React Dashboard (5173)`.

**Stop local processes:**
```powershell
Get-NetTCPConnection -LocalPort 8000, 5173, 3002 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
```

---

## 🔍 Troubleshooting

### Check ports are bound
```powershell
# Windows
Get-NetTCPConnection -LocalPort 8000, 5173, 3002 -ErrorAction SilentlyContinue
```
```bash
# Unix
lsof -i :8000,5173,3002
```

### Check container logs
```bash
docker logs ai_backend --tail 50
docker logs ai_frontend --tail 50
docker logs whatsapp_bridge --tail 50
```

### Backend health check
```bash
curl http://localhost:8000/health
```

### Frontend reachable
Open http://localhost:5173 in a browser.
