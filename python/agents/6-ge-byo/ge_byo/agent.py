from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools import ToolContext

def auth_header_provider(context: ToolContext) -> dict[str, str]:
    """
    Dynamically injects the bearer token from the session state at runtime.
    Gemini Enterprise injects the token into context.state["codelab"].
    """
    access_token = context.state.get("codelab")
    if not access_token:
        # Fallback or error if missing
        access_token = "mock-token"
    return {"Authorization": f"Bearer {access_token}"}

# Initialize toolset once, injecting headers dynamically via header_provider
vertexai_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://discoveryengine.googleapis.com/mcp"
    ),
    tool_filter=['search'],
    header_provider=auth_header_provider
)

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='ge_byo',
    instruction="""
        You are a helpful assistant that always
        use the Vertex AI MCP search tool to answer the user's query even if it seems impossible to get an answer.
        Always use the servingConfig projects/626210666927/locations/global/collections/default_collection/engines/codelab_1771524014204/servingConfigs/default_serving_config""",
    tools=[vertexai_mcp]
)
