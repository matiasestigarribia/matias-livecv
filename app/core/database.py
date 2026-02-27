from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"statement_cache_size": 0},  # Neon pooler (PgBouncer) compatibility
)

async def get_session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
