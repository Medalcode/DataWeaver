import pandas as pd
import pytest
from app.engine.engine import RuleEngine
from app.engine.validator import WorkflowValidationError


def test_rule_engine_run_success():
    engine = RuleEngine()
    df = pd.DataFrame(
        [
            {"Status": "Active", "Amount": 100},
            {"Status": "Inactive", "Amount": 50},
            {"Status": "Active", "Amount": 200},
        ]
    )
    workflow = {
        "steps": [
            {"type": "filter", "column": "Status", "operator": "=", "value": "Active"},
            {
                "type": "aggregate",
                "group_by": "Status",
                "field": "Amount",
                "op": "sum",
                "target_sheet": "ActiveSummary",
            },
        ]
    }

    result = engine.run(df, workflow)

    assert "ActiveSummary" in result["outputs"]
    assert len(result["logs"]) == 2
    summary_df = result["outputs"]["ActiveSummary"]
    assert summary_df["Amount"].iloc[0] == 300


def test_rule_engine_preview():
    engine = RuleEngine()
    df = pd.DataFrame(
        [
            {"Region": "North", "Sales": 10},
            {"Region": "South", "Sales": 20},
        ]
    )
    workflow = {
        "steps": [
            {"type": "filter", "column": "Region", "operator": "=", "value": "North", "target_sheet": "PreviewSheet"},
        ]
    }

    preview_res = engine.preview(df, workflow, max_rows=10)

    assert len(preview_res["before"]) == 2
    assert preview_res["after"]["sheet"] == "PreviewSheet"
    assert len(preview_res["after"]["rows"]) == 1
    assert preview_res["after"]["rows"][0]["Region"] == "North"


def test_rule_engine_empty_workflow():
    engine = RuleEngine()
    df = pd.DataFrame([{"A": 1}])
    with pytest.raises(WorkflowValidationError, match="Workflow must contain at least one step"):
        engine.run(df, {"steps": []})


def test_rule_engine_missing_steps_key():
    engine = RuleEngine()
    df = pd.DataFrame([{"A": 1}])
    with pytest.raises(WorkflowValidationError, match="must contain 'steps' array"):
        engine.run(df, {})


def test_rule_engine_unknown_rule_type():
    engine = RuleEngine()
    df = pd.DataFrame([{"A": 1}])
    workflow = {"steps": [{"type": "non_existent_rule"}]}
    with pytest.raises(WorkflowValidationError, match="Unknown rule type"):
        engine.run(df, workflow)
