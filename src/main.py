from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
from brightspace_parser import parse_brightspace_duedates
from autolab_parser import parse_autolab_duedates
from calendar_sync import add_to_calendar
from text_message import send_text
from tophat_parser import parse_tophat_duedates
from ubx_parser import parse_ubx_duedates
from due_date import DueDate

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    config = json.load(f)

def fetch_all_due_dates() -> list[DueDate]:
    due_dates = []

    print(f"Fetching Brightspace...")
    try:
        due_dates += parse_brightspace_duedates()
    except Exception as e:
        print(f"Failed to fetch Brightspace due dates: {e}")

    print(f"Fetching Autolab...")
    if config["autolab_courses"]:
        try:
            due_dates += parse_autolab_duedates()
        except Exception as e:
            print(f"Failed to fetch Autolab due dates: {e}")    
    else:
        print("No Autolab courses configured, skipping...")

    print(f"Fetching TopHat...")
    if config["tophat_courses"]:
        try:
            due_dates += parse_tophat_duedates()
        except Exception as e:
            print(f"Failed to fetch TopHat due dates: {e}")
    else:
        print("No TopHat courses configured, skipping...")

    print(f"Fetching UBX...")
    if config["ubx_courses"]:
        try:
            due_dates += parse_ubx_duedates()
        except Exception as e:
            print(f"Failed to fetch UBX due dates: {e}")
    else:
        print("No UBX courses configured, skipping...")

    return due_dates

    

if __name__ == "__main__":
    now = datetime.now(ZoneInfo("America/New_York"))
    print(f"Running at {now.strftime('%Y-%m-%d %I:%M %p')}")

    due_dates = fetch_all_due_dates()
    print(f"Found {len(due_dates)} upcoming due dates")
    for due_date in due_dates:
        print(f"{due_date.course} - {due_date.title} - {due_date.due_date.strftime('%Y-%m-%d %I:%M %p')}")

    send_text(due_dates)
    add_to_calendar(due_dates)