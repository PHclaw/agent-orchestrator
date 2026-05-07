"""
Conditional Step - If/else branching.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..context import Context
from ..agent import AgentWrapper
from .step import Step
from .sequential import SequentialStep


@dataclass
class ConditionalStep(Step):
    """
    Conditional execution - if/else branching.
    
    Evaluates a condition function and runs either if_true or if_false agents.
    """
    
    # Condition function: takes Context, returns bool
    condition: Callable[[Context], bool] = None
    
    # Agents to run if condition is True
    if_true: List[AgentWrapper] = field(default_factory=list)
    
    # Agents to run if condition is False
    if_false: List[AgentWrapper] = field(default_factory=list)
    
    def execute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents based on condition."""
        # Evaluate condition
        try:
            result = self.condition(ctx)
        except Exception as e:
            ctx.set_error(f"{self.name}_condition", e)
            raise
        
        # Choose branch
        agents = self.if_true if result else self.if_false
        
        # Run selected agents sequentially
        results = {}
        
        for agent in agents:
            try:
                output = agent(ctx)
                results[agent.name] = output
                ctx.set_output(agent.name, output)
                
            except Exception as e:
                ctx.set_error(agent.name, e)
                results[agent.name] = None
                
                if not self.continue_on_error:
                    raise
        
        # Store branch decision
        ctx.metadata[f"{self.name}_branch"] = "if_true" if result else "if_false"
        
        return results
    
    async def aexecute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents based on condition (async)."""
        import inspect
        
        # Evaluate condition (sync or async)
        try:
            if inspect.iscoroutinefunction(self.condition):
                result = await self.condition(ctx)
            else:
                result = self.condition(ctx)
        except Exception as e:
            ctx.set_error(f"{self.name}_condition", e)
            raise
        
        # Choose branch
        agents = self.if_true if result else self.if_false
        
        # Run selected agents sequentially
        results = {}
        
        for agent in agents:
            try:
                if inspect.iscoroutinefunction(agent.callable):
                    output = await agent.callable(ctx)
                else:
                    output = agent(ctx)
                
                results[agent.name] = output
                ctx.set_output(agent.name, output)
                
            except Exception as e:
                ctx.set_error(agent.name, e)
                results[agent.name] = None
                
                if not self.continue_on_error:
                    raise
        
        ctx.metadata[f"{self.name}_branch"] = "if_true" if result else "if_false"
        
        return results