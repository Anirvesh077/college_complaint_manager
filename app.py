from __future__ import annotations

import csv
import json
import os
import shutil
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
REPORT_DIR = APP_DIR / "reports"
JSON_FILE = DATA_DIR / "complaints.json"
CSV_FILE = DATA_DIR / "complaints.csv"
AUDIT_FILE = DATA_DIR / "audit.log"

CATEGORIES = [
    "Facilities", "Academics", "Hostel", "Library", "Transport",
    "IT & Wi-Fi", "Canteen", "Safety", "Administration", "Other"
]
STATUSES = ["Open", "In Progress", "Resolved", "Rejected"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]


@dataclass
class Complaint:
    complaint_id: str
    student_name: str
    student_id: str
    department: str
    category: str
    title: str
    description: str
    priority: str
    status: str
    created_on: str
    due_on: str
    updated_on: str
    resolution_note: str = ""

    @classmethod
    def from_dict(cls, row):
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: row.get(k, "") for k in allowed})


def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    if not JSON_FILE.exists():
        JSON_FILE.write_text("[]", encoding="utf-8")
    if not AUDIT_FILE.exists():
        AUDIT_FILE.write_text("College Complaint Manager audit log\n", encoding="utf-8")


def audit(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {message}\n")


def load_complaints():
    ensure_storage()
    try:
        raw = json.loads(JSON_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("The complaint file must contain a JSON list.")
        records = []
        for item in raw:
            try:
                c = Complaint.from_dict(item)
                if c.complaint_id and c.title:
                    records.append(c)
            except (TypeError, ValueError):
                continue
        return records
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        backup = JSON_FILE.with_suffix(".corrupt-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".json")
        try:
            shutil.copy2(JSON_FILE, backup)
        except OSError:
            pass
        print(f"\nHeads-up: the saved data could not be read ({exc}). A fresh data file will be created.")
        JSON_FILE.write_text("[]", encoding="utf-8")
        audit(f"Storage recovery: {exc}")
        return []


def save_complaints(records):
    ensure_storage()
    temp = JSON_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps([asdict(c) for c in records], indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(JSON_FILE)
    export_csv(records)


def export_csv(records, destination=CSV_FILE):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = list(Complaint.__dataclass_fields__.keys())
    with destination.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(c) for c in records)


def prompt(label, required=True, max_len=160):
    while True:
        value = input(f"{label}: ").strip()
        if not value and required:
            print("Please enter a value. You can use letters and numbers.")
            continue
        if len(value) > max_len:
            print(f"Please keep this to {max_len} characters or fewer.")
            continue
        return value


def choose(label, options, default=None):
    print(f"\n{label}")
    for i, option in enumerate(options, 1):
        suffix = " (default)" if option == default else ""
        print(f"  {i}. {option}{suffix}")
    while True:
        raw = input(f"Choose 1-{len(options)}" + (f" [Enter = {default}]" if default else "") + ": ").strip()
        if not raw and default:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw)-1]
        print("That choice isn't on the list. Please try again.")


def ask_date(label, default):
    while True:
        raw = input(f"{label} [YYYY-MM-DD, default {default}]: ").strip() or default
        try:
            parsed = date.fromisoformat(raw)
            return parsed.isoformat()
        except ValueError:
            print("Please use a real date in YYYY-MM-DD format (for example 2026-11-20).")


def next_id(records):
    used = {c.complaint_id for c in records}
    n = 1
    while f"CF-{n:04d}" in used:
        n += 1
    return f"CF-{n:04d}"


def add_complaint(records):
    print("\n" + "=" * 62 + "\n  NEW COMPLAINT\n" + "=" * 62)
    name = prompt("Student name", max_len=80)
    student_id = prompt("Student ID / roll number", max_len=30)
    department = prompt("Department / course", max_len=80)
    category = choose("Category", CATEGORIES)
    title = prompt("Short title", max_len=100)
    description = prompt("What happened? (one or two sentences)", max_len=1000)
    priority = choose("Priority", PRIORITIES, "Medium")
    today = date.today()
    due_default = (today + timedelta(days=7 if priority in ("High", "Urgent") else 14)).isoformat()
    due = ask_date("Target resolution date", due_default)
    now = datetime.now().isoformat(timespec="seconds")
    c = Complaint(next_id(records), name, student_id, department, category, title,
                  description, priority, "Open", today.isoformat(), due, now)
    records.append(c)
    save_complaints(records)
    audit(f"Created {c.complaint_id}: {c.title}")
    print(f"\n✓ Complaint saved. Your reference number is {c.complaint_id}.")
    print("Keep this number so you can check progress later.")


def print_table(records):
    if not records:
        print("\nNo complaints match that search.")
        return
    print()
    print(f"{'REF':<9} {'DATE':<10} {'CATEGORY':<15} {'PRIORITY':<8} {'STATUS':<13} TITLE")
    print("-" * 88)
    for c in records:
        title = c.title[:34] + ("…" if len(c.title) > 34 else "")
        print(f"{c.complaint_id:<9} {c.created_on:<10} {c.category[:14]:<15} {c.priority:<8} {c.status:<13} {title}")
    print(f"\nShowing {len(records)} record(s).")


def show_details(c):
    print("\n" + "-" * 62)
    print(f"{c.complaint_id}  |  {c.title}")
    print("-" * 62)
    for label, value in [
        ("Student", f"{c.student_name} ({c.student_id})"),
        ("Department", c.department), ("Category", c.category),
        ("Priority", c.priority), ("Status", c.status),
        ("Submitted", c.created_on), ("Target date", c.due_on),
        ("Last updated", c.updated_on), ("Description", c.description),
        ("Resolution note", c.resolution_note or "Not added yet")
    ]:
        print(f"{label:<17}: {value}")


def search_complaints(records):
    print("\nSEARCH COMPLAINTS")
    term = prompt("Enter a keyword, reference number, student ID, or leave blank to filter by category", required=False).lower()
    if term:
        found = [c for c in records if term in " ".join(asdict(c).values()).lower()]
    else:
        category = choose("Filter by category", CATEGORIES)
        found = [c for c in records if c.category == category]
    print_table(found)
    if found and input("\nOpen a record? Enter its reference number, or press Enter to return: ").strip():
        ref = input("Reference number: ").strip().upper()
        match = next((c for c in found if c.complaint_id == ref), None)
        if match:
            show_details(match)
        else:
            print("I couldn't find that reference in these results.")


def update_status(records):
    ref = prompt("Complaint reference (for example CF-0001)").upper()
    c = next((x for x in records if x.complaint_id == ref), None)
    if not c:
        print("No complaint found with that reference.")
        return
    show_details(c)
    c.status = choose("New status", STATUSES, c.status)
    if c.status in ("Resolved", "Rejected"):
        c.resolution_note = prompt("Short note for the record", required=False, max_len=500)
    c.updated_on = datetime.now().isoformat(timespec="seconds")
    save_complaints(records)
    audit(f"Updated {ref} to {c.status}")
    print(f"\n✓ {ref} is now marked as {c.status}.")


def dashboard(records):
    total = len(records)
    counts = Counter(c.status for c in records)
    categories = Counter(c.category for c in records)
    today = date.today()
    overdue = [c for c in records if c.status not in ("Resolved", "Rejected") and c.due_on < today.isoformat()]
    resolved_days = []
    for c in records:
        if c.status == "Resolved":
            try:
                resolved_days.append((date.fromisoformat(c.updated_on[:10]) - date.fromisoformat(c.created_on)).days)
            except ValueError:
                pass
    print("\n" + "=" * 62 + "\n  CAMPUS OVERVIEW\n" + "=" * 62)
    print(f"Total complaints : {total}")
    for status in STATUSES:
        print(f"{status:<17}: {counts[status]}")
    print(f"Overdue / pending: {len(overdue)}")
    if resolved_days:
        print(f"Average days to resolve (resolved records): {sum(resolved_days)/len(resolved_days):.1f}")
    else:
        print("Average days to resolve: Not enough resolved records yet.")
    print("\nMost reported categories:")
    for category, count in categories.most_common(5):
        print(f"  {category:<18} {count:>3}")
    if overdue:
        print("\n⚠ Needs attention (past target date):")
        for c in overdue[:10]:
            print(f"  {c.complaint_id}  {c.title}  — due {c.due_on}")
    else:
        print("\n✓ No pending complaints are past their target date.")


def export_reports(records):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md = REPORT_DIR / f"summary-{stamp}.md"
    txt = REPORT_DIR / f"summary-{stamp}.txt"
    csv_path = REPORT_DIR / f"complaints-{stamp}.csv"
    counts = Counter(c.status for c in records)
    lines = ["# College Complaint Manager — Summary", "",
             f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", "",
             f"- Total complaints: **{len(records)}**"]
    lines += [f"- {s}: **{counts[s]}**" for s in STATUSES]
    lines += ["", "## Complaint register", "", "| Reference | Student | Category | Priority | Status | Due |",
              "|---|---|---|---|---|---|"]
    for c in records:
        lines.append(f"| {c.complaint_id} | {c.student_name} | {c.category} | {c.priority} | {c.status} | {c.due_on} |")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text("\n".join(lines).replace("**", "").replace("#", "") + "\n", encoding="utf-8")
    export_csv(records, csv_path)
    audit(f"Exported reports to {REPORT_DIR}")
    print(f"\n✓ Reports created:\n  {md.relative_to(APP_DIR)}\n  {txt.relative_to(APP_DIR)}\n  {csv_path.relative_to(APP_DIR)}")


def import_csv(records):
    path_text = prompt("Path to CSV file")
    path = Path(path_text).expanduser()
    if not path.is_file():
        print("I can't see that file. Check the path and try again.")
        return
    added, skipped = 0, 0
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"student_name", "student_id", "department", "category", "title", "description"}
            if not required.issubset(set(reader.fieldnames or [])):
                print("This CSV is missing required columns: " + ", ".join(sorted(required)))
                return
            for row in reader:
                try:
                    category = row.get("category", "").strip()
                    priority = row.get("priority", "Medium").strip().title()
                    status = row.get("status", "Open").strip().title()
                    if category not in CATEGORIES or priority not in PRIORITIES or status not in STATUSES:
                        skipped += 1
                        continue
                    today = date.today().isoformat()
                    records.append(Complaint(
                        next_id(records), row["student_name"].strip(), row["student_id"].strip(),
                        row["department"].strip(), category, row["title"].strip(),
                        row["description"].strip(), priority, status, today,
                        row.get("due_on", today).strip() or today,
                        datetime.now().isoformat(timespec="seconds"),
                        row.get("resolution_note", "").strip()
                    ))
                    added += 1
                except (KeyError, TypeError):
                    skipped += 1
        save_complaints(records)
        audit(f"CSV import: {added} added, {skipped} skipped")
        print(f"\nImport finished: {added} added, {skipped} skipped.")
    except (OSError, csv.Error) as exc:
        print(f"Couldn't import that file: {exc}")


