import sqlite3

db_path = r'e:\bài tập lớn\python\StoryHub\backend\storyhub.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Synchronizing retail_stock for all volumes ---")

# Update retail_stock to be the count of non-deleted retail items for each volume
cursor.execute("""
    UPDATE volume
    SET retail_stock = (
        SELECT COUNT(*) 
        FROM item 
        WHERE item.volume_id = volume.id 
          AND item.item_type = 'retail' 
          AND item.deleted_at IS NULL
    )
""")

print(f"Updated {conn.total_changes} rows.")

conn.commit()
conn.close()
print("Synchronization complete.")
