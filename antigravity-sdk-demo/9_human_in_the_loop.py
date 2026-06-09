import asyncio
import sys
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from google.antigravity.utils import interactive

# Load environment variables
load_dotenv()

def publish_document(content: str) -> str:
    """Publishes a document to the live website."""
    return "Document successfully published!"

async def main():
    print("--- Human in the Loop (HITL) Demo ---")
    
    # We use policy.ask_user to intercept the 'publish_document' tool call.
    # The interactive.ask_user_handler provides a CLI prompt (y/n) for the user.
    config = LocalAgentConfig(
        model="gemini-2.5-flash",
        tools=[publish_document],
        policies=[
            policy.ask_user("publish_document", handler=interactive.ask_user_handler)
        ]
    )
    
    async with Agent(config) as agent:
        print("User: Please publish a new document about Antigravity.")
        print("(The agent will attempt to call publish_document, which will trigger a CLI prompt for you.)\n")
        
        # This chat call will block when the tool is attempted, 
        # waiting for you to type 'y' or 'n' in the terminal.
        try:
            response = await agent.chat("Please publish a new document about Antigravity.")
            print("\nAgent:", await response.text())
        except Exception as e:
            # If you run this in an environment without a true TTY, interactive_cli might fail
            print(f"\nExecution finished/failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
