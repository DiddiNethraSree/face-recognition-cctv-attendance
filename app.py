from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "attendance_secret"

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
            else:
                return redirect("/staff")

        return "Invalid credentials"

    return render_template("login.html")


# ---------- STAFF DASHBOARD ----------
@app.route("/staff")
def staff():
    if session.get("role") != "staff":
        return redirect("/")

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT student_id,
               ROUND(SUM(present)*100.0/COUNT(*),2) AS percent
        FROM attendance
        GROUP BY student_id
    """)
    data = cur.fetchall()
    con.close()

    eligible = [d for d in data if d[1] > 75]
    condonation = [d for d in data if 65 <= d[1] <= 75]
    detained = [d for d in data if d[1] < 65]

    return render_template(
        "staff_dashboard.html",
        eligible=eligible,
        condonation=condonation,
        detained=detained
    )

# ---------- STUDENT DASHBOARD ----------
@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/")

    sid = session["user_id"]   # ✅ FIXED HERE

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
        records=rows
    )

app.run(debug=True)

