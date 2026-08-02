from app.engine.rules.aggregate import AggregateRule
from app.engine.rules.base import Rule
from app.engine.rules.filter import FilterRule
from app.engine.rules.move import MoveRule

RULE_REGISTRY: dict[str, type[Rule]] = {
    "filter": FilterRule,
    "aggregate": AggregateRule,
    "group_sum": AggregateRule,  # Alias for backward compatibility
    "move": MoveRule,
}


def get_rule(rule_type: str) -> Rule:
    """Factory method to get rule instance by type."""
    if rule_type not in RULE_REGISTRY:
        raise ValueError(f"Unknown rule type: {rule_type}")
    return RULE_REGISTRY[rule_type]()
