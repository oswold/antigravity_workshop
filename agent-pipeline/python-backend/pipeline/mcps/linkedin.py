"""
LinkedIn MCP client — fetches LinkedIn posts using uvx mcp-server-fetch
with --ignore-robots-txt, running as a subprocess inside the container.

This bypasses the Docker Desktop MCP gateway (which is unreachable from
inside the container via host.docker.internal) and calls the fetch server
directly, just like fetch.py does for regular web articles.
"""
import os
from pipeline.mcps.mcp_client_helper import call_mcp_tool_subprocess


def fetch_linkedin_post(url: str) -> dict:
    """
    Fetch a LinkedIn post's content by calling uvx mcp-server-fetch
    with --ignore-robots-txt as a subprocess.
    """
    uv_path = os.path.join(os.environ.get("USERPROFILE", ""), ".local", "bin", "uvx.exe")
    if not os.path.exists(uv_path):
        uv_path = "uvx"

    result_text = call_mcp_tool_subprocess(
        [uv_path, "mcp-server-fetch", "--ignore-robots-txt"],
        "fetch",
        {"url": url, "max_length": 3000},
    )

    return {
        "url": url,
        "type": "linkedin",
        "title": f"LinkedIn Post: {url}",
        "summary": result_text[:2000],
    }

