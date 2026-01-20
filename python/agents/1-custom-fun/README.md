# Custom Func

Dev assistant that integrates custom workflow with GWS steps

# **Prerequisites**

* Python 3.10+  
* A Google Cloud project

# Google Cloud Project Setup

1. **Enable APIs:** In your Google Cloud project, enable the ["Gmail"](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
   & ["Calendar"](https://console.cloud.google.com/apis/library/calendar.googleapis.com) APIs.  
1. **Configure OAuth Consent Screen:** Go to [APIs & Services > OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).  
   * Select **Internal** and create the screen.
1. **Create OAuth 2.0 Credentials:**  
   * Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials).  
   * Click **Create Credentials** > **OAuth 2.0 Client ID**.  
   * Select **Desktop Application** for the application type.  
   * Click **Create**.  
   * Download and save the file as `credentials.json` in your project folder.
1. Create [Gemini API key from Google AI Studio](https://aistudio-preprod.corp.google.com/app/api-keys) and associate it to the Google Cloud Project.

# Set Environment Variables

Create a file named `.env` in the `local_assist` directory based on the `.env.example` template and set the Gemini API key.

```
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=<YOUR_GOOGLE_API_KEY>
```

# Install

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run dev session from anywhere in local

adk run /path/to/local_assist
