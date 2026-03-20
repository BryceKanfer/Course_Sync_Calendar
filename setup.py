import subprocess
import sys
import json
import os
import platform

def install_dependencies():
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print("Dependencies installed.\n")

def setup_env():
    if os.path.exists(".env"):
        print(".env already exists, skipping...\n")
        return
    print("Setting up .env file...\n")

    fields = {}

    print("-- TopHat --")
    fields["TOPHAT_EMAIL"] = input("  Enter your UB email: ").strip()
    fields["TOPHAT_PASSWORD"] = input("  Enter your UB password: ").strip()

    print("\n-- Autolab --")
    fields["AUTOLAB_EMAIL"] = input("  Enter your UB email: ").strip()
    fields["AUTOLAB_PASSWORD"] = input("  Enter your UB password: ").strip()

    print("\n-- UBX --")
    fields["UBX_EMAIL"] = input("  Enter your UB email: ").strip()
    fields["UBX_PASSWORD"] = input("  Enter your UB password: ").strip()

    print("\n-- Brightspace --")
    print("  To get your Brightspace calendar URL:")
    print("  1. Go to ublearns.buffalo.edu")
    print("  2. Click the calendar icon")
    print("  3. Click 'Subscribe' or 'Get calendar feed'")
    print("  4. Copy the URL")
    fields["BRIGHTSPACE_CALENDAR_URL"] = input("  Enter BRIGHTSPACE_CALENDAR_URL: ").strip()

    print("\n-- Gmail --")
    fields["GMAIL_ADDRESS"] = input("  Enter your Gmail address: ").strip()

    print("  To get your Gmail App Password:")
    print("  1. Go to myaccount.google.com")
    print("  2. Search 'App Passwords'")
    print("  3. Create one named 'Course Sync'")
    print("  4. Copy the 16 character password")
    fields["GMAIL_APP_PASSWORD"] = input("  Enter your Gmail App Password: ").strip()

    print("\n-- Phone --")
    fields["PHONE_NUMBER"] = input("  Enter your 10 digit phone number (no dashes or spaces): ").strip()

    print("\n-- Google Calendar --")
    print("  To get your Google Calendar ID:")
    print("  1. Open Google Calendar")
    print("  2. Click the three dots next to your 'Due Dates' calendar")
    print("  3. Click 'Settings and sharing'")
    print("  4. Scroll down to 'Integrate calendar'")
    print("  5. Copy the Calendar ID")
    fields["GOOGLE_CALENDAR_ID"] = input("  Enter your Google Calendar ID: ").strip()

    with open(".env", "w") as f:
        for key, value in fields.items():
            f.write(f"{key}={value}\n")
    print("\n.env saved.\n")

def setup_config():
    if os.path.exists("config.json"):
        print("config.json already exists, skipping...\n")
        return

    def prompt_courses(name: str) -> list[str]:
        print(f"\nEnter your {name} courses (press Enter with no input when done):")
        print(" Note: Course names should match exactly how they appear on the platforms.")
        courses = []
        while True:
            course = input(f"  {name} course: ").strip()
            if not course:
                break
            courses.append(course)
        return courses

    print("Setting up course config...")
    config = {
        "autolab_courses": prompt_courses("Autolab"),
        "tophat_courses": prompt_courses("TopHat"),
        "ubx_courses": prompt_courses("UBX"),
    }

    print("\nCommon carrier gateways:")
    print("  Verizon SMS:  vtext.com")
    print("  Verizon MMS:  vzwpix.com")
    print("  AT&T:         txt.att.net")
    print("  T-Mobile:     tmomail.net")
    print("  Sprint:       messaging.sprintpcs.com")
    config["carrier_gateway"] = input("Enter your carrier gateway: ").strip()

    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("\nconfig.json saved.\n")

def make_executable():
    if platform.system() != "Windows":
        import stat
        run_sh = os.path.join(os.path.dirname(__file__), "run.sh")
        st = os.stat(run_sh)
        os.chmod(run_sh, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print("run.sh made executable.\n")

def setup_service_account():
    if os.path.exists("service_account.json"):
        print("service_account.json already exists, skipping...\n")
        return
    print("Google Calendar Service Account Setup:")
    print("  1. Go to console.cloud.google.com")
    print("  2. Select your project")
    print("  3. Go to IAM & Admin -> Service Accounts")
    print("  4. Click your service account -> Keys -> Add Key -> JSON")
    print("  5. Download the JSON file")
    print("  6. Rename it to 'service_account.json'")
    print("  7. Place it in the project root folder")
    input("Press Enter once service_account.json is in the project root...")
    if os.path.exists("service_account.json"):
        print("service_account.json found.\n")
        print("  Remember to share your Google Calendar with the service account email")
        print("  with 'Make changes to events' permission.")
    else:
        print("Warning: service_account.json not found.\n")

def setup_task_scheduler():
    if platform.system() == "Windows":
        print("\nTo schedule daily runs on Windows:")
        print("  1. Open Task Scheduler")
        print("  2. Click 'Create Basic Task'")
        print("  3. Name it 'Course Sync'")
        print("  4. Trigger: Daily at 11:00 AM")
        print("  5. Action: Start a program -> browse to run.bat")
        print("  6. Finish")
    else:
        print("\nTo schedule daily runs on Mac/Linux add this to your crontab:")
        print("  0 11 * * * /path/to/run.sh")

if __name__ == "__main__":
    install_dependencies()
    setup_service_account()
    setup_env()
    setup_config()
    make_executable()
    print("Setup complete! Run run.bat (Windows) or ./run.sh (Mac/Linux) to start the program.")
    setup_task_scheduler()
