from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "mysecretkey"
    SESSION_COOKIE_NAME: str = "em_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 30
    ENV: str = "development"  # Default to development
    RESEND_API_KEY: str = "re_XWEw3J25_EkNSTcGKLvNErCd8AVpBhvTP"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug: Print the DATABASE_URL being used
        print(f"DATABASE_URL from environment: {self.DATABASE_URL}")
        print(f"ENV: {self.ENV}")
        
        # Determine environment based on multiple factors
        is_local_development = (
            self.ENV.lower() in ["development", "dev", "local"] or
            "localhost" in self.DATABASE_URL or
            "127.0.0.1" in self.DATABASE_URL or
            self.DATABASE_URL == "sqlite:///./app.db" or
            # Check if we're running locally (not in a cloud environment)
            not any(cloud_indicator in self.DATABASE_URL.lower() for cloud_indicator in [
                "railway", "heroku", "render", "vercel", "fly.io", "aws", "azure", "gcp"
            ])
        )
        
        # Only override to SQLite if we're definitely in local development
        if is_local_development and not self.DATABASE_URL.startswith("sqlite"):
            print("Local development detected - using SQLite")
            self.DATABASE_URL = "sqlite:///./app.db"
            # Set BASE_URL for local development
            self.BASE_URL = "http://localhost:8000"
        elif "railway" in self.DATABASE_URL.lower() or "heroku" in self.DATABASE_URL.lower():
            print("Production environment detected - using provided database")
            # Set BASE_URL for production
            self.BASE_URL = "https://www.yourbudgetpulse.online"
        else:
            print(f"Using configured database: {self.DATABASE_URL}")
        
        print(f"Final DATABASE_URL: {self.DATABASE_URL}")
        print(f"Final BASE_URL: {self.BASE_URL}")
    
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