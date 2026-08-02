from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

try:
    from pydantic import EmailStr
    from pydantic.networks import import_email_validator
    import_email_validator()
except (ImportError, Exception):  # pragma: no cover
    EmailStr = str  # Fallback to str if email-validator is missing in environment


# Auth schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime


# Workflow schemas
class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Workflow version schemas
class WorkflowVersionCreate(BaseModel):
    rules: dict[str, Any]


class WorkflowVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    version_number: int
    rules_json: dict[str, Any]
    created_at: datetime


# File schemas
class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    columns: list[str]


# Execution schemas
class ExecutionCreate(BaseModel):
    workflow_version_id: UUID
    file_id: UUID


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_version_id: UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None


class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_index: int
    step_type: str
    message: str
    affected_rows: int
    created_at: datetime


# Preview schema
class PreviewRequest(BaseModel):
    file_id: UUID
    rules: dict[str, Any]


class PreviewResponse(BaseModel):
    before: list[dict]
    after: dict
    logs: list[dict]
