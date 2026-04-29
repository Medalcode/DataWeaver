import os
from datetime import datetime, timedelta
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi import File as FastAPIFile
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_current_user, get_password_hash, verify_password
from app.core.config import settings
from app.core.database import get_db
from app.core.models import (
    Company,
    Execution,
    ExecutionFile,
    ExecutionLog,
    Membership,
    Role,
    User,
    Workflow,
    WorkflowVersion,
)
from app.core.models import File as FileModel
from app.core.schemas import (
    ExecutionCreate,
    ExecutionLogResponse,
    ExecutionResponse,
    FileUploadResponse,
    PreviewRequest,
    PreviewResponse,
    Token,
    UserRegister,
    UserResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowVersionCreate,
    WorkflowVersionResponse,
)
from app.engine.engine import engine
from app.tasks.workflow_execution import execute_workflow_task

# --- MAIN ROUTER ---
api_router = APIRouter()


# --- AUTHENTICATION ---
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    hashed_password = get_password_hash(user_data.password)
    user = User(email=user_data.email, password_hash=hashed_password)
    db.add(user)
    db.flush()
    company_name = user_data.company_name or f"{user_data.email}'s Company"
    company = Company(name=company_name)
    db.add(company)
    db.flush()
    owner_role = db.query(Role).filter(Role.name == "owner").first() or Role(name="owner")
    db.add(owner_role)
    db.flush()
    membership = Membership(user_id=user.id, company_id=company.id, role_id=owner_role.id)
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


@auth_router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    access_token = create_access_token(
        data={"sub": str(user.id), "company_id": str(membership.company_id) if membership else None}
    )
    return {"access_token": access_token, "token_type": "bearer"}


api_router.include_router(auth_router)


# --- EXECUTIONS ---
exec_router = APIRouter(prefix="/executions", tags=["Executions"])


@exec_router.post("", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def create_execution(
    execution_data: ExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.id == execution_data.workflow_version_id)
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow version not found"
        )
    file = db.query(FileModel).filter(FileModel.id == execution_data.file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    execution = Execution(
        company_id="temp-company-id",
        workflow_version_id=execution_data.workflow_version_id,
        status="pending",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    execute_workflow_task.delay(
        str(execution.id), str(execution_data.workflow_version_id), str(execution_data.file_id)
    )
    return execution


@exec_router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return execution


@exec_router.get("/{execution_id}/logs", response_model=list[ExecutionLogResponse])
def get_execution_logs(
    execution_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(ExecutionLog)
        .filter(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.step_index)
        .all()
    )


@exec_router.get("/{execution_id}/output")
async def get_execution_output(
    execution_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    exec_file = (
        db.query(ExecutionFile)
        .filter(ExecutionFile.execution_id == execution_id, ExecutionFile.role == "output")
        .first()
    )
    if not exec_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not found")
    file = db.query(FileModel).filter(FileModel.id == exec_file.file_id).first()
    if not file or not os.path.exists(file.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(path=file.storage_path, filename=file.original_filename)


@exec_router.post("/preview", response_model=PreviewResponse)
async def preview_workflow(
    preview_data: PreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = db.query(FileModel).filter(FileModel.id == preview_data.file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    df = pd.read_excel(file.storage_path)
    return engine.preview(df, preview_data.rules, max_rows=20)


api_router.include_router(exec_router)


# --- FILES ---
files_router = APIRouter(prefix="/files", tags=["Files"])


@files_router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Excel supported")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = uuid4()
    storage_path = os.path.join(
        settings.UPLOAD_DIR, f"{file_id}{os.path.splitext(file.filename)[1]}"
    )
    with open(storage_path, "wb") as buffer:
        buffer.write(await file.read())
    df = pd.read_excel(storage_path)
    file_record = FileModel(
        id=file_id,
        company_id="temp-company-id",
        original_filename=file.filename,
        storage_path=storage_path,
        file_type="input",
        expires_at=datetime.utcnow() + timedelta(hours=settings.FILE_EXPIRATION_HOURS),
    )
    db.add(file_record)
    db.commit()
    return {"file_id": file_id, "filename": file.filename, "columns": df.columns.tolist()}


@files_router.get("/{file_id}/download")
async def download_file(
    file_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record or not os.path.exists(file_record.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(path=file_record.storage_path, filename=file_record.original_filename)


api_router.include_router(files_router)


# --- WORKFLOWS ---
workflows_router = APIRouter(prefix="/workflows", tags=["Workflows"])


@workflows_router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = Workflow(
        company_id="temp-company-id", name=workflow_data.name, description=workflow_data.description
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@workflows_router.get("", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Workflow).filter(Workflow.is_active == True).all()


@workflows_router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


@workflows_router.post(
    "/{workflow_id}/versions",
    response_model=WorkflowVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_version(
    workflow_id: str,
    version_data: WorkflowVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    latest_version = (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version_number.desc())
        .first()
    )
    next_version = (latest_version.version_number + 1) if latest_version else 1
    version = WorkflowVersion(
        workflow_id=workflow_id,
        version_number=next_version,
        rules_json=version_data.rules,
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@workflows_router.get("/{workflow_id}/versions", response_model=list[WorkflowVersionResponse])
def list_workflow_versions(
    workflow_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version_number.desc())
        .all()
    )


api_router.include_router(workflows_router)
