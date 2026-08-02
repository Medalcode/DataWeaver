from typing import Any

from app.engine.context import ExecutionContext
from app.engine.rules.base import Rule

SUPPORTED_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "contains"}


class FilterRule(Rule):
    """Filter rows based on column conditions."""

    def execute(self, context: ExecutionContext, params: dict[str, Any]):
        column = params.get("column")
        operator = params.get("operator")
        value = params.get("value")

        df = context.current_df

        if operator == "=":
            mask = df[column] == value
        elif operator == "!=":
            mask = df[column] != value
        elif operator == ">":
            mask = df[column] > value
        elif operator == "<":
            mask = df[column] < value
        elif operator == ">=":
            mask = df[column] >= value
        elif operator == "<=":
            mask = df[column] <= value
        elif operator == "contains":
            mask = df[column].astype(str).str.contains(str(value), case=False, na=False)
        else:
            raise ValueError(f"Unsupported operator: {operator}")

        context.current_df = df[mask]
        context.log("filter", f"Filtered by {column} {operator} {value}", len(context.current_df))
        return context.current_df

    def validate_params(self, params: dict[str, Any], df_columns: set[str]) -> None:
        if "column" not in params:
            raise ValueError("filter requires 'column'")
        column = params["column"]
        if column not in df_columns:
            raise ValueError(f"column '{column}' does not exist in dataframe")

        if "operator" not in params:
            raise ValueError("filter requires 'operator'")
        operator = params["operator"]
        if operator not in SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")

        if "value" not in params:
            raise ValueError("filter requires 'value'")

        target_sheet = params.get("target_sheet")
        if target_sheet is not None and not str(target_sheet).strip():
            raise ValueError("'target_sheet' cannot be empty")
