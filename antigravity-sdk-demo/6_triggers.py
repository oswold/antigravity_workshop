import asyncio
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.triggers import every, TriggerContext

# Load environment variables
load_dotenv()

async def _moderator_nudge(ctx: TriggerContext) -> None:
    """A trigger function that runs on an interval."""
    print("\n[TRIGGER] Sending an asynchronous nudge to the agent...")
    # This sends a message asynchronously into the agent's context
    await ctx.send("Please wrap up your thoughts quickly, time is running out.")

async def main():
    print("--- Triggers Demo ---")
    
    # We set up a trigger that fires every 5 seconds for demo purposes.
    config = LocalAgentConfig(
        model="gemini-2.5-flash",
        triggers=[every(5, _moderator_nudge)]
    )
    
    async with Agent(config) as agent:
        print("User: Explain the history of the universe. (Waiting for 6 seconds to see the trigger fire...)")
        
        # Start the chat, but we will intentionally use asyncio.sleep to simulate a long wait
        # In reality, triggers run concurrently and can interrupt or steer the agent during long processing.
        # Here we just wait a bit and let the trigger fire.
        task = asyncio.create_task(agent.chat("Explain the history of the universe."))
        
        # Wait slightly longer than the trigger interval
        await asyncio.sleep(6)
        
        response = await task
        print("\nAgent:", await response.text())

if __name__ == "__main__":
    asyncio.run(main())
