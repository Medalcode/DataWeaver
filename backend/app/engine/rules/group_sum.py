from app.engine.rules.base import Rule


class GroupSumRule(Rule):
    """Group by column and sum another column"""
    
    def execute(self, context, params):
        group_by = params.get("group_by")
        field = params.get("field")
        target_sheet = params.get("target_sheet")
        
        if not all([group_by, field, target_sheet]):
            raise ValueError("group_by, field, and target_sheet are required")
        
        if group_by not in context.current_df.columns:
            raise ValueError(f"Column '{group_by}' not found")
        
        if field not in context.current_df.columns:
            raise ValueError(f"Column '{field}' not found")
        
        # Group and sum
        grouped_df = (
            context.current_df
            .groupby(group_by, as_index=False)[field]
            .sum()
        )
        
        context.outputs[target_sheet] = grouped_df
        context.log(
            "group_sum",
            f"Grouped by '{group_by}', summed '{field}', created sheet '{target_sheet}'",
            len(grouped_df)
        )
