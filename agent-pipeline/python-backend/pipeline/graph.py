"""
LangGraph StateGraph definition for the AI Pulse pipeline.
Flow: fetch_notes → link_review (HITL) → research → write → review (HITL) → publish | reject
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator


class PipelineState(TypedDict):
    run_id: str
    topic: str
    days: int
    model: str
    trigger: str                # "manual" or "cron"
    notes: list[dict]           # Raw WhatsApp notes
    selected_links: list[str]   # Links chosen by user in link-review UI
    research_data: list[dict]   # Summarised sources
    newsletter: str             # Final markdown
    approval: bool | None       # HITL publish decision
    user_feedback: str | None   # HITL user revision feedback
    revision_count: int         # Track revision iterations
    error: str | None
    include_uncrawlable: bool   # Whether to include failed/uncrawlable links in references
    uncrawlable_links: list[str] # List of links that failed checking
    research_cache: dict        # Cache of pre-fetched research results


def build_graph():
    from pipeline.nodes.fetch_notes import fetch_notes_node
    from pipeline.nodes.link_review import link_review_node
    from pipeline.nodes.research import research_node
    from pipeline.nodes.write import write_node
    from pipeline.nodes.review import review_node
    from pipeline.nodes.publish import publish_node
    from pipeline.nodes.rejected import rejected_node

    g = StateGraph(PipelineState)

    g.add_node("fetch_notes",  fetch_notes_node)
    g.add_node("link_review",  link_review_node)
    g.add_node("research",     research_node)
    g.add_node("write",        write_node)
    g.add_node("review",       review_node)
    g.add_node("publish",      publish_node)
    g.add_node("rejected",     rejected_node)

    g.set_entry_point("fetch_notes")
    g.add_edge("fetch_notes", "link_review")
    g.add_edge("link_review", "research")
    g.add_edge("research",    "write")
    g.add_edge("write",       "review")

    # Conditional edge: approve → publish, feedback → write, else → rejected
    def route_review(s: PipelineState):
        if s.get("approval") is True:
            return "publish"
        elif s.get("user_feedback"):
            return "write"
        else:
            return "rejected"

    g.add_conditional_edges(
        "review",
        route_review,
        {"publish": "publish", "write": "write", "rejected": "rejected"},
    )
    g.add_edge("publish",  END)
    g.add_edge("rejected", END)

    return g.compile()
