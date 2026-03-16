import os
import json
import requests
from dotenv import load_dotenv
from datetime import date, datetime
from icalendar import Calendar
from due_date import DueDate
from zoneinfo import ZoneInfo

load_dotenv()
BRIGHTSPACE_CALENDAR_URL = os.getenv('BRIGHTSPACE_CALENDAR_URL')
seen_file = "seen_brightspace.json"

if not BRIGHTSPACE_CALENDAR_URL:
    raise EnvironmentError("BRIGHTSPACE_CALENDAR_URL is not set in .env")
    
def from_ical_component(component,due_date) -> DueDate:
    title = component.get('SUMMARY')
    course = component.get('LOCATION') or "Unknown Course"
    description = component.get('DESCRIPTION') or ""
    if "quiz" in title.lower():
        event_type = "quiz"
    elif "lab" in title.lower():
        event_type = "lab"
    else:
        event_type = "assignment"
    source = "Brightspace"     
    return DueDate(title, due_date, course, event_type, description, source)

def load_seen_ids() -> set:
    if os.path.exists(seen_file):
        with open(seen_file) as f:
            return set(json.load(f))
    return set()

def save_seen_ids(ids: set):
    with open(seen_file, "w") as f:
        json.dump(list(ids), f)

def parse_brightspace_duedates() -> list[DueDate]:
    try:
        response = requests.get(BRIGHTSPACE_CALENDAR_URL, timeout=10)
        response.raise_for_status()
        calendar_data = Calendar.from_ical(response.content)
    except requests.RequestException as e:
        print(f"Failed to fetch calendar: {e}")
        return []
    

    due_dates = []
    seen_uids = load_seen_ids()
    date_now = datetime.now(ZoneInfo("America/New_York"))

    for component in calendar_data.walk():
        if component.name == "VEVENT":
            due_date = component.get('DTSTART').dt
            if isinstance(due_date, date) and not isinstance(due_date, datetime):
                due_date = datetime(due_date.year, due_date.month, due_date.day, 23, 59, 59, tzinfo=ZoneInfo("America/New_York"))
            else:
                due_date = due_date.astimezone(ZoneInfo("America/New_York"))
            if due_date >= date_now:
                uid = str(component.get('UID'))
                if uid not in seen_uids:
                    seen_uids.add(uid)
                    due_dates.append(from_ical_component(component,due_date))
    save_seen_ids(seen_uids)

    return due_dates


