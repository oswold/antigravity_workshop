import asyncio
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig

# Load environment variables
load_dotenv()

async def main():
    print("--- Memory Types Demo ---")
    print("The google-antigravity SDK implicitly manages session memory as long as you retain the Agent instance.\n")
    
    config = LocalAgentConfig(model="gemini-2.5-flash")
    
    # Session Memory: The context is preserved across turns inside the same `async with` block.
    async with Agent(config) as agent:
        print("User: My favorite color is blue.")
        await agent.chat("My favorite color is blue.")
        
        print("User: What is my favorite color?")
        response = await agent.chat("What is my favorite color?")
        print("Agent:", await response.text())
        
        print("\nManually accessing conversation history:")
        for i, step in enumerate(agent.conversation.history):
            print(f"  Step {i}: Type: {step.type.value}, Source: {step.source.value}")

if __name__ == "__main__":
    asyncio.run(main())
