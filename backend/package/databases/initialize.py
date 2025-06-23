from sqlmodel import SQLModel
from .engine import engine
from sqlmodel import text

def get_extensions():
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
        conn.commit()

def create_db_tables():
    with engine.begin() as conn:
        SQLModel.metadata.create_all(conn)

def initialize_memories():
    get_extensions()
    create_db_tables()