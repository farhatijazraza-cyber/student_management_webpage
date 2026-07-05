import sqlite3

def get_connection():
    conn = sqlite3.connect("school.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Students Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            father_name TEXT,
            father_id TEXT,
            class_name TEXT NOT NULL,
            dob DATE,
            gender TEXT,
            address TEXT,
            contact TEXT,
            photo TEXT DEFAULT 'default.png'
        )
    """)

    # 2. Vouchers Table (NEW: Billing Logic ke liye)
    # Is mein hum mahine ka bill generate karenge
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            month TEXT,
            year TEXT,
            current_fee REAL,
            arrears REAL,
            total_payable REAL,
            paid_amount REAL DEFAULT 0,
            remaining_balance REAL,
            status TEXT DEFAULT 'Unpaid',
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)

    # 3. Payments Table (NEW: Har transaction ka record)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_id INTEGER,
            amount_received REAL,
            date_paid DATE,
            FOREIGN KEY (voucher_id) REFERENCES vouchers (id)
        )
    """)

    # 4. Exams Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT,
            exam_date TEXT
        )
    """)

    # 5. Subjects Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL UNIQUE
        )
    """)

    # 6. Marks Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            marks_obtained INTEGER NOT NULL,
            total_marks INTEGER NOT NULL DEFAULT 100,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(exam_id) REFERENCES exams(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
    """)

    # 7. Attendance Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id),
            UNIQUE(student_id, date)
        )
    """)

    conn.commit()
    conn.close()
    print("Database Initialized with Accounting Tables!")

if __name__ == "__main__":
    init_db()