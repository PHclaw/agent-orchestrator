"""
Base Step - Abstract base class for workflow steps.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..context import Context
from ..agent import AgentWrapper


@dataclass
class Step(ABC):
    """
    Base class for all workflow steps.
    
    A step is a unit of work in a workflow. It can contain one or more agents.
    """
    
    name: str
    
    # Agents in this step
    agents: List[AgentWrapper] = field(default_factory=list)
    
    # Description
    description: Optional[str] = None
    
    # Continue on error?
    continue_on_error: bool = False
    
    # Tags
    tags: List[str] = field(default_factory=list)
    
    @abstractmethod
    def execute(self, ctx: Context) -> Dict[str, Any]:
        """
        Execute this step.
        
        Args:
            ctx: Workflow context
            
        Returns:
            Dict of agent_name -> result
        """
        pass
    
    @abstractmethod
    async def aexecute(self, ctx: Context) -> Dict[str, Any]:
        """
        Execute this step asynchronously.
        
        Args:
            ctx: Workflow context
            
        Returns:
            Dict of agent_name -> result
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, agents={len(self.agents)})"
