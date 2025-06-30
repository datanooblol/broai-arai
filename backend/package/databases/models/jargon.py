# from sqlmodel import SQLModel, Field, Relationship
# from typing import Optional, TYPE_CHECKING
# from package.databases.utils import datetime, now_utc
# from uuid import uuid4
# from sqlalchemy.dialects.postgresql import JSONB

# if TYPE_CHECKING:
#     from .document import Document  # Avoid circular import issues

# class Jargon(SQLModel, table=True):
#     """This class will be updated later for searching and indexing use cases"""
#     id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
#     jargon: str
#     evidence: str
#     explanation: str
#     document_id: str = Field(foreign_key="document.id")

#     meta: dict = Field(sa_type=JSONB, default_factory=dict)
#     created_at: datetime = Field(default_factory=now_utc)
#     updated_at: datetime = Field(default_factory=now_utc)

#     document: Optional["Document"] = Relationship(back_populates="jargons")

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from package.databases.utils import datetime, now_utc
from uuid import uuid4
from sqlalchemy import Column, event
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.schema import DDL

if TYPE_CHECKING:
    from .document import Document  # Avoid circular import issues

class Jargon(SQLModel, table=True):
    """This class will be updated later for searching and indexing use cases"""
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    jargon: str
    evidence: str
    explanation: str
    document_id: str = Field(foreign_key="document.id")

    meta: dict = Field(sa_type=JSONB, default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    # Add full-text search vector on 'jargon'
    search_vector: Optional[str] = Field(
        sa_column=Column("search_vector", TSVECTOR), 
        # index=True
    )

    document: Optional["Document"] = Relationship(back_populates="jargons")

# --- Full-text search trigger setup ---
# Create trigger after table creation to keep `search_vector` up-to-date with `jargon`
search_trigger = DDL("""
CREATE TRIGGER jargon_search_vector_update
BEFORE INSERT OR UPDATE ON jargon
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', jargon);
""")

# Attach the trigger creation after table creation
@event.listens_for(Jargon.__table__, "after_create")
def create_search_trigger(target, connection, **kw):
    connection.execute(search_trigger)