
import asyncio
import json
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///e:/bài tập lớn/python/StoryHub/storyhub.db"

async def test_history():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        query = text("""
            SELECT 
                al.id,
                al.created_at AS timestamp,
                al.action,
                al.entity_type,
                al.entity_id,
                al.actor_user_id,
                al.before_json AS before,
                al.after_json AS after,
                al.ip_address,
                al.device_id,
                u.full_name AS user_name
            FROM audit_log al
            LEFT JOIN user u ON al.actor_user_id = u.id
            WHERE al.entity_type IN ('title', 'volume', 'item', 'cover')
            ORDER BY al.created_at DESC
            LIMIT 10 OFFSET 0
        """)
        
        result = await session.execute(query)
        rows = result.mappings().all()
        print(f"Rows found: {len(rows)}")
        
        for row in rows:
            print(f"Row: {row['id']}, timestamp type: {type(row['timestamp'])}")
            try:
                ts = row["timestamp"].isoformat() if row["timestamp"] else ""
                before_data = json.loads(row["before"]) if row["before"] else None
                after_data = json.loads(row["after"]) if row["after"] else None
                print(f"  OK: {row['id']}")
            except Exception as e:
                print(f"  ERROR Row {row['id']}: {e}")

if __name__ == "__main__":
    asyncio.run(test_history())
