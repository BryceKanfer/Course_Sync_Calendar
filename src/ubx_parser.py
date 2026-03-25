from datetime import datetime 
import json
import os
import re
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from due_date import DueDate

# Load environment variables and config
load_dotenv()
UBX_EMAIL = os.getenv('UBX_EMAIL')
UBX_PASSWORD = os.getenv('UBX_PASSWORD')
with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    config = json.load(f)
UBX_COURSES = config["ubx_courses"]

# Validate environment variables and config
if not UBX_EMAIL:
    raise EnvironmentError("UBX_EMAIL is not set in .env")
if not UBX_PASSWORD:
    raise EnvironmentError("UBX_PASSWORD is not set in .env")
if not UBX_COURSES:
    raise ValueError("ubx_courses list is empty. Please add course names to the list in config.json")

# Parse the text into datetime object using regex.
def parse_due_date(due_day: str, due_time: str) -> datetime | None:
    match = re.search(r'(\d{1,2}:\d{2} [AP]M)', due_time)
    if not match:
        return None
    due_time = match.group(1)
    time = datetime.strptime(due_time, "%I:%M %p")
    dt = datetime.strptime(due_day, "%a, %b %d, %Y").replace(hour=time.hour, minute=time.minute, second=59, tzinfo=ZoneInfo("America/New_York"))
    return dt

# Reduce titles using regex to extract repeat word.
def parse_title(title: str) -> str:
    match = re.search(r'Homework \d+', title)
    title = match.group(0) if match else title
    return title

# Traverse UBX courses and extract due dates. Return a list of DueDate objects.
def parse_ubx_duedates() -> list[DueDate]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://apps.learning.buffalo.edu/authn/login", wait_until="domcontentloaded")
        page.click("id=provider-name")
        page.fill("#login", UBX_EMAIL)
        page.fill("#password", UBX_PASSWORD)
        page.click("text=Log in")
        page.click("text=Yes, this is my device")

        due_dates = []
        now = datetime.now(ZoneInfo("America/New_York"))

        for course in UBX_COURSES:
            page.click("text=" + course)
            page.locator('a.nav-link[href*="/dates"]').click()
            page.wait_for_load_state("networkidle")            
            content = page.inner_text("body")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            for i, line in enumerate(lines):
                if "due" in line:
                    title = parse_title(lines[i]) if i >= 1 else "Unknown"
                    if "Homework" in lines[i - 2] if i >= 2 else "":
                        due = parse_due_date(lines[i - 1] if i >= 2 else "", lines[i])
                    else:
                        due = parse_due_date(lines[i - 2] if i >= 2 else "", lines[i])

                    # Skip if due date is not found or in the past.
                    if due is None:
                        continue
                    elif due >= now:
                        due_dates.append(DueDate(title, due, course, "assignment", "", "UBX"))

            page.goto("https://apps.learning.buffalo.edu/learner-dashboard/", wait_until="domcontentloaded")

        browser.close()

    return due_dates