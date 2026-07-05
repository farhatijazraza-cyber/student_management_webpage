import sqlite3

def add_payment_method():
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    try:
        # Vouchers table mein payment_method column add karna
        cursor.execute("ALTER TABLE vouchers ADD COLUMN payment_method TEXT DEFAULT 'Cash';")
        print("Success: 'payment_method' column added successfully!")
    except sqlite3.OperationalError:
        print("Note: Column 'payment_method' already exists.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    add_payment_method()