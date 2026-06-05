import os
import json
import httpx
from urllib.parse import urljoin, urlparse, urlunparse

def _get_headers(sse_url: str) -> dict:
    headers = {"Accept": "text/event-stream"}
    token = os.environ.get("MCP_GATEWAY_AUTH_TOKEN")
    if token and any(h in sse_url for h in ("localhost", "127.0.0.1", "host.docker.internal")):
        headers["Authorization"] = f"Bearer {token}"
    return headers

def _resolve_post_url(sse_url: str, data: str) -> str:
    post_url = urljoin(sse_url, data)
    parsed_sse = urlparse(sse_url)
    parsed_post = urlparse(post_url)
    if parsed_post.netloc.startswith(("localhost:", "127.0.0.1:")):
        parsed_post = parsed_post._replace(netloc=parsed_sse.netloc)
        post_url = urlunparse(parsed_post)
    return post_url

def _handle_jsonrpc_message(msg: dict, initialized: bool, post_url: str, post_headers: dict, client: httpx.Client, tool_name: str, tool_args: dict) -> tuple:
    """
    Handles a decoded JSON-RPC message.
    Returns (new_initialized_state, result_text, error_message, should_break)
    """
    if msg.get("id") == 1 and not initialized:
        client.post(post_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=post_headers)
        tool_req = {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool_name, "arguments": tool_args}
        }
        client.post(post_url, json=tool_req, headers=post_headers)
        return True, None, None, False
    elif msg.get("id") == 2:
        if msg.get("error"):
            return initialized, None, msg["error"]["message"], True
        else:
            res_text = msg.get("result", {}).get("content", [{}])[0].get("text", "")
            return initialized, res_text, None, True
            
    return initialized, None, None, False

def call_mcp_tool_sse(sse_url: str, tool_name: str, tool_args: dict, timeout: float = 45.0) -> str:
    """
    Connect to the legacy HTTP+SSE MCP server at sse_url, perform initialization,
    and make a synchronous tool call.
    """
    headers = _get_headers(sse_url)
    post_url = None
    initialized = False
    result_text = None
    error_message = None
    post_headers = {}

    client = httpx.Client(timeout=timeout)
    
    with client.stream("GET", sse_url, headers=headers) as response:
        event_name = None
        data_buffer = []

        for line in response.iter_lines():
            line = line.strip()
            if not line:
                if not data_buffer:
                    continue
                
                data = "".join(data_buffer)
                if event_name == "endpoint":
                    post_url = _resolve_post_url(sse_url, data)
                    post_headers = {"Accept": "application/json", "Content-Type": "application/json"}
                    if "Authorization" in headers:
                        post_headers["Authorization"] = headers["Authorization"]

                    init_req = {
                        "jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "clientInfo": {"name": "ai-pulse-py", "version": "1.0"},
                            "capabilities": {}
                        }
                    }
                    client.post(post_url, json=init_req, headers=post_headers)
                else:
                    try:
                        msg = json.loads(data)
                        initialized, res, err, should_break = _handle_jsonrpc_message(
                            msg, initialized, post_url, post_headers, client, tool_name, tool_args
                        )
                        if should_break:
                            result_text = res
                            error_message = err
                            break
                    except json.JSONDecodeError:
                        pass
                
                event_name = None
                data_buffer = []
                continue

            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_buffer.append(line[len("data:"):].strip())

    if error_message:
        raise RuntimeError(error_message)
    if result_text is not None:
        return result_text
    raise TimeoutError(f"SSE call timed out for tool {tool_name}")
