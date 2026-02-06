from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import pandas as pd

from app.database import get_db
from app.models import User, Execution, ExecutionLog, WorkflowVersion, File as FileModel
from app.auth import get_current_user
from app.schemas import (
    ExecutionCreate,
    ExecutionResponse,
    ExecutionLogResponse,
    PreviewRequest,
    PreviewResponse
)
from app.tasks.workflow_execution import execute_workflow_task
from app.engine.engine import engine

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def create_execution(
    execution_data: ExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and start a workflow execution"""
    
    # Verify workflow version exists
    version = db.query(WorkflowVersion).filter(
        WorkflowVersion.id == execution_data.workflow_version_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow version not found"
        )
    
    # Verify file exists
    file = db.query(FileModel).filter(FileModel.id == execution_data.file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Create execution record
    execution = Execution(
        company_id="temp-company-id",  # TODO: Get from user context
        workflow_version_id=execution_data.workflow_version_id,
        status="pending"
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Dispatch Celery task
    execute_workflow_task.delay(
        str(execution.id),
        str(execution_data.workflow_version_id),
        str(execution_data.file_id)
    )
    
    return execution


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution status"""
    
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # TODO: Check company_id authorization
    
    return execution


@router.get("/{execution_id}/logs", response_model=List[ExecutionLogResponse])
def get_execution_logs(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution logs"""
    
    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.step_index)
        .all()
    )
    
    return logs


@router.get("/{execution_id}/output")
async def get_execution_output(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download execution output file"""
    
    from app.models import ExecutionFile
    
    # Get output file
    exec_file = (
        db.query(ExecutionFile)
        .filter(
            ExecutionFile.execution_id == execution_id,
            ExecutionFile.role == "output"
        )
        .first()
    )
    
    if not exec_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found"
        )
    
    file = db.query(FileModel).filter(FileModel.id == exec_file.file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File record not found"
        )
    
    from fastapi.responses import FileResponse
    import os
    
    if not os.path.exists(file.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file.storage_path,
        filename=file.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/preview", response_model=PreviewResponse)
async def preview_workflow(
    preview_data: PreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview workflow execution without persisting results"""
    
    # Get file
    file = db.query(FileModel).filter(FileModel.id == preview_data.file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Read Excel
    try:
        df = pd.read_excel(file.storage_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read Excel file: {str(e)}"
        )
    
    # Run preview
    try:
        result = engine.preview(df, preview_data.rules, max_rows=20)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preview failed: {str(e)}"
        )
