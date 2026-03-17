import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from due_date import DueDate
from playwright.sync_api import sync_playwright

load_dotenv()
AUTOLAB_EMAIL = os.getenv('AUTOLAB_EMAIL')
AUTOLAB_PASSWORD = os.getenv('AUTOLAB_PASSWORD')
autolab_courses = ["CSE 305: Programming Languages (Both sections) (s26)", "CSE 396: Intro Theory of Computation (s26)"]
seen_file = "seen_autolab.json"

if not AUTOLAB_EMAIL:
    raise EnvironmentError("AUTOLAB_EMAIL is not set in .env")
if not AUTOLAB_PASSWORD:
    raise EnvironmentError("AUTOLAB_PASSWORD is not set in .env")
if autolab_courses == []:
    raise ValueError("autolab_courses list is empty. Please add course names to the list in ubx_parser.py")

def parse_due_date(due_text: str) -> datetime | None:
    match = re.search(r'Due:\s+\w+,\s+(\w+ \d+ at \d+:\d+[ap]m)', due_text)
    if not match:
        return None
    dt = datetime.strptime(f"{match.group(1)} {datetime.now().year}", "%b %d at %I:%M%p %Y")
    return dt.replace(tzinfo=ZoneInfo("America/New_York"))

def load_seen_titles() -> set:
    if os.path.exists(seen_file):
        with open(seen_file) as f:
            return set(json.load(f))
    return set()

def save_seen_titles(titles: set):
    with open(seen_file, "w") as f:
        json.dump(list(titles), f)

def parse_autolab_duedates():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        page = browser.new_page()

        page.goto("https://autolab.cse.buffalo.edu/auth/users/sign_in", wait_until="domcontentloaded")
        page.click("input[value='Sign in with Shibboleth']")
        page.fill("#login", AUTOLAB_EMAIL)
        page.fill("#password", AUTOLAB_PASSWORD)
        page.click("text=Log in")
        page.click("text=Yes, this is my device")
        
        due_dates = []
        SEEN_TITLES = load_seen_titles()
        now = datetime.now(ZoneInfo("America/New_York"))

        for course in autolab_courses:
            page.click("text=" + course)
            page.wait_for_load_state("networkidle")            
            content = page.inner_text("body")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            for i, line in enumerate(lines):
                if "Due:" in line:
                    title = lines[i - 1]
                    due = parse_due_date(lines[i])
                    if due >= now and (course + ": " + title) not in SEEN_TITLES:
                        due_dates.append(DueDate(title, due, course, "assignment", "", "Autolab"))
                        SEEN_TITLES.add(course + ": " + title)
            page.goto("https://autolab.cse.buffalo.edu/courses", wait_until="domcontentloaded")

        save_seen_titles(SEEN_TITLES)
        return due_dates