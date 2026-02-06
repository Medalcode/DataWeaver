import pandas as pd


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


def validate_workflow(workflow: dict, df: pd.DataFrame):
    """Validate workflow against dataframe before execution"""
    
    if "steps" not in workflow:
        raise WorkflowValidationError("Workflow must contain 'steps' array")
    
    if not isinstance(workflow["steps"], list):
        raise WorkflowValidationError("'steps' must be an array")
    
    if len(workflow["steps"]) == 0:
        raise WorkflowValidationError("Workflow must contain at least one step")
    
    columns = set(df.columns)
    
    for idx, step in enumerate(workflow["steps"]):
        if "type" not in step:
            raise WorkflowValidationError(f"Step {idx}: missing 'type' field")
        
        step_type = step["type"]
        
        # Validate filter rule
        if step_type == "filter":
            if "column" not in step:
                raise WorkflowValidationError(f"Step {idx}: filter requires 'column'")
            
            if step["column"] not in columns:
                raise WorkflowValidationError(
                    f"Step {idx}: column '{step['column']}' does not exist in dataframe"
                )
            
            if "operator" not in step:
                raise WorkflowValidationError(f"Step {idx}: filter requires 'operator'")
            
            if "value" not in step:
                raise WorkflowValidationError(f"Step {idx}: filter requires 'value'")
        
        # Validate move rule
        elif step_type == "move":
            if "target_sheet" not in step:
                raise WorkflowValidationError(f"Step {idx}: move requires 'target_sheet'")
        
        # Validate group_sum rule
        elif step_type == "group_sum":
            if "group_by" not in step:
                raise WorkflowValidationError(f"Step {idx}: group_sum requires 'group_by'")
            
            if "field" not in step:
                raise WorkflowValidationError(f"Step {idx}: group_sum requires 'field'")
            
            if "target_sheet" not in step:
                raise WorkflowValidationError(f"Step {idx}: group_sum requires 'target_sheet'")
            
            if step["group_by"] not in columns:
                raise WorkflowValidationError(
                    f"Step {idx}: column '{step['group_by']}' does not exist"
                )
            
            if step["field"] not in columns:
                raise WorkflowValidationError(
                    f"Step {idx}: column '{step['field']}' does not exist"
                )
