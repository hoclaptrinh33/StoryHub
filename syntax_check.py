import sqlite3
conn = sqlite3.connect('backend/storyhub.db')
cursor = conn.cursor()

print("=== USERS ===")
for row in cursor.execute("SELECT id, username, role FROM user"):
    print(row)
cursor.execute("""UPDATE price_rule 
SET k_rent = 0.05, k_deposit = 0.3, d_floor = 1000 
WHERE id = 1; """)
conn.commit()

print("\n=== inventory_log ===")
for row in cursor.execute("""SELECT * FROM inventory_log 
WHERE target_type = 'VOLUME' 
  AND action_type = 'STOCK_IN'
  AND date(created_at) BETWEEN '2026-04-04' AND '2026-05-04';"""):
    print(row)

conn.close()