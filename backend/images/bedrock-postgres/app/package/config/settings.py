from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
load_dotenv()  # Load .env into environment variables

class Settings(BaseSettings):
    # DATABASE_URL: str
    VECTOR_SIZE: int = 1024
    DEBUG: bool = False
    DB_HOST: str = os.getenv("DB_HOST", "memory.datanooblol.com")
    DB_PORT: int = 5432

    # class Config:
    #     env_file = ".env"
    #     case_sensitive = True

# Singleton pattern — reuse this instance
settings = Settings()