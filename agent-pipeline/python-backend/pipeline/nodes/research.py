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
from pipeline.mcps.linkedin import fetch_linkedin_post
from pipeline.mcps.deepwiki import fetch_github_summary


def is_youtube(url: str) -> bool:
    return bool(re.search(r"youtube\.com|youtu\.be", url, re.I))


def is_linkedin(url: str) -> bool:
    return bool(re.search(r"linkedin\.com", url, re.I))


def is_github(url: str) -> bool:
    return bool(re.search(r"github\.com/[^/]+/[^/]+", url, re.I))


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
        if is_youtube(url):
            tool_name = "YouTube Transcript MCP"
        elif is_linkedin(url):
            tool_name = "LinkedIn MCP"
        elif is_github(url):
            tool_name = "Deepwiki MCP"
        else:
            tool_name = "Fetch MCP"
        
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
            elif is_linkedin(url):
                result = fetch_linkedin_post(url)
            elif is_github(url):
                result = fetch_github_summary(url)
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
