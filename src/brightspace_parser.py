import os
import json
import requests
from dotenv import load_dotenv
from datetime import date, datetime, timezone, timedelta
from icalendar import Calendar
from due_date import DueDate
from zoneinfo import ZoneInfo

import due_date

load_dotenv(r"C:\Users\bryce\VsCodeProjects\Course_Sync_Calender\.env")
Brightspace_Url = os.getenv('BRIGHTSPACE_CALENDAR_URL')
SEEN_FILE = "seen_events.json"
    
def from_ical_component(component,due_date) -> 'DueDate':
        title = component.get('SUMMARY')
        course = component.get('LOCATION') or 'Unknown Course'
        description = component.get('DESCRIPTION') or ''
        if "quiz" in title.lower():
            event_type = "quiz"
        elif "lab" in title.lower():
            event_type = "lab"
        else:
            event_type = "assignment"
        source = 'Brightspace'
        due_date = due_date.astimezone(ZoneInfo("America/New_York"))        
        return DueDate(title, due_date, course, event_type, description, source)

def load_seen_ids() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_ids(ids: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(ids), f)

def parse_to_duedate() -> list[DueDate]:
    calendar_data = Calendar.from_ical(requests.get(Brightspace_Url).content)
    dueDates = []
    seen_uids = load_seen_ids()

    for component in calendar_data.walk():
        if component.name == "VEVENT":
            due_date = component.get('DTSTART').dt
            if isinstance(due_date, date) and not isinstance(due_date, datetime):
                due_date = datetime(due_date.year, due_date.month, due_date.day, tzinfo=timezone.utc)
            if due_date >= datetime.now(timezone.utc):
                uid = str(component.get('UID'))
                if uid not in seen_uids:
                    seen_uids.add(uid)
                    dueDates.append(from_ical_component(component,due_date))
    save_seen_ids(seen_uids)

    return dueDates


