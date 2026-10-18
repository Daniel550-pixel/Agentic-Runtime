"""Typed state objects shared by runtime components."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ToolCall:
    tool_name: str
    arguments: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class RunState:
    input_text: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    status: RunStatus = RunStatus.PENDING
    step_count: int = 0
    max_steps: int = 20
    result: object | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def transition(self, new_status: RunStatus) -> None:
        allowed = {
            RunStatus.PENDING: {RunStatus.RUNNING, RunStatus.CANCELLED},
            RunStatus.RUNNING: {RunStatus.WAITING_APPROVAL, RunStatus.SUCCEEDED,
                                RunStatus.FAILED, RunStatus.CANCELLED},
            RunStatus.WAITING_APPROVAL: {RunStatus.RUNNING, RunStatus.CANCELLED,
                                         RunStatus.FAILED},
            RunStatus.SUCCEEDED: set(),
            RunStatus.FAILED: set(),
            RunStatus.CANCELLED: set(),
        }
        if new_status not in allowed[self.status]:
            raise ValueError(f"Invalid run transition: {self.status} -> {new_status}")
        self.status = new_status
        self.updated_at = utc_now()
