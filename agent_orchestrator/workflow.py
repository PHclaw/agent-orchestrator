"""
Workflow - Defines an orchestration of multiple agents.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from .context import Context
from .agent import AgentWrapper
from .steps import Step, SequentialStep, ParallelStep, ConditionalStep


@dataclass
class Workflow:
    """
    A workflow orchestrates multiple agents.
    
    Workflows are built by adding steps (sequential, parallel, conditional).
    Each step can contain agents or other nested workflows.
    """
    
    name: str
    
    # Steps in this workflow
    steps: List[Step] = field(default_factory=list)
    
    # Description
    description: Optional[str] = None
    
    # Max retries for the entire workflow
    max_retries: int = 0
    
    # Timeout for entire workflow
    timeout: float = 0.0
    
    # Tags for categorization
    tags: List[str] = field(default_factory=list)
    
    # Callbacks
    on_start: Optional[Callable[[Context], None]] = None
    on_end: Optional[Callable[[Context], None]] = None
    on_error: Optional[Callable[[Context, Exception], None]] = None
    
    def add_agent(self, agent: Union[AgentWrapper, Callable], name: str = None, **kwargs) -> "Workflow":
        """
        Add an agent as a sequential step.
        
        Args:
            agent: AgentWrapper or callable
            name: Step name (defaults to agent name)
            **kwargs: Additional Step parameters
            
        Returns:
            self for chaining
        """
        if callable(agent) and not isinstance(agent, AgentWrapper):
            agent = AgentWrapper.from_function(agent, name=name)
        
        step = SequentialStep(
            name=name or agent.name,
            agents=[agent],
            **kwargs
        )
        self.steps.append(step)
        return self
    
    def add_sequential(self, name: str, agents: List[Union[AgentWrapper, Callable]], **kwargs) -> "Workflow":
        """
        Add a sequential step (agents run one after another).
        
        Args:
            name: Step name
            agents: List of agents
            **kwargs: Additional Step parameters
            
        Returns:
            self for chaining
        """
        wrapped = [
            AgentWrapper.from_function(a) if callable(a) and not isinstance(a, AgentWrapper) else a
            for a in agents
        ]
        self.steps.append(SequentialStep(name=name, agents=wrapped, **kwargs))
        return self
    
    def add_parallel(self, name: str, agents: List[Union[AgentWrapper, Callable]], **kwargs) -> "Workflow":
        """
        Add a parallel step (agents run simultaneously).
        
        Args:
            name: Step name
            agents: List of agents
            **kwargs: Additional Step parameters
            
        Returns:
            self for chaining
        """
        wrapped = [
            AgentWrapper.from_function(a) if callable(a) and not isinstance(a, AgentWrapper) else a
            for a in agents
        ]
        self.steps.append(ParallelStep(name=name, agents=wrapped, **kwargs))
        return self
    
    def add_conditional(
        self,
        name: str,
        condition: Callable[[Context], bool],
        if_true: List[Union[AgentWrapper, Callable]],
        if_false: List[Union[AgentWrapper, Callable]] = None,
        **kwargs
    ) -> "Workflow":
        """
        Add a conditional step (if/else branching).
        
        Args:
            name: Step name
            condition: Function that takes Context and returns bool
            if_true: Agents to run if condition is True
            if_false: Agents to run if condition is False (optional)
            **kwargs: Additional Step parameters
            
        Returns:
            self for chaining
        """
        wrap = lambda agents: [
            AgentWrapper.from_function(a) if callable(a) and not isinstance(a, AgentWrapper) else a
            for a in (agents or [])
        ]
        self.steps.append(ConditionalStep(
            name=name,
            condition=condition,
            if_true=wrap(if_true),
            if_false=wrap(if_false or []),
            **kwargs
        ))
        return self
    
    def add_loop(
        self,
        name: str,
        agents: List[Union[AgentWrapper, Callable]],
        condition: Callable[[Context], bool] = None,
        max_iterations: int = 10,
        **kwargs
    ) -> "Workflow":
        """
        Add a loop step (repeat agents until condition is met).
        
        Args:
            name: Step name
            agents: Agents to loop
            condition: Continue condition (if None, loops max_iterations times)
            max_iterations: Safety limit
            **kwargs: Additional Step parameters
            
        Returns:
            self for chaining
        """
        from .steps import LoopStep
        wrapped = [
            AgentWrapper.from_function(a) if callable(a) and not isinstance(a, AgentWrapper) else a
            for a in agents
        ]
        self.steps.append(LoopStep(
            name=name,
            agents=wrapped,
            condition=condition,
            max_iterations=max_iterations,
            **kwargs
        ))
        return self
    
    def run(self, input_data: Dict[str, Any] = None) -> Context:
        """
        Run the workflow synchronously.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Context with outputs populated
        """
        from .engines import Engine
        engine = Engine(workflow=self)
        return engine.run(input_data)
    
    async def arun(self, input_data: Dict[str, Any] = None) -> Context:
        """
        Run the workflow asynchronously.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Context with outputs populated
        """
        from .engines import AsyncEngine
        engine = AsyncEngine(workflow=self)
        return await engine.arun(input_data)
    
    def __repr__(self) -> str:
        return f"Workflow(name={self.name!r}, steps={len(self.steps)})"