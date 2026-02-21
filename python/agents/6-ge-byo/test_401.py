import asyncio
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

class MockContext:
    def __init__(self):
        self._invocation_context = None
        self.state = {"codelab": "mock"}

async def main():
    ctx = MockContext()
    
    mcp = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="http://localhost:8888/mcp",
            timeout=15.0,
            sse_read_timeout=15.0
        ),
        tool_filter=['search']
    )
    
    try:
        tools = await mcp.get_tools(readonly_context=ctx)
        print("Got tools:", tools)
    except Exception as e:
        print("Exception caught in get_tools:", type(e), e)

if __name__ == '__main__':
    asyncio.run(main())
