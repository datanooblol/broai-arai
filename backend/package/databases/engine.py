from sqlmodel import create_engine
from package.config.settings import settings
from .models import *

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)