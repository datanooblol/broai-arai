from sqlmodel import Field, SQLModel
from package.databases.utils import datetime, now_utc

class ProjectDocumentLink(SQLModel, table=True):
    project_id: str = Field(foreign_key="project.id", primary_key=True)
    document_id: str = Field(foreign_key="document.id", primary_key=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)