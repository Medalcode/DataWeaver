from typing import Dict, List
import pandas as pd


class ExecutionContext:
    """Maintains state during workflow execution"""
    
    def __init__(self, df: pd.DataFrame):
        self.current_df = df
        self.outputs: Dict[str, pd.DataFrame] = {}
        self.logs: List[dict] = []

    def log(self, step_type: str, message: str, affected_rows: int = 0):
        """Add a log entry for auditing"""
        self.logs.append({
            "step_type": step_type,
            "message": message,
            "affected_rows": affected_rows
        })

    def get_result(self):
        """Return final execution result"""
        return {
            "outputs": self.outputs,
            "logs": self.logs
        }
