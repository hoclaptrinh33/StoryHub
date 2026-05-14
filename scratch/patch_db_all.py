import sqlite3
import os

def patch_db(db_path):
    print(f"Checking {db_path}...")
    if not os.path.exists(db_path):
        print("  File not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE item ADD COLUMN item_type TEXT DEFAULT 'rental'")
        print(f"  Column 'item_type' added to 'item' table in {db_path}.")
    except sqlite3.OperationalError as e:
        print(f"  Note: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    patch_db('storyhub.db')
    patch_db('backend/storyhub.db')
