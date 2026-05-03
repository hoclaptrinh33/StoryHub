import sqlite3

# Đường dẫn đến file database của bạn (thay đổi cho đúng)
DB_PATH = "storyhub.db"  # Ví dụ: "storyhub.db", "database.db", ...

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Truy vấn volume id = 21
    cursor.execute("SELECT id, retail_stock, deleted_at FROM volume WHERE id = ?", (21,))
    row = cursor.fetchone()
    
    if row:
        print(f"✅ Tìm thấy volume 21:")
        print(f"   - retail_stock: {row[1]}")
        print(f"   - deleted_at: {row[2]}")
        if row[2] is not None:
            print("   ⚠️ Volume đã bị xóa mềm (deleted_at khác NULL)")
        else:
            print("   ✅ Volume còn hoạt động (deleted_at NULL)")
    else:
        print("❌ Không tìm thấy volume nào có id = 21")
    
    # Liệt kê tất cả volume đang hoạt động (deleted_at NULL)
    cursor.execute("SELECT id, retail_stock FROM volume WHERE deleted_at IS NULL LIMIT 20")
    active_volumes = cursor.fetchall()
    print("\n📚 Các volume đang hoạt động (deleted_at NULL):")
    for vid, stock in active_volumes:
        print(f"   - id: {vid}, retail_stock: {stock}")
    
    conn.close()
except Exception as e:
    print(f"Lỗi: {e}")