def seed_demo():
    records = load_complaints()
    if records:
        print("Sample data was not added because your complaint list is already populated.")
        return
    names = ["Aarav Sharma", "Diya Reddy", "Kabir Nair", "Ananya Das", "Ishaan Patel",
             "Meera Iyer", "Rohan Gupta", "Sara Khan", "Arjun Rao", "Nisha Verma"]
    departments = ["Computer Science", "Mechanical", "Commerce", "Electrical", "Biotechnology"]
    titles = [
        ("IT & Wi-Fi", "Wi-Fi drops in the library", "The connection disconnects every few minutes during study hours."),
        ("Facilities", "Broken classroom fan", "The fan in the second-floor classroom is not working."),
        ("Hostel", "Water supply timing", "Water is unavailable in the hostel bathrooms early in the morning."),
        ("Academics", "Timetable clash", "Two required classes are scheduled at the same time."),
        ("Canteen", "Drinking water station", "The drinking water station near the canteen needs attention."),
        ("Library", "Need longer library hours", "Students preparing for exams would benefit from later closing time."),
        ("Transport", "Bus route delay", "The evening bus has been arriving late this week."),
        ("Safety", "Broken corridor light", "A corridor light near the stairs is not working."),
        ("Administration", "ID card correction", "The department name printed on the ID card is incorrect."),
        ("Other", "Lost-and-found notice", "Please provide a visible place to post lost item notices.")
    ]
    today = date.today()
    for i in range(40):
        cat, title, desc = titles[i % len(titles)]
        created = today - timedelta(days=(i * 3) % 25)
        status = ["Open", "In Progress", "Resolved", "Open", "Rejected"][i % 5]
        due = created + timedelta(days=7 if i % 3 else 3)
        updated = created + timedelta(days=2 if status == "Resolved" else 1)
        records.append(Complaint(
            f"CF-{i+1:04d}", names[i % len(names)], f"STU{1001+i}",
            departments[i % len(departments)], cat, f"{title} #{i+1}",
            desc, PRIORITIES[i % len(PRIORITIES)], status, created.isoformat(),
            due.isoformat(), datetime.combine(updated, datetime.min.time()).isoformat(),
            "Checked by the campus office." if status == "Resolved" else ""
        ))
    save_complaints(records)
    audit("Loaded 40 demo complaints")
    print("✓ Added 40 realistic sample records. You can safely explore the dashboard and search.")


