from typing import List

from sqlmodel import Session, select
from sqlalchemy import func, or_, and_

from package.databases.models.term import Term
from package.databases.utils import now_utc


class TermManagement:
    def __init__(self):
        pass

    def create_terms(self, terms: List[Term], session: Session):
        session.add_all(terms)
        session.commit()
        session.close()
    
    def read_term(self, term_id: str, session: Session):
        statement = select(Term).where(Term.id == term_id)
        jargon = session.exec(statement).one_or_none()
        session.close()
        return jargon

    def read_terms(self, session: Session):
        statement = select(Term)
        results = session.exec(statement).all()
        return results

    def update_term(self, term: Term, session: Session):
        term.updated_at = now_utc()
        session.add(term)
        session.commit()
        session.refresh(term)
        session.close()
        return term

    def delete_term(self, term: Term, session: Session):
        session.delete(term)
        session.commit()
        session.close()
        return term

    def read_similar_terms(
        self,
        term: str,
        session: Session,
        document_ids: List[str] | None = None,
        limit: int = 5,
        similarity: float = 0.3
    ):
        """Search for similar terms via fulltext or similarity, optionally filtering by document IDs."""
        ts_query = func.to_tsquery("english", term)
        fulltext_condition = Term.search_vector.op('@@')(ts_query)
        similarity_condition = func.similarity(Term.term, term) > similarity
        or_condition = or_(fulltext_condition, similarity_condition)

        if document_ids is not None:
            document_filter = Term.document_id.in_(document_ids)
            final_condition = and_(document_filter, or_condition)
        else:
            final_condition = or_condition

        statement = select(Term).where(final_condition).limit(limit)
        results = session.exec(statement).all()
        return results