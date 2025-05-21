from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = 'postgres'
    POSTGRES_DB_NAME: str = 'chronary_time_tracker'
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_PORT: int = 35432
    POSTGRES_HOST: str = 'localhost'

    # JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"

    # General
    PROJECT_NAME: str = "Chronary Time Tracker Service"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

