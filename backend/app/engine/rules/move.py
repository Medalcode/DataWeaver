from app.engine.rules.base import Rule


class MoveRule(Rule):
    """Move current dataframe to a named output sheet"""
    
    def execute(self, context, params):
        target_sheet = params.get("target_sheet")
        
        if not target_sheet:
            raise ValueError("target_sheet is required")
        
        context.outputs[target_sheet] = context.current_df.copy()
        context.log(
            "move",
            f"Moved {len(context.current_df)} rows to sheet '{target_sheet}'",
            len(context.current_df)
        )
