from datetime import datetime
from zoneinfo import ZoneInfo
from brightspace_parser import parse_brightspace_duedates
from autolab_parser import parse_autolab_duedates
from calendar_sync import add_to_calendar
from text_message import send_text
from tophat_parser import parse_tophat_duedates
from ubx_parser import parse_ubx_duedates
from due_date import DueDate


def fetch_all_due_dates() -> list[DueDate]:
    due_dates = []

    for name, parser in [
        ("Brightspace", parse_brightspace_duedates),
        ("Autolab", parse_autolab_duedates),
        ("TopHat", parse_tophat_duedates),
        ("UBX", parse_ubx_duedates),
    ]:
        try:
            print(f"Fetching {name}...")
            due_dates += parser()
        except Exception as e:
            print(f"Failed to fetch {name}: {e}")

    return due_dates

    

if __name__ == "__main__":
    now = datetime.now(ZoneInfo("America/New_York"))
    print(f"Running at {now.strftime('%Y-%m-%d %I:%M %p')}")

    due_dates = fetch_all_due_dates()
    print(f"Found {len(due_dates)} upcoming due dates")

    send_text(due_dates)
    add_to_calendar(due_dates)