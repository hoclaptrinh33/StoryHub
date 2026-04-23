import sqlite3
import os

db_path = "backend/storyhub.db"

def fix_db():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(item)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "item_type" not in columns:
            print("Adding 'item_type' column to 'item' table...")
            cursor.execute("ALTER TABLE item ADD COLUMN item_type TEXT DEFAULT 'retail'")
            conn.commit()
            print("Successfully added 'item_type' column.")
        else:
            print("'item_type' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fix_db()
