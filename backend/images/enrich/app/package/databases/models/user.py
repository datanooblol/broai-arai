from sqlmodel import Relationship, SQLModel, Field
from package.databases.utils import datetime, now_utc
from typing import List, TYPE_CHECKING
from uuid import uuid4
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

if TYPE_CHECKING:
    from .project import Project  # Avoid circular import issues

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    
    username: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    role: UserRole = Field(default=UserRole.USER)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    projects: List["Project"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

# Example usage:
# if current_user.role != UserRole.ADMIN:
#     raise HTTPException(status_code=403, detail="Admin access required")

# if not user.is_active:
#     raise HTTPException(status_code=403, detail="Account disabled")