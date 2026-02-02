import asyncio
from infrastructure.config.database import engine
from infrastructure.db.models import Base

async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(main())