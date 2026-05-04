import sqlite3
conn = sqlite3.connect('backend/storyhub.db')
cursor = conn.cursor()

print("=== USERS ===")
for row in cursor.execute("SELECT id, username, role FROM user"):
    print(row)

cursor.execute("INSERT OR IGNORE INTO customer (id, name, phone, membership_level) VALUES (1, 'Khách lẻ', '0000000000', 'standard');")
conn.commit()
print("\n=== CUSTOMERS ===")
for row in cursor.execute("SELECT id, name, phone FROM customer LIMIT 5"):
    print(row)

conn.close()