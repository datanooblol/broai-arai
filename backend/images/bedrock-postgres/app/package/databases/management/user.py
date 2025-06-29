from package.databases.models.user import User
from sqlmodel import Session, select
from package.databases.utils import now_utc, BadRequestError
# from fastapi import HTTPException

class UserManagement:
    def __init__(self,):
        pass

    def create_user(self, user: User, session: Session):
        # Check for unique username
        if session.exec(select(User).where(User.username == user.username)).first():
            session.close()
            raise BadRequestError(detail="Username already taken.")

        # Check for unique email
        if session.exec(select(User).where(User.email == user.email)).first():
            session.close()
            raise BadRequestError(detail="Email already registered.")
                
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()
        return user
    
    def read_user(self, user_id: str, session: Session):
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).one_or_none()
        session.close()
        return user

    def update_user(self, user: User, session: Session):
        user.updated_at = now_utc()
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()
        return user

    def delete_user(self, user: User, session: Session):
        session.delete(user)
        session.commit()
        session.close()
        return user

    def read_user_projects(self, user_id: str, session: Session):
        user = session.get(User, user_id)
        projects = user.projects if user else []
        session.close()
        return projects