from sqlmodel import SQLModel, Field, Relationship
from package.utils.utils import datetime, now_utc
from typing import TYPE_CHECKING, Optional, List
from uuid import uuid4
from .project_document_link import ProjectDocumentLink  # Avoid circular import issues

if TYPE_CHECKING:
    from .user import User  # Avoid circular import issues
    from .document import Document  # Avoid circular import issues

class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    description: str = Field(nullable=False)
    user_id: str = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    owner: Optional["User"] = Relationship(back_populates="projects")
    
    documents: List["Document"] = Relationship(
        back_populates="projects",
        link_model=ProjectDocumentLink,
    )