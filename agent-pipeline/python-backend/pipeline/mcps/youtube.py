"""
YouTube Transcript MCP client.
Uses: npx -y @kimtaeyoon83/mcp-server-youtube-transcript
No auth required — hits YouTube timedtext API directly.
"""
import json, subprocess, time


def fetch_youtube_transcript(url: str) -> dict:
    result_text = _call_mcp_tool(
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


def _call_mcp_tool(cmd: list, tool_name: str, tool_args: dict) -> str:
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
        text=True, encoding="utf-8", errors="replace", shell=True,
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
    raise TimeoutError(f"YouTube MCP timed out for {tool_args.get('url', 'unknown URL')}")
