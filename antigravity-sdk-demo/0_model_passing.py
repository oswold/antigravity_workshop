import asyncio
import os
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig

# Automatically locate and load the .env file (even if it's in the parent directory)
load_dotenv()

async def main():
    # LocalAgentConfig automatically looks up the GEMINI_API_KEY environment variable.
    config = LocalAgentConfig(model="gemini-2.5-flash")
    async with Agent(config) as agent:
        response = await agent.chat("Say hello in one word.")
        print("Agent response:", await response.text())

if __name__ == "__main__":
    asyncio.run(main())
