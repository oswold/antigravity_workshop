import os
import json
import httpx
from urllib.parse import urljoin

def call_mcp_tool_sse(sse_url: str, tool_name: str, tool_args: dict, timeout: float = 45.0) -> str:
    """
    Connect to the legacy HTTP+SSE MCP server at sse_url, perform initialization,
    and make a synchronous tool call.
    """
    headers = {"Accept": "text/event-stream"}
    token = os.environ.get("MCP_GATEWAY_AUTH_TOKEN")
    if token and any(h in sse_url for h in ("localhost", "127.0.0.1", "host.docker.internal")):
        headers["Authorization"] = f"Bearer {token}"

    post_url = None
    initialized = False
    result_text = None
    error_message = None

    client = httpx.Client(timeout=timeout)
    
    with client.stream("GET", sse_url, headers=headers) as response:
        event_name = None
        data_buffer = []

        for line in response.iter_lines():
            line = line.strip()
            if not line:
                # End of event reached
                if data_buffer:
                    data = "".join(data_buffer)
                    if event_name == "endpoint":
                        # Server sends POST messages endpoint URL
                        post_url = urljoin(sse_url, data)
                        
                        # Rewrite localhost/127.0.0.1 in the returned URL to match the host in sse_url
                        # (e.g. host.docker.internal) so containerized clients route correctly.
                        from urllib.parse import urlparse, urlunparse
                        parsed_sse = urlparse(sse_url)
                        parsed_post = urlparse(post_url)
                        if parsed_post.netloc.startswith("localhost:") or parsed_post.netloc.startswith("127.0.0.1:"):
                            parsed_post = parsed_post._replace(netloc=parsed_sse.netloc)
                            post_url = urlunparse(parsed_post)
                            
                        post_headers = {"Accept": "application/json", "Content-Type": "application/json"}
                        if "Authorization" in headers:
                            post_headers["Authorization"] = headers["Authorization"]

                        # Send initialize request
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
                        # Check for JSON-RPC messages
                        try:
                            msg = json.loads(data)
                            if msg.get("id") == 1 and not initialized:
                                initialized = True
                                # Send initialized notification
                                client.post(post_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=post_headers)
                                # Send tools/call request
                                tool_req = {
                                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                    "params": {"name": tool_name, "arguments": tool_args}
                                }
                                client.post(post_url, json=tool_req, headers=post_headers)
                            elif msg.get("id") == 2:
                                if msg.get("error"):
                                    error_message = msg["error"]["message"]
                                else:
                                    result_text = msg.get("result", {}).get("content", [{}])[0].get("text", "")
                                break
                        except json.JSONDecodeError:
                            pass
                    
                    # Reset event data
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
