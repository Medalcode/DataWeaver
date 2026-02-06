from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import os
from datetime import datetime, timedelta
from uuid import uuid4

from app.database import get_db
from app.models import User, File as FileModel
from app.auth import get_current_user
from app.schemas import FileUploadResponse
from app.config import settings
from jose import jwt

router = APIRouter(prefix="/files", tags=["Files"])


def get_company_id(current_user: User = Depends(get_current_user)) -> str:
    """Extract company_id from user context"""
    # In production, get this from JWT or user's active company
    return "temp-company-id"  # TODO: Implement properly


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload Excel file and extract column information"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported"
        )
    
    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_id = uuid4()
    file_extension = os.path.splitext(file.filename)[1]
    storage_filename = f"{file_id}{file_extension}"
    storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
    
    # Save file
    with open(storage_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Read Excel to get columns
    try:
        df = pd.read_excel(storage_path)
        columns = df.columns.tolist()
    except Exception as e:
        os.remove(storage_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read Excel file: {str(e)}"
        )
    
    # Save file record (simplified - TODO: add proper company_id)
    file_record = FileModel(
        id=file_id,
        company_id="temp-company-id",  # TODO: Get from current_user
        original_filename=file.filename,
        storage_path=storage_path,
        file_type="input",
        expires_at=datetime.utcnow() + timedelta(hours=settings.FILE_EXPIRATION_HOURS)
    )
    db.add(file_record)
    db.commit()
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "columns": columns
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a file"""
    
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # TODO: Check company_id authorization
    
    if not os.path.exists(file_record.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_record.storage_path,
        filename=file_record.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
