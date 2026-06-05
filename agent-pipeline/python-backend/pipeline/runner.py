"""
Pipeline runner — invokes the LangGraph graph and streams events via SSE.
"""
import asyncio
from state import emit, pipeline_states


async def run_pipeline_graph(run_id: str, topic: str, days: int, model: str, graph, trigger: str = "manual"):
    emit(run_id, {"type": "started", "runId": run_id, "topic": topic, "model": model, "days": days, "trigger": trigger})

    initial_state = {
        "run_id": run_id,
        "topic": topic,
        "days": days,
        "model": model,
        "trigger": trigger,
        "notes": [],
        "selected_links": [],
        "research_data": [],
        "newsletter": "",
        "approval": None,
        "user_feedback": None,
        "revision_count": 0,
        "error": None,
        "include_uncrawlable": False,
        "uncrawlable_links": [],
        "research_cache": {},
    }

    try:
        # Run the graph — it will block at HITL nodes polling pipeline_states
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: graph.invoke(initial_state))
    except Exception as e:
        import traceback
        traceback.print_exc()
        emit(run_id, {"type": "error", "message": str(e)})
