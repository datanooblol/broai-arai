from typing import Literal, List, Optional, Any
from pydantic import BaseModel, Field
from sentence_transformers.cross_encoder import CrossEncoder
from package.databases.models.longterm import LongTerm
from package.databases.management.longterm import EmbedMethod

class ReRanker(BaseModel):
    model_id:Literal["cross-encoder/ms-marco-MiniLM-L6-v2"] = Field(default="cross-encoder/ms-marco-MiniLM-L6-v2")
    model:Any = None

    def __init__(self, **data):
        super().__init__(**data)
        self.model = self.get_model()

    def get_model(self):
        return CrossEncoder(model_name_or_path=self.model_id)
    
    def get_embed_method(self, embed_method:EmbedMethod):
        return {}

    def run(self, search_query:str, longterms:List[LongTerm], embed_method:EmbedMethod, limit:int=5):
        paired_sentences = [[search_query, longterm.model_dump().get(embed_method)] for longterm in longterms]
        scores = self.model.predict(paired_sentences)
        top_rank = scores.argsort()[::-1][:limit]
        ranked_contents = [longterms[n] for n in top_rank]
        ranked_scores = scores[top_rank]
        return ranked_contents, ranked_scores.tolist()