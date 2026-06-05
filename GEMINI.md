# Agentic AI 101: Project Context & AI Instructions (GEMINI.md)

This file (`GEMINI.md`) provides persistent background context and instructions for the Gemini CLI and any related Agentic AI systems operating in this workspace.

## Project Context
- **Workshop Name:** Agentic AI 101 — Build Your Automated Newsletter & Research Agent Pipeline
- **Goal:** Develop an autonomous LangGraph-powered Agent Pipeline that reads personal notes (via WhatsApp MCP), researches content (via YouTube Transcript MCP and Fetch MCP), constructs a newsletter using Gemini 2.5 Flash or local Gemma via Ollama, and publishes it to GitHub Pages via the GitHub MCP/REST API on a cron schedule.
- **Stack:** Python FastAPI + LangGraph (backend · `:8000`) · React + Vite (dashboard · `:5173`) · Node.js Baileys bridge (WhatsApp · `:3002`)

## AI Operating Rules & Guardrails
1. **Safety First (Sandboxing):** Never execute destructive OS commands (like deleting user files). Always respect sandboxing constraints and workspace boundaries.
2. **Human-in-the-Loop (HITL):** For high-stakes tools like `publish_node` (GitHub Pages push) or `send_email` (Gmail smtplib), always pause execution and ask the human for approval: `[GUARDRAIL] Do you approve? (Y/N)`. This is enforced in `pipeline/nodes/review.py`.
3. **Domain Restriction:** Act as a Tech Researcher. Only process data related to Technology, AI, and Productivity. If user data contains personal gossip or financial info, immediately halt the chain and output `REJECTED_TOPIC`. Enforced in `pipeline/guardrails/pii_guard.py`.

## Available Resources & Skills
- **Skills:**
  - `infographic_generator` (located at `.agents/skills/infographic_generator/SKILL.md`) — generates Mermaid.js structural infographics from content summaries.
  - `deploy_pipeline` (located at `.agents/skills/deploy_pipeline/SKILL.md`) — automates system verification and launches the full stack (FastAPI backend, React dashboard, WhatsApp Bridge) via Docker Compose or native shells.
- **MCP Integrations:**
  - `WhatsApp Bridge` — Baileys-based Node.js HTTP bridge at `http://localhost:3002` (QR auth once)
  - `YouTube Transcript MCP` — `npx -y @kimtaeyoon83/mcp-server-youtube-transcript` (no auth)
  - `Fetch MCP` — `uvx mcp-server-fetch` (reads any public URL as Markdown, no auth)
  - `LinkedIn MCP` — Subprocess wrapper calling `mcp-server-fetch` with `--ignore-robots-txt` to fetch LinkedIn posts
  - `Deepwiki MCP` — Connects to DeepWiki HTTP+SSE legacy server at `https://mcp.deepwiki.com/mcp` for repository summaries
  - `GitHub MCP` — `https://api.githubcopilot.com/mcp/` (OAuth via VS Code, no PAT needed inside Antigravity)
- **Advanced Tools:** Use the `browser_subagent` for live web visual routing when necessary. Use `--approval-mode default` to enforce HITL before any tool execution.

## Pipeline Flow (LangGraph StateGraph)
```
fetch_notes → link_review [HITL #1] → research → write → review [HITL #2] → publish / rejected
```
- `fetch_notes` — calls WhatsApp bridge, applies domain guardrail
- `link_review` — pauses for human link selection; auto-cancels if 0 links found
- `research` — routes YouTube URLs to YouTube Transcript MCP, LinkedIn URLs to LinkedIn MCP, GitHub repository URLs to Deepwiki MCP, and all others to Fetch MCP
- `write` — calls Gemini 2.5 Flash (cloud) or Gemma (Ollama local)
- `review` — pauses for human approval; can be manually cancelled via Stop button
- `publish` — pushes newsletter to GitHub Pages via REST API; sends real email via smtplib; updates `index.html`

## Development Status
- ✅ Python FastAPI backend with LangGraph StateGraph fully operational
- ✅ React dashboard with live SSE streaming, HITL gates, cancel button, subscriber emails input
- ✅ WhatsApp Baileys bridge with self-message filtering and link extraction
- ✅ YouTube Transcript MCP and Fetch MCP wired as real subprocess MCP calls
- ✅ GitHub MCP configured in `.gemini/settings.json` for IDE use; REST API for pipeline publish
- ✅ Gemini 2.5 Flash (cloud) and Gemma (Ollama local) writer agent
- ✅ APScheduler cron scheduling configurable from the dashboard UI
- ✅ GitHub Pages publish with unique content-hash filenames and auto-updating `index.html`
