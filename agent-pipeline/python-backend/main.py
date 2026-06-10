# FastAPI entry point — Sakthi's Corner Newsletter Agent Pipeline
# SSE streaming + REST endpoints mirroring the original Node.js server.

import asyncio
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from pipeline.graph import build_graph
from scheduler.cron import scheduler, schedule_pipeline, stop_pipeline
from state import pipeline_states, sse_queues

load_dotenv(override=True)

# ── Lifespan: start/stop APScheduler ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="Sakthi's Corner Backend (Python)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    from datetime import datetime, timezone
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}

# ── POST /api/pipeline/run ────────────────────────────────────────────────────
@app.post("/api/pipeline/run")
async def run_pipeline(req: Request):
    body = await req.json()
    topic = body.get("topic", "AI")
    days = int(body.get("days", 7))
    model = body.get("model", "gemini")
    emails = body.get("emails", "")
    run_id = str(uuid4())

    pipeline_states[run_id] = {
        "run_id": run_id, "topic": topic, "days": days, "model": model, "emails": emails,
        "status": "running", "logs": [],
        "awaiting_approval": False, "approval": None,
        "awaiting_link_selection": False, "selected_links": None,
        "newsletter": None,
    }
    sse_queues[run_id] = asyncio.Queue()

    # Fire pipeline in background
    asyncio.create_task(_run(run_id, topic, days, model))
    return JSONResponse({"runId": run_id})

async def _run(run_id, topic, days, model):
    from pipeline.runner import run_pipeline_graph
    await run_pipeline_graph(run_id, topic, days, model, graph)

# ── GET /api/pipeline/events/:runId — SSE ────────────────────────────────────
@app.get("/api/pipeline/events/{run_id}")
async def events(run_id: str):
    async def generator():
        # Replay existing logs first (late-connect catch-up)
        s = pipeline_states.get(run_id, {})
        for log in s.get("logs", []):
            yield {"data": __import__("json").dumps(log)}

        q = sse_queues.get(run_id)
        if not q:
            return
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=30)
                yield {"data": __import__("json").dumps(event)}
                if event.get("type") in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield {"data": __import__("json").dumps({"type": "ping"})}
    return EventSourceResponse(generator())

# ── POST /api/pipeline/cancel/:runId ─────────────────────────────────────────
@app.post("/api/pipeline/cancel/{run_id}")
async def cancel_pipeline(run_id: str):
    s = pipeline_states.get(run_id)
    if s:
        s["cancelled"] = True
    return JSONResponse({"ok": True})

# ── POST /api/pipeline/approve/:runId — HITL gate ────────────────────────────
@app.post("/api/pipeline/approve/{run_id}")
async def approve(run_id: str, req: Request):
    body = await req.json()
    s = pipeline_states.get(run_id)
    if not s:
        return JSONResponse({"error": "Run not found"}, status_code=404)
    if not s.get("awaiting_approval"):
        return JSONResponse({"error": "Not awaiting approval"}, status_code=400)

    feedback = body.get("feedback")
    if feedback:
        s["user_feedback"] = feedback
        s["approval"] = None
        s["awaiting_approval"] = False
        return JSONResponse({"ok": True, "feedback": feedback})
    else:
        s["approval"] = bool(body.get("approved"))
        s["awaiting_approval"] = False
        return JSONResponse({"ok": True, "approved": s["approval"]})

# ── POST /api/pipeline/select-links/:runId — Link selection gate ─────────────
@app.post("/api/pipeline/select-links/{run_id}")
async def select_links(run_id: str, req: Request):
    body = await req.json()
    s = pipeline_states.get(run_id)
    if not s:
        return JSONResponse({"error": "Run not found"}, status_code=404)
    s["selected_links"] = body.get("links", [])
    s["include_uncrawlable"] = body.get("include_uncrawlable", False)
    s["awaiting_link_selection"] = False
    return JSONResponse({"ok": True, "count": len(s["selected_links"])})

# ── GET /api/pipeline/state/:runId ───────────────────────────────────────────
@app.get("/api/pipeline/state/{run_id}")
async def get_state(run_id: str):
    return pipeline_states.get(run_id, {"status": "not_found"})

# ── GET /api/pipeline/newsletter/:runId ──────────────────────────────────────
@app.get("/api/pipeline/newsletter/{run_id}")
async def get_newsletter(run_id: str):
    s = pipeline_states.get(run_id, {})
    if not s.get("newsletter"):
        return JSONResponse({"error": "Newsletter not ready"}, status_code=404)
    return {"newsletter": s["newsletter"]}

# ── POST /api/pipeline/cron ───────────────────────────────────────────────────
@app.post("/api/pipeline/cron")
async def set_cron(req: Request):
    body = await req.json()
    expression = body.get("expression", "0 8 * * 1")
    topic = body.get("topic", "AI")
    model = body.get("model", "gemini")
    days = int(body.get("days", 7))
    emails = body.get("emails", "")
    try:
        schedule_pipeline(expression, topic, model, days, emails, graph)
        return {"ok": True, "expression": expression}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# ── DELETE /api/pipeline/cron ─────────────────────────────────────────────────
@app.delete("/api/pipeline/cron")
async def del_cron():
    stop_pipeline()
    return {"ok": True}
