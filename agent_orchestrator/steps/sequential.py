"""
Sequential Step - Agents run one after another.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..context import Context
from ..agent import AgentWrapper
from .step import Step


@dataclass
class SequentialStep(Step):
    """
    Sequential execution - agents run one after another.
    
    Each agent's output is added to context before the next agent runs.
    This allows downstream agents to use upstream outputs.
    """
    
    def execute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents sequentially."""
        results = {}
        
        for agent in self.agents:
            try:
                result = agent(ctx)
                results[agent.name] = result
                ctx.set_output(agent.name, result)
                
            except Exception as e:
                ctx.set_error(agent.name, e)
                results[agent.name] = None
                
                if not self.continue_on_error:
                    raise
        
        return results
    
    async def aexecute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents sequentially (async)."""
        results = {}
        
        for agent in self.agents:
            try:
                # Check if agent callable is async
                import inspect
                if inspect.iscoroutinefunction(agent.callable):
                    result = await agent.callable(ctx)
                else:
                    result = agent(ctx)
                
                results[agent.name] = result
                ctx.set_output(agent.name, result)
                
            except Exception as e:
                ctx.set_error(agent.name, e)
                results[agent.name] = None
                
                if not self.continue_on_error:
                    raise
        
        return results