"""Fail-closed tool authorization policy."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_approval: bool = False


@dataclass(slots=True)
class PolicyEngine:
    """Allow only explicitly configured tools; approval-required tools never auto-run."""

    allowed_tools: set[str] = field(default_factory=set)
    approval_required_tools: set[str] = field(default_factory=set)

    def evaluate(self, tool_name: str) -> PolicyDecision:
        if tool_name not in self.allowed_tools:
            return PolicyDecision(False, f"Tool '{tool_name}' is not allowlisted.")
        if tool_name in self.approval_required_tools:
            return PolicyDecision(False, f"Tool '{tool_name}' requires explicit approval.",
                                  requires_approval=True)
        return PolicyDecision(True, "Tool is allowlisted and does not require approval.")
