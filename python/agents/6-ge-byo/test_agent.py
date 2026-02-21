import unittest
import asyncio
from unittest.mock import patch, MagicMock

from ge_byo.agent import vertexai_mcp, auth_header_provider

class MockContext:
    def __init__(self, token=None):
        self.state = {}
        if token:
            self.state["codelab"] = token

class TestAgentTokenInjection(unittest.IsolatedAsyncioTestCase):

    def test_auth_header_provider_with_token(self):
        context = MockContext(token="valid-token-123")
        headers = auth_header_provider(context)
        self.assertEqual(headers["Authorization"], "Bearer valid-token-123")

    def test_auth_header_provider_without_token(self):
        context = MockContext()
        headers = auth_header_provider(context)
        self.assertEqual(headers["Authorization"], "Bearer mock-token")

    async def test_mcp_toolset_uses_header_provider(self):
        context = MockContext(token="dynamic-test-token-456")
        
        class AsyncMock(MagicMock):
            async def __call__(self, *args, **kwargs):
                return super(AsyncMock, self).__call__(*args, **kwargs)

        with patch.object(vertexai_mcp._mcp_session_manager, 'create_session', new_callable=AsyncMock) as mock_create_session:
            mock_session_instance = MagicMock()
            mock_session_instance.list_tools = AsyncMock(return_value=MagicMock(tools=[]))
            mock_create_session.return_value = mock_session_instance
            
            await vertexai_mcp.get_tools(readonly_context=context)
            
            mock_create_session.assert_called_once()
            call_kwargs = mock_create_session.call_args.kwargs
            headers = call_kwargs.get('headers')
            
            self.assertIsNotNone(headers, "Headers should be passed to create_session")
            self.assertEqual(headers.get("Authorization"), "Bearer dynamic-test-token-456")

if __name__ == '__main__':
    unittest.main()
