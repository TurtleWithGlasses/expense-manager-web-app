from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ensure we're using SQLite for local development
database_url = settings.DATABASE_URL
if "postgres" in database_url.lower() or "railway" in database_url.lower():
    print("⚠️  Detected PostgreSQL URL, forcing SQLite for local development")
    database_url = "sqlite:///./app.db"

print(f"🔧 Creating database engine with URL: {database_url}")

engine = create_engine(
    database_url, 
    pool_pre_ping=True, 
    future=True,
    # SQLite-specific settings
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)