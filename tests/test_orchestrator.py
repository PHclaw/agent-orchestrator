"""
Tests for agent-orchestrator.
"""

import pytest
import asyncio
from agent_orchestrator import (
    Workflow,
    Context,
    AgentWrapper,
    SequentialStep,
    ParallelStep,
    ConditionalStep,
    LoopStep,
    Engine,
    AsyncEngine,
)


# Helper agents
def agent_a(ctx: Context) -> str:
    return "result_a"

def agent_b(ctx: Context) -> str:
    return "result_b"

def agent_with_input(ctx: Context) -> str:
    return ctx.get("query", "default")

def agent_writes_output(ctx: Context) -> str:
    ctx.set("shared_data", "from_agent")
    return "wrote"

def agent_reads_output(ctx: Context) -> str:
    return ctx.get("shared_data", "not_found")


class TestAgentWrapper:
    """Tests for AgentWrapper."""
    
    def test_basic_execution(self):
        agent = AgentWrapper(name="test_agent", callable=agent_a)
        ctx = Context()
        result = agent(ctx)
        assert result == "result_a"
        assert ctx.get_output("test_agent") == "result_a"
    
    def test_with_input(self):
        agent = AgentWrapper(name="input_agent", callable=agent_with_input)
        ctx = Context(input={"query": "hello"})
        result = agent(ctx)
        assert result == "hello"
    
    def test_from_function(self):
        agent = AgentWrapper.from_function(agent_b)
        assert agent.name == "agent_b"
        result = agent(Context())
        assert result == "result_b"


class TestContext:
    """Tests for Context."""
    
    def test_get_set(self):
        ctx = Context()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"
    
    def test_input_outputs_priority(self):
        ctx = Context(input={"key": "input_value"})
        ctx.set("key", "output_value")
        assert ctx.get("key") == "output_value"  # outputs take priority
    
    def test_timing(self):
        ctx = Context()
        import time
        ctx.start_timer("step1")
        time.sleep(0.01)
        duration = ctx.end_timer("step1")
        assert duration >= 0.01


class TestSequentialStep:
    """Tests for SequentialStep."""
    
    def test_sequential_execution(self):
        step = SequentialStep(
            name="seq",
            agents=[
                AgentWrapper(name="a", callable=agent_a),
                AgentWrapper(name="b", callable=agent_b),
            ]
        )
        ctx = Context()
        results = step.execute(ctx)
        assert results["a"] == "result_a"
        assert results["b"] == "result_b"
    
    def test_data_sharing(self):
        step = SequentialStep(
            name="seq",
            agents=[
                AgentWrapper(name="writer", callable=agent_writes_output),
                AgentWrapper(name="reader", callable=agent_reads_output),
            ]
        )
        ctx = Context()
        step.execute(ctx)
        assert ctx.get("shared_data") == "from_agent"
        assert ctx.get_output("reader") == "from_agent"


class TestParallelStep:
    """Tests for ParallelStep."""
    
    def test_parallel_execution(self):
        step = ParallelStep(
            name="par",
            agents=[
                AgentWrapper(name="a", callable=agent_a),
                AgentWrapper(name="b", callable=agent_b),
            ]
        )
        ctx = Context()
        results = step.execute(ctx)
        assert results["a"] == "result_a"
        assert results["b"] == "result_b"
    
    @pytest.mark.asyncio
    async def test_async_execution(self):
        step = ParallelStep(
            name="par_async",
            agents=[
                AgentWrapper(name="a", callable=agent_a),
                AgentWrapper(name="b", callable=agent_b),
            ]
        )
        ctx = Context()
        results = await step.aexecute(ctx)
        assert results["a"] == "result_a"
        assert results["b"] == "result_b"


class TestConditionalStep:
    """Tests for ConditionalStep."""
    
    def test_if_true_branch(self):
        step = ConditionalStep(
            name="cond",
            condition=lambda ctx: True,
            if_true=[AgentWrapper(name="a", callable=agent_a)],
            if_false=[AgentWrapper(name="b", callable=agent_b)],
        )
        ctx = Context()
        results = step.execute(ctx)
        assert results["a"] == "result_a"
        assert "b" not in results
        assert ctx.metadata["cond_branch"] == "if_true"
    
    def test_if_false_branch(self):
        step = ConditionalStep(
            name="cond",
            condition=lambda ctx: False,
            if_true=[AgentWrapper(name="a", callable=agent_a)],
            if_false=[AgentWrapper(name="b", callable=agent_b)],
        )
        ctx = Context()
        results = step.execute(ctx)
        assert results["b"] == "result_b"
        assert "a" not in results
        assert ctx.metadata["cond_branch"] == "if_false"


class TestLoopStep:
    """Tests for LoopStep."""
    
    def test_fixed_iterations(self):
        step = LoopStep(
            name="loop",
            agents=[AgentWrapper(name="counter", callable=agent_a)],
            max_iterations=3,
        )
        ctx = Context()
        results = step.execute(ctx)
        assert ctx.metadata["loop_iterations"] == 3
    
    def test_conditional_loop(self):
        call_count = [0]
        
        def counter(ctx: Context):
            call_count[0] += 1
            ctx.set("count", call_count[0])
            return call_count[0]
        
        def should_continue(ctx: Context) -> bool:
            return ctx.get("count", 0) < 3
        
        step = LoopStep(
            name="loop",
            agents=[AgentWrapper(name="counter", callable=counter)],
            condition=should_continue,
            max_iterations=10,
        )
        ctx = Context()
        results = step.execute(ctx)
        assert ctx.metadata["loop_iterations"] == 3
        assert ctx.metadata["loop_stopped"] == "condition_met"


class TestWorkflow:
    """Tests for Workflow."""
    
    def test_simple_workflow(self):
        wf = Workflow(name="test_wf")
        wf.add_agent(agent_a)
        wf.add_agent(agent_b)
        
        ctx = wf.run()
        assert ctx.get_output("agent_a") == "result_a"
        assert ctx.get_output("agent_b") == "result_b"
    
    def test_workflow_with_input(self):
        wf = Workflow(name="test_wf")
        wf.add_agent(AgentWrapper(name="input_agent", callable=agent_with_input))
        
        ctx = wf.run(input_data={"query": "hello"})
        assert ctx.get_output("input_agent") == "hello"
    
    def test_mixed_steps(self):
        wf = Workflow(name="mixed")
        wf.add_sequential("seq", [agent_a, agent_b])
        wf.add_parallel("par", [agent_a, agent_b])
        
        ctx = wf.run()
        # Sequential agents ran first, then parallel agents
        assert ctx.get_output("agent_a") == "result_a"
        assert ctx.get_output("agent_b") == "result_b"
        assert "mixed_duration" in ctx.metadata.get("timing", {})
    
    @pytest.mark.asyncio
    async def test_async_workflow(self):
        wf = Workflow(name="async_wf")
        wf.add_agent(agent_a)
        
        ctx = await wf.arun()
        assert ctx.get_output("agent_a") == "result_a"


class TestEngine:
    """Tests for Engine."""
    
    def test_engine_execution(self):
        wf = Workflow(name="engine_test")
        wf.add_agent(agent_a)
        
        engine = Engine(wf)
        ctx = engine.run()
        assert ctx.get_output("agent_a") == "result_a"
    
    def test_callbacks(self):
        events = []
        
        wf = Workflow(
            name="callback_test",
            on_start=lambda ctx: events.append("start"),
            on_end=lambda ctx: events.append("end"),
        )
        wf.add_agent(agent_a)
        
        engine = Engine(wf)
        engine.run()
        
        assert events == ["start", "end"]