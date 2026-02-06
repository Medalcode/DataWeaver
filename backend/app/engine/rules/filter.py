from app.engine.rules.base import Rule


class FilterRule(Rule):
    """Filter rows based on column conditions"""
    
    def execute(self, context, params):
        column = params.get("column")
        operator = params.get("operator")
        value = params.get("value")
        
        if column not in context.current_df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")
        
        df = context.current_df
        
        # Apply operator
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
        
        filtered_df = df[mask]
        
        context.current_df = filtered_df
        context.log(
            "filter",
            f"Filtered by {column} {operator} {value}",
            len(filtered_df)
        )
