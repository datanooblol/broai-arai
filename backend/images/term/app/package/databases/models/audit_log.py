from package.databases.utils import datetime, now_utc
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import uuid4
from sqlalchemy.dialects.postgresql import JSONB

class AuditLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)

    user_id: Optional[str] = Field(foreign_key="user.id", index=True)
    action: str = Field(index=True)  # e.g., "create", "update", "delete"
    model: str = Field(index=True)   # e.g., "Document", "Project"
    record_id: str = Field(index=True) # e.g. id of the record of each model: proejct.id, document.id
    details: Optional[dict] = Field(sa_type=JSONB, default_factory=dict)    # Optional: JSON diff or summary
    ip_address: Optional[str] = None

    created_at: datetime = Field(default_factory=now_utc)

# Exmaple usage: on ip_address

# this case is for FastAPI endpoint without reverse proxy setup

# from fastapi import Request, APIRouter

# router = APIRouter()

# @router.get("/some-endpoint")
# async def endpoint(request: Request):
#     client_host = request.client.host
#     return {"ip": client_host}

# this case is for FastAPI endpoint with reverse proxy setup
# from fastapi import Request, APIRouter, Depends

# router = APIRouter()

# async def get_ip(request: Request) -> str:
#     x_forwarded_for = request.headers.get("X-Forwarded-For")
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(",")[0].strip()
#     else:
#         ip = request.client.host
#     return ip

# async def ip_dependency(request: Request) -> str:
#     return get_client_ip(request)

# @router.post("/projects/")
# async def create_project(ip_address: str = Depends(ip_dependency), /* other params */):
#     # ip_address is ready to use