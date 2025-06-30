from package.databases.models.jargon import Jargon
from sqlmodel import Session, select
from package.databases.utils import now_utc, BadRequestError
from typing import List

class JargonManagement:
    def __init__(self):
        pass

    def create_jargons(self, jargons: List[Jargon], session: Session):
        session.add_all(jargons)
        session.commit()
        session.close()
    
    def read_jargon(self, jargon_id: str, session: Session):
        statement = select(Jargon).where(Jargon.id == jargon_id)
        jargon = session.exec(statement).one_or_none()
        session.close()
        return jargon

    def read_jargons(self, session: Session):
        statement = select(Jargon)
        results = session.exec(statement).all()
        return results

    def update_jargon(self, jargon: Jargon, session: Session):
        jargon.updated_at = now_utc()
        session.add(jargon)
        session.commit()
        session.refresh(jargon)
        session.close()
        return jargon

    def delete_jargon(self, jargon: Jargon, session: Session):
        session.delete(jargon)
        session.commit()
        session.close()
        return jargon

    def read_similar_jargons(self, query: str, session: Session, limit: int = 5):
        """Decide to use either fulltext search or similarity search"""
        pass