# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import google.auth

from google.cloud import discoveryengine_v1
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools import ToolContext, FunctionTool
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Client injects a bearer token into the ToolContext state.
# The key pattern is "CLIENT_AUTH_NAME_<random_digits>".
# We dynamically parse this token to authenticate our MCP and API calls.
CLIENT_AUTH_NAME = "enterprise-ai"

def get_project_id():
    """Fetches the consumer project ID from the environment natively."""
    _, project = google.auth.default()
    return project

def find_serving_config_path():
    """Dynamically finds the default serving config in the engine."""
    project_id = get_project_id()
    engines = discoveryengine_v1.EngineServiceClient().list_engines(
        parent=f"projects/{project_id}/locations/global/collections/default_collection"
    )
    return f"{list(engines)[0].name}/servingConfigs/default_serving_config"

def _get_access_token_from_context(tool_context: ToolContext) -> str:
    """Helper method to dynamically parse the intercepted bearer token from the context state."""
    pattern = re.compile(fr"^{re.escape(CLIENT_AUTH_NAME)}_\d+$")
    # Handle ADK varying state object types (Raw Dict vs ADK State)
    state_dict = tool_context.state.to_dict() if hasattr(tool_context.state, 'to_dict') else tool_context.state
    matching_keys = [k for k in state_dict.keys() if pattern.match(k)]
    return state_dict.get(matching_keys[0])

def auth_header_provider(tool_context: ToolContext) -> dict[str, str]:
    token = _get_access_token_from_context(tool_context)
    return {"Authorization": f"Bearer {token}"}

def create_calendar_event(start_date: str, end_date: str, title: str, attendees: list[str], tool_context: ToolContext) -> dict:
    """Creates a Google Calendar event."""
    creds = Credentials(token=_get_access_token_from_context(tool_context))
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': title,
        'start': { 'dateTime': start_date },
        'end': { 'dateTime': end_date },
        'attendees': [{'email': email} for email in attendees],
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return {"status": "success", "event_id": event.get('id'), "link": event.get('htmlLink')}

vertexai_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://discoveryengine.googleapis.com/mcp",
        timeout=30.0,
        sse_read_timeout=30.0
    ),
    tool_filter=['search'],
    # The auth_header_provider dynamically injects the bearer token.
    header_provider=auth_header_provider
)

# Answer nicely the following user queries:
#  - Please find my meetings for today, I need their titles and links
#  - What is the latest Drive file I created?
#  - What is the latest Gmail message I received?
#  - Please schedule a meeting with someone@example.com tomorrow between 10am and 11am ET.

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name='enterprise_ai',
    instruction=f"""
        You are a helpful assistant that always uses the Vertex AI MCP search tool to answer the user's message, unless the user asks you to create a calendar event.
        If the user asks you to create a calendar event, use the create_calendar_event tool.
        You MUST unconditionally use the Vertex AI MCP search tool to find answer, even if you believe you already know the answer or believe the Vertex AI MCP search tool does not contain the data.
        The Vertex AI MCP search tool accesses the user's data through datastores including Google Drive, Google Calendar, and Gmail.
        Only use the Vertex AI MCP search tool with servingConfig and query parameters, do not use any other parameters.
        Always use the servingConfig {find_serving_config_path()} while using the Vertex AI MCP search tool.
    """,
    tools=[vertexai_mcp, FunctionTool(create_calendar_event)]
)
