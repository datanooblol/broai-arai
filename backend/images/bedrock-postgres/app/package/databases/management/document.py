from package.databases.models.document import Document
from sqlmodel import Session, select
from package.databases.utils import now_utc, BadRequestError
# from fastapi import HTTPException

class DocumentManagement:
    def __init__(self):
        pass

    def create_document(self, document: Document, session: Session):
        # Check for unique document source and type
        if session.exec(select(Document).where(
            (Document.source == document.source) & (Document.type == document.type)
        )).first():
            session.close()
            raise BadRequestError(detail="Document with this source and type already exists.")

        session.add(document)
        session.commit()
        session.refresh(document)
        session.close()
        return document
    
    def read_document(self, document_id: str, session: Session):
        statement = select(Document).where(Document.id == document_id)
        document = session.exec(statement).one_or_none()
        session.close()
        return document

    def read_documents(self, session: Session):
        statement = select(Document)
        documents = session.exec(statement).all()
        session.close()
        return documents

    def update_document(self, document: Document, session: Session):
        document.updated_at = now_utc()
        session.add(document)
        session.commit()
        session.refresh(document)
        session.close()
        return document

    def delete_document(self, document: Document, session: Session):
        session.delete(document)
        session.commit()
        session.close()
        return document
    
    def read_document_longterms(self, document_id: str, session: Session):
        document = session.get(Document, document_id)
        longterms = document.longterms if document else []
        session.close()
        return longterms

    # def read_document_jargons(self, document_id: str, session: Session):
    #     document = session.get(Document, document_id)
    #     jargons = document.jargons if document else []
    #     session.close()
    #     return jargons

    def read_document_terms(self, document_id: str, session: Session):
        document = session.get(Document, document_id)
        terms = document.terms if document else []
        session.close()
        return terms