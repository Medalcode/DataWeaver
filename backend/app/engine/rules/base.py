from abc import ABC, abstractmethod
from typing import Any

from app.engine.context import ExecutionContext


class Rule(ABC):
    """Base class for all workflow rules with automatic materialization and validation support."""

    def run_execute(self, context: ExecutionContext, params: dict[str, Any]) -> None:
        """Wrapper to handle common logic like target_sheet before/after custom execution."""
        result_df = self.execute(context, params)

        # Super-Param: target_sheet (Global Materialization)
        target_sheet = params.get("target_sheet")
        if target_sheet:
            context.outputs[target_sheet] = (
                result_df if result_df is not None else context.current_df
            ).copy()

    @abstractmethod
    def execute(self, context: ExecutionContext, params: dict[str, Any]) -> Any:
        """Custom transformation logic for each rule."""
        pass

    @abstractmethod
    def validate_params(self, params: dict[str, Any], df_columns: set[str]) -> None:
        """Validate step parameters against the input DataFrame schema (Polymorphic Validation)."""
        pass
