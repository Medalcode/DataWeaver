import os
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.models import Execution, ExecutionFile, ExecutionLog, WorkflowVersion
from app.core.models import File as FileModel
from app.engine.engine import engine
from app.tasks import celery_app


@celery_app.task(
    name="execute_workflow",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=3600,
    time_limit=3900,
)
def execute_workflow_task(self, execution_id: str, workflow_version_id: str, input_file_id: str):
    db = SessionLocal()

    try:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise Exception(f"Execution {execution_id} not found")

        execution.status = "running"
        execution.started_at = datetime.now(timezone.utc)
        db.commit()

        version = (
            db.query(WorkflowVersion)
            .filter(WorkflowVersion.id == workflow_version_id)
            .first()
        )
        if not version:
            raise Exception(f"Workflow version {workflow_version_id} not found")

        input_file = db.query(FileModel).filter(FileModel.id == input_file_id).first()
        if not input_file:
            raise Exception(f"Input file {input_file_id} not found")

        df = pd.read_excel(input_file.storage_path)
        result = engine.run(df, version.rules_json)

        for idx, log in enumerate(result["logs"]):
            exec_log = ExecutionLog(
                execution_id=execution_id,
                step_index=idx,
                step_type=log["step_type"],
                message=log["message"],
                affected_rows=log["affected_rows"],
            )
            db.add(exec_log)

        output_file_ids = []
        for sheet_name, output_df in result["outputs"].items():
            output_filename = f"output_{execution_id}_{sheet_name}.xlsx"
            output_path = os.path.join(settings.UPLOAD_DIR, output_filename)
            output_df.to_excel(output_path, index=False, sheet_name=sheet_name)

            output_file = FileModel(
                company_id=execution.company_id,
                original_filename=f"{sheet_name}.xlsx",
                storage_path=output_path,
                file_type="output",
                expires_at=datetime.now(timezone.utc)
                + timedelta(hours=settings.FILE_EXPIRATION_HOURS),
            )
            db.add(output_file)
            db.flush()
            output_file_ids.append(str(output_file.id))

            exec_file = ExecutionFile(
                execution_id=execution_id, file_id=output_file.id, role="output"
            )
            db.add(exec_file)

        execution.status = "success"
        execution.finished_at = datetime.now(timezone.utc)
        db.commit()

        return {"status": "success", "output_files": output_file_ids}

    except Exception as e:
        execution.status = "failed"
        execution.finished_at = datetime.now(timezone.utc)
        execution.error_message = str(e)
        db.commit()
        try:
            self.retry(exc=e)
        except Exception:
            raise

    finally:
        db.close()
