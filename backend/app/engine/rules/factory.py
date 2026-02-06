from app.engine.rules.filter import FilterRule
from app.engine.rules.move import MoveRule
from app.engine.rules.group_sum import GroupSumRule


RULE_REGISTRY = {
    "filter": FilterRule,
    "move": MoveRule,
    "group_sum": GroupSumRule,
}


def get_rule(rule_type: str):
    """Factory method to get rule instance by type"""
    if rule_type not in RULE_REGISTRY:
        raise ValueError(f"Unknown rule type: {rule_type}")
    
    return RULE_REGISTRY[rule_type]()


def get_available_rules():
    """Return list of available rule types"""
    return list(RULE_REGISTRY.keys())
