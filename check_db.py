import sqlite3
import os

db_path = r'e:\bài tập lớn\python\StoryHub\storyhub.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT id, name, cover_url FROM title;")
    rows = cursor.fetchall()
    print("--- Titles ---")
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['name']}, Cover: {row['cover_url']}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
