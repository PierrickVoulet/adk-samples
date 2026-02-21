import os
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_toolset import StreamableHTTPConnectionParams

from dotenv import load_dotenv

load_dotenv()

vertexai_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://discoveryengine.googleapis.com/mcp",
        headers={'Authorization': 'Bearer ' + os.getenv('GOOGLE_ACCESS_TOKEN')}
    ),
    tool_filter=['search']
)

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='vertexai_mcp_agent',
    instruction="""
        You are a helpful assistant that always
        use the Vertex AI MCP search tool to answer the user's query.
        Always use the servingConfig """ + os.getenv("VERTEXAI_SERVING_CONFIG"),
    tools=[vertexai_mcp]
)
