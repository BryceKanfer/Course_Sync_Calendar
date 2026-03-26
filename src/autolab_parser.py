import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from due_date import DueDate
from playwright.sync_api import sync_playwright

# Load environment variables and config.json
load_dotenv()
AUTOLAB_EMAIL = os.getenv('AUTOLAB_EMAIL')
AUTOLAB_PASSWORD = os.getenv('AUTOLAB_PASSWORD')
with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    config = json.load(f)
autolab_courses = config["autolab_courses"]

# Validate environment variables and config
if not AUTOLAB_EMAIL:
    raise EnvironmentError("AUTOLAB_EMAIL is not set in .env")
if not AUTOLAB_PASSWORD:
    raise EnvironmentError("AUTOLAB_PASSWORD is not set in .env")

# Parse str of a date into datetime object using regex
def parse_due_date(due_text: str) -> datetime | None:
    match = re.search(r'Due:\s+\w+,\s+(\w+ \d+ at \d+:\d+[ap]m)', due_text)
    if not match:
        return None
    dt = datetime.strptime(f"{match.group(1)} {datetime.now().year}", "%b %d at %I:%M%p %Y")
    return dt.replace(tzinfo=ZoneInfo("America/New_York"))

# Traverse Autolab courses and extract due dates. Return a list of DueDate objects.
def parse_autolab_duedates() -> list[DueDate]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://autolab.cse.buffalo.edu/auth/users/sign_in", wait_until="domcontentloaded")
        page.click("input[value='Sign in with Shibboleth']")
        page.fill("#login", AUTOLAB_EMAIL)
        page.fill("#password", AUTOLAB_PASSWORD)
        page.click("text=Log in")
        page.click("text=Yes, this is my device")
        
        due_dates = []
        now = datetime.now(ZoneInfo("America/New_York"))

        for course in autolab_courses:
            page.click("text=" + course)
            page.wait_for_load_state("domcontentloaded")            
            content = page.inner_text("body")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            for i, line in enumerate(lines):
                if "Due:" in line:
                    title = lines[i - 1] if i >= 1 else "Unknown"
                    due = parse_due_date(lines[i])
                    if due is None:
                        continue
                    elif due >= now:
                        due_dates.append(DueDate(title, due, course, "assignment", "", "Autolab"))

            page.goto("https://autolab.cse.buffalo.edu/courses", wait_until="domcontentloaded")

        browser.close()

    return due_dates