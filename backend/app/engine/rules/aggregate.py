from typing import Any

from app.engine.context import ExecutionContext
from app.engine.rules.base import Rule

SUPPORTED_OPS = {"sum", "mean", "count", "max", "min"}


class AggregateRule(Rule):
    """Super-Skill: Resumen interactivo (sum, mean, count, max, min)."""

    def execute(self, context: ExecutionContext, params: dict[str, Any]):
        group_by = params.get("group_by")
        field = params.get("field")
        op = params.get("op", "sum")

        grouped_df = context.current_df.groupby(group_by, as_index=False)[field].agg(op)

        context.log("aggregate", f"Grouped by {group_by} applying {op} on {field}", len(grouped_df))
        return grouped_df

    def validate_params(self, params: dict[str, Any], df_columns: set[str]) -> None:
        if "group_by" not in params:
            raise ValueError("aggregate requires 'group_by'")
        group_by = params["group_by"]
        if group_by not in df_columns:
            raise ValueError(f"column '{group_by}' does not exist")

        if "field" not in params:
            raise ValueError("aggregate requires 'field'")
        field = params["field"]
        if field not in df_columns:
            raise ValueError(f"column '{field}' does not exist")

        if "target_sheet" not in params or not str(params["target_sheet"]).strip():
            raise ValueError("aggregate requires 'target_sheet'")

        op = params.get("op", "sum")
        if op not in SUPPORTED_OPS:
            raise ValueError(f"Unsupported aggregation operation: {op}")
