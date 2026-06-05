"""
APScheduler cron integration for the pipeline.
"""
import asyncio
from uuid import uuid4
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
_job = None


def schedule_pipeline(expression: str, topic: str, model: str, days: int, emails: str, graph):
    global _job
    if _job:
        _job.remove()

    # Parse 5-field cron expression for APScheduler
    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError("Cron expression must have 5 fields: minute hour day month day_of_week")

    minute, hour, day, month, day_of_week = fields
    trigger = CronTrigger(
        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
    )

    def _run():
        from state import pipeline_states, sse_queues
        from pipeline.runner import run_pipeline_graph
        run_id = str(uuid4())
        pipeline_states[run_id] = {
            "run_id": run_id, "topic": topic, "days": days, "model": model, "emails": emails,
            "status": "running", "logs": [],
            "awaiting_approval": False, "approval": None,
            "awaiting_link_selection": False, "selected_links": None,
            "newsletter": None,
        }
        sse_queues[run_id] = asyncio.Queue()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_pipeline_graph(run_id, topic, days, model, graph, trigger="cron"))

    _job = scheduler.add_job(_run, trigger=trigger, id="pipeline_cron", replace_existing=True)
    print(f"[Cron] Scheduled: {expression} — topic: {topic}")


def stop_pipeline():
    global _job
    if _job:
        _job.remove()
        _job = None
    print("[Cron] Stopped")
