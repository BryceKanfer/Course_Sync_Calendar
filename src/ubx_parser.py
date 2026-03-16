from datetime import datetime 
from email.mime import text
import json
import os
import re
import time
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from due_date import DueDate


load_dotenv()
UBX_EMAIL = os.getenv('UBX_EMAIL')
UBX_PASSWORD = os.getenv('UBX_PASSWORD')
UBX_COURSES = ["MTH 309 (Rai)"]
seen_file = "seen_ubx.json"

if not UBX_EMAIL:
    raise EnvironmentError("UBX_EMAIL is not set in .env")
if not UBX_PASSWORD:
    raise EnvironmentError("UBX_PASSWORD is not set in .env")
if UBX_COURSES == []:
    raise ValueError("ubx_courses list is empty. Please add course names to the list in ubx_parser.py")

def parse_due_date(due_day: str, due_time: str) -> datetime:
    match = re.search(r'(\d{1,2}:\d{2} [AP]M)', due_time)
    due_time = match.group(1)
    time = datetime.strptime(due_time, "%I:%M %p")
    dt = datetime.strptime(due_day, "%a, %b %d, %Y").replace(hour=time.hour, minute=time.minute, second=59, tzinfo=ZoneInfo("America/New_York"))
    return dt

def parse_title(title: str) -> str:
    match = re.search(r'Homework \d+', title)
    title = match.group(0) if match else "Unknown Assignment"
    return title

def load_seen_titles() -> set:
    if os.path.exists(seen_file):
        with open(seen_file) as f:
            return set(json.load(f))
    return set()

def save_seen_titles(titles: set):
    with open(seen_file, "w") as f:
        json.dump(list(titles), f)

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
        SEEN_TITLES = load_seen_titles()

        for course in UBX_COURSES:
            page.click("text=" + course)
            page.locator('a.nav-link[href*="/dates"]').click()
            page.wait_for_load_state("networkidle")            
            content = page.inner_text("body")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            for i, line in enumerate(lines):
                if "due" in line:
                    title = parse_title(lines[i])
                    due_date = parse_due_date(lines[i - 2], lines[i])
                    if (course + ": " + title) not in SEEN_TITLES:
                        SEEN_TITLES.add(course + ": " + title)
                        due_dates.append(DueDate(title, due_date, course, "assignment", "", "UBX"))
                        print(f"Added {title} for {course} due on {due_date}")
            page.goto("https://apps.learning.buffalo.edu/learner-dashboard/", wait_until="domcontentloaded")

    save_seen_titles(SEEN_TITLES)
    return due_dates

parse_ubx_duedates()
    