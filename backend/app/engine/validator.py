import pandas as pd

from app.engine.rules.factory import get_rule


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""

    pass


def validate_workflow(workflow: dict, df: pd.DataFrame) -> None:
    """Validate workflow definition against dataframe before execution using polymorphic rule validation."""

    if "steps" not in workflow:
        raise WorkflowValidationError("Workflow must contain 'steps' array")

    if not isinstance(workflow["steps"], list):
        raise WorkflowValidationError("'steps' must be an array")

    if len(workflow["steps"]) == 0:
        raise WorkflowValidationError("Workflow must contain at least one step")

    columns = set(df.columns)

    for idx, step in enumerate(workflow["steps"]):
        if not isinstance(step, dict) or "type" not in step:
            raise WorkflowValidationError(f"Step {idx}: missing 'type' field")

        step_type = step["type"]

        try:
            rule = get_rule(step_type)
            rule.validate_params(step, columns)
        except ValueError as e:
            raise WorkflowValidationError(f"Step {idx}: {str(e)}") from e
        except Exception as e:
            raise WorkflowValidationError(f"Step {idx} validation error: {str(e)}") from e
