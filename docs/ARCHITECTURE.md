# Architecture

## Runtime boundary

The initial vertical slice separates four responsibilities:

- Run state: explicit lifecycle transitions and a bounded step counter.
- Policy engine: fail-closed tool allowlisting; sensitive tools can require approval.
- Tool registry: named handlers with a stable invocation contract.
- Event ledger: SQLite-backed append-only audit events.

AgentRuntime coordinates these components. It does not call an LLM or infer a plan yet. Model adapters and planners must produce proposed tool calls; the runtime remains the authority that decides whether a call may execute.

## Invariants

1. A tool is never invoked unless its name is allowlisted.
2. A tool marked as approval-required is never invoked automatically.
3. Policy decisions and tool lifecycle events are written to the ledger.
4. Run transitions are explicit; terminal states cannot be reopened.
5. A run has a configurable maximum number of tool steps.

## Planned components

1. Durable approval records bound to the exact action and arguments.
2. Planner interface and provider adapters.
3. Memory interfaces with scoped access and provenance.
4. Evaluation harness and deterministic test scenarios.
5. Metrics, structured logging, tracing, and API service.
