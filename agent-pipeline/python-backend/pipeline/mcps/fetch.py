"""
Fetch MCP client — fetches any public URL and returns Markdown content.
Uses: uvx mcp-server-fetch  (no auth required)
"""
import json, subprocess, time, os


def fetch_web_article(url: str) -> dict:
    uv_path = os.path.join(os.environ.get("USERPROFILE", ""), ".local", "bin", "uvx.exe")
    if not os.path.exists(uv_path):
        uv_path = "uvx"

    result_text = _call_mcp_tool(
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


def _call_mcp_tool(cmd: list, tool_name: str, tool_args: dict) -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    init_req = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05",
                   "clientInfo": {"name": "ai-pulse-py", "version": "1.0"},
                   "capabilities": {}},
    })
    tool_req = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    })

    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", env=env, shell=True,
    )
    proc.stdin.write(init_req + "\n")
    proc.stdin.flush()

    initialized = False
    deadline = time.time() + 45

    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        try:
            msg = json.loads(line.strip())
            if msg.get("id") == 1 and not initialized:
                initialized = True
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
                proc.stdin.write(tool_req + "\n")
                proc.stdin.flush()
            elif msg.get("id") == 2:
                proc.kill()
                if msg.get("error"):
                    raise RuntimeError(msg["error"]["message"])
                return msg.get("result", {}).get("content", [{}])[0].get("text", "")
        except (json.JSONDecodeError, KeyError):
            continue

    proc.kill()
    raise TimeoutError(f"Fetch MCP timed out for {tool_args.get('url', 'unknown URL')}")
