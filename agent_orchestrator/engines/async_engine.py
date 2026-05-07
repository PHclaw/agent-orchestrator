"""
AsyncEngine - Asynchronous workflow execution.
"""

import asyncio
from typing import Any, Dict, Optional
from ..context import Context
from ..workflow import Workflow


class AsyncEngine:
    """
    Asynchronous workflow execution engine.
    
    Executes all steps in a workflow, supporting async agents.
    """
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
    
    async def arun(self, input_data: Dict[str, Any] = None) -> Context:
        """
        Execute the workflow asynchronously.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Context with outputs populated
        """
        ctx = Context(input=input_data or {})
        
        # Callback: on_start (sync or async)
        if self.workflow.on_start:
            import inspect
            if inspect.iscoroutinefunction(self.workflow.on_start):
                await self.workflow.on_start(ctx)
            else:
                self.workflow.on_start(ctx)
        
        try:
            ctx.start_timer(self.workflow.name)
            
            # Execute each step
            for step in self.workflow.steps:
                await step.aexecute(ctx)
            
            duration = ctx.end_timer(self.workflow.name)
            
            # Callback: on_end
            if self.workflow.on_end:
                import inspect
                if inspect.iscoroutinefunction(self.workflow.on_end):
                    await self.workflow.on_end(ctx)
                else:
                    self.workflow.on_end(ctx)
            
        except Exception as e:
            ctx.end_timer(self.workflow.name)
            
            # Callback: on_error
            if self.workflow.on_error:
                import inspect
                if inspect.iscoroutinefunction(self.workflow.on_error):
                    await self.workflow.on_error(ctx, e)
                else:
                    self.workflow.on_error(ctx, e)
            
            raise
        
        return ctx
    
    def run(self, input_data: Dict[str, Any] = None) -> Context:
        """
        Execute the workflow synchronously (wraps async).
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Context with outputs populated
        """
        return asyncio.run(self.arun(input_data))