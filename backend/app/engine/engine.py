import pandas as pd
from typing import Dict

from app.engine.context import ExecutionContext
from app.engine.rules.factory import get_rule
from app.engine.validator import validate_workflow


class RuleEngine:
    """Main orchestrator for workflow execution"""
    
    def run(self, df: pd.DataFrame, workflow: dict) -> Dict:
        """
        Execute a workflow on a dataframe
        
        Args:
            df: Input pandas DataFrame
            workflow: Workflow definition with steps
            
        Returns:
            Dict with outputs and logs
            
        Raises:
            WorkflowValidationError: If workflow is invalid
            Exception: If execution fails
        """
        # Validate before execution
        validate_workflow(workflow, df)
        
        # Initialize context
        context = ExecutionContext(df)
        
        # Execute each step
        for idx, step in enumerate(workflow["steps"]):
            try:
                rule_type = step["type"]
                rule = get_rule(rule_type)
                rule.execute(context, step)
            except Exception as e:
                context.log(
                    "error",
                    f"Step {idx} ({rule_type}) failed: {str(e)}",
                    0
                )
                raise Exception(f"Execution failed at step {idx}: {str(e)}")
        
        return context.get_result()
    
    def preview(self, df: pd.DataFrame, workflow: dict, max_rows: int = 20) -> Dict:
        """
        Preview workflow execution without persisting
        
        Args:
            df: Input DataFrame
            workflow: Workflow definition
            max_rows: Maximum rows to return in preview
            
        Returns:
            Dict with before/after snapshots
        """
        validate_workflow(workflow, df)
        
        # Take snapshot before
        before = df.head(max_rows).to_dict(orient="records")
        
        # Execute workflow
        result = self.run(df, workflow)
        
        # Take snapshot after
        after_data = {}
        if result["outputs"]:
            # Show first output sheet
            first_sheet = list(result["outputs"].keys())[0]
            after_data["sheet"] = first_sheet
            after_data["rows"] = result["outputs"][first_sheet].head(max_rows).to_dict(orient="records")
        else:
            # No outputs created, show filtered current_df (not available after execution)
            after_data["rows"] = []
        
        return {
            "before": before,
            "after": after_data,
            "logs": result["logs"]
        }


# Singleton instance
engine = RuleEngine()
