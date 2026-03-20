import json
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from due_date import DueDate

# Load environment variable and config
load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
SEEN_CALENDAR_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seen_calendar.json")
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json")

# Validate environment variable
if not CALENDAR_ID:
    raise EnvironmentError("GOOGLE_CALENDAR_ID is not set in .env")

# Initialize Google Calendar API client
def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def load_seen_calendar() -> set:
    if os.path.exists(SEEN_CALENDAR_FILE):
        with open(SEEN_CALENDAR_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_calendar(seen: set):
    with open(SEEN_CALENDAR_FILE, "w") as f:
        json.dump(list(seen), f)

# Add new due dates to Google Calendar, avoiding duplicates.
def add_to_calendar(due_dates: list[DueDate]):
    service = get_calendar_service()
    seen = load_seen_calendar()
    new_additions = False

    for d in due_dates:
        calendar_seen_key = f"{d.source}: {d.course}: {d.title}"
        if calendar_seen_key not in seen:

            # Create a calendar event from  due_date object
            event = {
                "summary": f"[{d.source}] {d.title}",
                "location": d.course,
                "description": f"Source: {d.source}\nCourse: {d.course}\nType: {d.event_type}\n\n{d.description}",
                "start": {
                    "dateTime": d.due_date.isoformat(),
                    "timeZone": "America/New_York"
                },
                "end": {
                    "dateTime": d.due_date.isoformat(),
                    "timeZone": "America/New_York"
                }
            }

            # Add event to calendar and mark as seen. If it fails, print an error but continue with the next event.
            try:
                service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                new_additions = True
                seen.add(calendar_seen_key)
                print(f"Added to calendar: {d.title}")
            except Exception as e:
                print(f"Failed to add {d.title}: {e}")
    if new_additions:
        save_seen_calendar(seen)

