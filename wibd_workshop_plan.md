# Workshop Plan: Agentic AI 101 — Build Your Automated Newsletter & Research Agent Pipeline

**Total Duration**: 2 Hours (1 Hour Conceptual & 1 Hour Hands-on)
**Target Audience**: Students, Developers, Tech Enthusiasts (Beginner/Intermediate)
**Theme**: Building a fully autonomous LangGraph-powered Agent Pipeline that reads your WhatsApp notes, researches links via real MCP tools, writes a newsletter with Gemini or local Gemma, and publishes it to GitHub Pages on a schedule.

> **No mocks. No simulations. Every agent step calls a real tool.**

---

## 🎯 The Business Problem: "AI Pulse Weekly"

> **Scenario**: You are a busy developer who saves interesting AI & tech articles, YouTube talks, and links to your own WhatsApp every week — but never has time to read them. Your team also wants a weekly digest. Today you build an **autonomous agent** that does it all for you — reading, researching, writing, and publishing — on a schedule, while you sleep.

### What Gets Built (End-to-End)

| Layer | What It Is | Tech |
|---|---|---|
| 🖥️ **Dashboard UI** | Control the pipeline, watch live agent progress, approve the newsletter | React + Vite (`:5173`) |
| ⚙️ **Agent Backend** | LangGraph StateGraph chaining real MCP tools, two HITL guardrail gates | Python FastAPI + LangGraph (`:8000`) |
| 📱 **WhatsApp Bridge** | Local Node.js server that authenticates with your WhatsApp and exposes an HTTP API | Node.js + Baileys (`:3002`) |
| 🌐 **Published Output** | A GitHub Pages newsletter site + real Gmail delivery | GitHub REST API + smtplib |

### The Autonomous Pipeline Flow

```
⏰ Cron Trigger (APScheduler)
      │
      ▼
💬 WhatsApp Bridge ──► Fetch self-messages with links (last N days)
      │
      ▼ [GUARDRAIL #1 — Link Review UI]
🔗 Human selects which links to research
      │
      ▼
🔍 Research Agent
      ├─ YouTube URL  → YouTube Transcript MCP
      └─ Other URLs   → Fetch MCP (universal web reader)
      │
      ▼
✍️  Writer Agent ──► Gemini 2.5 Flash (cloud) or local Gemma via Ollama
      │
      ▼ [GUARDRAIL #2 — Human Approval UI]
👤 Human reviews the newsletter and approves/rejects
      │
      ▼
🚀 Publish ──► GitHub Pages (REST API) + Gmail (smtplib)
```

---

## 🗂️ Repository Structure

```
podcasts/
├── GEMINI.md                          ← AI context & guardrails for Gemini CLI
├── wibd_workshop_plan.md              ← This file
├── .agents/
│   └── skills/
│       └── infographic_generator/
│           └── SKILL.md              ← Gemini CLI skill for Mermaid infographics
└── agent-pipeline/
    ├── frontend/                      ← React + Vite dashboard
    │   ├── src/
    │   │   ├── App.jsx
    │   │   └── App.css
    │   ├── index.html
    │   └── package.json
    ├── python-backend/                ← FastAPI + LangGraph pipeline
    │   ├── main.py                    ← API entry point (REST + SSE)
    │   ├── state.py                   ← Shared in-memory state & SSE emitter
    │   ├── requirements.txt
    │   ├── .env.example               ← Copy to .env and fill in secrets
    │   ├── pipeline/
    │   │   ├── graph.py               ← LangGraph StateGraph definition
    │   │   ├── runner.py              ← Async graph invoker
    │   │   ├── nodes/
    │   │   │   ├── fetch_notes.py     ← Calls WhatsApp bridge
    │   │   │   ├── link_review.py     ← HITL gate #1 (link selection)
    │   │   │   ├── research.py        ← Routes links to YouTube/Fetch MCP
    │   │   │   ├── write.py           ← Calls Gemini or Ollama/Gemma
    │   │   │   ├── review.py          ← HITL gate #2 (publish approval)
    │   │   │   ├── publish.py         ← GitHub Pages REST + Gmail smtplib
    │   │   │   └── rejected.py
    │   │   ├── mcps/
    │   │   │   ├── whatsapp.py        ← HTTP client for the Baileys bridge
    │   │   │   ├── youtube.py         ← Spawns YouTube Transcript MCP process
    │   │   │   └── fetch.py           ← Spawns Fetch MCP process
    │   │   └── guardrails/
    │   │       └── pii_guard.py       ← Topic/PII pre-prompt check
    │   └── scheduler/
    │       └── cron.py                ← APScheduler wrapper
    └── whatsapp-bridge-js/            ← Baileys-based WhatsApp HTTP bridge
        ├── bridge.js
        └── package.json
```

