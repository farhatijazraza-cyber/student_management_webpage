import sqlite3

def add_payment_date():
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    try:
        # Payment date column add karna (Default empty)
        cursor.execute("ALTER TABLE vouchers ADD COLUMN payment_date TEXT;")
        print("Success: 'payment_date' column added!")
    except sqlite3.OperationalError:
        print("Note: Column already exists.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_payment_date()