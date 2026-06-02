from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_current_company_id
from app.core.database import get_db
from app.core.models import User, Workflow, WorkflowVersion
from app.core.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowVersionCreate,
    WorkflowVersionResponse,
)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    workflow = Workflow(
        company_id=company_id, name=workflow_data.name, description=workflow_data.description
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("", response_model=list[WorkflowResponse])
def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    return (
        db.query(Workflow)
        .filter(Workflow.company_id == company_id, Workflow.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.company_id == company_id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


@router.post(
    "/{workflow_id}/versions",
    response_model=WorkflowVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_version(
    workflow_id: str,
    version_data: WorkflowVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.company_id == company_id).first()
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


@router.get("/{workflow_id}/versions", response_model=list[WorkflowVersionResponse])
def list_workflow_versions(
    workflow_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.company_id == company_id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    
    return (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version_number.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
