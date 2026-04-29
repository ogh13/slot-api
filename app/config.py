from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str        
    REDIS_URL: str = "redis://redis:6379"
    API_KEY: str = "dev-api-key-change-in-prod"
    API_BASE_URL: str = "http://api:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()