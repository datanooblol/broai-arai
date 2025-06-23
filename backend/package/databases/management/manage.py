from sqlmodel import Session, select, text
from package.databases.models import LongTerm
from package.utils.utils import now_utc
from broai.experiments.huggingface_embedding import BAAIEmbedding
from typing import Literal

EmbedMethod = Literal["raw", "enrich", "combo"]

em = BAAIEmbedding()

class LongTermManagement:
    def __init__(self, embedding=em):
        self.embedding = embedding
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
        raise ValueError(f"Invalid embed_method: {embed_method}")

    def embed_texts(self, embed_method: EmbedMethod, session:Session):
        statement = select(LongTerm).where(self.embed_method.get(embed_method).is_(None))
        results = session.exec(statement).all()
        texts = self._get_texts(results, embed_method)
        vectors = self.embedding.run(texts)
        now = now_utc()
        for result, vector in zip(results, vectors):
            if embed_method=="raw":
                result.raw_embedding = list(vector)
            elif embed_method=="enrich":
                result.enrich_embedding = list(vector)
            elif embed_method=="combo":
                result.combo_embedding = list(vector)
            result.updated_at = now
        session.add_all(results)
        session.commit()
        session.close()

    def read_similar_text(self, query:str, embed_method: EmbedMethod, session:Session, sources:list[str]|None=None, limit:int=5):
        vector = self.embedding.run(sentences=[query])[0]
        statement = select(LongTerm)
        if sources:
            statement.where(text("meta ->> 'source' = ANY(:sources)"))
        statement = statement.order_by(self.embed_method.get(embed_method).l2_distance(vector)).limit(limit).params(sources=sources)
        results = session.exec(statement).all()
        session.close()
        return results