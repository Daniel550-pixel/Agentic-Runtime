"""Minimal governed execution loop; planning and model adapters are separate layers."""

from dataclasses import dataclass, field
from typing import Any

from .ledger import EventLedger
from .models import RunState, RunStatus, ToolCall
from .policy import PolicyEngine
from .tools import ToolRegistry


class ApprovalRequired(PermissionError):
    """Raised when a tool needs a human decision before execution."""


class ToolExecutionError(RuntimeError):
    """Raised when a registered tool fails during execution."""


@dataclass(slots=True)
class AgentRuntime:
    policy: PolicyEngine
    tools: ToolRegistry
    ledger: EventLedger
    max_steps: int = 20
    _runs: dict[str, RunState] = field(default_factory=dict)

    def create_run(self, input_text: str) -> RunState:
        state = RunState(input_text=input_text, max_steps=self.max_steps)
        self._runs[state.run_id] = state
        self.ledger.append(state.run_id, "run.created",
                           {"input_text": input_text, "max_steps": state.max_steps})
        return state

    def execute_tool(self, state: RunState, call: ToolCall) -> object:
        if state.status == RunStatus.PENDING:
            state.transition(RunStatus.RUNNING)
            self.ledger.append(state.run_id, "run.started", {})
        if state.status != RunStatus.RUNNING:
            raise RuntimeError(f"Cannot execute a tool while run is {state.status}.")
        if state.step_count >= state.max_steps:
            state.error = "Maximum step count exceeded."
            state.transition(RunStatus.FAILED)
            self.ledger.append(state.run_id, "run.failed", {"error": state.error})
            raise ToolExecutionError(state.error)

        decision = self.policy.evaluate(call.tool_name)
        self.ledger.append(state.run_id, "policy.evaluated",
                           {"tool_name": call.tool_name, "allowed": decision.allowed,
                            "reason": decision.reason,
                            "requires_approval": decision.requires_approval})
        if decision.requires_approval:
            state.transition(RunStatus.WAITING_APPROVAL)
            self.ledger.append(state.run_id, "approval.required", {"tool_name": call.tool_name})
            raise ApprovalRequired(decision.reason)
        if not decision.allowed:
            raise PermissionError(decision.reason)

        tool = self.tools.get(call.tool_name)
        state.step_count += 1
        self.ledger.append(state.run_id, "tool.started",
                           {"tool_name": call.tool_name, "step": state.step_count})
        try:
            result = tool.handler(call.arguments)
        except Exception as exc:
            state.error = f"{type(exc).__name__}: {exc}"
            state.transition(RunStatus.FAILED)
            self.ledger.append(state.run_id, "tool.failed",
                               {"tool_name": call.tool_name, "error": state.error})
            raise ToolExecutionError(state.error) from exc

        state.result = result
        self.ledger.append(state.run_id, "tool.completed",
                           {"tool_name": call.tool_name, "result_type": type(result).__name__})
        return result

    def complete_run(self, state: RunState, result: Any = None) -> RunState:
        if state.status != RunStatus.RUNNING:
            raise RuntimeError(f"Cannot complete a run while it is {state.status}.")
        if result is not None:
            state.result = result
        state.transition(RunStatus.SUCCEEDED)
        self.ledger.append(state.run_id, "run.succeeded", {"steps": state.step_count})
        return state
