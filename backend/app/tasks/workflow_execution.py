import pandas as pd
from datetime import datetime
from uuid import UUID
import os

from app.tasks import celery_app
from app.engine.engine import engine
from app.database import SessionLocal
from app.models import Execution, ExecutionLog, WorkflowVersion, File as FileModel


@celery_app.task(name="execute_workflow")
def execute_workflow_task(execution_id: str, workflow_version_id: str, input_file_id: str):
    """
    Celery task to execute a workflow asynchronously
    
    Args:
        execution_id: UUID of the execution record
        workflow_version_id: UUID of the workflow version
        input_file_id: UUID of the input file
    """
    db = SessionLocal()
    
    try:
        # Get execution record
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise Exception(f"Execution {execution_id} not found")
        
        # Update status to running
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        db.commit()
        
        # Get workflow version
        version = db.query(WorkflowVersion).filter(WorkflowVersion.id == workflow_version_id).first()
        if not version:
            raise Exception(f"Workflow version {workflow_version_id} not found")
        
        # Get input file
        input_file = db.query(FileModel).filter(FileModel.id == input_file_id).first()
        if not input_file:
            raise Exception(f"Input file {input_file_id} not found")
        
        # Read Excel file
        df = pd.read_excel(input_file.storage_path)
        
        # Execute workflow
        result = engine.run(df, version.rules_json)
        
        # Save logs
        for idx, log in enumerate(result["logs"]):
            exec_log = ExecutionLog(
                execution_id=execution_id,
                step_index=idx,
                step_type=log["step_type"],
                message=log["message"],
                affected_rows=log["affected_rows"]
            )
            db.add(exec_log)
        
        # Save output files
        from app.config import settings
        output_file_ids = []
        
        for sheet_name, output_df in result["outputs"].items():
            # Generate output file
            output_filename = f"output_{execution_id}_{sheet_name}.xlsx"
            output_path = os.path.join(settings.UPLOAD_DIR, output_filename)
            
            output_df.to_excel(output_path, index=False, sheet_name=sheet_name)
            
            # Create file record
            from datetime import timedelta
            output_file = FileModel(
                company_id=execution.company_id,
                original_filename=f"{sheet_name}.xlsx",
                storage_path=output_path,
                file_type="output",
                expires_at=datetime.utcnow() + timedelta(hours=settings.FILE_EXPIRATION_HOURS)
            )
            db.add(output_file)
            db.flush()
            
            output_file_ids.append(str(output_file.id))
            
            # Link to execution
            from app.models import ExecutionFile
            exec_file = ExecutionFile(
                execution_id=execution_id,
                file_id=output_file.id,
                role="output"
            )
            db.add(exec_file)
        
        # Mark as success
        execution.status = "success"
        execution.finished_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success",
            "output_files": output_file_ids
        }
        
    except Exception as e:
        # Mark as failed
        execution.status = "failed"
        execution.finished_at = datetime.utcnow()
        execution.error_message = str(e)
        db.commit()
        
        return {
            "status": "failed",
            "error": str(e)
        }
    
    finally:
        db.close()
