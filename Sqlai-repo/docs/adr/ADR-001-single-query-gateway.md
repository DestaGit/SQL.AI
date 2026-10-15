# ADR-001: Single Query Gateway for all surfaces

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** GW-01

## Context
SQL.AI will have several ways to run queries: the editor, AI drafting, the API, dashboards and schedules. If each surface checked policy on its own, a new surface could ship without checks, and rules would drift between surfaces.

## Decision
All query execution goes through one Query Gateway. Only the executor service, called only by the gateway, holds warehouse credentials.

## Consequences
- One place to enforce, test and audit policy.
- New surfaces get governance automatically.
- The gateway is a critical path: it must be highly available and fast (p95 gate decision under 300 ms).
- A pipeline invariant test must fail the build if any route reaches the executor without a gate decision.

## Alternatives considered
| Option | Why not |
|---|---|
| Checks in each surface | Bypass risk; rules drift |
| Rely only on warehouse permissions | No approvals, budget, purpose or cross-warehouse evidence |
