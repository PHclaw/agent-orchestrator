# Agent Orchestrator

**Multi-agent orchestration library for AI agents** — sequential, parallel, conditional workflows.

## Installation

```bash
pip install agent-orchestrator
```

## Quick Start

```python
from agent_orchestrator import Workflow, AgentWrapper, Context

# Define agents
def researcher(ctx: Context) -> str:
    query = ctx.get("query")
    # ... research logic ...
    ctx.set("research_result", "found data")
    return "researched"

def writer(ctx: Context) -> str:
    data = ctx.get("research_result")
    # ... write logic ...
    return "article written"

def reviewer(ctx: Context) -> str:
    return "reviewed and approved"

# Create workflow
wf = Workflow(name="content_pipeline")
wf.add_agent(researcher)
wf.add_agent(writer)
wf.add_agent(reviewer)

# Run
ctx = wf.run(input_data={"query": "AI agents"})
print(ctx.outputs)  # All agent outputs
```

## Features

### Sequential Execution

Agents run one after another, sharing context:

```python
wf.add_sequential("pipeline", [agent1, agent2, agent3])
```

### Parallel Execution

Agents run simultaneously:

```python
wf.add_parallel("concurrent", [agent1, agent2, agent3])
```

### Conditional Branching

If/else logic:

```python
wf.add_conditional(
    "check_type",
    condition=lambda ctx: ctx.get("type") == "urgent",
    if_true=[urgent_handler],
    if_false=[normal_handler]
)
```

### Loops

Repeat until condition is met:

```python
wf.add_loop(
    "refine",
    agents=[refiner],
    condition=lambda ctx: ctx.get("quality") < 0.9,
    max_iterations=10
)
```

### Async Support

```python
# Async agents
async def async_agent(ctx: Context):
    await some_async_operation()
    return "done"

# Run workflow async
ctx = await wf.arun(input_data={"query": "..."})
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Workflow                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Steps: [Sequential, Parallel, Conditional, Loop]    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Context (shared state)                   │    │
│  │  • input    • outputs    • metadata    • errors      │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         AgentWrapper (retry, timeout, tracing)       │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Your Agent Callable                     │    │
│  │            (agent_orchestrator.Context -> Any)        │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Context API

```python
ctx.get("key")           # Get from outputs or input
ctx.set("key", value)    # Set in outputs
ctx.get_output("agent")  # Get specific agent output
ctx.has_error("agent")   # Check for errors
ctx.metadata             # Timing, retries, etc.
```

## Callbacks

```python
wf = Workflow(
    name="pipeline",
    on_start=lambda ctx: print("Starting..."),
    on_end=lambda ctx: print("Done!"),
    on_error=lambda ctx, e: print(f"Error: {e}"),
)
```

## License

MIT