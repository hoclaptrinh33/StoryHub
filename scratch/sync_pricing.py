import sqlite3

def update_pricing():
    dbs = ['storyhub.db', 'backend/storyhub.db']
    for db_path in dbs:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Cập nhật k_rent và k_deposit cho rule đang active
            cursor.execute("""
                UPDATE price_rule 
                SET k_rent = 0.05, k_deposit = 0.3 
                WHERE status = 'active'
            """)
            
            if cursor.rowcount > 0:
                print(f"SUCCESS: Updated {db_path} ({cursor.rowcount} row(s))")
            else:
                print(f"WARNING: No active rule found in {db_path}")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"ERROR: Could not update {db_path}: {e}")

if __name__ == "__main__":
    update_pricing()
