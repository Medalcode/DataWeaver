import io
import os
import shutil
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi import File as FastAPIFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_company_id, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.models import File as FileModel
from app.core.models import User
from app.core.schemas import FileUploadResponse

router = APIRouter(prefix="/files", tags=["Files"])

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    if not file.filename or not file.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx and .xls files are supported",
        )

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE // (1024*1024)}MB",
        )

    file_id = uuid4()
    ext = os.path.splitext(file.filename)[1].lower()
    storage_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")

    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(io.BytesIO(content), buffer)

    # Non-blocking async threadpool execution for heavy synchronous Excel parsing
    df = await run_in_threadpool(pd.read_excel, storage_path)

    file_record = FileModel(
        id=file_id,
        company_id=company_id,
        original_filename=file.filename,
        storage_path=storage_path,
        file_type="input",
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.FILE_EXPIRATION_HOURS),
    )
    db.add(file_record)
    db.commit()

    return {"file_id": file_id, "filename": file.filename, "columns": df.columns.tolist()}


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    file_record = (
        db.query(FileModel)
        .filter(FileModel.id == file_id, FileModel.company_id == company_id)
        .first()
    )
    if not file_record or not os.path.exists(file_record.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(
        path=file_record.storage_path,
        filename=file_record.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
):
    file_record = (
        db.query(FileModel)
        .filter(FileModel.id == file_id, FileModel.company_id == company_id)
        .first()
    )
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if os.path.exists(file_record.storage_path):
        os.remove(file_record.storage_path)
    db.delete(file_record)
    db.commit()
