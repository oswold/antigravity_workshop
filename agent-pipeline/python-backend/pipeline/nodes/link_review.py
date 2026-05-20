"""
Node: link_review (HITL gate #1)
Pauses the pipeline so the user can select/deselect links before research runs.
"""
import time
import concurrent.futures
from state import emit, pipeline_states
from pipeline.nodes.research import is_youtube
from pipeline.mcps.youtube import fetch_youtube_transcript
from pipeline.mcps.fetch import fetch_web_article


def link_review_node(state: dict) -> dict:
    run_id = state["run_id"]
    notes  = state["notes"]

    # Extract all unique links from notes
    all_links = []
    seen = set()
    for note in notes:
        for link in note.get("links", []):
            if link not in seen:
                seen.add(link)
                all_links.append({
                    "url": link,
                    "source_text": note["text"][:120],
                    "date": note["date"],
                })

    if len(all_links) == 0:
        emit(run_id, {"type": "error", "message": "Zero links obtained. Pipeline automatically cancelled."})
        raise ValueError("Zero links obtained.")

    emit(run_id, {
        "type": "step", "step": "link_review", "status": "in_progress",
        "message": f"🔗 Pre-checking crawlability for {len(all_links)} links...",
    })

    research_cache = {}

    def check_one_link(link_item):
        url = link_item["url"]
        tool_name = "YouTube Transcript MCP" if is_youtube(url) else "Fetch MCP"
        try:
            if is_youtube(url):
                res = fetch_youtube_transcript(url)
            else:
                res = fetch_web_article(url)
            return link_item, True, res, None
        except Exception as e:
            return link_item, False, None, str(e)

    # Pre-check links in parallel to avoid stalling the pipeline
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(all_links), 5)) as executor:
        futures = [executor.submit(check_one_link, item) for item in all_links]
        for fut in concurrent.futures.as_completed(futures):
            item, crawlable, res, err = fut.result()
            item["crawlable"] = crawlable
            if crawlable:
                research_cache[item["url"]] = res
            else:
                item["error_message"] = err

    emit(run_id, {
        "type": "step", "step": "link_review", "status": "awaiting",
        "message": f"🔗 {len(all_links)} links found — review and select which to research",
        "links": all_links,
    })

    # Mark pipeline as awaiting link selection
    s = pipeline_states[run_id]
    s["awaiting_link_selection"] = True
    s["all_links"] = all_links
    s["research_cache"] = research_cache

    # Poll for user selection (POST /api/pipeline/select-links/:runId)
    deadline = time.time() + 600  # 10-min timeout
    while time.time() < deadline:
        s = pipeline_states.get(run_id, {})
        if s.get("cancelled"):
            emit(run_id, {"type": "error", "message": "Pipeline cancelled manually."})
            raise ValueError("Pipeline cancelled manually.")

        if not s.get("awaiting_link_selection"):
            selected = s.get("selected_links", [link["url"] for link in all_links if link.get("crawlable") != False])
            include_uncrawlable = s.get("include_uncrawlable", False)
            emit(run_id, {
                "type": "step", "step": "link_review", "status": "done",
                "detail": f"{len(selected)} links selected for research",
            })
            return {
                **state,
                "selected_links": selected,
                "include_uncrawlable": include_uncrawlable,
                "uncrawlable_links": [link["url"] for link in all_links if link.get("crawlable") == False],
                "research_cache": research_cache,
            }
        time.sleep(0.5)

    # Timeout — use all crawlable links
    selected = [link["url"] for link in all_links if link.get("crawlable") != False]
    emit(run_id, {
        "type": "step", "step": "link_review", "status": "done",
        "detail": f"Timeout — using all {len(selected)} crawlable links",
    })
    return {
        **state,
        "selected_links": selected,
        "include_uncrawlable": False,
        "uncrawlable_links": [link["url"] for link in all_links if link.get("crawlable") == False],
        "research_cache": research_cache,
    }