---

## 🔌 MCP Tools Used

| MCP Tool | Purpose | Install |
|---|---|---|
| **YouTube Transcript MCP** | Fetch full transcripts from YouTube videos without API keys | `npx -y @kimtaeyoon83/mcp-server-youtube-transcript` |
| **Fetch MCP** | Fetch and convert any public URL to clean Markdown text | `uvx mcp-server-fetch` |

These MCPs are invoked as **child subprocesses** over stdio using the MCP JSON-RPC protocol — no separate server to keep running. The Python backend spawns them on demand per-link during the Research step.

---

## ✅ Prerequisites (Complete Before the Workshop)

### 1. Accounts & Services
- **GitHub Account** — for publishing the newsletter to GitHub Pages
- **Google AI Studio Account** — for your `GEMINI_API_KEY` at [aistudio.google.com](https://aistudio.google.com)
- **Gmail Account** — for the subscriber email dispatch (requires an App Password)

### 2. Software (Install Locally)
| Tool | Version | Install |
|---|---|---|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Node.js & npm** | 18+ | [nodejs.org](https://nodejs.org) |
| **Git** | any | [git-scm.com](https://git-scm.com) |
| **VS Code** | any | [code.visualstudio.com](https://code.visualstudio.com) |
| **Gemini CLI** | latest | `npm install -g @google/gemini-cli` |
| **Ollama** *(optional, for local Gemma)* | latest | [ollama.com](https://ollama.com) |
| **uv / uvx** *(for Fetch MCP)* | latest | `pip install uv` |

### 3. API Keys & Tokens to Prepare
- `GEMINI_API_KEY` — from [aistudio.google.com](https://aistudio.google.com)
- `GITHUB_PERSONAL_ACCESS_TOKEN` — Fine-grained PAT with **Contents: Read & Write** permission on your newsletter repo
- `GITHUB_OWNER` — Your GitHub username
- `GITHUB_REPO` — A new empty repo called `ai-pulse-newsletter` (create it beforehand)
- `GMAIL_USER` — Your Gmail address
- `GMAIL_APP_PASSWORD` — A [Gmail App Password](https://myaccount.google.com/apppasswords) (not your login password)

---

## 🚀 Setup Guide — Step by Step

### Step 1: Clone the Repository
```bash
git clone <repository_url>
cd podcasts
```

---

### Alternative: Docker Setup 🐳
If you prefer not to install Node.js and Python locally, you can run the entire stack using Docker:

1. Copy `.env.example` to `.env` in the root folder and fill in your keys.
2. Build and start the containers in the background:
   ```bash
   docker-compose up -d --build
   ```
3. The WhatsApp bridge needs you to scan a QR code. Attach to it:
   ```bash
   docker attach whatsapp_bridge
   # Scan the QR code with your phone.
   # Then press Ctrl+P, Ctrl+Q to detach and leave it running.
   ```
4. Access the dashboard at `http://localhost:5173`. You can skip directly to **Step 6**.

---

### Step 2: WhatsApp Bridge Setup
The bridge authenticates with WhatsApp using a QR code on first run and saves the session permanently.

```bash
cd agent-pipeline/whatsapp-bridge-js
npm install
node bridge.js
```

On first run, a QR code appears in the terminal. Open WhatsApp on your phone → **Linked Devices** → **Link a Device** → Scan the QR. Once you see `✅ WhatsApp connected!`, the bridge is ready on `http://localhost:3002`.

**Verify the bridge is working:**
```bash
# Should return { "status": "ok", "connected": true }
curl http://localhost:3002/health

# Should return your recent self-messages (send a link to yourself first)
curl "http://localhost:3002/messages?days=7"
```

> **Do you need to keep it running all the time?**
> Yes — if you use the Cron scheduler for automated runs. The bridge only stores messages received *while it is running* (live cache, not historical). For manual one-off runs, you can start it just before running the pipeline.

> **Tip**: Send a tech link to yourself on WhatsApp *before* running the pipeline so there are messages to fetch.

### Step 3: Python Backend Setup

```bash
cd agent-pipeline/python-backend

# Create and activate a virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install all dependencies (use python -m pip on Windows if pip.exe is blocked)
python -m pip install -r requirements.txt
```

**Configure your environment variables:**
```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in your values:
```ini
GEMINI_API_KEY=your-gemini-api-key

GITHUB_OWNER=your-github-username
GITHUB_REPO=ai-pulse-newsletter
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...

GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

**Start the backend:**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Verify with:
```bash
curl http://localhost:8000/health
```

### Step 4: Frontend Dashboard Setup

```bash
cd agent-pipeline/frontend
npm install
npm run dev
```

Open your browser at **http://localhost:5173**. You should see the AI Pulse dashboard with the pipeline config, live event log, and newsletter preview panels.

### Step 5: (Optional) Local Gemma via Ollama

```bash
# Pull and run the Gemma model locally
ollama run gemma
```

Once running, select **🦙 Local Gemma (Ollama)** in the dashboard's Writer Agent Model dropdown. The backend connects to Ollama at `http://localhost:11434` automatically — no additional configuration needed.

**How to verify Gemma is being used:** Watch your terminal where `ollama run gemma` is running. When the Write Agent step executes, you will see Ollama printing tokens in real time and your CPU/GPU usage will spike.

### Step 6: Create the GitHub Pages Repository

1. Go to GitHub and create a new **public** repository named `ai-pulse-newsletter`.
2. Go to **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main` → Folder: `/ (root)`.
3. The pipeline will auto-create `index.html` and `newsletters/` on first publish.

---

## 🧭 Running the Full Pipeline

1. Open **Terminal 1** → start the WhatsApp bridge: `node bridge.js`
2. Open **Terminal 2** → start the Python backend: `uvicorn main:app --reload`
3. Open **Terminal 3** → start the React dashboard: `npm run dev`
4. Send a few tech article links to **yourself** on WhatsApp.
5. Open `http://localhost:5173`, configure the topic and click **▶ Run**.
6. Watch the live event log as each agent step executes.
7. **HITL Gate #1** — Review and select which extracted links to research.
8. **HITL Gate #2** — Review the generated newsletter and **Approve & Publish** or **Reject**.
9. On approval, the newsletter is published to GitHub Pages and emailed to subscribers.

---

## 💡 Hour 1 — Gemini CLI & Antigravity Capabilities (Hands-On)

This hour is fully interactive. Every participant runs each command in their own terminal. Each block introduces one core capability of Antigravity-driven development.

---

### 1. Setup & Orientation
```bash
# Install the Gemini CLI globally
npm install -g @google/gemini-cli

# Set your API key
# Windows:
$env:GEMINI_API_KEY="your-gemini-api-key"
# Mac/Linux:
export GEMINI_API_KEY="your-gemini-api-key"

# Enter interactive agent mode (reads GEMINI.md automatically for project context)
gemini
```

> **What is GEMINI.md?** Place a `GEMINI.md` file in the root of your project. The CLI ingests it automatically on every run — defining the agent's role, guardrails, available tools, and domain restrictions. This is your project's AI constitution.

---

### 2. Agent vs Subagent vs Agent Manager

**Concept:** An *Agent* is a top-level orchestrator that plans and delegates. A *Subagent* is a specialised child process spun up for a single bounded task (e.g., visual web browsing, code execution). The *Agent Manager* in Antigravity coordinates lifecycle, routing, and context boundaries between them.

```bash
# Top-level agent — general orchestration
gemini -p "Analyse the files in this project and give me a summary of the architecture"

# Spawn a browser subagent for live visual web routing
# (The main agent's context is NOT polluted by the browser session)
gemini -p "Launch the browser_subagent, navigate to https://news.ycombinator.com and summarise the top 3 AI posts"

# Inspect what the agent planned vs what it executed
gemini --debug -p "Fetch the top GitHub trending repos today"
```

---

### 3. Tools

**Concept:** Tools are granular, single-function execution modules the agent can call. Antigravity ships with built-in tools (web_search, web_fetch, read_file, run_shell) and you can extend with custom MCP tools.

```bash
# Use built-in tools directly
gemini "Use the web_search and web_fetch tools to summarise the top AI news today"

# List all available tools the agent knows about
gemini mcp list

# HITL tool approval mode — agent must ask permission before calling any tool
gemini --approval-mode default
# Try: gemini --approval-mode default "Search the web for LangGraph tutorials"
# → The agent will pause and ask: [GUARDRAIL] Do you approve running web_search?

# Debug mode — see every raw tool call and response
gemini --debug -p "Read the requirements.txt in agent-pipeline/python-backend and explain the dependencies"
```

---

### 4. MCP (Model Context Protocol)

**Concept:** MCPs extend the agent with domain-specific tools that run as external processes over a standardised JSON-RPC protocol. No custom API wrappers needed.

```bash
# Check which MCP servers are configured
gemini mcp list

# Invoke the YouTube Transcript MCP directly from the CLI
# (The agent will spawn npx @kimtaeyoon83/mcp-server-youtube-transcript as a subprocess)
gemini "Use the YouTube transcript MCP to get the transcript of https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Invoke the Fetch MCP to read any public web page as clean Markdown
gemini "Use the fetch MCP to get the content of https://langchain-ai.github.io/langgraph/ and summarise it"
```

> **How MCPs work in our pipeline:** `pipeline/mcps/youtube.py` and `pipeline/mcps/fetch.py` spawn these exact same MCP tools as child processes using MCP's JSON-RPC stdio protocol — the same mechanism the CLI uses.

---

### 5. Skills (Infographic Generator)

**Concept:** Skills are prompt-driven instruction templates defined in `.md` files under `.agents/skills/`. They give the agent a deterministic, reusable workflow to follow for specific tasks.

```bash
# View the infographic skill definition
cat .agents/skills/infographic_generator/SKILL.md

# Execute the skill from the CLI — generates Mermaid.js diagram output
gemini "Execute the infographic_generator skill on this summary:
LangGraph is a stateful graph framework for building multi-agent pipelines.
It supports conditional edges, HITL interrupts, and streaming.
Key nodes: fetch_notes, research, write, review, publish."

# The skill outputs Mermaid syntax — paste into https://mermaid.live to visualise
```

---

### 6. Hooks

**Concept:** Hooks intercept agent actions at specific lifecycle points — before generation, after tool call, before file write. They enable automatic PII stripping, audit logging, and policy enforcement *without modifying agent prompts*.

```bash
# Demo: Hooks defined in .gemini/settings.json
cat .gemini/settings.json

# Example hook concept — a pre-generation hook strips PII before the LLM sees the prompt:
# { "hooks": { "pre-generation": "node hooks/strip-pii.js" } }

# Try triggering the domain guardrail hook (defined in GEMINI.md):
gemini -p "Tell me about today's stock market prices"
# → Output: REJECTED_TOPIC (domain restriction: not Technology/AI/Productivity)
```

---

### 7. Sandbox & Sandboxing Workarounds

**Concept:** Sandboxing limits what the agent can do to your OS — it blocks destructive shell commands. Demonstrated live with the `--sandbox` flag.

```bash
# Show the sandbox blocking a destructive command
gemini "delete all files in the current directory" --sandbox
# → The CLI blocks the rm/del command and explains the restriction

# Docker sandbox — ultimate isolation — run agent in ephemeral container
docker run -it -v $(pwd):/workspace google/gemini-cli \
  "analyse the Python backend code and suggest one improvement" --sandbox

# Pipe large data into the agent safely without touching the filesystem
cat agent-pipeline/python-backend/pipeline/nodes/write.py | \
  gemini -p "Review this code for bugs and suggest improvements"
```

---

### 8. Git Worktrees — Safe Experimental Branches

**Concept:** The `-w` flag creates a Git Worktree — a fully isolated copy of your repo in a new branch. The agent experiments there without touching `main`. You can review, merge, or discard entirely.

```bash
# Create a worktree branch and run a refactoring task safely
gemini -p "Add input validation to the fetch_notes node" -w "feature/input-validation"

# List worktrees created by the agent
git worktree list

# Review changes before merging
git diff main feature/input-validation

# Discard if not happy
git worktree remove feature/input-validation
```

---

### 9. Session Isolation, History & Resume

**Concept:** Each Gemini CLI session has a unique thread ID. Sessions can be listed and resumed — the agent remembers context, tool results, and decisions from where it left off.

```bash
# List all past sessions
gemini --list-sessions

# Resume a specific session by ID
gemini -r <session-id>

# Context files — GEMINI.md must be in the workspace root
# to be automatically loaded into every new and resumed session
ls GEMINI.md

# Checkpointing — auto Git snapshot before any AI write
# Enable in ~/.gemini/settings.json:
# { "checkpointing": { "enabled": true } }
# Then restore if the agent made a mistake:
# /restore   (inside interactive shell)

# Token caching stats — see cost savings on repeated large-file reads
gemini --debug -p "read all files in the pipeline/nodes folder and summarise each one"
# → Look for context caching metrics in the debug output
```

---


## 🛡️ Guardrails & Safety (Implemented in the Pipeline)

### HITL Gate #1 — Link Selection (before Research)
After WhatsApp messages are fetched, the pipeline **pauses** and presents all extracted links in the dashboard. You check/uncheck which links the Research Agent should process before it runs.

### HITL Gate #2 — Publish Approval (before GitHub + Gmail)
After the newsletter is generated, the pipeline **pauses** and displays it in the dashboard preview panel. You must click **✅ Approve & Publish** to proceed. Clicking **❌ Reject** terminates the run without publishing.

### Input Guardrail — Domain Policy
Defined in `pipeline/guardrails/pii_guard.py`. If the research topic is outside Technology, AI, or Productivity domains (e.g., personal gossip, financial info), the pipeline immediately halts and emits `REJECTED_TOPIC`.

### Auto-Cancel on Zero Links
If WhatsApp messages are fetched but contain zero links, the pipeline auto-cancels with a clear error message rather than running empty research steps.

### Manual Cancel
The **Stop** button in the dashboard immediately cancels the pipeline (even mid-HITL wait) by setting a `cancelled` flag that all polling loops check.

---

## 🏗️ Architecture Deep Dive

### LangGraph StateGraph
The pipeline is a stateful `StateGraph` — not a linear script. Each node is a Python function that receives the full state dict and returns updates to it. The graph is compiled once on startup and reused across runs.

```
fetch_notes → link_review → research → write → review → publish
                                                       ↘ rejected (on rejection/cancel)
```

### Server-Sent Events (SSE)
Real-time log streaming from Python backend to React frontend uses SSE (`/api/pipeline/events/{run_id}`). The backend emits typed events (`step`, `mcp_call`, `newsletter_ready`, `complete`, `error`) which the dashboard renders live without polling.

### HITL Polling Pattern
HITL nodes run **synchronously in a thread pool** (via `run_in_executor`). They poll `pipeline_states[run_id]` every 500ms while waiting for the user action on the frontend. The async FastAPI event loop is never blocked.

### Why MCPs over Headless Browsers?
| | MCP Tools | Headless Browser |
|---|---|---|
| **Speed** | Milliseconds (API call) | Seconds (full DOM render) |
| **Stability** | Versioned APIs | CSS selectors break weekly |
| **Bot Detection** | Not triggered | CAPTCHAs immediately |
| **Security** | Strict tool whitelist | Full web access risk |

---

## 🔧 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `WhatsApp bridge is not running` | Bridge process stopped | `cd whatsapp-bridge-js && node bridge.js` |
| `WhatsApp bridge not yet connected` | QR not scanned yet | Check bridge terminal, scan the QR |
| `Zero links obtained. Pipeline automatically cancelled.` | No links in your WhatsApp self-messages | Send a tech article link to yourself on WhatsApp first |
| `GEMINI_API_KEY not set` | Missing env var | Check your `.env` file |
| `404 Not Found` on Gemini model | Using a deprecated model name | Ensure `gemini-2.5-flash` in `write.py` |
| `No GITHUB_PERSONAL_ACCESS_TOKEN` | Missing env var | Add PAT to `.env` |
| `403 Forbidden` on GitHub | PAT missing Contents: Write permission | Edit your PAT on GitHub → Permissions → Contents → Read & Write |
| `//` in GitHub API URL | `GITHUB_OWNER` is empty in `.env` | Set `GITHUB_OWNER=your-github-username` |
| `uvicorn not recognized` | Running outside the virtual environment | Run `.\venv\Scripts\activate` first |
| `pip.exe blocked` by policy | Windows Application Control | Use `python -m pip install ...` instead |
| Gemma not responding | Ollama not running | Run `ollama run gemma` in a separate terminal |

---

## 🕒 Workshop Agenda (2 Hours)

---

### ⏱️ Hour 1 — Antigravity & Gemini CLI Capabilities (Hands-On)

> **Goal**: Every attendee leaves with a comprehensive, practical understanding of agent-driven development using Antigravity. Each capability is demonstrated with a live command.

| Time | Capability | What Happens |
|---|---|---|
| **0:00 – 0:05** | **Intro & Setup** | Install Gemini CLI, set `GEMINI_API_KEY`, open the project, run `gemini` for the first time |
| **0:05 – 0:12** | **GEMINI.md & Project Context** | Show how `GEMINI.md` auto-loads into every session as the AI constitution. Edit it live and see the agent's behaviour change |
| **0:12 – 0:20** | **Agent / Subagent / Agent Manager** | Run the top-level orchestrator vs a browser subagent. Show how context is isolated between parent and child agents |
| **0:20 – 0:27** | **Tools & HITL Approval Mode** | Demo `web_search` + `web_fetch` tools. Enable `--approval-mode default` and watch the agent pause for permission before every tool call |
| **0:27 – 0:35** | **MCP (Model Context Protocol)** | `gemini mcp list`. Invoke the YouTube Transcript MCP and Fetch MCP directly from the CLI. Explain how they map to the pipeline's `mcps/` modules |
| **0:35 – 0:43** | **Skills — Infographic Generator** | Read the skill definition. Execute the `infographic_generator` skill on a live summary. Render the Mermaid output at mermaid.live |
| **0:43 – 0:49** | **Hooks & Guardrails** | Show how hooks intercept pre-generation. Trigger `REJECTED_TOPIC` by asking about stocks. Show the domain guardrail in `GEMINI.md` |
| **0:49 – 0:55** | **Sandbox & Worktrees** | Run `--sandbox` blocking a destructive command. Use `-w` to create a worktree branch for a safe experimental change |
| **0:55 – 1:00** | **Sessions, Checkpointing & Token Caching** | `--list-sessions`, `-r <id>` to resume. Enable checkpointing in settings. Show debug token caching metrics |

---

### ⏱️ Hour 2 — Run the Pipeline & Develop Using Antigravity (Hands-On)

> **Goal**: Attendees set up all three services, run the real end-to-end pipeline, then pick a feature or bug fix and use the Antigravity capabilities from Hour 1 to implement it — the agent writes and explains the code, the human reviews and approves.

#### Part A — Get Everything Running (20 min)

| Time | Activity |
|---|---|
| **1:00 – 1:05** | Start the **WhatsApp bridge** (`node bridge.js`), scan QR, verify `curl http://localhost:3002/health` |
| **1:05 – 1:08** | Activate venv, start **Python backend** (`uvicorn main:app --reload`), verify `/health` |
| **1:08 – 1:10** | Start **React dashboard** (`npm run dev`), open `http://localhost:5173` |
| **1:10 – 1:20** | Send a YouTube link + a tech article to yourself on WhatsApp. Click **▶ Run** and watch live SSE events stream in real time |

#### Part B — Experience the Full Pipeline (20 min)

| Time | Activity |
|---|---|
| **1:20 – 1:27** | **HITL Gate #1** — Link Review panel appears. Select/deselect links. Confirm and watch the Research Agent call YouTube Transcript MCP + Fetch MCP |
| **1:27 – 1:35** | **Writer Agent** — Newsletter is generated by Gemini 2.5 Flash. Preview in the right panel |
| **1:35 – 1:42** | **HITL Gate #2** — Approve & Publish. Watch the pipeline push to GitHub Pages and send a real email to subscribers |
| **1:42 – 1:45** | Open the live GitHub Pages URL. Verify `index.html` updated with the new newsletter link |

#### Part C — Develop a Feature Using Antigravity (15 min)

> Each attendee picks one item from the list below and uses the Gemini CLI — with the capabilities learned in Hour 1 — to implement it. The agent reads the existing code, proposes a change in an isolated worktree, and the attendee reviews and merges.

**Suggested tasks (pick one):**
- 🔧 Add a new newsletter section (e.g., "💬 Community Quote of the Week") to the Writer Agent's system prompt in `write.py`
- 🔧 Add a new input guardrail — block links from specific domains (e.g., social media) in `link_review.py`
- 🔧 Extend `index.html` generation to include a publication timestamp alongside the newsletter link
- 🔧 Add a `GET /api/pipeline/runs` endpoint to `main.py` that lists all run IDs and their statuses
- 🔧 Improve the email body in `publish.py` to send HTML-formatted content instead of plain text

```bash
# Example: Use Antigravity in a safe worktree to add the feature
gemini -w "feature/my-change" -p "Read pipeline/nodes/write.py and add a new 'Community Quote' 
section to the SYSTEM_PROMPT. Show me the diff before applying."

# Review, then merge
git diff main feature/my-change
git merge feature/my-change
```

#### Part D — Wrap-Up (5 min)

| Time | Activity |
|---|---|
| **1:55 – 2:00** | Recap: what did each Antigravity capability contribute to the build? Which ones would you use day-to-day? Q&A |

---

## 🌐 Key URLs & References

| Resource | Link |
|---|---|
| Google AI Studio (API Key) | https://aistudio.google.com |
| Gemini CLI Docs | https://github.com/google-gemini/gemini-cli |
| LangGraph Docs | https://langchain-ai.github.io/langgraph/ |
| YouTube Transcript MCP | https://github.com/kimtaeyoon83/mcp-server-youtube-transcript |
| Fetch MCP | https://github.com/modelcontextprotocol/servers/tree/main/src/fetch |
| Baileys (WhatsApp Bridge) | https://github.com/WhiskeySockets/Baileys |
| Ollama (Local LLMs) | https://ollama.com |
| Mermaid Live Editor | https://mermaid.live |
| GitHub Fine-grained PATs | https://github.com/settings/tokens?type=beta |
| Gmail App Passwords | https://myaccount.google.com/apppasswords |
