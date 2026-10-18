# Security model

This is an early development scaffold, not a production security certification.

- Default deny: only explicitly allowlisted tools may execute.
- No implicit approval: approval-required tools stop before handler invocation.
- Auditability: policy decisions and tool outcomes are appended to a local SQLite ledger.
- Bounded execution: every run has a maximum tool-step count.
- Secrets: use environment variables or a dedicated secret manager; never commit environment files.
- Isolation: tool handlers execute in-process in this initial version. Do not register untrusted code or expose this runtime to untrusted callers until sandboxing, authentication, authorization, and resource limits are implemented.
- Approval gap: this version records that approval is required but does not implement approval grants or resumption. Do not treat approval as complete.
