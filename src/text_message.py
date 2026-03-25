import json
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from due_date import DueDate

# Load environment variables and config
load_dotenv()
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    config = json.load(f)
CARRIER_GATEWAY = config["carrier_gateway"]

# Validate environment variables and config
if not GMAIL_ADDRESS:
    raise EnvironmentError("GMAIL_ADDRESS is not set in .env")
if not GMAIL_APP_PASSWORD:
    raise EnvironmentError("GMAIL_APP_PASSWORD is not set in .env")
if not PHONE_NUMBER:
    raise EnvironmentError("PHONE_NUMBER is not set in .env")
if not CARRIER_GATEWAY:
    raise ValueError("carrier_gateway is not set in config.json")

# Format a DueDate object into a string for the text message
def format_due_date(d: DueDate) -> str:
    time = d.due_date.strftime("%I:%M %p").lstrip("0")
    return f"• {d.title} ({d.course}) at {time}\n"

# Format the list of due dates into a message string, grouping by due today and upcoming in the next 7 days.
def format_message(due_dates: list[DueDate]) -> str:
    now = datetime.now(ZoneInfo("America/New_York"))
    today = now.date()
    in_7_days = today + timedelta(days=7)

    due_today = [d for d in due_dates if d.due_date.date() == today]
    upcoming = [d for d in due_dates if today < d.due_date.date() <= in_7_days]
    upcoming.sort(key=lambda d: d.due_date)

    lines = []
    lines.append(f"- Course Sync Summary -\n")

    lines.append("Due Today:\n")
    if due_today:
        for d in due_today:
            lines.append(format_due_date(d))
    else:
        lines.append("Nothing due today")

    lines.append("")
    lines.append("Upcoming (next 7 days):\n")
    if upcoming:
        for d in upcoming:
            date_str = d.due_date.strftime("%a, %b ") + str(d.due_date.day)
            time_str = d.due_date.strftime("%I:%M %p").lstrip("0")
            lines.append(f"• {d.title} ({d.course})")
            lines.append(f"  {date_str} at {time_str}\n")
    else:
        lines.append("Nothing upcoming")

    return "\n".join(lines)

# Use Gmail SMTP to send the email to the carrier gateway. Handle any exceptions and print an error message if sending fails.
def send_text(due_dates: list[DueDate]):
    message = format_message(due_dates)
    recipient = f"{PHONE_NUMBER}@{CARRIER_GATEWAY}"

    msg = MIMEText(message)
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = recipient
    msg['Subject'] = ""

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient, msg.as_string())
        print("Text sent successfully")
    except Exception as e:
        print(f"Failed to send text: {e}")