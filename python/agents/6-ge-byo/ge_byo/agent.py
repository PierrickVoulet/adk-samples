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
from dotenv import load_dotenv
load_dotenv()

from google.cloud import discoveryengine_v1
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools import ToolContext

MODEL = "gemini-2.5-flash"
VERTEXAI_MCP_AUTH_NAME = "vertexai-mcp"
VERTEXAI_SEARCH_TIMEOUT = 15.0

def get_project_id():
    """Fetches the consumer project ID from the environment natively."""
    _, project = google.auth.default()
    if project:
        return project
    raise Exception(f"Failed to resolve GCP Project ID from environment.")

def find_serving_config_path():
    """Dynamically finds the default serving config in the engine."""
    project_id = get_project_id()
    
    engines = discoveryengine_v1.EngineServiceClient().list_engines(
        parent=f"projects/{project_id}/locations/global/collections/default_collection"
    )
    for engine in engines:
        # engine.name natively contains the numeric Project Number
        return f"{engine.name}/servingConfigs/default_serving_config"
    raise Exception(f"No Discovery Engines found in project {project_id}")

def auth_header_provider(context: ToolContext) -> dict[str, str]:
    # Dynamically find the first key that matches VERTEXAI_MCP_AUTH_NAME_number (e.g., "vertexai-mcp_12345")
    escaped_name = re.escape(VERTEXAI_MCP_AUTH_NAME)
    pattern = re.compile(fr"^{escaped_name}_\d+$")
    matching_keys = [k for k in context.state.keys() if pattern.match(k)]
    if matching_keys:
        return {"Authorization": f"Bearer {context.state.get(matching_keys[0])}"}
    raise Exception(f"No bearer token found in ToolContext state matching pattern {pattern.pattern}")

vertexai_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://discoveryengine.googleapis.com/mcp",
        timeout=VERTEXAI_SEARCH_TIMEOUT,
        sse_read_timeout=VERTEXAI_SEARCH_TIMEOUT
    ),
    tool_filter=['search'],
    header_provider=auth_header_provider
)

# Answer nicely the following user queries:
#  - Please find my meetings for today, I need their titles and links
#  - What is the latest Drive file I created?
#  - What is the latest Gmail message I received?

root_agent = LlmAgent(
    model=MODEL,
    name='ge_byo',
    instruction=f"""
        You are a helpful assistant that always uses the Vertex AI MCP search tool to answer the user's message.
        You MUST unconditionally use the Vertex AI MCP search tool to find answer, even if you believe you already know the answer or believe the Vertex AI MCP search tool does not contain the data.
        The Vertex AI MCP search tool accesses the user's data through datastores including Google Drive, Google Calendar, and Gmail.
        Only use the Vertex AI MCP search tool with servingConfig and query parameters, do not use any other parameters.
        Always use the servingConfig {find_serving_config_path()} while using the Vertex AI MCP search tool.
    """,
    tools=[vertexai_mcp]
)
