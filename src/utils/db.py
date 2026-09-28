from sqlalchemy.orm import declarative_base
from src.utils.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker,AsyncSession

Base= declarative_base()

engine = create_async_engine(url=settings.DB_CONNECTION,echo=False)

SessionLocal = async_sessionmaker(bind=engine,class_=AsyncSession,expire_on_commit=False)

async def get_db():
    async with SessionLocal() as db:
        yield db