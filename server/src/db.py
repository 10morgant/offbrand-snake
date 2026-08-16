import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DEFAULT_DB_URL = "postgresql+psycopg2://appuser:StrongPassword123@localhost:5432/python"
db: str = os.environ.get("DB_URL", DEFAULT_DB_URL)


def get_async_db_url() -> str:
    if db.startswith("postgresql+psycopg2://"):
        return db.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return db


async def get_session():
    engine = create_async_engine(get_async_db_url(), echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
