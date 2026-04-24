import asyncio
from sqlalchemy import text
from app.db.session import get_db_session
from app.api.v1.endpoints.customers import CustomerListItem

async def test():
    async for session in get_db_session():
        query_str = "SELECT id, name, phone, membership_level, deposit_balance, debt, blacklist_flag, address FROM customer WHERE name LIKE '%Lê Hải Đăng%' LIMIT 5"
        result = await session.execute(text(query_str))
        rows = result.mappings().all()
        for row in rows:
            c = CustomerListItem(
                id=row["id"],
                name=row["name"],
                phone=row["phone"],
                membership_level=row["membership_level"],
                deposit_balance=row["deposit_balance"],
                debt=row["debt"],
                blacklist_flag=bool(row["blacklist_flag"]),
                address=row["address"],
            )
            print(f"ID: {c.id}, Name: {c.name[:10]}, Addr: {c.address}")
        break

if __name__ == "__main__":
    asyncio.run(test())
