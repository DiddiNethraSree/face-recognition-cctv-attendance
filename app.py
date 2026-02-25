from flask import Flask, render_template, request, redirect, session
import sqlite3
import database
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import database as dbmod

app = Flask(__name__)
app.secret_key = "attendance_secret"

# Initialize DB on startup
database.init_db()

DB = "attendance.db"

def get_db():
    return sqlite3.connect(DB)

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        role = request.form.get("role")

        con = sqlite3.connect(DB)
        cur = con.cursor()

        cur.execute(
            "SELECT role FROM users WHERE user_id=? AND password=?",
            (user_id, password)
        )
        row = cur.fetchone()
        con.close()

        if row and row[0] == role:
            session["user_id"] = user_id
            session["role"] = role

            if role == "student":
                return redirect("/student")
            elif role == "hod":
                return redirect("/hod")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------- FORGOT PASSWORD ROUTES ----------

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        user_id = request.form.get("reg_no")
        dob = request.form.get("dob")

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id=? AND dob=? AND role='student'", (user_id, dob))
        user = cur.fetchone()
        con.close()

        if user:
            session["reset_user_id"] = user_id
            return redirect("/reset-password")
        else:
            return render_template("forget_password_student.html", error="Invalid Register Number or DOB")

    return render_template("forget_password_student.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_user_id" not in session:
        return redirect("/forgot-password")

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            return render_template("rest_password_student.html", error="Passwords do not match")

        user_id = session["reset_user_id"]
        con = get_db()
        cur = con.cursor()
        cur.execute("UPDATE users SET password=? WHERE user_id=?", (new_password, user_id))
        con.commit()
        con.close()

        session.pop("reset_user_id", None)
        return render_template("reset_success.html")

    return render_template("rest_password_student.html")


# ---------- HOD DASHBOARD ----------
@app.route("/hod")
def hod():
    if session.get("role") != "hod":
        return redirect("/")

    time_filter = request.args.get("filter", "all")
    
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE role='student'")
    students_seed = [r[0] for r in cur.fetchall()]
    today_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
    if students_seed and dbmod.is_working_day(today_str):
        database.init_today(students_seed)

    query = """
        SELECT student_id,
               ROUND(SUM(present)*100.0/COUNT(*),2) AS percent
        FROM attendance
    """
    params = []

    if time_filter != "all":
        days = 7
        if time_filter == "15days":
            days = 15
        elif time_filter == "30days":
            days = 30
        
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query += " WHERE date >= ?"
        params.append(start_date)

    query += " GROUP BY student_id"

    cur.execute(query, params)
    data = cur.fetchall()
    
    # Also fetch full attendance list for the "Master List" view
    list_query = "SELECT student_id, date, first_seen_time, present FROM attendance"
    if time_filter != "all":
        list_query += " WHERE date >= ?"
    list_query += " ORDER BY date DESC, student_id ASC"
    
    cur.execute(list_query, params)
    master_list = cur.fetchall()

    con.close()

    eligible = [d for d in data if d[1] >= 75]
    condonation = [d for d in data if 65 <= d[1] < 75]
    detained = [d for d in data if d[1] < 65]

    return render_template(
        "hod_dashboard.html",
        eligible=eligible,
        condonation=condonation,
        detained=detained,
        master_list=master_list,
        current_filter=time_filter,
        is_today_working=dbmod.is_working_day(today_str),
        attendance_windows=[("07:30","10:00"),("10:30","13:00")]
    )


# ---------- STUDENT DASHBOARD ----------
@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/")

    sid = session["user_id"]
    today_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
    if dbmod.is_working_day(today_str):
        database.init_today([sid])

    con = get_db()
    cur = con.cursor()
    cur.execute(
        "SELECT date, present FROM attendance WHERE student_id=?",
        (sid,)
    )
    rows = cur.fetchall()
    con.close()

    total = len(rows)
    present = sum(r[1] for r in rows)
    percent = round((present / total) * 100, 2) if total else 0

    return render_template(
        "student_dashboard.html",
        student_id=sid,
        percent=percent,
        records=rows,
        is_today_working=dbmod.is_working_day(today_str),
        attendance_windows=[("07:30","10:00"),("10:30","13:00")]
    )

@app.route("/hod/add-student", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "hod":
        return redirect("/")
    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password") or "123"
        dob = request.form.get("dob")
        con = get_db()
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id, password, role, dob) VALUES (?, ?, 'student', ?)", (user_id, password, dob))
        con.commit()
        con.close()
        database.init_today([user_id])
        return redirect("/hod")
    return render_template("add_student.html")

app.run(debug=True)

