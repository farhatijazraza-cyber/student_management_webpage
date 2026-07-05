from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
from werkzeug.utils import secure_filename
import os

admission_bp = Blueprint('admission', __name__, url_prefix='/admission')

DB_PATH = "school.db"

# ---------- Add Student (Admission Home) ----------
@admission_bp.route("/", methods=["GET", "POST"])
def admission_home():
    if request.method == "POST":
        name = request.form.get("name")
        father_name = request.form.get("father_name")
        father_id = request.form.get("father_id") 
        dob = request.form.get("dob")
        class_name = request.form.get("class_name")
        contact = request.form.get("contact")
        address = request.form.get("address")
        
        # Discount ko float mein convert karna zaroori hai taake math calculation sahi ho
        discount = request.form.get("discount", 0)
        if not discount: discount = 0
        discount = float(discount)

        # Photo Handle Karein
        file = request.files.get('photo')
        photo_filename = "default.png"
        
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            # Folder check karein agar mojud nahi toh banayein
            upload_path = 'static/uploads/students'
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
                
            # Unique filename: Name + Contact (taake overlap na ho)
            photo_filename = f"{secure_filename(name)}_{contact}.jpg" 
            file.save(os.path.join(upload_path, photo_filename))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            c.execute("""
                INSERT INTO students (name, father_name, father_id, dob, class_name, contact, address, discount, photo) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (name, father_name, father_id, dob, class_name, contact, address, discount, photo_filename)
            )
            conn.commit()
            flash(f"Student {name} registered successfully with Rs.{discount} monthly scholarship!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            conn.close()

        return redirect(url_for("admission.view_students"))

    return render_template("admission/add_student.html")

# ---------- View Students ----------
@admission_bp.route("/view")
def view_students():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Is se data column names ke sath milta hai
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template("admission/view_students.html", students=students)

# ---------- Delete Student ----------
@admission_bp.route("/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Student record deleted!", "danger")
    return redirect(url_for("admission.view_students"))

# ---------- Edit Student (Form) ----------
@admission_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        father_name = request.form.get("father_name")
        dob = request.form.get("dob")
        class_name = request.form.get("class_name")
        contact = request.form.get("contact")
        address = request.form.get("address")

        c.execute("""UPDATE students SET name=?, father_name=?, dob=?, class_name=?, contact=?, address=? 
                     WHERE id=?""", (name, father_name, dob, class_name, contact, address, id))
        conn.commit()
        conn.close()
        flash("Student record updated!", "info")
        return redirect(url_for("admission.view_students"))

    c.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = c.fetchone()
    conn.close()
    return render_template("admission/edit_student.html", student=student)

# ---------- Student Profile View ----------
@admission_bp.route("/profile/<int:id>")
def student_profile(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = c.fetchone()
    conn.close()
    
    if student is None:
        flash("Student not found!", "danger")
        return redirect(url_for('admission.view_students'))
        
    return render_template("admission/student_profile.html", student=student)