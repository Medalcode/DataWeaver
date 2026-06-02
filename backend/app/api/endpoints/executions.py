import os

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_current_company_id
from app.core.database import get_db
from app.core.models import (
    Execution,
    ExecutionFile,
    ExecutionLog,
    User,
    WorkflowVersion,
)
from app.core.models import File as FileModel
from app.core.schemas import (
    ExecutionCreate,
    ExecutionLogResponse,
    ExecutionResponse,
    PreviewRequest,
    PreviewResponse,
)
from app.engine.engine import engine
from app.tasks.workflow_execution import execute_workflow_task

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def create_execution(
    execution_data: ExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
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
    file = db.query(FileModel).filter(FileModel.id == execution_data.file_id, FileModel.company_id == company_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        
    execution = Execution(
        company_id=company_id,
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


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    execution = db.query(Execution).filter(Execution.id == execution_id, Execution.company_id == company_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return execution


@router.get("/{execution_id}/logs", response_model=list[ExecutionLogResponse])
def get_execution_logs(
    execution_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    execution = db.query(Execution).filter(Execution.id == execution_id, Execution.company_id == company_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
        
    return (
        db.query(ExecutionLog)
        .filter(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.step_index)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{execution_id}/output")
async def get_execution_output(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    execution = db.query(Execution).filter(Execution.id == execution_id, Execution.company_id == company_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
        
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


@router.post("/preview", response_model=PreviewResponse)
async def preview_workflow(
    preview_data: PreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    file = db.query(FileModel).filter(FileModel.id == preview_data.file_id, FileModel.company_id == company_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    df = pd.read_excel(file.storage_path)
    return engine.preview(df, preview_data.rules, max_rows=20)
