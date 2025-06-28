from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Load .env into environment variables

class Settings(BaseSettings):
    DATABASE_URL: str
    VECTOR_SIZE: int
    DEBUG: bool = False
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton pattern — reuse this instance
settings = Settings()