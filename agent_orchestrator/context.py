"""
Context - Shared state between agents in a workflow.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time


@dataclass
class Context:
    """
    Shared context for agents in a workflow.
    
    Agents can read from and write to this context to share data.
    """
    
    # Input data for the workflow
    input: Dict[str, Any] = field(default_factory=dict)
    
    # Output data from each step (step_name -> result)
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata (timing, token usage, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: Dict[str, Exception] = field(default_factory=dict)
    
    # Retry counts
    retries: Dict[str, int] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from context (checks outputs first, then input)."""
        if key in self.outputs:
            return self.outputs[key]
        return self.input.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in outputs."""
        self.outputs[key] = value
    
    def get_output(self, step_name: str, default: Any = None) -> Any:
        """Get output from a specific step."""
        return self.outputs.get(step_name, default)
    
    def set_output(self, step_name: str, value: Any) -> None:
        """Set output for a specific step."""
        self.outputs[step_name] = value
    
    def has_error(self, step_name: str) -> bool:
        """Check if a step has an error."""
        return step_name in self.errors
    
    def get_error(self, step_name: str) -> Optional[Exception]:
        """Get error for a step."""
        return self.errors.get(step_name)
    
    def set_error(self, step_name: str, error: Exception) -> None:
        """Set error for a step."""
        self.errors[step_name] = error
    
    def start_timer(self, step_name: str) -> float:
        """Start timing a step, returns start time."""
        start = time.time()
        if "timing" not in self.metadata:
            self.metadata["timing"] = {}
        self.metadata["timing"][f"{step_name}_start"] = start
        return start
    
    def end_timer(self, step_name: str) -> float:
        """End timing a step, returns duration in seconds."""
        end = time.time()
        timing = self.metadata.get("timing", {})
        start = timing.get(f"{step_name}_start", end)
        duration = end - start
        timing[f"{step_name}_duration"] = duration
        self.metadata["timing"] = timing
        return duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Export context as a dictionary."""
        return {
            "input": self.input,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "errors": {k: str(v) for k, v in self.errors.items()},
            "retries": self.retries,
        }
