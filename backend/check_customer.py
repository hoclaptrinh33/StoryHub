import sqlite3

def check():
    conn = sqlite3.connect('storyhub.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, address FROM customer WHERE name LIKE '%Hải Đăng%';")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Phone: {row[2]}, HasAddr: {row[3] is not None}")
    conn.close()

if __name__ == "__main__":
    check()
