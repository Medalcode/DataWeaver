from typing import Any

from app.engine.context import ExecutionContext
from app.engine.rules.base import Rule


class MoveRule(Rule):
    """Legacy wrapper for simple move, now mostly handled by Super-Param target_sheet."""

    def execute(self, context: ExecutionContext, params: dict[str, Any]):
        context.log("move", "Materialized current sheet", len(context.current_df))
        return context.current_df

    def validate_params(self, params: dict[str, Any], df_columns: set[str]) -> None:
        if "target_sheet" not in params or not str(params["target_sheet"]).strip():
            raise ValueError("move requires 'target_sheet'")
