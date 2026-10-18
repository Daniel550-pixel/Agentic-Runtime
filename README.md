# Agentic Runtime

A production-oriented foundation for policy-governed AI agents. The runtime separates proposed actions from authorized execution: models may propose, but the runtime policy gate decides.

## Current capabilities

- Explicit run lifecycle state machine with terminal-state protection.
- Fail-closed tool authorization: tools must be explicitly allowlisted.
- Approval-required actions stop before their handler can execute.
- SQLite event ledger for run, policy, and tool lifecycle events.
- Typed tool registry and bounded tool-step count.
- Pytest test suite and GitHub Actions CI on Python 3.11–3.13.

## Status

This is the first development milestone, not yet a complete production runtime. It does not yet include an LLM planner/provider adapter, durable approval grants and resumption, external sandboxing, long-term memory, an HTTP API, or production observability. See docs/ARCHITECTURE.md and docs/SECURITY.md.

## Quick start

Requires Python 3.11 or newer.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check .
pytest
```

## Minimal usage

```python
from agentic_runtime import AgentRuntime, EventLedger, PolicyEngine, Tool, ToolCall, ToolRegistry

tools = ToolRegistry()
tools.register(Tool("add", "Add two numbers", lambda args: args["a"] + args["b"]))

with EventLedger(":memory:") as ledger:
    runtime = AgentRuntime(
        policy=PolicyEngine(allowed_tools={"add"}),
        tools=tools,
        ledger=ledger,
    )
    run = runtime.create_run("Add 2 and 3")
    result = runtime.execute_tool(run, ToolCall("add", {"a": 2, "b": 3}))
    runtime.complete_run(run, result)
    print(run.status, run.result)
```

Do not expose this initial implementation to untrusted callers or register untrusted code. The first release is a foundation for development and review, not a security certification.
