import sqlite3
from datetime import datetime

DB_PATH = "attendance.db"

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
        role TEXT
    )
    """)

    # Seed some default users if not exists
    users = [
        ('student1', '123', 'student'),
        ('student2', '123', 'student'),
        ('student3', '123', 'student'),
        ('staff1', '123', 'staff'),
        ('hod1', '123', 'hod')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", users)

    conn.commit()
    conn.close()


# ---------------- MARK ALL STUDENTS ABSENT FOR TODAY ----------------
def init_today(all_students):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

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

    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M:%S")

    cursor.execute("""
    UPDATE attendance
    SET present = 1, first_seen_time = ?
    WHERE student_id = ? AND date = ?
    """, (time_now, student_id, today))

    conn.commit()
    conn.close()
