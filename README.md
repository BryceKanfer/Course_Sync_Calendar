# Course Sync Calendar
 
Automatically fetches assignment due dates from University at Buffalo (UB) course platforms, sends a daily text summary, and syncs everything to your Google Calendar.

## Supported Platforms
- **Brightspace** — via iCal feed
- **Autolab** — via Playwright browser automation
- **TopHat** — via Playwright browser automation
- **UBX** — via Playwright browser automation

 
## Getting Started
 
### Prerequisites
**Instructions for the following are provided in setup.py:**
- Python 3.10+
- Google Cloud project with Google Calendar API enabled
- Google Service Account credentials
- Gmail account with an App Password
- Phone number for SMS/MMS delivery

### Features
- Aggregates all upcoming assignments in one place
- Sends daily SMS summaries (today + next 7 days)
- Automatically syncs with Google Calendar
- Headless browser automation for platforms without accessible APIs
 
### Setup
1. Fork and clone the repository
2. Run the setup script from the project root:
```
python setup.py
```
This will:
- Install dependencies
- Install Chromium (for Playwright)
- Guide you through .env and config.json setup
- Make run.sh executable (Mac/Linux)
  
## Usage
 
**Windows:**
```
run.bat
```
 
**Mac/Linux:**
```
./run.sh
```
#### You can also schedule this to run daily using:
- Windows Task Scheduler
- cron (Mac/Linux)
