# Enterprise AI Integrations

> **Note:** This project is part of an official Google Codelab ([link pending](#)).

This repository demonstrates two distinct integration patterns for Gemini Enterprise: building custom generative AI agents (Bring Your Own Agent) and integrating default Gemini Enterprise capabilities into Google Workspace.

## Project Structure

The project is divided into two independent directories, demonstrating different implementation concepts:

*   **`agent/`**: Demonstrates the "Bring Your Own Agent" (BYO) paradigm using the Agent Development Kit (ADK). It contains the backend Python architecture, tool definitions, and deployment scripts for configuring and pushing a custom Conversational Generative AI Model to the Google Cloud Vertex AI Reasoning Engine.
*   **`add-on/`**: Demonstrates how to build a Google Apps Script Workspace Add-on to interact with Gemini Enterprise natively. **Note:** This Add-on requests and interacts with the *default* Gemini Enterprise Agent (via the Reasoning Engine API), *not* the custom ADK agent defined in the neighboring `agent/` folder. It provides native integrations for the generic default agent across Gmail sidebars and Google Chat.

## Deployment

Refer to the respective internal `README.md` files located in the `agent/` and `add-on/` directories for precise setup variables and publishing instructions tailored to each integration.
