from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use the DATABASE_URL from settings (already handled by config.py)
database_url = settings.DATABASE_URL

print(f"Creating database engine with URL: {database_url}")

# Create engine with appropriate settings
if "sqlite" in database_url:
    engine = create_engine(
        database_url, 
        pool_pre_ping=True, 
        future=True,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL settings
    engine = create_engine(
        database_url, 
        pool_pre_ping=True, 
        future=True,
        pool_size=10,
        max_overflow=20
    )
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)