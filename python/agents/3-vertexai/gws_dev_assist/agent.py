from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools import agent_tool
from google.adk.tools.google_search_tool import GoogleSearchTool

gws_developer_assistant_google_search_agent = LlmAgent(
  name='GWS_Developer_Assistant_google_search_agent',
  model='gemini-2.5-flash',
  description=(
      'Agent specialized in performing Google searches.'
  ),
  sub_agents=[],
  instruction='Use the GoogleSearchTool to find information on the web.',
  tools=[
    GoogleSearchTool()
  ],
)
root_agent = LlmAgent(
  name='GWS_Developer_Assistant',
  model='gemini-2.5-flash',
  description=(
      'Answer questions from GWS developers'
  ),
  sub_agents=[],
  instruction='1. Use the Google Search tool to answer any generic question about Google Workspace platform and development\n2. Use the GWS Dev Assist tools when the user requests really specific information about an API or scope\n3. Reply with follow questions if the question cannot be easily answered',
  tools=[
    agent_tool.AgentTool(agent=gws_developer_assistant_google_search_agent),
    McpToolset(
      connection_params=StreamableHTTPConnectionParams(
        url='https://workspace-developer.goog/mcp',
      ),
    )
  ],
)
