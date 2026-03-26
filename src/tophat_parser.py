import json
import os
import re
import time
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from due_date import DueDate
from datetime import datetime, timedelta

# Load environment variables and config
load_dotenv()
TOPHAT_EMAIL = os.getenv('TOPHAT_EMAIL')
TOPHAT_PASSWORD = os.getenv('TOPHAT_PASSWORD')
with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    config = json.load(f)
TOPHAT_COURSES = config["tophat_courses"]

# Validate environment variables and config
if not TOPHAT_EMAIL:
    raise EnvironmentError("TOPHAT_EMAIL is not set in .env")
if not TOPHAT_PASSWORD:
    raise EnvironmentError("TOPHAT_PASSWORD is not set in .env")

# Parse text into datetime object using regex. 
def parse_due_date(due_text: str) -> datetime | None:
    now = datetime.now(ZoneInfo("America/New_York"))

    # Check for relative due dates like "Due in 3 days" or "Due in 5 hours"
    match1 = re.search(r'(\d+)\s+(day|hour)', due_text)
    if match1:
        number = int(match1.group(1))
        unit = match1.group(2)
        if unit == "day":
            return now + timedelta(days=number)
        elif unit == "hour":
            return now + timedelta(hours=number)

    # Check for absolute due dates like "Due on September 30, 2024 at 11:59 PM" or "Due September 30, 2024"
    match2 = re.search(r'Due\s+(?:on\s+)?(\w+ \d+,\s+\d+(?::\d+ [AP]M)?(?:\s+\d{4})?)', due_text)
    if match2:
        date_str = match2.group(1)
        if re.search(r'\d{4}', date_str):
            if re.search(r'[AP]M', date_str):
                fmt = "%B %d, %I:%M %p %Y" if len(date_str.split()[0]) > 3 else "%b %d, %I:%M %p %Y"
                return datetime.strptime(date_str, fmt).replace(tzinfo=ZoneInfo("America/New_York"))
            else:
                fmt = "%B %d, %Y" if len(date_str.split()[0]) > 3 else "%b %d, %Y"
                return datetime.strptime(date_str, fmt).replace(hour=23, minute=59, second=59, tzinfo=ZoneInfo("America/New_York"))
        else:
            fmt = "%B %d, %I:%M %p %Y" if len(date_str.split()[0]) > 3 else "%b %d, %I:%M %p %Y"
            return datetime.strptime(f"{date_str} {now.year}", fmt).replace(tzinfo=ZoneInfo("America/New_York"))
    
    return None

# Traverse Tophat courses and extract due dates. Return a list of DueDate objects.
def parse_tophat_duedates() -> list[DueDate]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://app.tophat.com/login", wait_until="domcontentloaded")
        page.fill("#select-input-1", "University at Buffalo SUNY")
        page.wait_for_selector("text=University at Buffalo SUNY")
        page.keyboard.press("Enter")
        page.click("text=Log in with school")
        page.fill("#login", TOPHAT_EMAIL)
        page.fill("#password", TOPHAT_PASSWORD)
        page.click("text=Log in")
        page.click("text=Yes, this is my device")

        due_dates = []
        now = datetime.now(ZoneInfo("America/New_York"))

        for course in TOPHAT_COURSES:
            page.click("text=" + course)
            page.click("[data-click-id='content-space-navigation-button-assigned-for-grades']")
            try:
                page.wait_for_selector("text=Unanswered question(s)", timeout=10000)
            except:
                pass
            time.sleep(2)

            content = page.inner_text("body")
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            
            course_due_dates = []
            for i, line in enumerate(lines):
                if "Due" in line:
                    title = lines[i - 2] if i >= 2 else "Unknown"
                    due = parse_due_date(line)

                    if due is None:
                        continue
                    elif due >= now:
                        course_due_dates.append(DueDate(title, due, course, "assignment", "", "TopHat"))

            # Pop last due date, because it is a repeat of the first one.            
            if course_due_dates:
                course_due_dates.pop()
            due_dates += course_due_dates

            page.goto("https://app.tophat.com/e", wait_until="domcontentloaded")

        browser.close()
    
    return due_dates