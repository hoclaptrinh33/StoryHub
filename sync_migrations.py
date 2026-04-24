import sqlite3
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
MIGRATIONS_DIR = BASE_DIR / "backend" / "app" / "db" / "migrations"

# Kiểm tra thư mục migrations có tồn tại không
if not MIGRATIONS_DIR.exists():
    print(f"❌ Không tìm thấy thư mục migrations tại: {MIGRATIONS_DIR}")
    exit(1)

# Tìm tất cả file .up.sql trong thư mục migrations
sql_files = list(MIGRATIONS_DIR.glob("*.up.sql"))
if not sql_files:
    print("❌ Không tìm thấy file .up.sql nào trong thư mục migrations")
    exit(1)

# Sắp xếp theo tên file (số thứ tự đầu tiên)
def extract_number(filename):
    match = re.search(r'^(\d+)', filename.name)
    return int(match.group(1)) if match else 999

sql_files.sort(key=extract_number)

print(f"📂 Tìm thấy {len(sql_files)} migration files:")
for f in sql_files:
    print(f"   - {f.name}")

# Tìm database
db_files = list(BASE_DIR.glob("*.db"))
if db_files:
    DB_PATH = db_files[0]
    print(f"📁 Tìm thấy database: {DB_PATH}")
else:
    DB_PATH = BASE_DIR / "storyhub.db"
    print(f"📁 Chưa có database, sẽ tạo mới: {DB_PATH}")

def run_migrations():
    # Backup database cũ
    if DB_PATH.exists() and DB_PATH.is_file():
        backup = DB_PATH.with_suffix('.backup.db')
        DB_PATH.rename(backup)
        print(f"💾 Đã backup database cũ thành {backup}")
    elif DB_PATH.exists():
        print(f"⚠️ Đường dẫn {DB_PATH} là thư mục, bỏ qua backup.")
    else:
        print("ℹ️ Không có database cũ.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for migration_file in sql_files:
        print(f"➡️ Đang chạy: {migration_file.name}")
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        try:
            cursor.executescript(sql_script)
            conn.commit()
        except Exception as e:
            print(f"🔥 Lỗi tại {migration_file.name}: {e}")
            conn.rollback()
            break
    else:
        print("✅ Migration hoàn tất! Database đã sẵn sàng.")

    conn.close()

if __name__ == "__main__":
    run_migrations()