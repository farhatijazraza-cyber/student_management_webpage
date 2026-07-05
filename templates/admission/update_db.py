import sqlite3

def add_discount_column():
    try:
        conn = sqlite3.connect("school.db")
        cursor = conn.cursor()
        
        # Student table mein discount column add karna
        cursor.execute("ALTER TABLE students ADD COLUMN discount REAL DEFAULT 0;")
        
        conn.commit()
        print("Success: 'discount' column added to students table!")
    except sqlite3.OperationalError:
        print("Note: Column 'discount' already exists or table not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_discount_column()