"""
Fetch MCP client — fetches any public URL and returns Markdown content.
Uses: uvx mcp-server-fetch  (no auth required)
"""
import os
from pipeline.mcps.mcp_client_helper import call_mcp_tool_subprocess


def fetch_web_article(url: str) -> dict:
    uv_path = os.path.join(os.environ.get("USERPROFILE", ""), ".local", "bin", "uvx.exe")
    if not os.path.exists(uv_path):
        uv_path = "uvx"

    result_text = call_mcp_tool_subprocess(
        [uv_path, "mcp-server-fetch"],
        "fetch",
        {"url": url, "max_length": 3000},
    )
    return {
        "url": url,
        "type": "web",
        "title": f"Article: {url}",
        "summary": result_text[:2000],
    }


