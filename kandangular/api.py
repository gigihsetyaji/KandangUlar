import secrets
from typing import Annotated
from asgiref.sync import sync_to_async
from django.conf import settings
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from kandangular.web.models import Project

bearer = HTTPBearer(auto_error=False)
def require_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None or not secrets.compare_digest(credentials.credentials, settings.API_TOKEN):
        raise HTTPException(401, "Token tidak valid", headers={"WWW-Authenticate": "Bearer"})

class ProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)

class ProjectOutput(ProjectInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

api = FastAPI(title="KandangUlar API", version="0.1.0", docs_url="/docs" if settings.DEBUG else None, redoc_url=None, openapi_url="/openapi.json" if settings.DEBUG else None, dependencies=[Depends(require_token)])

@api.get("/v1/projects", response_model=list[ProjectOutput])
async def projects(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    return await sync_to_async(list)(Project.objects.order_by("-id")[offset:offset + limit])

@api.post("/v1/projects", response_model=ProjectOutput, status_code=201)
async def create_project(payload: ProjectInput):
    return await sync_to_async(Project.objects.create)(**payload.model_dump())
