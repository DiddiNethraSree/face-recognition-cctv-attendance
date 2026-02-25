import sqlite3
from datetime import datetime, date
from zoneinfo import ZoneInfo
import urllib.request
import re

DB_PATH = "attendance.db"

def now_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata"))

# ---------------- INITIALIZE DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        date TEXT,
        first_seen_time TEXT,
        present INTEGER,
        UNIQUE(student_id, date)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        dob TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        date TEXT PRIMARY KEY,
        name TEXT
    )
    """)

    # Check if dob column exists, if not add it (for existing databases)
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'dob' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")

    # Seed some default users if not exists
    users = [
        ('student1', '123', 'student', '2000-01-01'),
        ('student2', '123', 'student', '2000-01-02'),
        ('student3', '123', 'student', '2000-01-03'),
        ('21CSE001', '123', 'student', '2003-05-15'),
        ('hod1', '123', 'hod', None)
    ]
    cursor.executemany("INSERT OR REPLACE INTO users (user_id, password, role, dob) VALUES (?, ?, ?, ?)", users)

    try:
        sync_holidays_google()
    except Exception:
        pass

    conn.commit()
    conn.close()

# ---------------- HOLIDAYS & WORKING DAY ----------------
def is_working_day(date_str: str) -> bool:
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    if dt.weekday() == 6:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM holidays WHERE date=?", (date_str,))
    row = cur.fetchone()
    conn.close()
    return row is None

def sync_holidays_google():
    year = now_ist().date().year
    url = "https://calendar.google.com/calendar/ical/en.indian%23holiday%40group.v.calendar.google.com/public/basic.ics"
    with urllib.request.urlopen(url, timeout=5) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    events = re.split(r"BEGIN:VEVENT", content)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for ev in events:
        mdate = re.search(r"DTSTART;VALUE=DATE:(\d{8})", ev)
        msum = re.search(r"SUMMARY:(.+)", ev)
        if mdate and msum:
            ymd = mdate.group(1)
            y, m, d = ymd[0:4], ymd[4:6], ymd[6:8]
            if int(y) in (year, year+1):
                ds = f"{y}-{m}-{d}"
                name = msum.group(1).strip()
                cur.execute("INSERT OR IGNORE INTO holidays (date, name) VALUES (?, ?)", (ds, name))
    conn.commit()
    conn.close()

# ---------------- MARK ALL STUDENTS ABSENT FOR TODAY ----------------
def init_today(all_students):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = now_ist().strftime("%Y-%m-%d")

    for student in all_students:
        cursor.execute("""
        INSERT OR IGNORE INTO attendance (student_id, date, first_seen_time, present)
        VALUES (?, ?, NULL, 0)
        """, (student, today))

    conn.commit()
    conn.close()


# ---------------- MARK STUDENT PRESENT ----------------
def mark_present(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = now_ist().strftime("%Y-%m-%d")
    time_now = now_ist().strftime("%H:%M:%S")

    cursor.execute("""
    UPDATE attendance
    SET present = 1, first_seen_time = ?
    WHERE student_id = ? AND date = ?
    """, (time_now, student_id, today))

    conn.commit()
    conn.close()
