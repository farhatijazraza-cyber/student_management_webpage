from flask import Blueprint, render_template, request, redirect
from database import get_connection
from datetime import date

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/")
def attendance_home():
    conn = get_connection()
    records = conn.execute("""
        SELECT attendance.*, students.name
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """).fetchall()
    conn.close()
    return render_template("attendance.html", records=records)


@attendance_bp.route("/mark", methods=["POST"])
def mark_attendance():
    student_id = request.form["student_id"]
    status = request.form["status"]

    conn = get_connection()
    conn.execute("""
        INSERT INTO attendance (student_id, date, status)
        VALUES (?, ?, ?)
    """, (student_id, date.today(), status))

    conn.commit()
    conn.close()
    return redirect("/attendance/")
