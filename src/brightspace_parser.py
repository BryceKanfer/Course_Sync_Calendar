import os
import requests
from dotenv import load_dotenv
from datetime import date, datetime
from icalendar import Calendar
from due_date import DueDate
from zoneinfo import ZoneInfo

# Load environment variables
load_dotenv()
BRIGHTSPACE_CALENDAR_URL = os.getenv('BRIGHTSPACE_CALENDAR_URL')

# Validate environment variables
if not BRIGHTSPACE_CALENDAR_URL:
    raise EnvironmentError("BRIGHTSPACE_CALENDAR_URL is not set in .env")

# Convert an iCal component to a DueDate object    
def from_ical_component(component,due_date) -> DueDate:
    title = component.get('SUMMARY') or "Unknown Title"
    course = component.get('LOCATION') or "Unknown Course"
    description = component.get('DESCRIPTION') or ""
    if "quiz" in title.lower():
        event_type = "quiz"
    elif "lab" in title.lower():
        event_type = "lab"
    elif any(x in title.lower() for x in ("exam", "midterm", "final")):
        event_type = "exam"
    else:
        event_type = "assignment"
    source = "Brightspace"     
    return DueDate(title, due_date, course, event_type, description, source)

# Fetch the Brightspace calendar, parse it, and extract due dates. Return a list of DueDate objects.
def parse_brightspace_duedates() -> list[DueDate]:

    # Fetch calendar data from Brightspace and parse it using icalendar.
    try:
        response = requests.get(BRIGHTSPACE_CALENDAR_URL, timeout=10)
        response.raise_for_status()
        calendar_data = Calendar.from_ical(response.content)
    except requests.RequestException as e:
        print(f"Failed to fetch calendar: {e}")
        return []
    

    due_dates = []
    date_now = datetime.now(ZoneInfo("America/New_York"))

    for component in calendar_data.walk():
        if component.name == "VEVENT":
            due_date = component.get('DTSTART').dt

            # Skip events that are marked as "available" in the title, as these are not actual due dates
            title = component.get('SUMMARY') or ""
            if "available" in title.lower():
                continue
            
            # Convert date to datetime if it's a date, and ensure it's in the correct timezone
            if isinstance(due_date, date) and not isinstance(due_date, datetime):
                due_date = datetime(due_date.year, due_date.month, due_date.day, 23, 59, 59, tzinfo=ZoneInfo("America/New_York"))
            else:
                due_date = due_date.astimezone(ZoneInfo("America/New_York"))

            if due_date >= date_now:
                due_dates.append(from_ical_component(component,due_date))

    return due_dates


