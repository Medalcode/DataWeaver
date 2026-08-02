from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from app.core.models import Execution, File as FileModel, Workflow, WorkflowVersion
from app.tasks.maintenance import cleanup_expired_files_task
from app.tasks.workflow_execution import execute_workflow_task


def test_cleanup_expired_files_task(tmp_path):
    # Create temporary expired file
    file_path = tmp_path / "expired_file.xlsx"
    file_path.write_text("dummy excel content")

    mock_db = MagicMock()
    mock_file = MagicMock()
    mock_file.storage_path = str(file_path)
    mock_file.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    mock_db.query().filter().all.return_value = [mock_file]

    with patch("app.tasks.maintenance.SessionLocal", return_value=mock_db):
        cleanup_expired_files_task()

    assert not file_path.exists()
    mock_db.delete.assert_called_once_with(mock_file)
    mock_db.commit.assert_called_once()


def test_execute_workflow_task_file_not_found():
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None

    task_self = MagicMock()
    task_self.request.retries = 0
    task_self.max_retries = 3

    with patch("app.tasks.workflow_execution.SessionLocal", return_value=mock_db):
        with pytest.raises(FileNotFoundError):
            execute_workflow_task(task_self, "exec-1", "ver-1", "file-1")
