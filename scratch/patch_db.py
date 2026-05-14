import sqlite3

def patch_db():
    conn = sqlite3.connect('storyhub.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE item ADD COLUMN item_type TEXT DEFAULT 'rental'")
        print("Column 'item_type' added to 'item' table.")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    patch_db()
