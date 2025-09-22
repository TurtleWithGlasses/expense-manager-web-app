from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "mysecretkey"
    SESSION_COOKIE_NAME: str = "em_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 30
    ENV: str = "dev"
    
    # Only force SQLite for local development (when ENV=dev)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug: Print the DATABASE_URL being used
        print(f"🔍 DATABASE_URL from environment: {self.DATABASE_URL}")
        print(f"🔍 ENV: {self.ENV}")
        
        # Only override to SQLite for local development
        if self.ENV.lower() == "dev" and ("postgres" in self.DATABASE_URL.lower() or "railway" in self.DATABASE_URL.lower()):
            print("🔄 Overriding PostgreSQL URL with SQLite for local development")
            self.DATABASE_URL = "sqlite:///./app.db"
        
        print(f"✅ Final DATABASE_URL: {self.DATABASE_URL}")
    
    # Add these email settings to the main Settings class
    SMTP_SERVER: str = "mail.talivio.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "info@yourbudgetpulse.online"
    SMTP_PASSWORD: str = "123456"
    FROM_EMAIL: str = "info@yourbudgetpulse.online"  # Use authenticated email as sender
    FROM_NAME: str = "Budget Pulse"
    BASE_URL: str = "http://localhost:8000"

    # ✅ Pydantic v2 way to load .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()