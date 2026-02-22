# Enterprise AI Agent (built as Gemini Enterprise BYO Agent)

This repository contains a specialized Gemini Enterprise Agent built using the Google Agent Development Kit (ADK). The primary objective of this agent is to act as an Enterprise AI Assistant by querying your organization's data corpus using the Vertex AI Search MCP toolset.

## Key Features

1. **Dynamic Vertex AI Serving Configs:** 
   The agent automatically discovers your project's `default_collection` engine and dynamically binds its queries to the `default_serving_config`.
   
2. **Dynamic Authentication (`ToolContext`):** 
   When deployed as a Bring-Your-Own (BYO) model via Gemini Enterprise, the session state dynamically passes an authentication token (e.g., `enteprise-ai_12345`). This agent intercepts the `ToolContext` state and extracts the token at runtime using regex pattern matching (`^enteprise-ai_\d+$`) to securely execute calls using a Bearer token.

3. **Graceful Timeouts:**
   The `McpToolset` streaming components have been intentionally configured with an explicit 15-second `timeout` and `sse_read_timeout` to prevent the agent from hanging infinitely on backend network issues.

4. **Google Chat Integration:**
   The agent natively includes a `send_direct_message` tool powered by the `google-apps-chat` SDK. This allows the AI to immediately send direct messages to Workspace users inside Google Chat. It seamlessly reuses the same authentication token extracted from the `ToolContext` used for Vertex AI.

## Deployment

This agent is designed exclusively to be deployed as a backend for a Gemini Enterprise (GE) Bring-Your-Own (BYO) Agent. It **will not** work successfully if tested locally via standard ADK run commands because it relies entirely on the external GE gateway to dynamically inject OAuth tokens into the `ToolContext` at runtime.

This code is part of a complete tutorial on integrating custom MCP servers. For full instructions on how to set up the GE environment, provision authentication, and link this custom agent to the frontend, refer to the [official tutorial guide here (link pending...)](#).

Deploy this agent directly to Vertex AI Agent Engines using the ADK CLI:

```bash
adk deploy agent_engine \
  --project=your-gcp-project-id \
  --region=us-central1 \
  --display_name="Enterprise AI" \
  --trace_to_cloud \
  --otel_to_cloud \
  enterprise_ai
```
