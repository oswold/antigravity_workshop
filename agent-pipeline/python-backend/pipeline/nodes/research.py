"""
Node: research
Routes each selected link to the correct MCP tool:
  - YouTube URL  →  YouTube Transcript MCP (npx @kimtaeyoon83/mcp-server-youtube-transcript)
  - All others   →  Fetch MCP (uvx mcp-server-fetch)
"""
import re
from state import emit
from pipeline.mcps.youtube import fetch_youtube_transcript
from pipeline.mcps.fetch import fetch_web_article


def is_youtube(url: str) -> bool:
    return bool(re.search(r"youtube\.com|youtu\.be", url, re.I))


def research_node(state: dict) -> dict:
    run_id   = state["run_id"]
    links    = state.get("selected_links", [])
    cache    = state.get("research_cache", {})

    emit(run_id, {
        "type": "step", "step": "research", "status": "in_progress",
        "message": f"🔍 Research Agent — processing {len(links)} links via MCPs...",
    })

    results = []
    for url in links:
        tool_name = "YouTube Transcript MCP" if is_youtube(url) else "Fetch MCP"
        
        if url in cache:
            results.append(cache[url])
            emit(run_id, {
                "type": "mcp_call", "tool": tool_name, "status": "success",
                "detail": f"{cache[url].get('title', url)[:80]} (from cache)",
            })
            continue

        emit(run_id, {
            "type": "mcp_call", "tool": tool_name, "status": "calling",
            "detail": url,
        })
        try:
            if is_youtube(url):
                result = fetch_youtube_transcript(url)
            else:
                result = fetch_web_article(url)

            emit(run_id, {
                "type": "mcp_call", "tool": tool_name, "status": "success",
                "detail": f"{result.get('title', url)[:80]}",
            })
            results.append(result)
        except Exception as e:
            emit(run_id, {
                "type": "mcp_call", "tool": tool_name, "status": "warn",
                "detail": f"Failed for {url}: {e}",
            })

    emit(run_id, {
        "type": "step", "step": "research", "status": "done",
        "detail": f"Processed {len(results)} sources",
    })
    return {**state, "research_data": results}
