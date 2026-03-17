import json
import os
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from due_date import DueDate
from datetime import datetime, timedelta

load_dotenv()
TOPHAT_EMAIL = os.getenv('TOPHAT_EMAIL')
TOPHAT_PASSWORD = os.getenv('TOPHAT_PASSWORD')
TOPHAT_COURSES = ["CSE396LR Intro Theory of Computation Spring26","CSE 305 - Programming Language (Spring 2026) - A1"]
seen_file = "seen_tophat.json"

if not TOPHAT_EMAIL:
    raise EnvironmentError("TOPHAT_EMAIL is not set in .env")
if not TOPHAT_PASSWORD:
    raise EnvironmentError("TOPHAT_PASSWORD is not set in .env")
if TOPHAT_COURSES == []:
    raise ValueError("tophat_courses list is empty. Please add course names to the list in ubx_parser.py")

def parse_due_date(due_text: str) -> datetime:
    now = datetime.now(ZoneInfo("America/New_York"))
   
    parts = due_text.split()
    number = int(parts[2])
    if "day" in due_text:
        return now + timedelta(days=number)
    elif "hour" in due_text:
        return now + timedelta(hours=number)
    else:
        return now

def load_seen_titles() -> set:
    if os.path.exists(seen_file):
        with open(seen_file) as f:
            return set(json.load(f))
    return set()

def save_seen_titles(titles: set):
    with open(seen_file, "w") as f:
        json.dump(list(titles), f)


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
        SEEN_TITLES = load_seen_titles()
        now = datetime.now(ZoneInfo("America/New_York"))

        for course in TOPHAT_COURSES:
            page.click("text=" + course)
            page.click("[data-click-id='content-space-navigation-button-assigned-for-grades']")
            page.wait_for_load_state("networkidle")            
            content = page.inner_text("body")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            for i, line in enumerate(lines):
                if "Due in" in line:
                    title = lines[i - 2]
                    due = parse_due_date(line)
                    if due >= now and (course + ": " + title) not in SEEN_TITLES:
                        SEEN_TITLES.add(course + ": " + title)
                        due_dates.append(DueDate(title, due, course, "assignment", "", "TopHat"))
            page.goto("https://app.tophat.com/e", wait_until="domcontentloaded")

        browser.close()

    save_seen_titles(SEEN_TITLES)
    return due_dates