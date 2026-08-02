import os
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.models import File as FileModel
from app.tasks import celery_app


@celery_app.task(name="cleanup_expired_files")
def cleanup_expired_files_task():
    """
    Celery task to delete expired files from disk and database.
    Runs periodically via Celery Beat.
    """
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        expired_files = db.query(FileModel).filter(FileModel.expires_at < now_utc).all()
        for file in expired_files:
            if os.path.exists(file.storage_path):
                os.remove(file.storage_path)
            db.delete(file)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
