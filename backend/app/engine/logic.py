"""
Re-export module for backward compatibility.
All rules and factories are modularized under app.engine.rules.
"""

from app.engine.rules import (
    RULE_REGISTRY,
    AggregateRule,
    FilterRule,
    MoveRule,
    Rule,
    get_rule,
)

__all__ = [
    "Rule",
    "FilterRule",
    "AggregateRule",
    "MoveRule",
    "RULE_REGISTRY",
    "get_rule",
]
