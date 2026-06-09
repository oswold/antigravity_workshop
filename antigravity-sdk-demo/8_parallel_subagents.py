import asyncio
import os
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig

# Load environment variables
load_dotenv()

def list_files(path: str = ".") -> str:
    """Lists files in a directory."""
    return f"Files in {path}: {', '.join(os.listdir(path)[:5])}..."

def count_files(path: str = ".") -> str:
    """Counts files in a directory."""
    return f"Total file count in {path}: {len(os.listdir(path))}"

async def main():
    print("--- Parallel Subagents Demo ---")
    
    lister_config = LocalAgentConfig(
        model="gemini-2.5-flash",
        system_instructions="You are the File Lister Agent. Use the list_files tool to list the files in the directory.",
        tools=[list_files]
    )
    
    counter_config = LocalAgentConfig(
        model="gemini-2.5-flash",
        system_instructions="You are the File Counter Agent. Use the count_files tool to count the files in the directory.",
        tools=[count_files]
    )
    
    agents = {
        "Lister": Agent(lister_config),
        "Counter": Agent(counter_config)
    }
    
    async with agents["Lister"] as lister, agents["Counter"] as counter:
        print("Dispatching parallel requests to subagents...")
        
        # Run the two subagent tasks concurrently
        task1 = lister.chat("List the files in the current directory.")
        task2 = counter.chat("Count the files in the current directory.")
        
        resp_lister, resp_counter = await asyncio.gather(task1, task2)
        
        print(f"\n[Lister Subagent Result]: {await resp_lister.text()}")
        print(f"\n[Counter Subagent Result]: {await resp_counter.text()}")

if __name__ == "__main__":
    asyncio.run(main())
