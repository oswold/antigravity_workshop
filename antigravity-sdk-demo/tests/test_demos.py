import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import importlib.util

# -----------------------------------------------------------------------------
# 1. Setup global mocks for the google.antigravity SDK before importing anything
# -----------------------------------------------------------------------------

mock_ag = MagicMock()

# Mock Agent Instance
mock_agent_instance = AsyncMock()
mock_agent_instance.__aenter__.return_value = mock_agent_instance
mock_agent_instance.__aexit__.return_value = False

# Mock Agent Response
mock_response = AsyncMock()
mock_response.text.return_value = "mocked response text"
mock_agent_instance.chat.return_value = mock_response

# Mock Agent constructor
mock_ag.Agent.return_value = mock_agent_instance

# Mock LocalAgentConfig
mock_ag.LocalAgentConfig = MagicMock()

# Mock Types
mock_types = MagicMock()
mock_types.McpSseServer = MagicMock()
mock_types.McpStreamableHttpServer = MagicMock()
mock_ag.types = mock_types

# Inject into sys.modules
sys.modules['google.antigravity'] = mock_ag
sys.modules['google.antigravity.hooks'] = MagicMock()
sys.modules['google.antigravity.utils'] = MagicMock()
sys.modules['google.antigravity.triggers'] = MagicMock()
sys.modules['google.antigravity.mcp'] = MagicMock()

# Re-configure hooks to avoid type errors since some scripts inherit from it directly
class DummyHook:
    async def pre_generation(self, context, prompt): return prompt
    async def post_tool_call(self, context, tool_name, tool_args, tool_result): return tool_result
    async def run(self, context, data): return None

class DummyHooksModule:
    PostToolCallHook = DummyHook

sys.modules['google.antigravity.hooks'].hooks = DummyHooksModule
sys.modules['google.antigravity.hooks'].PostToolCallHook = DummyHook

# -----------------------------------------------------------------------------
# 2. Test Cases
# -----------------------------------------------------------------------------

def load_module_from_file(module_name, filepath):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class TestAntigravityDemos(unittest.IsolatedAsyncioTestCase):
    
    async def test_single_and_multi_agent(self):
        mod = load_module_from_file("m_single_and_multi_agent", os.path.join(base_dir, "1_single_and_multi_agent.py"))
        await mod.main()

    async def test_memory_types(self):
        mod = load_module_from_file("m_memory_types", os.path.join(base_dir, "2_memory_types.py"))
        # Memory types script iterates through agent.conversation.history
        mock_agent_instance.conversation = MagicMock()
        mock_agent_instance.conversation.history = []
        await mod.main()

    async def test_guardrails(self):
        mod = load_module_from_file("m_guardrails", os.path.join(base_dir, "3_guardrails.py"))
        await mod.main()

    async def test_hooks(self):
        mod = load_module_from_file("m_hooks", os.path.join(base_dir, "4_hooks.py"))
        await mod.main()

    async def test_triggers(self):
        mod = load_module_from_file("m_triggers", os.path.join(base_dir, "6_triggers.py"))
        # The demo waits for 6 seconds, we can patch asyncio.sleep to run fast to avoid slowing down tests
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await mod.main()
            
    async def test_mcp_docker_gateway(self):
        mod = load_module_from_file("m_mcp_docker_gateway", os.path.join(base_dir, "7_mcp_docker_gateway.py"))
        await mod.main()

    async def test_parallel_subagents(self):
        mod = load_module_from_file("m_parallel_subagents", os.path.join(base_dir, "8_parallel_subagents.py"))
        await mod.main()
        
    async def test_human_in_the_loop(self):
        mod = load_module_from_file("m_human_in_the_loop", os.path.join(base_dir, "9_human_in_the_loop.py"))
        await mod.main()

if __name__ == '__main__':
    unittest.main()
