from package.databases.engine import engine
from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session

def Depends(func):
    return next(func())