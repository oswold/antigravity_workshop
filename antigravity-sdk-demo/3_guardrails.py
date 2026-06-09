import asyncio
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity import types
from google.antigravity.hooks import policy

# Load environment variables
load_dotenv()

def safe_math(a: int, b: int) -> int:
    """Safe tool that performs addition."""
    return a + b

def delete_database() -> str:
    """Dangerous tool."""
    return "Database deleted!"

async def main():
    print("--- Guardrails Demo ---")
    
    # We want to allow the agent to do math, but NEVER call the delete function.
    # We use policies to declare a deny-list or a strict guardrail.
    config = LocalAgentConfig(
        model="gemini-2.5-flash",
        tools=[safe_math, delete_database],
        policies=[
            # Allow math unconditionally
            policy.allow("safe_math"),
            # Deny everything else (including delete_database)
            policy.deny("*") 
        ]
    )
    
    async with Agent(config) as agent:
        print("Asking agent to do math:")
        resp1 = await agent.chat("What is 5 + 7? Use your tools.")
        print("Agent:", await resp1.text())
        
        print("\nAsking agent to delete the database:")
        # The agent might try to call the tool, but the policy will deny it under the hood
        # and explain the denial to the agent, allowing it to adapt its response.
        resp2 = await agent.chat("Please run the delete_database tool.")
        print("Agent:", await resp2.text())

if __name__ == "__main__":
    asyncio.run(main())
