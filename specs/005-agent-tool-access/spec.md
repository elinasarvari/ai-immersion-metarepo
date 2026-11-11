# Feature Specification: Agent Tool Access (retired)

**Feature Branch**: `feature/005-agent-tool-access`

**Created**: 2026-11-09

**Status**: Retired (2026-11-11)

## Why it was retired

This feature provided the tools AI agents used to read case data, record findings, draft
notices and check simulated verification sources. The MVP has no AI agents, so nothing calls
these tools.

## What replaced it

IDs are not reused. References elsewhere point to the new IDs.

| Old ID | Now | Topic |
|---|---|---|
| FR-005-01 to FR-005-06, FR-005-09, FR-005-11 | Removed | The 11 agent tools and their rules |
| FR-005-07 | Removed | Simulated response times, failures and timeouts |
| FR-005-08 | Removed | Tool call audit |
| FR-005-10 | Removed | Case-scoped system credential on every tool call |
| FR-005-12 | FR-002-22 | Identity and income answers from the synthetic data set, as an ordinary lookup |
| SC-005-01 to SC-005-04 | Removed | Tool access, audit and simulation targets |

The `tool_calls` and `agent_runs` collections in the baseline migration stay as they are, unused.
FR-000-22 (system credential for agent steps) is not exercised in the MVP.
