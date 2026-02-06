import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> int:
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        print("POSTGRES_DSN is not set", file=sys.stderr)
        return 2

    engine = create_async_engine(dsn, pool_pre_ping=True)

    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return 0
    except Exception as e:
        print(f"DB not ready: {e!r}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))