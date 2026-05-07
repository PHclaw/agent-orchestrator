"""
Parallel Step - Agents run simultaneously.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..context import Context
from ..agent import AgentWrapper
from .step import Step


@dataclass
class ParallelStep(Step):
    """
    Parallel execution - agents run simultaneously.
    
    All agents receive the same context snapshot. Results are merged
    after all agents complete.
    """
    
    # Max concurrent agents (0 = unlimited)
    max_concurrent: int = 0
    
    def execute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents in parallel using threads."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        max_workers = self.max_concurrent or len(self.agents)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for agent in self.agents:
                future = executor.submit(self._run_agent, agent, ctx)
                futures[future] = agent
            
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    result = future.result()
                    results[agent.name] = result
                except Exception as e:
                    ctx.set_error(agent.name, e)
                    results[agent.name] = None
                    if not self.continue_on_error:
                        for f in futures:
                            f.cancel()
                        raise
        
        return results
    
    def _run_agent(self, agent: AgentWrapper, ctx: Context) -> Any:
        """Run a single agent (for thread pool)."""
        result = agent(ctx)
        ctx.set_output(agent.name, result)
        return result
    
    async def aexecute(self, ctx: Context) -> Dict[str, Any]:
        """Run agents in parallel (async)."""
        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent) if self.max_concurrent else None
        
        async def _run(agent: AgentWrapper):
            if semaphore:
                async with semaphore:
                    return await self._arun_agent(agent, ctx)
            return await self._arun_agent(agent, ctx)
        
        tasks = [_run(agent) for agent in self.agents]
        completed = await asyncio.gather(*tasks, return_exceptions=self.continue_on_error)
        
        for agent, result in zip(self.agents, completed):
            if isinstance(result, Exception):
                ctx.set_error(agent.name, result)
                results[agent.name] = None
                if not self.continue_on_error:
                    raise result
            else:
                results[agent.name] = result
                ctx.set_output(agent.name, result)
        
        return results
    
    async def _arun_agent(self, agent: AgentWrapper, ctx: Context) -> Any:
        """Run a single agent asynchronously."""
        import inspect
        if inspect.iscoroutinefunction(agent.callable):
            result = await agent.callable(ctx)
        else:
            result = agent(ctx)
        ctx.set_output(agent.name, result)
        return result