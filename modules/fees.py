from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import date # Yeh top par import karein
import datetime

fees_bp = Blueprint('fees', __name__, url_prefix='/fees')
DB_PATH = "school.db"

@fees_bp.route("/")
def fees_home():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Saare students ki list (Dropdown ke liye)
    all_students = conn.execute("SELECT id, name, class_name FROM students ORDER BY name ASC").fetchall()
    
    # 2. Saare vouchers (Pending list ke liye)
    vouchers = conn.execute("""
        SELECT v.*, s.name, s.class_name 
        FROM vouchers v 
        JOIN students s ON v.student_id = s.id
        ORDER BY v.id DESC
    """).fetchall()

    # 3. Unique classes (Batch printing filter ke liye)
    classes = conn.execute("SELECT DISTINCT class_name FROM students").fetchall()
    
    conn.close()
    
    # Yaad se 'all_students' ko yahan shamil karein
    return render_template("fees/fees_home.html", 
                           vouchers=vouchers, 
                           classes=classes, 
                           all_students=all_students)

import datetime

@fees_bp.route("/generate", methods=["POST"])
def generate_vouchers():
    month = request.form.get("month")
    # Current date se automatic saal (year) nikalne ke liye:
    year = str(datetime.datetime.now().year) 
    
    # User jo fee form mein likhega (Default 3000)
    base_fee = float(request.form.get("monthly_fee", 3000))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Duplicate Check: Kya is month aur year ke vouchers ban chuke hain?
    existing = cursor.execute("SELECT id FROM vouchers WHERE month = ? AND year = ?", (month, year)).fetchone()
    if existing:
        conn.close()
        flash(f"Vouchers for {month} {year} are already generated!", "danger")
        return redirect(url_for('fees.fees_home'))

    # 2. Get all students with their individual discounts
    students = cursor.execute("SELECT id, name, discount FROM students").fetchall()
    
    for s in students:
        s_id = s[0]
        s_discount = s[2] if s[2] else 0 # Student ka scholarship
        
        # 3. Pichla balance (Arrears) check karein
        last_v = cursor.execute("""
            SELECT remaining_balance FROM vouchers 
            WHERE student_id=? ORDER BY id DESC LIMIT 1
        """, (s_id,)).fetchone()
        
        arrears = last_v[0] if last_v else 0
        
        # 4. Final Calculation
        # Is mahine ki net fee = (Base Fee - Individual Discount)
        current_month_net = base_fee - s_discount
        total_to_pay = current_month_net + arrears
        
        cursor.execute("""
            INSERT INTO vouchers (
                student_id, month, year, current_fee, arrears, 
                total_payable, remaining_balance, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_id, month, year, current_month_net, arrears, total_to_pay, total_to_pay, 'Unpaid'))
        
    conn.commit()
    conn.close()
    flash(f"Successfully generated vouchers for {month} {year}. Individual discounts applied!", "success")
    return redirect(url_for('fees.fees_home'))

@fees_bp.route("/pay/<int:v_id>", methods=["GET", "POST"])
def pay_voucher(v_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    voucher = cursor.execute("""
        SELECT v.*, s.name, s.class_name, s.father_name FROM vouchers v 
        JOIN students s ON v.student_id = s.id WHERE v.id = ?
    """, (v_id,)).fetchone()

    if request.method == "POST":
        receiving = float(request.form.get("receiving_amount", 0))
        # Form se payment method uthayen
        method = request.form.get("payment_method", "Cash")
        today_date = date.today().strftime("%Y-%m-%d")
        
        # 1. Maujooda voucher update karein (Date aur Method ke sath)
        new_paid_total = voucher['paid_amount'] + receiving
        new_balance = voucher['total_payable'] - new_paid_total
        status = 'Paid' if new_balance <= 0 else 'Partial'
        
        cursor.execute("""
            UPDATE vouchers 
            SET paid_amount = ?, remaining_balance = ?, status = ?, 
                payment_date = ?, payment_method = ?
            WHERE id = ?
        """, (new_paid_total, new_balance, status, today_date, method, v_id))
        
        # 2. AUTO-UPDATE LOGIC (Future Vouchers)
        future_vouchers = cursor.execute("""
            SELECT id FROM vouchers 
            WHERE student_id = ? AND id > ? 
            ORDER BY id ASC
        """, (voucher['student_id'], v_id)).fetchall()

        for f_v in future_vouchers:
            cursor.execute("""
                UPDATE vouchers 
                SET arrears = arrears - ?, 
                    total_payable = total_payable - ?,
                    remaining_balance = remaining_balance - ?
                WHERE id = ?
            """, (receiving, receiving, receiving, f_v['id']))
        
        conn.commit()
        conn.close()
        flash(f"Payment of Rs.{receiving} via {method} received!", "success")
        return redirect(url_for('fees.view_receipt', v_id=v_id))

    conn.close()
    return render_template("fees/pay_voucher.html", v=voucher)

@fees_bp.route("/receipt/<int:v_id>")
def view_receipt(v_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    receipt_data = conn.execute("""
        SELECT v.*, s.name, s.father_name, s.class_name 
        FROM vouchers v JOIN students s ON v.student_id = s.id 
        WHERE v.id = ?
    """, (v_id,)).fetchone()
    conn.close()
    return render_template("fees/receipt.html", receipt=receipt_data)

@fees_bp.route("/history")
def payment_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Aaj ki date (Format: YYYY-MM-DD)
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    
    # Sirf wo vouchers jin par aaj payment hui hai
    # Note: Humein vouchers table mein 'payment_date' column chahiye hoga agar accurate history chahiye
    # Filhal hum wo dikhate hain jo 'Paid' ya 'Partial' hain
    history = conn.execute("""
        SELECT v.*, s.name, s.class_name 
        FROM vouchers v 
        JOIN students s ON v.student_id = s.id
        WHERE v.paid_amount > 0
        ORDER BY v.id DESC
    """).fetchall()
    
    total_collected = sum(row['paid_amount'] for row in history)
    
    conn.close()
    return render_template("fees/payment_history.html", history=history, total=total_collected)

@fees_bp.route("/print_batch/<class_name>/<month>")
def print_batch(class_name, month):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Class aur Month ke hisaab se vouchers fetch karein
    vouchers = conn.execute("""
        SELECT v.*, s.name, s.father_name, s.class_name, s.contact 
        FROM vouchers v 
        JOIN students s ON v.student_id = s.id 
        WHERE s.class_name = ? AND v.month = ?
    """, (class_name, month)).fetchall()
    
    conn.close()
    return render_template("fees/print_batch.html", vouchers=vouchers, month=month, class_name=class_name)

@fees_bp.route("/delete_payment/<int:v_id>")
def delete_payment(v_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Purana data nikalen
    v = cursor.execute("SELECT * FROM vouchers WHERE id = ?", (v_id,)).fetchone()
    if not v:
        conn.close()
        return "Voucher not found", 404

    paid_to_reverse = v['paid_amount']
    s_id = v['student_id']

    # 2. Current Voucher ko reset karein
    cursor.execute("""
        UPDATE vouchers SET 
        paid_amount = 0, 
        remaining_balance = total_payable, 
        status = 'Unpaid', 
        payment_date = NULL, 
        payment_method = NULL 
        WHERE id = ?
    """, (v_id,))

    # 3. Future Vouchers ka balance wapis barhayen (Reverse Chain Update)
    cursor.execute("""
        UPDATE vouchers 
        SET arrears = arrears + ?, 
            total_payable = total_payable + ?,
            remaining_balance = remaining_balance + ?
        WHERE student_id = ? AND id > ?
    """, (paid_to_reverse, paid_to_reverse, paid_to_reverse, s_id, v_id))

    conn.commit()
    conn.close()
    flash(f"Payment of Rs.{paid_to_reverse} deleted and accounts adjusted!", "warning")
    return redirect(url_for('fees.fees_home'))

from datetime import date

@fees_bp.route("/daily_report")
def daily_report():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Aaj ki date
    today = date.today().strftime("%Y-%m-%d")
    
    # Aaj ki saari payments nikalen
    daily_payments = cursor.execute("""
        SELECT v.*, s.name, s.class_name 
        FROM vouchers v 
        JOIN students s ON v.student_id = s.id
        WHERE v.payment_date = ? AND v.paid_amount > 0
    """, (today,)).fetchall()
    
    # Payment methods ke hisaab se calculation
    cash_total = sum(row['paid_amount'] for row in daily_payments if row['payment_method'] == 'Cash')
    bank_total = sum(row['paid_amount'] for row in daily_payments if row['payment_method'] != 'Cash')
    grand_total = cash_total + bank_total
    
    conn.close()
    return render_template("fees/daily_report.html", 
                           payments=daily_payments, 
                           cash=cash_total, 
                           bank=bank_total, 
                           total=grand_total,
                           today=today)

@fees_bp.route("/statement/<int:s_id>")
def student_statement(s_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Student ki basic info
    student = cursor.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
    
    # Bache ke saare mahino ke vouchers (history)
    history = cursor.execute("""
        SELECT * FROM vouchers 
        WHERE student_id = ? 
        ORDER BY id ASC
    """, (s_id,)).fetchall()
    
    # Total calculation
    total_billed = sum(row['total_payable'] for row in history)
    total_paid = sum(row['paid_amount'] for row in history)
    total_balance = sum(row['remaining_balance'] for row in history)
    
    conn.close()
    return render_template("fees/statement.html", 
                           student=student, 
                           history=history, 
                           billed=total_billed, 
                           paid=total_paid, 
                           balance=total_balance)

# Function ka naam 'generate_single_voucher_post' hona chahiye
@fees_bp.route("/generate_single_post", methods=["POST"])
def generate_single_voucher_post():
    s_id = request.form.get("student_id")
    month = request.form.get("month")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Student detail nikalen
    student = cursor.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
    
    # Check if voucher already exists
    existing = cursor.execute("SELECT id FROM vouchers WHERE student_id = ? AND month = ?", (s_id, month)).fetchone()
    
    if existing:
        # flash message handle karein
        pass 
    else:
        # Fee calculation (Default 3000 - discount)
        current_fee = 3000 - student['discount']
        
        # Pichla balance (Arrears)
        last_v = cursor.execute("SELECT remaining_balance FROM vouchers WHERE student_id = ? ORDER BY id DESC LIMIT 1", (s_id,)).fetchone()
        arrears = last_v['remaining_balance'] if last_v else 0
        
        total = current_fee + arrears
        
        cursor.execute("""
            INSERT INTO vouchers (student_id, month, current_fee, arrears, total_payable, remaining_balance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (s_id, month, current_fee, arrears, total, total, 'Unpaid'))
        conn.commit()
        
    conn.close()
    return redirect(url_for('fees.fees_home'))

@fees_bp.route("/print_single/<int:v_id>")
def print_single(v_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Query mein s.student_id ko s.id kar diya gaya hai
    voucher = conn.execute("""
        SELECT v.*, s.name, s.father_name, s.class_name , s.id as student_id
        FROM vouchers v 
        JOIN students s ON v.student_id = s.id 
        WHERE v.id = ?
    """, (v_id,)).fetchone()
    
    conn.close()
    
    if not voucher:
        flash("Voucher nahi mila!", "danger")
        return redirect(url_for('fees.fees_home'))

    # Kyunke print_batch.html loop mangta hai, hum isay list mein bhejenge
    return render_template("fees/print_batch.html", 
                           vouchers=[voucher], 
                           class_name=voucher['class_name'],
                           month=voucher['month'])