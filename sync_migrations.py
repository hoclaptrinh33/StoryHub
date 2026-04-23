import sqlite3
import os

db_path = 'storyhub.db'

def fix():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Ensure schema_migrations table exists
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    
    # Check if item_type exists
    cursor.execute("PRAGMA table_info(item)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'item_type' in columns:
        print("Detected 'item_type' column. Marking migration 0005 as applied.")
        cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('0005_add_item_type')")
    
    # Check if 'sold' is in check constraint
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='item'")
    sql = cursor.fetchone()[0]
    if "'sold'" in sql:
        print("Detected 'sold' status support. Marking migration 0006 as applied.")
        cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('0006_allow_sold_status')")

    # Mark 0001, 0003, 0004 as applied if they likely are (tables exist)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'title' in tables:
        cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('0001_initial_schema')")
    if 'user' in tables:
        cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('0003_create_user_table')")
    if 'price_rule' in tables:
        cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('0004_pricing_rules_and_snapshots')")
        
    conn.commit()
    conn.close()
    print("Migration table synced successfully.")

if __name__ == "__main__":
    fix()
