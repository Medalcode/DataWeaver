import pandas as pd
import pytest
from app.engine.context import ExecutionContext
from app.engine.logic import AggregateRule, FilterRule, MoveRule
from app.engine.validator import WorkflowValidationError, validate_workflow


def test_filter_rule():
    df = pd.DataFrame(
        [
            {"Status": "OK", "Amount": 10},
            {"Status": "NO", "Amount": 5},
        ]
    )

    context = ExecutionContext(df)

    rule = FilterRule()
    params = {"type": "filter", "column": "Status", "operator": "=", "value": "OK"}
    rule.run_execute(context, params)

    assert len(context.current_df) == 1
    assert context.current_df.iloc[0]["Status"] == "OK"
    assert context.logs and context.logs[-1]["step_type"] == "filter"


def test_aggregate_rule():
    df = pd.DataFrame(
        [
            {"Category": "A", "Amount": 10},
            {"Category": "A", "Amount": 5},
            {"Category": "B", "Amount": 3},
        ]
    )

    context = ExecutionContext(df)

    # AggregateRule replaces GroupSumRule
    rule = AggregateRule()
    params = {
        "type": "aggregate",
        "group_by": "Category",
        "field": "Amount",
        "target_sheet": "sums",
        "op": "sum",
    }
    rule.run_execute(context, params)

    assert "sums" in context.outputs
    sums_df = context.outputs["sums"]
    assert sums_df.loc[sums_df["Category"] == "A", "Amount"].iloc[0] == 15


def test_super_param_target_sheet():
    df = pd.DataFrame([{"Val": 1}, {"Val": 2}])
    context = ExecutionContext(df)

    # Test that FilterRule (or any rule) can materialize via target_sheet
    rule = FilterRule()
    params = {
        "type": "filter",
        "column": "Val",
        "operator": ">",
        "value": 1,
        "target_sheet": "filtered_output",
    }
    rule.run_execute(context, params)

    assert "filtered_output" in context.outputs
    assert len(context.outputs["filtered_output"]) == 1


def test_move_rule():
    df = pd.DataFrame([{"Val": 1}, {"Val": 2}])
    context = ExecutionContext(df)

    rule = MoveRule()
    params = {"type": "move", "target_sheet": "moved_sheet"}
    rule.run_execute(context, params)

    assert "moved_sheet" in context.outputs
    assert len(context.outputs["moved_sheet"]) == 2


def test_polymorphic_validation_success():
    df = pd.DataFrame({"Status": ["OK"], "Amount": [10]})
    workflow = {
        "steps": [
            {"type": "filter", "column": "Status", "operator": "=", "value": "OK"},
            {"type": "aggregate", "group_by": "Status", "field": "Amount", "target_sheet": "summary"},
        ]
    }
    validate_workflow(workflow, df)  # should not raise


def test_polymorphic_validation_missing_column():
    df = pd.DataFrame({"Status": ["OK"]})
    workflow = {
        "steps": [
            {"type": "filter", "column": "NonExistent", "operator": "=", "value": "OK"},
        ]
    }
    with pytest.raises(WorkflowValidationError, match="column 'NonExistent' does not exist"):
        validate_workflow(workflow, df)
