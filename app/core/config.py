from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "mysecretkey"
    SESSION_COOKIE_NAME: str = "em_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 30
    ENV: str = "dev"
    
    # Add these email settings to the main Settings class
    SMTP_SERVER: str = "mail.talivio.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "info@yourbudgetpulse.online"
    SMTP_PASSWORD: str = "123456"
    FROM_EMAIL: str = "noreply@yourbudgetpulse.online"
    FROM_NAME: str = "Budget Pulse"
    BASE_URL: str = "http://localhost:8000"

    # ✅ Pydantic v2 way to load .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()