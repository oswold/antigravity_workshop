import asyncio
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig

# Load environment variables
load_dotenv()

async def single_agent_demo():
    print("--- Single Agent Workflow ---")
    config = LocalAgentConfig(model="gemini-2.5-flash", system_instructions="You are a helpful assistant.")
    async with Agent(config) as agent:
        response = await agent.chat("What is the capital of France?")
        print("Agent:", await response.text())

async def multi_agent_demo():
    print("\n--- Multi Agent Workflow ---")
    
    # We create two agents with different personas
    alice_config = LocalAgentConfig(model="gemini-2.5-flash", system_instructions="You are Alice. You are highly technical and concise.")
    bob_config = LocalAgentConfig(model="gemini-2.5-flash", system_instructions="You are Bob. You are creative and explain things using metaphors.")
    
    agents = {
        "Alice": Agent(alice_config),
        "Bob": Agent(bob_config)
    }
    
    # Start the context managers for both agents concurrently
    async with agents["Alice"] as alice, agents["Bob"] as bob:
        topic = "How does a CPU work?"
        print(f"Topic: {topic}\n")
        
        # Parallel execution: Ask both agents simultaneously
        async def ask(name, agent):
            resp = await agent.chat(topic)
            return name, await resp.text()
            
        tasks = [ask(name, ag) for name, ag in agents.items()]
        results = await asyncio.gather(*tasks)
        
        for name, text in results:
            print(f"[{name}]: {text}\n")

async def main():
    await single_agent_demo()
    await multi_agent_demo()

if __name__ == "__main__":
    asyncio.run(main())
