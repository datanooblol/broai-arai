from sqlmodel import SQLModel
from .engine import engine  # your existing engine

def drop_all_tables():
    with engine.begin() as conn:
        SQLModel.metadata.drop_all(conn)
    print("✅ All tables dropped.")