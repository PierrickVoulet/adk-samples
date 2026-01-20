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

"""Enterprise Search agent."""

from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool

# Configuration
DATASTORE_NAME = "projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATASTORE_ID}"

root_agent = Agent(
    name="enteprise_search",
    model="gemini-2.5-flash",
    tools=[VertexAiSearchTool(data_store_id=DATASTORE_NAME)],
    instruction=f"""You are a helpful assistant that answers questions based on information found in the Vertex AI Search datastore: {DATASTORE_NAME}.
    Use the Vertex AI Search tool to find relevant information before answering.
    If the answer isn't in the emails, say that you couldn't find the information.
    """,
    description="Answers questions using a specific Vertex AI Search datastore.",
)
