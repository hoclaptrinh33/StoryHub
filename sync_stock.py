import sqlite3

db_path = r'e:\bài tập lớn\python\StoryHub\backend\storyhub.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tạo bảng promotion
cursor.execute("""
    CREATE TABLE IF NOT EXISTS promotion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        discount_type TEXT NOT NULL CHECK (discount_type IN ('percent', 'amount')),
        discount_value INTEGER NOT NULL,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Tạo bảng promotion_item
cursor.execute("""
    CREATE TABLE IF NOT EXISTS promotion_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        promotion_id INTEGER NOT NULL,
        target_type TEXT NOT NULL CHECK (target_type IN ('volume', 'title')),
        target_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (promotion_id) REFERENCES promotion(id) ON DELETE CASCADE
    )
""")

print("Tables 'promotion' and 'promotion_item' created successfully.")
conn.commit()
conn.close()