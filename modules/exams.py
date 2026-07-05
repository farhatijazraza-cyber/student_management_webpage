from flask import Blueprint, render_template, request, redirect, url_for
from database import get_connection

exams_bp = Blueprint("exams", __name__, url_prefix="/exams")

# 1. EXAMS HOME (View all exams)
@exams_bp.route("/")
def exams_home():
    conn = get_connection()
    exams = conn.execute("SELECT * FROM exams").fetchall()
    conn.close()
    return render_template("exams.html", exams=exams)

# 2. ADD EXAM
@exams_bp.route("/add", methods=["POST"])
def add_exam():
    exam_name = request.form.get("exam_name")
    exam_date = request.form.get("exam_date")
    conn = get_connection()
    conn.execute("INSERT INTO exams (exam_name, exam_date) VALUES (?, ?)", (exam_name, exam_date))
    conn.commit()
    conn.close()
    return redirect(url_for("exams.exams_home"))

# 3. DELETE EXAM
@exams_bp.route("/delete/<int:id>")
def delete_exam(id):
    conn = get_connection()
    conn.execute("DELETE FROM exams WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("exams.exams_home"))

# 4. MARKS HOME (Add Marks & Subjects Page)
@exams_bp.route("/marks")
def marks_page():
    conn = get_connection()
    # Fetch students, exams, and subjects for dropdowns
    students = conn.execute("SELECT id, name FROM students").fetchall()
    all_exams = conn.execute("SELECT id, exam_name FROM exams").fetchall()
    subjects = conn.execute("SELECT id, subject_name FROM subjects").fetchall()
    
    # Fetch existing marks records
    query = """
        SELECT m.id, s.name, e.exam_name, sub.subject_name, 
               m.marks_obtained, m.total_marks, m.student_id
        FROM marks m
        JOIN students s ON m.student_id = s.id
        JOIN exams e ON m.exam_id = e.id
        JOIN subjects sub ON m.subject_id = sub.id
    """
    marks_list = conn.execute(query).fetchall()
    conn.close()
    return render_template("marks.html", 
                           students=students, 
                           exams=all_exams, 
                           subjects=subjects, 
                           marks=marks_list)

# 5. ADD SUBJECT
@exams_bp.route("/subjects/add", methods=["POST"])
def add_subject():
    sub_name = request.form.get("subject_name")
    if sub_name:
        conn = get_connection()
        conn.execute("INSERT OR IGNORE INTO subjects (subject_name) VALUES (?)", (sub_name,))
        conn.commit()
        conn.close()
    return redirect(url_for("exams.marks_page"))

# 6. ADD MARKS (The function that likely broke)
@exams_bp.route("/marks/add", methods=["POST"])
def add_marks():
    data = (
        request.form['student_id'], 
        request.form['exam_id'], 
        request.form['subject_id'], 
        request.form['marks_obtained'], 
        request.form.get('total_marks', 100)
    )
    conn = get_connection()
    conn.execute("INSERT INTO marks (student_id, exam_id, subject_id, marks_obtained, total_marks) VALUES (?,?,?,?,?)", data)
    conn.commit()
    conn.close()
    return redirect(url_for("exams.marks_page"))

# 7. STUDENT REPORT (Result Card)
@exams_bp.route("/report/<int:student_id>")
def student_report(student_id):
    conn = get_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    query = """
        SELECT e.exam_name, sub.subject_name, m.marks_obtained, m.total_marks
        FROM marks m
        JOIN exams e ON m.exam_id = e.id
        JOIN subjects sub ON m.subject_id = sub.id
        WHERE m.student_id = ?
    """
    report_data = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return render_template("student_result.html", student=student, results=report_data)

@exams_bp.route("/positions/<int:exam_id>")
def view_positions(exam_id):
    conn = get_connection()
    # Query jo total marks calculate karke bacho ko rank karegi
    query = """
        SELECT s.name, 
               SUM(m.marks_obtained) as total_obtained, 
               SUM(m.total_marks) as total_allowed,
               (CAST(SUM(m.marks_obtained) AS FLOAT) / SUM(m.total_marks)) * 100 as percentage
        FROM marks m
        JOIN students s ON m.student_id = s.id
        WHERE m.exam_id = ?
        GROUP BY m.student_id
        ORDER BY total_obtained DESC
        LIMIT 3
    """
    top_students = conn.execute(query, (exam_id,)).fetchall()
    
    exam_info = conn.execute("SELECT exam_name FROM exams WHERE id = ?", (exam_id,)).fetchone()
    conn.close()
    return render_template("positions.html", students=top_students, exam=exam_info)

# Date Sheet View & Add Page
@exams_bp.route("/datesheet/<int:exam_id>")
def view_datesheet(exam_id):
    conn = get_connection()
    # Exam ki details aur subjects fetch karna dropdown ke liye
    exam = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    subjects = conn.execute("SELECT * FROM subjects").fetchall()
    
    # Existing Datesheet fetch karna
    query = """
        SELECT ds.*, sub.subject_name 
        FROM datesheets ds
        JOIN subjects sub ON ds.subject_id = sub.id
        WHERE ds.exam_id = ?
        ORDER BY ds.exam_date ASC
    """
    datesheet = conn.execute(query, (exam_id,)).fetchall()
    conn.close()
    return render_template("datesheet.html", exam=exam, subjects=subjects, datesheet=datesheet)

# Save Date Sheet Entry
@exams_bp.route("/datesheet/add", methods=["POST"])
def add_datesheet_entry():
    exam_id = request.form.get("exam_id")
    data = (
        exam_id,
        request.form.get("subject_id"),
        request.form.get("exam_date"),
        request.form.get("start_time"),
        request.form.get("end_time"),
        request.form.get("room_no")
    )
    conn = get_connection()
    conn.execute("""
        INSERT INTO datesheets (exam_id, subject_id, exam_date, start_time, end_time, room_no) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()
    return redirect(url_for("exams.view_datesheet", exam_id=exam_id))