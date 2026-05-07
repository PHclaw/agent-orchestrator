"""
Agent Wrapper - Wraps any callable to be used as an agent in workflows.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Union
from .context import Context


@dataclass
class AgentWrapper:
    """
    Wrapper for agents to be used in workflows.
    
    An agent is any callable that takes a Context and returns a result.
    This wrapper provides retry logic, timeout, and name tracking.
    """
    
    name: str
    
    # The callable that performs the agent's work
    callable: Callable[[Context], Any]
    
    # Optional description
    description: Optional[str] = None
    
    # Max retries on failure
    max_retries: int = 0
    
    # Timeout in seconds (0 = no timeout)
    timeout: float = 0.0
    
    # Tags for filtering/grouping
    tags: list = field(default_factory=list)
    
    def __call__(self, ctx: Context) -> Any:
        """Execute the agent with retry logic."""
        attempt = 0
        
        while attempt <= self.max_retries:
            ctx.retries[self.name] = attempt
            
            try:
                ctx.start_timer(self.name)
                
                if self.timeout > 0:
                    # TODO: Add timeout support with asyncio for async engines
                    result = self.callable(ctx)
                else:
                    result = self.callable(ctx)
                
                duration = ctx.end_timer(self.name)
                ctx.set_output(self.name, result)
                
                # Clear any previous error if retry succeeded
                if self.name in ctx.errors:
                    del ctx.errors[self.name]
                
                return result
                
            except Exception as e:
                duration = ctx.end_timer(self.name)
                ctx.set_error(self.name, e)
                
                if attempt < self.max_retries:
                    attempt += 1
                    continue
                else:
                    # Max retries exhausted, propagate error
                    raise
        
        return ctx.get_output(self.name)
    
    def run(self, input_data: Dict[str, Any] = None) -> Context:
        """
        Run this agent standalone (creates a fresh context).
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Context with outputs populated
        """
        ctx = Context(input=input_data or {})
        self(ctx)
        return ctx
    
    @classmethod
    def from_function(cls, func: Callable, name: str = None, **kwargs):
        """
        Create an AgentWrapper from a function.
        
        Args:
            func: The function to wrap
            name: Agent name (defaults to function name)
            **kwargs: Additional AgentWrapper parameters
            
        Returns:
            AgentWrapper instance
        """
        return cls(
            name=name or func.__name__,
            callable=func,
            description=kwargs.get("description", func.__doc__),
            **{k: v for k, v in kwargs.items() if k != "description"}
        )