import unittest
import asyncio
from unittest.mock import patch, MagicMock

from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import ToolContext

from ge_byo.agent import vertexai_mcp

class MockContext:
    def __init__(self, token=None):
        self._invocation_context = None
        self.state = {}
        if token:
            self.state["codelab"] = token

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

class TestAgentTimeoutAnd401(unittest.IsolatedAsyncioTestCase):

    def test_timeout_configuration(self):
        # Verify that timeout parameters are set correctly
        params = vertexai_mcp._connection_params
        self.assertEqual(params.timeout, 15.0)
        self.assertEqual(params.sse_read_timeout, 15.0)

    async def test_tool_run_401_recovery(self):
        # We want to verify that run_async catches exceptions and returns the 401 error payload
        context = MockContext(token="invalid-token")
        
        # We patch mcp_toolset's get_tools to yield a pseudo-tool
        with patch('ge_byo.agent.McpToolset.get_tools', new_callable=AsyncMock) as mock_get_tools:
            
            # Create a mock tool that throws a 401 error
            class MockTool:
                def __init__(self):
                    self.name = "search"
                async def run_async(self, *args, **kwargs):
                    raise Exception("401 Unauthorized mock exception")

            mock_tool = MockTool()
            mock_get_tools.return_value = [mock_tool]
            
            tools = await vertexai_mcp.get_tools(readonly_context=context)
            self.assertEqual(len(tools), 1)
            
            tool = tools[0]
            # Since vertexai_mcp wraps run_async, calling it should not throw but return the {"error": ...} payload
            result = await tool.run_async()
            
            self.assertIn("error", result)
            self.assertTrue(result["error"].startswith("401 Unauthorized"))

if __name__ == '__main__':
    unittest.main()
