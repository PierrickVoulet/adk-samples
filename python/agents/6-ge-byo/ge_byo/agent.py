import sys
import logging
import types
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

AUTH_ID = "codelab_1771649435557"

def auth_header_provider(context: ToolContext) -> dict[str, str]:
    # Debug: Print the entire ToolContext and InvocationContext to see what's available
    logger.info(f"DEBUG ToolContext State: {context.state}")
    
    if getattr(context, '_invocation_context', None):
        inv_ctx = context._invocation_context
        logger.info(f"DEBUG InvocationContext dict: {getattr(inv_ctx, '__dict__', None)}")
        logger.info(f"DEBUG InvocationContext class fields: {dir(inv_ctx)}")
        if getattr(inv_ctx, 'session', None):
             logger.info(f"DEBUG Session dict: {getattr(inv_ctx.session, '__dict__', None)}")

    access_token = context.state.get(AUTH_ID)
    if not access_token:
        logger.warning(f"No bearer token found in ToolContext state. Falling back to mock-token.")
        access_token = "mock-token"
    else:
        logger.info("Successfully injected bearer token from ToolContext state.")
    return {"Authorization": f"Bearer {access_token}"}

class SafeMcpToolset(McpToolset):
    """
    Subclass McpToolset to catch 401 errors during tool execution so they
    return as a clean string to the LLM without crashing or hanging the agent.
    """
    async def get_tools(self, readonly_context=None):
        try:
            tools = await super().get_tools(readonly_context)
        except Exception as e:
            err_str = str(e)
            if '401' in err_str or 'Unauthorized' in err_str:
                logger.error(f"401 Unauthorized during get_tools: {err_str}")
            # If we fail to get tools, we must raise so the user knows.
            raise e

        # Wrap the tools run_async to catch 401s and other connection errors
        for t in tools:
            orig_run = t.run_async
            async def safe_run(self_tool, *args, **kwargs):
                try:
                    return await orig_run(*args, **kwargs)
                except Exception as ex:
                    err_str = str(ex)
                    if '401' in err_str or 'Unauthorized' in err_str:
                        return {"error": "401 Unauthorized: The provided token is invalid or expired."}
                    return {"error": f"Tool execution failed: {err_str}"}
            t.run_async = types.MethodType(safe_run, t)
            
        return tools

# Note: We set both timeout (connection timeout) and sse_read_timeout to 15.0 seconds
# to prevent the agent from hanging for up to 3000 seconds when calling the search tool.
vertexai_mcp = SafeMcpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://discoveryengine.googleapis.com/mcp",
        timeout=15.0,
        sse_read_timeout=15.0
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
