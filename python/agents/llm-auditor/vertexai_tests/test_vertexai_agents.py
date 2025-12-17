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

"""Deployment script for LLM Auditor."""

import os
import uuid
import asyncio

from dotenv import load_dotenv
import vertexai
from google.genai import types
from a2a.types import ( Part, Task )

load_dotenv()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")
reasoning_engine_id = os.getenv("REASONING_ENGINE_ID", "2201330030947074048")

print(f"PROJECT: {project_id}")
print(f"LOCATION: {location}")
print(f"REASONING ENGINE ID: {reasoning_engine_id}")
    
RESOURCE_NAME = f"projects/{project_id}/locations/{location}/reasoningEngines/{reasoning_engine_id}"

client = vertexai.Client(
    project=project_id,
    location=location,
    # http_options=types.HttpOptions(
    #     api_version="v1beta1",
        # base_url=f"https://{location}-aiplatform.googleapis.com/"
    # )
)

remote_agent = client.agent_engines.get(name=RESOURCE_NAME)

# print(remote_agent)
print("Reasoning Engine Name: " + remote_agent.api_resource.name)

message_data = {
  "messageId": str(uuid.uuid4().hex),
  "role": "user",
  "parts": [{"kind": "text", "text": "The last F1 winner is Alonso"}],
}

# response = asyncio.run(remote_agent.on_message_send(**message_data))
# print(response)

# task: Task = response[0][0]
# print(task.artifacts[0].parts[0].root.text)

# task_data = { "id": str(task.id) }
# response = asyncio.run(remote_agent.on_get_task(**task_data))
# print(response)

async def async_a2a_ai_agent():

    # Invoke the agent
    response = await remote_agent.on_message_send(**message_data)

    # The response contains a Task object with status and ID
    task_object = None
    for chunk in response:
        # Assuming the first chunk contains the task object
        if isinstance(chunk, tuple) and len(chunk) > 0 and hasattr(chunk[0], 'id'):
            task_object = chunk[0]
            break

    # Get the task id
    print(task_object)
    task_id = task_object.id

    # Get the task result
    task_data = {
        "id": task_id,
        # "historyLength": 1, # Include conversation history
    }
    result = await remote_agent.on_get_task(
        **task_data
    )

    # Artifacts contain the actual results
    for artifact in result.artifacts:
        # Access the text through the 'root' attribute of the Part object
        if artifact.parts and hasattr(artifact.parts[0], 'root') and hasattr(artifact.parts[0].root, 'text'):
            print(f"**Answer**:\n {artifact.parts[0].root.text}")
        else:
            print("Could not extract text from artifact parts.")

    # Answer: Rome is the capital of Italy...

asyncio.run(async_a2a_ai_agent())
