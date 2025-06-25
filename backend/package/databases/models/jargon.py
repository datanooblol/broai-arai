from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from package.utils.utils import datetime, now_utc
from uuid import uuid4
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .document import Document  # Avoid circular import issues

class Jargon(SQLModel, table=True):
    """This class will be updated later for searching and indexing use cases"""
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    term: str
    definition: str
    document_id: str = Field(foreign_key="document.id")

    meta: dict = Field(sa_type=JSONB, default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    document: Optional["Document"] = Relationship(back_populates="jargons")