"""
YouTube Transcript MCP client.
Uses: npx -y @kimtaeyoon83/mcp-server-youtube-transcript
No auth required — hits YouTube timedtext API directly.
"""
from pipeline.mcps.mcp_client_helper import call_mcp_tool_subprocess


def fetch_youtube_transcript(url: str) -> dict:
    result_text = call_mcp_tool_subprocess(
        ["npx", "-y", "@kimtaeyoon83/mcp-server-youtube-transcript"],
        "get_transcript",
        {"url": url, "lang": "en", "include_timestamps": False, "strip_ads": True},
    )
    transcript = result_text[:3000]
    return {
        "url": url,
        "type": "youtube",
        "title": f"YouTube: {url}",
        "summary": transcript,
        "raw_transcript": result_text,
    }


