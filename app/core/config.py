from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "mysecretkey"
    SESSION_COOKIE_NAME: str = "em_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 30
    ENV: str = "development"  # Default to development
    RESEND_API_KEY: str = "re_XWEw3J25_EkNSTcGKLvNErCd8AVpBhvTP"
    
    # Only force SQLite for local development
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug: Print the DATABASE_URL being used
        print(f"🔍 DATABASE_URL from environment: {self.DATABASE_URL}")
        print(f"🔍 ENV: {self.ENV}")
        
        # Check if we're in a production environment (Railway, Heroku, etc.)
        is_production = (
            "railway" in self.DATABASE_URL.lower() or
            "heroku" in self.DATABASE_URL.lower() or
            "render" in self.DATABASE_URL.lower() or
            "vercel" in self.DATABASE_URL.lower() or
            "fly.io" in self.DATABASE_URL.lower() or
            ("postgresql" in self.DATABASE_URL.lower() and 
             "localhost" not in self.DATABASE_URL.lower() and 
             "127.0.0.1" not in self.DATABASE_URL.lower() and
             "postgres-p" not in self.DATABASE_URL.lower() and  # Railway internal hostname
             "internal" not in self.DATABASE_URL.lower())  # Internal hostnames
        )
        
        # Force SQLite for local development
        if is_production:
            print("🌐 Using production database configuration")
        else:
            print("🔄 Using SQLite for local development")
            self.DATABASE_URL = "sqlite:///./app.db"
            
        # Always use SQLite for local development (override any PostgreSQL)
        if "127.0.0.1" in self.DATABASE_URL or "localhost" in self.DATABASE_URL:
            print("🔄 Overriding to SQLite for localhost development")
            self.DATABASE_URL = "sqlite:///./app.db"
        
        print(f"✅ Final DATABASE_URL: {self.DATABASE_URL}")
    
    # Email settings for Google Workspace/Gmail
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "info@yourbudgetpulse.online"
    SMTP_PASSWORD: str = "aify lxiz krxq ncyf"
    FROM_EMAIL: str = "info@yourbudgetpulse.online"  # Use authenticated email as sender
    FROM_NAME: str = "Budget Pulse"
    BASE_URL: str = "http://localhost:8000"  # Default to localhost for development
    
    # Alternative SMTP settings for fallback (Google SMTP with SSL)
    SMTP_SERVER_ALT: str = "smtp.gmail.com"  # Alternative server
    SMTP_PORT_ALT: int = 465  # SSL port
    
    # Resend settings for production (when SMTP is blocked)
    RESEND_FROM_EMAIL: str = "info@yourbudgetpulse.online"
    RESEND_FROM_NAME: str = "Budget Pulse"

    # ✅ Pydantic v2 way to load .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()