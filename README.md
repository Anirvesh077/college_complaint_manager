# College Complaint Manager

A friendly, local-first Python app for registering campus complaints, tracking progress, searching records, and producing reports. It is designed around the GreenFuture Hack Project #23 brief.

## What is included

- A simple, guided terminal menu (no coding knowledge needed to use it).
- Complaint reference numbers such as `CF-0001`.
- Validation for blank values, long text, dates, and menu choices.
- Categories, priorities, due dates, and status tracking.
- Automatic local saving to JSON; a CSV copy is kept in sync.
- Keyword and category search.
- Overview with status totals, average resolution time, and overdue alerts.
- Markdown, text, and CSV report export.
- CSV bulk import with basic row validation.
- Audit log and recovery behavior if the JSON file is damaged.
- 40 realistic demo records, added only when the database is empty.
- Automated tests using Python's built-in `unittest`.

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.10 or newer
- No third-party Python packages are required.

Check Python:
```bash
python --version
```
On some Windows installations, use:
```powershell
py --version
```

## Run it on Windows

1. Download and unzip `College_Complaint_Manager.zip`.
2. Open the extracted `college_complaint_manager` folder.
3. Double-click `run_windows.bat`.
4. The menu opens in a terminal window. Type a menu number and press Enter.
5. Choose `7` to load 40 demo records (only works when the database is empty).
6. Choose `4` to see the overview, `2` to search, or `5` to export reports.
7. Choose `0` to exit. Your data is saved automatically.

If Windows says Python is not installed, install Python 3.10+ from https://www.python.org/downloads/ and tick **Add Python to PATH** during setup. Then reopen the project folder and run the batch file again.

## Run it on macOS / Linux

Open Terminal, move into the extracted folder, then run:
```bash
chmod +x run_unix.sh
./run_unix.sh
```
Or run directly:
```bash
python3 app.py
```

## First demo: a smooth 3-minute walkthrough

1. Start the app.
2. Select `7` to load the sample campus records.
3. Select `4` and explain the totals, categories, average resolution time, and overdue alerts.
4. Select `2`, search for `Wi-Fi`, and open one matching complaint.
5. Select `3`, enter a reference such as `CF-0001`, and change its status.
6. Select `5` to export reports.
7. Open the `reports` folder and show the generated Markdown, TXT, and CSV files.
8. Exit and restart the app to demonstrate that the records persist.

For a clean live demonstration, use the demo dataset first. The app only loads it into an empty database.

## Menu guide

| Option | What it does |
|---|---|
| 1 | Register a complaint |
| 2 | Search by keyword, reference, student ID, or category |
| 3 | Update status (staff workflow) |
| 4 | View campus summary and overdue items |
| 5 | Export Markdown, text, and CSV reports |
| 6 | Import a compatible CSV file |
| 7 | Add 40 sample complaints to an empty database |
| 0 | Exit safely |

## Where your data lives

- `data/complaints.json` — main saved records.
- `data/complaints.csv` — spreadsheet-friendly copy, refreshed on save.
- `data/audit.log` — timestamped activity log.
- `reports/` — generated report files.

Back up the `data` folder if you are using real complaints. This is a local demonstration app, not a secure production case-management system. It does not include user accounts, encryption, network access, or role-based access control. Avoid entering sensitive personal or medical details.

## Run the tests

Windows:
```powershell
py -m unittest discover -s tests -v
```
macOS / Linux:
```bash
python3 -m unittest discover -s tests -v
```

## CSV import format

Your CSV needs these columns:
`student_name, student_id, department, category, title, description`

Optional columns:
`priority, status, due_on, resolution_note`

Category, priority, and status values must match the choices shown in the app. The import assigns fresh reference numbers so existing records are not overwritten.

## Troubleshooting

- **The window closes immediately:** run `python app.py` from Command Prompt/Terminal so you can read the message.
- **`python` is not recognized:** try `py app.py` on Windows or `python3 app.py` on macOS/Linux.
- **I made a mistake while entering data:** complete the current prompt, then use search and status update as appropriate. For major cleanup, back up the `data` folder before editing files.
- **The JSON file is damaged:** the app attempts to preserve a timestamped copy and create a fresh empty file. Check `data` for the backup and `data/audit.log` for the recovery note.

## Project structure

```text
college_complaint_manager/
├── app.py
├── README.md
├── run_windows.bat
├── run_unix.sh
├── requirements.txt
├── data/
│   ├── complaints.json
│   └── audit.log
├── reports/
└── tests/
    └── test_app.py
```

Have a great demo!
