import sqlite3

def fix_database():
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    try:
        # Students table mein discount column add karna
        cursor.execute("ALTER TABLE students ADD COLUMN discount REAL DEFAULT 0;")
        print("Success: 'discount' column added!")
    except sqlite3.OperationalError:
        print("Note: Column already exists.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_database()