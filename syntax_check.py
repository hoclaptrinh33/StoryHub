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

print("\n=== rule ===")
for row in cursor.execute("""SELECT
                    id,
                    version_no,
                    k_rent,
                    k_deposit,
                    d_floor,
                    used_demand_factor,
                    used_cap_ratio
                FROM price_rule
                WHERE status = 'active'
                  AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
                  AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP)
                ORDER BY activated_at DESC, id DESC
                LIMIT 1;"""):
    print(row)

conn.close()