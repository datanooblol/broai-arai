from sqlmodel import create_engine
from package.config.settings import settings
from .models import *

DATABASE_URL = f"postgresql://broai:broai@{settings.DB_HOST}:{settings.DB_PORT}/arai"
engine = create_engine(DATABASE_URL, echo=settings.DEBUG)