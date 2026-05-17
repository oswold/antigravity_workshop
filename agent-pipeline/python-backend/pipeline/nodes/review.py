"""
Node: review (HITL gate #2)
Waits for human approval via POST /api/pipeline/approve/:runId
"""
import time
from state import emit, pipeline_states


def review_node(state: dict) -> dict:
    run_id = state["run_id"]

    emit(run_id, {
        "type": "step", "step": "review", "status": "awaiting",
        "message": "👤 [GUARDRAIL] Waiting for human approval to publish...",
    })

    deadline = time.time() + 600  # 10-minute timeout
    while time.time() < deadline:
        s = pipeline_states.get(run_id, {})
        if s.get("cancelled"):
            emit(run_id, {"type": "error", "message": "Pipeline cancelled manually."})
            raise ValueError("Pipeline cancelled manually.")
        
        # Check for revision feedback first
        if s.get("user_feedback"):
            feedback = s["user_feedback"]
            s["user_feedback"] = None # Consume it
            s["awaiting_approval"] = False
            emit(run_id, {
                "type": "step", "step": "review",
                "status": "in_progress",
                "detail": f"🔄 Requesting revision: '{feedback[:60]}...'",
            })
            return {
                **state, 
                "approval": False, 
                "user_feedback": feedback, 
                "revision_count": state.get("revision_count", 0) + 1
            }

        # Check for final approval/rejection
        if s.get("approval") is not None:
            approved = s["approval"]
            emit(run_id, {
                "type": "step", "step": "review",
                "status": "done" if approved else "rejected",
                "detail": "✅ Approved by human" if approved else "❌ Rejected by human",
            })
            return {**state, "approval": approved, "user_feedback": None}
        time.sleep(0.5)

    emit(run_id, {"type": "step", "step": "review", "status": "rejected",
                  "detail": "Timeout — auto-rejected"})
    return {**state, "approval": False, "user_feedback": None}