def menu():
    ensure_storage()
    print("\n" + "=" * 62)
    print("  COLLEGE COMPLAINT MANAGER")
    print("  A clearer way to raise an issue and follow its progress")
    print("=" * 62)
    while True:
        records = load_complaints()
        print("\nMAIN MENU")
        print("  1. Register a complaint")
        print("  2. Search / view complaints")
        print("  3. Update complaint status (staff)")
        print("  4. Campus overview & overdue alerts")
        print("  5. Export reports")
        print("  6. Import complaints from CSV")
        print("  7. Load 40 demo records (empty database only)")
        print("  0. Exit")
        choice = input("\nWhat would you like to do? ").strip()
        if choice == "1":
            add_complaint(records)
        elif choice == "2":
            search_complaints(records)
        elif choice == "3":
            update_status(records)
        elif choice == "4":
            dashboard(records)
        elif choice == "5":
            export_reports(records)
        elif choice == "6":
            import_csv(records)
        elif choice == "7":
            seed_demo()
        elif choice == "0":
            print("\nThanks for helping make campus life better. Goodbye!\n")
            break
        else:
            print("Please choose one of the menu numbers (0–7).")


if __name__ == "__main__":
    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print("\n\nSession ended. Your saved complaints are safe.")
        sys.exit(0)
