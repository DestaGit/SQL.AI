# ADR-010: Group-size suppression with a companion count query

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** PRV-12

## Context
Suppressing only columns named like counts was bypassed by renaming and by `SUM(CASE …)` (findings A3, A4).

## Decision
For aggregate queries, run a companion query with the same `FROM`, `WHERE` and `GROUP BY` plus `COUNT(*)` on the same scoped data. Suppress every aggregate in a group under k rows, and any count-like value under k. Refuse grouped queries whose groups can't be matched to output rows.

## Consequences
- Small groups are protected whatever the query looks like.
- One extra query per aggregate request; some queries must add grouping columns to `SELECT`.
- Differential privacy remains a possible future mode for stronger protection against differencing.

## Alternatives considered
| Option | Why not |
|---|---|
| Name heuristics | Bypassed |
| Differential privacy by default | Changes every number; deferred as an option |
