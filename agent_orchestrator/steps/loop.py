"""
Loop Step - Repeat agents until condition is met.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..context import Context
from ..agent import AgentWrapper
from .step import Step


@dataclass
class LoopStep(Step):
    """
    Loop execution - repeat agents until condition is met.
    
    If no condition is provided, loops max_iterations times.
    """
    
    # Continue condition: takes Context, returns True to continue
    condition: Optional[Callable[[Context], bool]] = None
    
    # Maximum iterations (safety limit)
    max_iterations: int = 10
    
    def execute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents in a loop."""
        results = {}
        iteration = 0
        
        ctx.metadata[f"{self.name}_iterations"] = 0
        
        while True:
            # Check max iterations
            if iteration >= self.max_iterations:
                ctx.metadata[f"{self.name}_stopped"] = "max_iterations"
                break
            
            # Check condition (if provided)
            if self.condition is not None:
                try:
                    should_continue = self.condition(ctx)
                    if not should_continue:
                        ctx.metadata[f"{self.name}_stopped"] = "condition_met"
                        break
                except Exception as e:
                    ctx.set_error(f"{self.name}_condition", e)
                    raise
            
            # Run agents
            for agent in self.agents:
                try:
                    result = agent(ctx)
                    results[f"{agent.name}_{iteration}"] = result
                    ctx.set_output(f"{agent.name}_{iteration}", result)
                    
                except Exception as e:
                    ctx.set_error(f"{agent.name}_{iteration}", e)
                    results[f"{agent.name}_{iteration}"] = None
                    
                    if not self.continue_on_error:
                        raise
            
            iteration += 1
            ctx.metadata[f"{self.name}_iterations"] = iteration
            
            # If no condition, stop after one iteration if max_iterations is 1
            if self.condition is None and iteration >= self.max_iterations:
                break
        
        return results
    
    async def aexecute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents in a loop (async)."""
        import inspect
        
        results = {}
        iteration = 0
        
        ctx.metadata[f"{self.name}_iterations"] = 0
        
        while True:
            if iteration >= self.max_iterations:
                ctx.metadata[f"{self.name}_stopped"] = "max_iterations"
                break
            
            if self.condition is not None:
                try:
                    if inspect.iscoroutinefunction(self.condition):
                        should_continue = await self.condition(ctx)
                    else:
                        should_continue = self.condition(ctx)
                    
                    if not should_continue:
                        ctx.metadata[f"{self.name}_stopped"] = "condition_met"
                        break
                except Exception as e:
                    ctx.set_error(f"{self.name}_condition", e)
                    raise
            
            for agent in self.agents:
                try:
                    if inspect.iscoroutinefunction(agent.callable):
                        result = await agent.callable(ctx)
                    else:
                        result = agent(ctx)
                    
                    results[f"{agent.name}_{iteration}"] = result
                    ctx.set_output(f"{agent.name}_{iteration}", result)
                    
                except Exception as e:
                    ctx.set_error(f"{agent.name}_{iteration}", e)
                    results[f"{agent.name}_{iteration}"] = None
                    
                    if not self.continue_on_error:
                        raise
            
            iteration += 1
            ctx.metadata[f"{self.name}_iterations"] = iteration
            
            if self.condition is None and iteration >= self.max_iterations:
                break
        
        return results