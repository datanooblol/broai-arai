from sqlmodel import SQLModel, Field, Relationship
from package.databases.utils import datetime, now_utc
from typing import TYPE_CHECKING, List
from uuid import uuid4
from enum import Enum
from .project_document_link import ProjectDocumentLink  # Avoid circular import issues

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


if TYPE_CHECKING:
    from .project import Project  # Avoid circular import issues
    from .jargon import Jargon  # Avoid circular import issues
    from .longterm import LongTerm  # Avoid circular import issues

class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    source: str = Field(index=True, nullable=False)
    type: str = Field(index=True, nullable=False)
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    projects: List["Project"] = Relationship(
        back_populates="documents",
        link_model=ProjectDocumentLink,
    )
    jargons: List["Jargon"] = Relationship(
        back_populates="document",
    )
    longterms: List["LongTerm"] = Relationship(
        back_populates="document",
    )