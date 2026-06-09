import asyncio
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import hooks
from google.antigravity import types

# Load environment variables
load_dotenv()

class LoggingHook(hooks.PostToolCallHook):
    """Custom hook to log when a tool is called."""
    async def run(self, context: hooks.HookContext, data: types.ToolResult) -> None:
        print(f"[HOOK] Tool '{data.name}' executed. Result: {data.result}")

def read_file(path: str) -> str:
    """Reads a file's content."""
    return f"Content of {path}"

async def main():
    print("--- Hooks Demo ---")
    config = LocalAgentConfig(
        model="gemini-2.5-flash",
        tools=[read_file],
        hooks=[LoggingHook()]
    )
    
    async with Agent(config) as agent:
        response = await agent.chat("Can you read the file 'README.md'?")
        print("Agent:", await response.text())

if __name__ == "__main__":
    asyncio.run(main())
