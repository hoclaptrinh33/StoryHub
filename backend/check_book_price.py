import sqlite3

def check_book():
    conn = sqlite3.connect('storyhub.db')
    cursor = conn.cursor()
    query = """
    SELECT v.p_sell_new, v.isbn, t.name 
    FROM volume v 
    JOIN title t ON t.id = v.title_id 
    WHERE t.name LIKE '%Thực ra, mọi đứa trẻ%'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        print(f"Price: {row[0]}, ISBN: {row[1]}, Title: {row[2]}")
    conn.close()

if __name__ == "__main__":
    check_book()
