import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime, time
from zoneinfo import ZoneInfo
from database import init_today, mark_present, is_working_day

# ---------------- CONFIG ----------------
THRESHOLD = 0.45
ENCODINGS_PATH = "encodings.pickle"

# ---------------- LOAD ENCODINGS ----------------
with open(ENCODINGS_PATH, "rb") as f:
    data = pickle.load(f)

known_encodings = np.array(data["encodings"])
known_names = np.array(data["names"])

all_students = set(known_names)
present_students = set()

# Attendance windows
WINDOWS = [(time(7,30), time(10,0)), (time(10,30), time(13,0))]
IST = ZoneInfo("Asia/Kolkata")

def in_attendance_window(now=None):
    now = now or datetime.now(IST).time()
    for start, end in WINDOWS:
        if start <= now <= end:
            return True
    return False

# Initialize today's attendance only on working days
today_str = datetime.now(IST).strftime("%Y-%m-%d")
if is_working_day(today_str):
    init_today(all_students)

# ---------------- START CAMERA ----------------
cap = cv2.VideoCapture(0)
print("Press 'Q' to stop")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize for speed
    small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, boxes)

    for (top, right, bottom, left), encoding in zip(boxes, encodings):
        distances = face_recognition.face_distance(known_encodings, encoding)
        best_idx = np.argmin(distances)
        best_dist = distances[best_idx]

        # Scale back box
        top, right, bottom, left = top*2, right*2, bottom*2, left*2

        if best_dist < THRESHOLD and in_attendance_window() and is_working_day(datetime.now(IST).strftime("%Y-%m-%d")):
            student_id = known_names[best_idx]
            accuracy = round((1 - best_dist) * 100, 2)

            if student_id not in present_students:
                mark_present(student_id)
                present_students.add(student_id)

            label = f"{student_id} ({accuracy}%)"
            color = (0, 255, 0)
        else:
            label = "UNKNOWN"
            color = (0, 0, 255)

        # Draw box & label
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, top - 30), (right, top), color, -1)
        cv2.putText(
            frame, label,
            (left + 5, top - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (255, 255, 255), 2
        )

    cv2.imshow("CCTV Attendance", frame)

    if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
        print("✔ Attendance session ended by user")
        break

# ---------------- CLEAN EXIT ----------------
cap.release()
cv2.destroyAllWindows()

# ---------------- FINAL SUMMARY ----------------
print("\n📊 ATTENDANCE SUMMARY (PRESENT ONLY)")
print(f"Present: {len(present_students)}")
for s in sorted(present_students):
    print(" ✔", s)

