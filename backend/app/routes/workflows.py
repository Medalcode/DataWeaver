from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Workflow, WorkflowVersion
from app.auth import get_current_user
from app.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowVersionCreate,
    WorkflowVersionResponse
)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workflow"""
    
    workflow = Workflow(
        company_id="temp-company-id",  # TODO: Get from user context
        name=workflow_data.name,
        description=workflow_data.description
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    return workflow


@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all workflows for current company"""
    
    # TODO: Filter by company_id
    workflows = db.query(Workflow).filter(Workflow.is_active == True).all()
    
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific workflow"""
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # TODO: Check company_id authorization
    
    return workflow


@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_version(
    workflow_id: str,
    version_data: WorkflowVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new version of a workflow"""
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # TODO: Check company_id authorization
    
    # Get next version number
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
        created_by=current_user.id
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return version


@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersionResponse])
def list_workflow_versions(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all versions of a workflow"""
    
    versions = (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version_number.desc())
        .all()
    )
    
    return versions
