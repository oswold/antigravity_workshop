import asyncio
import os
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity import types

# Load local environment variables
load_dotenv()

async def main():
    print("--- MCP Docker Gateway Demo ---")
    
    token = os.environ.get("MCP_GATEWAY_AUTH_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else None

    # Configure the MCP server running in your Docker gateway using HTTP SSE transport
    mcp_server = types.McpStreamableHttpServer(
        name="gemini_api_doc_mcp",
        url="http://localhost:8080/mcp", # Adjust this URL to point to your Docker MCP Gateway streaming endpoint
        headers=headers,
        timeout=300.0 # Allow time for WSL2 / Docker container initialization
    )
    
    config = LocalAgentConfig(
        model="gemini-2.5-flash",
        mcp_servers=[mcp_server]
    )
    
    print("Connecting to MCP Server at http://localhost:8080/sse...")
    print("(Note: This will fail if the Docker container is not running and exposing the SSE endpoint.)\n")
    try:
        async with Agent(config) as agent:

            print("User: Can you search the Gemini API docs for how to use structured outputs?")
            response = await agent.chat("Can you search the Gemini API docs for how to use structured outputs?")
            print("\nAgent:", await response.text())
    except Exception as e:
        print(f"\nExecution finished/failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
