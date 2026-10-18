from pathlib import Path

import pytest

from agentic_runtime import (AgentRuntime, ApprovalRequired, EventLedger, PolicyEngine,
                             RunState, RunStatus, Tool, ToolCall, ToolExecutionError,
                             ToolRegistry)


@pytest.fixture
def runtime(tmp_path: Path) -> AgentRuntime:
    registry = ToolRegistry()
    registry.register(Tool("add", "Add two numbers",
                           lambda args: args["a"] + args["b"]))
    registry.register(Tool("explode", "Test failure path", lambda _args: 1 / 0))
    return AgentRuntime(
        policy=PolicyEngine(allowed_tools={"add", "explode"},
                            approval_required_tools={"explode"}),
        tools=registry,
        ledger=EventLedger(tmp_path / "events.sqlite3"),
    )


def test_allowlisted_tool_executes_and_is_audited(runtime: AgentRuntime) -> None:
    state = runtime.create_run("add two numbers")
    assert runtime.execute_tool(state, ToolCall("add", {"a": 2, "b": 3})) == 5
    assert state.step_count == 1
    assert [event["event_type"] for event in runtime.ledger.list_for_run(state.run_id)] == [
        "run.created", "run.started", "policy.evaluated", "tool.started", "tool.completed"
    ]


def test_unlisted_tool_is_denied_by_default(runtime: AgentRuntime) -> None:
    state = runtime.create_run("try unknown tool")
    with pytest.raises(PermissionError, match="not allowlisted"):
        runtime.execute_tool(state, ToolCall("delete_everything"))
    assert not any(e["event_type"] == "tool.started"
                   for e in runtime.ledger.list_for_run(state.run_id))


def test_approval_required_tool_never_executes_automatically(runtime: AgentRuntime) -> None:
    state = runtime.create_run("sensitive action")
    with pytest.raises(ApprovalRequired):
        runtime.execute_tool(state, ToolCall("explode"))
    assert state.status == RunStatus.WAITING_APPROVAL
    assert not any(e["event_type"] == "tool.started"
                   for e in runtime.ledger.list_for_run(state.run_id))


def test_tool_failure_is_recorded(runtime: AgentRuntime) -> None:
    runtime.policy.approval_required_tools.clear()
    state = runtime.create_run("test error handling")
    with pytest.raises(ToolExecutionError):
        runtime.execute_tool(state, ToolCall("explode"))
    assert state.status == RunStatus.FAILED
    assert runtime.ledger.list_for_run(state.run_id)[-1]["event_type"] == "tool.failed"


def test_state_machine_rejects_terminal_transition() -> None:
    state = RunState("example")
    state.transition(RunStatus.RUNNING)
    state.transition(RunStatus.SUCCEEDED)
    with pytest.raises(ValueError, match="Invalid run transition"):
        state.transition(RunStatus.RUNNING)
