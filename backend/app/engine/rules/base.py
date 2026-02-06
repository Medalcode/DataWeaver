from abc import ABC, abstractmethod
from app.engine.context import ExecutionContext


class Rule(ABC):
    """Base class for all workflow rules"""
    
    @abstractmethod
    def execute(self, context: ExecutionContext, params: dict):
        """Execute the rule with given parameters"""
        pass
