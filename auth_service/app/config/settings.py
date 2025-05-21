from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = 'postgres'
    POSTGRES_DB_NAME: str = 'chronary_auth'
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_PORT: int = 25432
    POSTGRES_HOST: str =  'localhost'

    # JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 3
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # General
    PROJECT_NAME: str = "Chronary Auth Service"
    API_V1_STR: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

