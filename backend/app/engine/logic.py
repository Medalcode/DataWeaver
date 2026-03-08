from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd
from app.engine.context import ExecutionContext


class Rule(ABC):
    """Base class for all workflow rules with automatic materialization support"""
    
    def run_execute(self, context: ExecutionContext, params: dict):
        """Wrapper to handle common logic like target_sheet before/after custom execution"""
        result_df = self.execute(context, params)
        
        # Super-Param: target_sheet (Global Materialization)
        target_sheet = params.get("target_sheet")
        if target_sheet:
            context.outputs[target_sheet] = (result_df if result_df is not None else context.current_df).copy()

    @abstractmethod
    def execute(self, context: ExecutionContext, params: dict):
        """Custom logic for each rule"""
        pass


class FilterRule(Rule):
    """Filter rows based on column conditions"""
    
    def execute(self, context, params):
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


class AggregateRule(Rule):
    """Super-Skill: Resumen interactivo (sum, mean, count, etc.)"""
    
    def execute(self, context, params):
        group_by = params.get("group_by")
        field = params.get("field")
        op = params.get("op", "sum")
        
        grouped_df = context.current_df.groupby(group_by, as_index=False)[field].agg(op)
        
        context.log("aggregate", f"Grouped by {group_by} applying {op} on {field}", len(grouped_df))
        return grouped_df


class MoveRule(Rule):
    """Legacy wrapper for simple move, now mostly handled by Super-Param target_sheet"""
    def execute(self, context, params):
        context.log("move", f"Materialized current sheet", len(context.current_df))
        return context.current_df


# --- Factory & Registry ---

RULE_REGISTRY = {
    "filter": FilterRule,
    "aggregate": AggregateRule,
    "group_sum": AggregateRule,  # Alias para compatibilidad
    "move": MoveRule
}


def get_rule(rule_type: str) -> Rule:
    """Factory method to get rule instance by type"""
    if rule_type not in RULE_REGISTRY:
        raise ValueError(f"Unknown rule type: {rule_type}")
    return RULE_REGISTRY[rule_type]()
