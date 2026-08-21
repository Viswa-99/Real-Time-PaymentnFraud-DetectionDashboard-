from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Synchronous engine for migrations and sync operations
SQLALCHEMY_DATABASE_URL = f"postgresql+psql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

# Asynchronous engine for FastAPI async routes
async_database_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

async_engine = create_async_engine(
    async_database_url,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, autocommit=False, autoflush=True)

# Base model for ORM
Base = declarative_base()

# Dependency to get sync DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get async DB session
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session