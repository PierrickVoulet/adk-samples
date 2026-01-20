# Copyright 2025 Google LLC
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

"""GE GWS agent."""

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
import requests

# Configuration
BASE_URL="https://discoveryengine.googleapis.com"
# projects/ge-gws-agents/locations/global/collections/default_collection/engines/ge_1767795760677
ENGINE_NAME="projects/{PROJECT_ID}/locations/global/collections/default_collection/engines/{ENGINE_ID}"
# Extract ID from authorization resource name: projects/ge-gws-agents/locations/global/authorizations/{AUTH_ID}
# gws-search_1767842690338
AUTH_ID="YOUR_AUTH_ID"

def search(query: str, tool_context: ToolContext) -> str:
    access_token = tool_context.state[f"{AUTH_ID}"]
    engine_url = f"{BASE_URL}/v1alpha/{ENGINE_NAME}"
    url = f"{engine_url}/servingConfigs/default_search:search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json={
        "query": query,
        "pageSize": 2,
        "spellCorrectionSpec": {"mode": "AUTO"},
        "languageCode": "en-US",
        "relevanceScoreSpec": {"returnRelevanceScore": True},
        "userInfo": {"timeZone": "America/New_York"},
        "contentSearchSpec": {"snippetSpec": {"returnSnippet": True}},
        "naturalLanguageQueryUnderstandingSpec": {"filterExtractionCondition": "ENABLED"}
    }).json()
    return r

root_agent = LlmAgent(
    name="GwsSearchAgent",
    model="gemini-2.5-flash",
    instruction="Return search results in JSON format",
    description="Searches Google Workspace data from data stores",
    tools=[search]
)
