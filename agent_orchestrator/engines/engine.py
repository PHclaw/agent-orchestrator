"""
Engine - Synchronous workflow execution.
"""

from typing import Any, Dict, Optional
from ..context import Context
from ..workflow import Workflow


class Engine:
    """
    Synchronous workflow execution engine.
    
    Executes all steps in a workflow sequentially.
    """
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
    
    def run(self, input_data: Dict[str, Any] = None) -> Context:
        """
        Execute the workflow.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Context with outputs populated
        """
        ctx = Context(input=input_data or {})
        
        # Callback: on_start
        if self.workflow.on_start:
            self.workflow.on_start(ctx)
        
        try:
            ctx.start_timer(self.workflow.name)
            
            # Execute each step
            for step in self.workflow.steps:
                step.execute(ctx)
            
            duration = ctx.end_timer(self.workflow.name)
            
            # Callback: on_end
            if self.workflow.on_end:
                self.workflow.on_end(ctx)
            
        except Exception as e:
            ctx.end_timer(self.workflow.name)
            
            # Callback: on_error
            if self.workflow.on_error:
                self.workflow.on_error(ctx, e)
            
            raise
        
        return ctx
