from dotenv import load_dotenv
load_dotenv()
# import asyncio
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools import ToolContext, FunctionTool

# class AuthenticatedMcpToolset(McpToolset):
#     """
#     Dynamically injects the bearer token from the session state.
#     """
#     def run(self, tool_name: str, args: dict, context: ToolContext):
#         try:
#             access_token = context.state["codelab"]
#             if not access_token:
#                 raise ValueError("No bearer token found in ToolContext state.")
#             self.connection_params.headers["Authorization"] = f"Bearer {access_token}"
#             return super().run(tool_name, args, context)
#         except Exception as e:
#             print(f"DEBUG: MCP Execution failed with: {str(e)}")
#             raise e

# # Initialize without a token (it will be injected at runtime)
# vertexai_mcp = AuthenticatedMcpToolset(
#     connection_params=StreamableHTTPConnectionParams(
#         url="https://discoveryengine.googleapis.com/mcp"
#     ),
#     tool_filter=['search']
# )

async def get_mcp_tools(tool_context: ToolContext):
    """
    Helper to fetch the token from the context and initialize the MCP toolset.
    Gemini Enterprise injects the token into tool_context.state[AUTH_ID]
    """
    access_token = tool_context.state.get("codelab") 
    if access_token is None:
        # raise ValueError("No bearer token found in ToolContext state for key 'codelab'")
        access_token = "mock-token"
    print(f"DEBUG: Initializing MCP Toolset with token: {access_token}")
    
    mcp_set = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://discoveryengine.googleapis.com/mcp",
            headers={'Authorization': 'Bearer ' + access_token}
        ),
        tool_filter=['search']
    )
    return await mcp_set.get_tools()

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='ge_byo',
    instruction="""
        You are a helpful assistant that always
        use the Vertex AI MCP search tool to answer the user's query even if it seems impossible to get an answer.
        Always use the servingConfig projects/626210666927/locations/global/collections/default_collection/engines/codelab_1771524014204/servingConfigs/default_serving_config""",
    # tools=[vertexai_mcp]
    tools=[get_mcp_tools]
)
