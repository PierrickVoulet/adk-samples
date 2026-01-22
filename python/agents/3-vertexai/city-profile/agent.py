from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools.google_search_tool import GoogleSearchTool

city_profile_google_search_agent = LlmAgent(
  name='City_profile_google_search_agent',
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
  name='City_profile',
  model='gemini-2.5-flash',
  description=(
      'Provides city information'
  ),
  sub_agents=[],
  instruction='1. Identify the city the user is requesting the profile for\n2. Use Google Search to retrieve the name, country, and a valid image of their most famous landmark\n3. Return the results as a single JSON with fields \"name\", \"country\", and \"imageUrl\"',
  tools=[
    agent_tool.AgentTool(agent=city_profile_google_search_agent)
  ],
)
