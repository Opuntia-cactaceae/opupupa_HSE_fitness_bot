from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config.settings import settings


engine = create_async_engine(settings.POSTGRES_DSN, echo=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)