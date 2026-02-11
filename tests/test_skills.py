import pandas as pd

from app.engine.context import ExecutionContext
from app.engine.rules.filter import FilterRule
from app.engine.rules.move import MoveRule
from app.engine.rules.group_sum import GroupSumRule


def test_filter_rule():
    df = pd.DataFrame([
        {"Status": "OK", "Amount": 10},
        {"Status": "NO", "Amount": 5},
    ])

    context = ExecutionContext(df)

    rule = FilterRule()
    params = {"type": "filter", "column": "Status", "operator": "=", "value": "OK"}
    rule.execute(context, params)

    assert len(context.current_df) == 1
    assert context.current_df.iloc[0]["Status"] == "OK"
    assert context.logs and context.logs[-1]["step_type"] == "filter"


def test_group_sum_and_move_rules():
    df = pd.DataFrame([
        {"Category": "A", "Amount": 10},
        {"Category": "A", "Amount": 5},
        {"Category": "B", "Amount": 3},
    ])

    context = ExecutionContext(df)

    group_rule = GroupSumRule()
    group_params = {"type": "group_sum", "group_by": "Category", "field": "Amount", "target_sheet": "sums"}
    group_rule.execute(context, group_params)

    assert "sums" in context.outputs
    sums_df = context.outputs["sums"]
    assert sums_df.loc[sums_df["Category"] == "A", "Amount"].iloc[0] == 15
    assert sums_df.loc[sums_df["Category"] == "B", "Amount"].iloc[0] == 3

    # Test move writes current_df to outputs
    move_rule = MoveRule()
    move_params = {"type": "move", "target_sheet": "final"}
    move_rule.execute(context, move_params)

    assert "final" in context.outputs
    assert len(context.outputs["final"]) == len(context.current_df)
    assert context.logs and any(l["step_type"] == "move" for l in context.logs)
