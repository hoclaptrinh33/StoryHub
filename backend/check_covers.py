import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('storyhub.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, cover_url FROM title")
        rows = cursor.fetchall()
        print(f"Total titles: {len(rows)}")
        ext_rows = [r for r in rows if str(r[2] or "").startswith("http")]
        print(f"Titles with external URLs: {len(ext_rows)}")
        for row in ext_rows[:10]:
            print(row)
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_db()
