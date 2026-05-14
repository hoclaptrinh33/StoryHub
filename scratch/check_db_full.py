import sqlite3

def check_db():
    conn = sqlite3.connect('storyhub.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print("Tables:", tables)
    
    # Check columns for 'item'
    cursor.execute("PRAGMA table_info(item)")
    item_cols = [c[1] for c in cursor.fetchall()]
    print("Item columns:", item_cols)
    
    conn.close()

if __name__ == "__main__":
    check_db()
