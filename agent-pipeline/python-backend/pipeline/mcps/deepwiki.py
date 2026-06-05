"""
Deepwiki MCP client — queries the deepwiki tool for repository summaries,
connecting via the Docker Desktop profile 'antigravity_mcp'.
"""
import os
import re
from pipeline.mcps.sse_client import call_mcp_tool_sse

# Use the direct Deepwiki URL instead of the deprecated/local gateway endpoint
DEEPWIKI_SSE_URL = os.environ.get("DEEPWIKI_SSE_URL", "https://mcp.deepwiki.com/mcp")

def fetch_github_summary(url: str) -> dict:
    """
    Fetch a repository summary using the DeepWiki MCP server.
    """
    # Parse owner/repo from GitHub URL
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    repo_name = f"{match.group(1)}/{match.group(2)}"

    # If calling the local gateway, fallback to the configured tool/arguments
    if any(h in DEEPWIKI_SSE_URL for h in ("localhost", "127.0.0.1", "host.docker.internal")):
        tool_name = os.environ.get("DEEPWIKI_TOOL_NAME", "ask_question")
        if tool_name == "ask_question":
            args = {
                "repoName": repo_name,
                "question": "Provide a comprehensive summary of this repository, including its main features, architecture, and technology stack."
            }
        else:
            args = {os.environ.get("DEEPWIKI_URL_ARG", "repo_url"): url}
    else:
        # Connect directly to deepwiki endpoint using ask_question tool
        tool_name = "ask_question"
        args = {
            "repoName": repo_name,
            "question": "Provide a comprehensive summary of this repository, including its main features, architecture, and technology stack."
        }

    try:
        # Set a short 5.0 second timeout so down/unreachable servers don't hang the pipeline
        result_text = call_mcp_tool_sse(
            DEEPWIKI_SSE_URL,
            tool_name,
            args,
            timeout=5.0
        )
    except Exception as e:
        # Fallback to standard Fetch MCP if DeepWiki server is offline or fails
        print(f"⚠️ DeepWiki MCP failed or timed out ({e}). Falling back to Fetch MCP...")
        try:
            from pipeline.mcps.fetch import fetch_web_article
            web_res = fetch_web_article(url)
            return {
                "url": url,
                "type": "github",
                "title": f"GitHub Repository: {url}",
                "summary": f"[Fetched via Fetch MCP Fallback] {web_res.get('summary', '')[:2000]}",
            }
        except Exception as fetch_err:
            raise RuntimeError(f"DeepWiki MCP failed ({e}) and Fetch MCP fallback failed ({fetch_err})")

    return {
        "url": url,
        "type": "github",
        "title": f"GitHub Repository: {url}",
        "summary": result_text[:2000],
    }
