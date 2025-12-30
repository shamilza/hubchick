from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "postgresql://hubchick:hubchick_dev_password@localhost:5432/hubchick_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@hubchick.com"
    email_from_name: str = "Hubchick"
    
    # Google Calendar
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Yandex Calendar
    yandex_client_id: Optional[str] = None
    yandex_client_secret: Optional[str] = None
    yandex_redirect_uri: str = "http://localhost:8000/api/v1/auth/yandex/callback"
    
    # Application
    environment: str = "development"
    debug: bool = True
    app_name: str = "Hubchick CRM"
    app_version: str = "1.0.0"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
