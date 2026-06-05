"""
LinkedIn MCP client — fetches LinkedIn posts using uvx mcp-server-fetch
with --ignore-robots-txt, running as a subprocess inside the container.

This bypasses the Docker Desktop MCP gateway (which is unreachable from
inside the container via host.docker.internal) and calls the fetch server
directly, just like fetch.py does for regular web articles.
"""
import json
import subprocess
import time
import os
from queue import Queue, Empty
from threading import Thread


def fetch_linkedin_post(url: str) -> dict:
    """
    Fetch a LinkedIn post's content by calling uvx mcp-server-fetch
    with --ignore-robots-txt as a subprocess.
    """
    uv_path = os.path.join(os.environ.get("USERPROFILE", ""), ".local", "bin", "uvx.exe")
    if not os.path.exists(uv_path):
        uv_path = "uvx"

    result_text = _call_fetch_mcp(
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


def _call_fetch_mcp(cmd: list, tool_name: str, tool_args: dict) -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    init_req = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "ai-pulse-py", "version": "1.0"},
            "capabilities": {},
        },
    })
    tool_req = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    })

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        shell=False,
    )
    proc.stdin.write(init_req + "\n")
    proc.stdin.flush()

    # Non-blocking reader thread so deadline is strictly respected
    q: Queue = Queue()

    def enqueue_output(out, queue):
        try:
            for line in iter(out.readline, ""):
                queue.put(line)
        except Exception:
            pass
        finally:
            out.close()

    t = Thread(target=enqueue_output, args=(proc.stdout, q), daemon=True)
    t.start()

    initialized = False
    deadline = time.time() + 45

    while time.time() < deadline:
        try:
            timeout = max(0.1, deadline - time.time())
            line = q.get(timeout=timeout)
        except Empty:
            break

        if not line:
            break
        try:
            msg = json.loads(line.strip())
            if msg.get("id") == 1 and not initialized:
                initialized = True
                proc.stdin.write(
                    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
                )
                proc.stdin.write(tool_req + "\n")
                proc.stdin.flush()
            elif msg.get("id") == 2:
                proc.kill()
                proc.wait()
                if msg.get("error"):
                    raise RuntimeError(msg["error"]["message"])
                return msg.get("result", {}).get("content", [{}])[0].get("text", "")
        except (json.JSONDecodeError, KeyError):
            continue

    proc.kill()
    proc.wait()
    raise TimeoutError(f"LinkedIn fetch timed out for {tool_args.get('url', 'unknown URL')}")
