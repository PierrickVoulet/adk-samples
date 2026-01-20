import datetime
import os.path
import re
import base64
from dateutil import parser as dateutil_parser
import dateparser
import pytz
from tzlocal import get_localzone
from typing import Optional, List, Dict
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.adk.agents import LlmAgent
from google.genai import types

from . import prompt

MODEL = "gemini-2.5-flash"

CREDENTIALS_FILE = "credentials.json"
TOKEN = "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        except (UnicodeDecodeError, ValueError):
            print("Warning: 'token.json' is invalid or has an encoding issue. Attempting to re-authorize.")
            os.remove(TOKEN)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        except (UnicodeDecodeError, ValueError):
            print("Warning: 'token.json' is invalid or has an encoding issue. Attempting to re-authorize.")
            os.remove(TOKEN)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def get_user_timezone() -> str:
    """
    Detect the user's local time zone. Falls back to 'America/New_York' if detection fails.
    """
    try:
        return str(get_localzone())
    except Exception as e:
        print(f"Warning: Could not detect local time zone ({str(e)}). Falling back to 'America/New_York'.")
        return "America/New_York"

def parse_natural_language_datetime(datetime_string: str, duration: Optional[str] = None, time_preference: Optional[str] = None) -> tuple[str, str, Optional[tuple[datetime.time, datetime.time]]]:
    """
    Parses a natural language date/time string in the user's local time zone
    and returns start and end times in ISO 8601 UTC format, plus optional time window.

    Args:
        datetime_string: Natural language input (e.g., "next Friday at 11 AM").
        duration: Optional duration (e.g., "1 hour", "for 30 minutes").
        time_preference: Optional preference (e.g., "morning", "9 AM to 2 PM").

    Returns:
        Tuple of (start_datetime, end_datetime, time_window) in ISO 8601 UTC and optional (start_time, end_time).
    """
    user_timezone = get_user_timezone() # Get the user's local timezone
    settings = {
        'TIMEZONE': user_timezone, # Interpret ambiguous times relative to user's TZ
        'TO_TIMEZONE': 'UTC',      # Always convert final output to UTC for Google Calendar API
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future', # Prioritize future dates for ambiguous phrases (e.g., "Friday")
        'DATE_ORDER': 'DMY',           # Explicitly set preferred date order
        'STRICT_PARSING': False        # Allow some flexibility in parsing
    }

    time_window = None
    # 1. Handle Time Preferences (e.g., "morning", "9 AM to 2 PM")
    if time_preference:
        if time_preference.lower() in ["morning", "afternoon", "evening"]:
            time_ranges = {
                "morning": (datetime.time(9, 0), datetime.time(12, 0)),
                "afternoon": (datetime.time(12, 0), datetime.time(17, 0)),
                "evening": (datetime.time(17, 0), datetime.time(21, 0))
            }
            time_window = time_ranges.get(time_preference.lower())
        else:
            try:
                # Regex for "HH AM/PM to HH AM/PM"
                match = re.match(r'(\d+\s*(?:AM|PM|am|pm))\s*to\s*(\d+\s*(?:AM|PM|am|pm))', time_preference, re.IGNORECASE)
                if match:
                    start_str, end_str = match.groups()
                    start_time = dateutil_parser.parse(start_str).time()
                    end_time = dateutil_parser.parse(end_str).time()
                    time_window = (start_time, end_time)
            except ValueError:
                print(f"Could not parse time preference: {time_preference}")

    # 2. First attempt: Parse with dateparser
    parsed_datetime = dateparser.parse(
        datetime_string,
        languages=['en'],
        settings=settings
    )

    # 3. Fallback for "next [day]" patterns (e.g., "next Friday at 11 AM") if dateparser fails
    if not parsed_datetime:
        match = re.match(r'next\s+([a-zA-Z]+)(?:\s+at\s+(.+?))?(?:\s+(morning|afternoon|evening))?$', datetime_string, re.IGNORECASE)
        if match:
            day_name, time_part, period = match.groups()

            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            if day_name.lower() not in day_map:
                raise ValueError(f"Invalid day name: {day_name}")

            target_weekday = day_map[day_name.lower()]
            current_date = datetime.datetime.now(pytz.timezone(user_timezone))
            current_weekday = current_date.weekday()
            days_ahead = (target_weekday - current_weekday + 7) % 7 # Calculate days until next target weekday
            if days_ahead == 0: days_ahead = 7 # If target is today, get next week's
            target_date = current_date + datetime.timedelta(days=days_ahead)

            # Determine default hour based on period if no explicit time_part
            default_hour = 9
            if period:
                period_map = {'morning': 9, 'afternoon': 13, 'evening': 18}
                default_hour = period_map.get(period.lower(), 9)
                time_part = time_part or f"{default_hour}:00" # Use default period time if no specific time

            if time_part:
                try:
                    time_parsed = dateutil_parser.parse(time_part, fuzzy=True)
                    parsed_datetime = target_date.replace(
                        hour=time_parsed.hour, minute=time_parsed.minute, second=0, microsecond=0
                    )
                except ValueError:
                    raise ValueError(f"Could not parse time part: {time_part}")
            else:
                parsed_datetime = target_date.replace(hour=default_hour, minute=0, second=0, microsecond=0)

    # 4. Final Fallback: Try dateutil.parser for general fuzzy parsing
    if not parsed_datetime:
        try:
            parsed_datetime = dateutil_parser.parse(datetime_string, fuzzy=True)
            # Make the parsed datetime timezone-aware in the user's local timezone
            parsed_datetime = pytz.timezone(user_timezone).localize(parsed_datetime)
        except ValueError:
            raise ValueError(f"Could not parse date/time: {datetime_string}")

    # 5. Convert final parsed datetime to UTC for Google Calendar API
    parsed_datetime = parsed_datetime.astimezone(pytz.UTC)
    start_datetime_iso = parsed_datetime.isoformat().replace('+00:00', 'Z')

    # 6. Calculate end time based on duration or default
    if duration:
        duration_minutes = parse_duration(duration)
        end_datetime_iso = (parsed_datetime + datetime.timedelta(minutes=duration_minutes)).isoformat().replace('+00:00', 'Z')
    else:
        # Default to 1 hour if no duration specified
        end_datetime_iso = (parsed_datetime + datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z')

    return start_datetime_iso, end_datetime_iso, time_window

def parse_duration(duration: str) -> int:
    """
    Parse a duration string into minutes.
    
    Args:
        duration: Duration string (e.g., "30 minutes", "for 1 hour").
    
    Returns:
        Duration in minutes.
    
    Raises:
        ValueError: If duration cannot be parsed.
    """
    duration_match = re.match(r'(?:for\s+)?(\d+)\s*(hour|hours|minute|minutes)', duration, re.IGNORECASE)
    if duration_match:
        value, unit = duration_match.groups()
        value = int(value)
        return value * 60 if unit.lower().startswith('hour') else value
    raise ValueError(f"Could not parse duration: {duration}")

def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    location: str = "",
    description: str = "",
    recurrence: Optional[str] = None,
    attendees: Optional[List[Dict[str, str]]] = None
):
    user_timezone = get_user_timezone()
    service = get_calendar_service()
    event = {
        "summary": summary,
        "start": {"dateTime": start_datetime, "timeZone": user_timezone},
        "end": {"dateTime": end_datetime, "timeZone": user_timezone},
    }

    if location and location.strip() != "":
        event["location"] = location
    if description and description.strip() != "":
        event["description"] = description
    if recurrence:
        event["recurrence"] = [recurrence]
    if attendees:
        event["attendees"] = attendees

    try:
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"Event created: {created.get('htmlLink')}"
    except HttpError as error:
        raise ValueError(f"Failed to create event: {str(error)}")

def get_latest_email():
    service = get_gmail_service()
    try:
        # Fetch the latest email
        results = service.users().messages().list(userId="me", q='label:inbox', maxResults=1).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No emails found."
        message = service.users().messages().get(userId="me", id=messages[0]["id"]).execute()
        return message
    except HttpError as error:
        raise ValueError(f"Failed to fetch email: {str(error)}")

def send_email_reply(
    user_email: str,
    original_email_recipient: str,
    original_email_subject: str,
    reply_body: str
):
    service = get_gmail_service()
    try:
        # Send the reply
        message = EmailMessage()
        message["From"] = user_email
        message["To"] = original_email_recipient
        message["Subject"] = f"RE: {original_email_subject}"
        message.set_content(reply_body)

        service.users().messages().send(
            userId="me",
            body={
                "raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            }
        ).execute()
        return f"Email reply sent successfully."
    except HttpError as error:
        raise ValueError(f"Failed to send email reply: {str(error)}")

root_agent = LlmAgent(
    model=MODEL,
    name='root_agent',
    instruction=prompt.ROOT_AGENT_PROMPT,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=[create_event, parse_natural_language_datetime, get_latest_email, send_email_reply],
)
