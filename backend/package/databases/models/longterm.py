from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector
from package.config.settings import settings
from typing import Any, Optional, TYPE_CHECKING
from package.utils.utils import datetime, now_utc
from uuid import uuid4

if TYPE_CHECKING:
    from .document import Document  # Avoid circular import issues

class LongTerm(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    
    raw: str = Field()
    raw_embedding: Optional[Any] = Field(default=None, sa_column=Column(Vector(settings.VECTOR_SIZE)))
    
    enrich: Optional[str] = Field(default=None)
    enrich_embedding: Optional[Any] = Field(default=None, sa_column=Column(Vector(settings.VECTOR_SIZE)))
    
    combo: Optional[str] = Field(default=None)
    combo_embedding: Optional[Any] = Field(default=None, sa_column=Column(Vector(settings.VECTOR_SIZE)))
    
    meta: dict = Field(sa_type=JSONB, default_factory=dict)
    
    document_id: str = Field(foreign_key="document.id")
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    document: Optional["Document"] = Relationship(back_populates="longterms")