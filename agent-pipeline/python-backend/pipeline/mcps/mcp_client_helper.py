import json
import subprocess
import time
import os
from queue import Queue, Empty
from threading import Thread

def _enqueue_output(out, queue):
    try:
        for line in iter(out.readline, ''):
            queue.put(line)
    except Exception:
        pass
    finally:
        out.close()

def _start_mcp_process(cmd: list) -> subprocess.Popen:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    return subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None,
        text=True, encoding="utf-8", errors="replace", env=env, shell=False,
    )

def _send_initialize(proc: subprocess.Popen):
    init_req = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05",
                   "clientInfo": {"name": "ai-pulse-py", "version": "1.0"},
                   "capabilities": {}},
    })
    proc.stdin.write(init_req + "\n")
    proc.stdin.flush()

def _handle_mcp_message(line: str, proc: subprocess.Popen, tool_req: str, state: dict) -> tuple:
    """
    Processes a single JSON-RPC line from the process's stdout.
    Returns (result_text_or_none, error_msg_or_none, stop_loop_boolean)
    """
    try:
        msg = json.loads(line.strip())
    except (json.JSONDecodeError, KeyError):
        return None, None, False

    if msg.get("id") == 1 and not state.get("initialized"):
        state["initialized"] = True
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.write(tool_req + "\n")
        proc.stdin.flush()
        return None, None, False
    elif msg.get("id") == 2:
        proc.kill()
        proc.wait()
        if msg.get("error"):
            return None, msg["error"]["message"], True
        result = msg.get("result", {}).get("content", [{}])[0].get("text", "")
        return result, None, True
    
    return None, None, False

def call_mcp_tool_subprocess(cmd: list, tool_name: str, tool_args: dict, timeout_secs: float = 45.0) -> str:
    tool_req = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    })

    proc = _start_mcp_process(cmd)
    _send_initialize(proc)

    q = Queue()
    t = Thread(target=_enqueue_output, args=(proc.stdout, q), daemon=True)
    t.start()

    state = {"initialized": False}
    deadline = time.time() + timeout_secs

    while time.time() < deadline:
        try:
            timeout = max(0.1, deadline - time.time())
            line = q.get(timeout=timeout)
        except Empty:
            break

        if not line:
            break

        result, err, finished = _handle_mcp_message(line, proc, tool_req, state)
        if finished:
            if err:
                raise RuntimeError(err)
            return result

    proc.kill()
    proc.wait()
    raise TimeoutError(f"MCP client call timed out for tool {tool_name} with args {tool_args}")
