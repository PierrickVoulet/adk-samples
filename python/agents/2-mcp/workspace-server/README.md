# Google Workspace MCP Server

An MCP server implementation that provides tools for interacting with Google Workspace services (Docs, Drive, Calendar, Gmail, etc.) using the [Model Context Protocol](https://modelcontextprotocol.io/).

## Prerequisites

Before running the server, you need a Google Cloud Project with the necessary APIs enabled and an OAuth2 Client ID.

1.  **Create a Google Cloud Project**.
2.  **Enable the following APIs**:
    *   Google Docs API
    *   Google Drive API
    *   Google Calendar API
    *   Gmail API
    *   Google Slides API
    *   Google Sheets API
    *   Google People API
3.  **Create OAuth 2.0 Credentials**:
    *   Go to "APIs & Services" > "Credentials".
    *   Create "OAuth client ID".
    *   Select "Desktop app".
    *   Download the JSON file and rename it to `credentials.json`.

## Usage

### Via npx

To run the server directly using `npx`, make sure your `credentials.json` file is in the current directory:

```bash
# 1. Place credentials.json in your current folder
# 2. Run the server
npx workspace-server
```

### Local Development

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Build the project**:
    ```bash
    npm run build
    ```

3.  **Start the server**:
    ```bash
    # Ensure credentials.json is in the project root
    npm start
    ```

## Authentication

When you run the server for the first time, it will:
1.  Look for `credentials.json` in the current directory (or project root).
2.  Open a browser window prompting you to log in with your Google account.
3.  After login, store the authentication tokens locally in `token.json`.

Subsequent runs will use the stored tokens.
