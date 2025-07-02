from sqlmodel import Session, select, text
from package.databases.models import LongTerm
from package.databases.utils import now_utc, BadRequestError
# from broai.experiments.huggingface_embedding import BAAIEmbedding
from typing import Literal

EmbedMethod = Literal["raw", "enrich", "combo"]


class LongTermManagement:
    def __init__(self):
        self.embed_method = {
            "raw": LongTerm.raw_embedding,
            "enrich": LongTerm.enrich_embedding,
            "combo": LongTerm.combo_embedding
        }

    def create_raws(self, longterms:list[LongTerm], session:Session):
        session.add_all(longterms)
        session.commit()
        session.close()

    def _get_texts(self, results, embed_method: EmbedMethod):
        if embed_method == "raw":
            return [result.raw for result in results]
        if embed_method == "enrich":
            return [result.enrich for result in results]
        if embed_method == "combo":
            return [result.combo for result in results]
        raise BadRequestError(detail=f"Invalid embed_method: {embed_method}")

    def update_longterms(self, longterms:list[LongTerm], session:Session):
        now = now_utc()
        for longterm in longterms:
            longterm.updated_at = now
        session.add_all(longterms)
        session.commit()
        session.close()
    
    def read_similar_text(self, vector, embed_method: EmbedMethod, session:Session, sources:list[str]|None=None, limit:int=5):
        statement = select(LongTerm)
        if sources:
            statement = statement.where(text("meta ->> 'source' = ANY(:sources)"))
        statement = statement.order_by(self.embed_method.get(embed_method).cosine_distance(vector)).limit(limit).params(sources=sources)
        results = session.exec(statement).all()
        session.close()
        return results    
    
    def read_longterm(self, longterm_id:str, session:Session):
        statement = select(LongTerm).where(LongTerm.id == longterm_id)
        results = session.exec(statement).first()
        session.close()
        return results

    def read_longterms_by_document(self, document_id:str, session:Session):
        statement = select(LongTerm).where(LongTerm.document_id == document_id)
        results = session.exec(statement).all()
        session.close()
        return results