from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Auth schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Workflow schemas
class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Workflow version schemas
class WorkflowVersionCreate(BaseModel):
    rules: Dict[str, Any]


class WorkflowVersionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    version_number: int
    rules_json: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


# File schemas
class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    columns: List[str]


# Execution schemas
class ExecutionCreate(BaseModel):
    workflow_version_id: UUID
    file_id: UUID


class ExecutionResponse(BaseModel):
    id: UUID
    workflow_version_id: UUID
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class ExecutionLogResponse(BaseModel):
    step_index: int
    step_type: str
    message: str
    affected_rows: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Preview schema
class PreviewRequest(BaseModel):
    file_id: UUID
    rules: Dict[str, Any]


class PreviewResponse(BaseModel):
    before: List[Dict]
    after: Dict
    logs: List[Dict]
