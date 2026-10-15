# ADR-011: Rolling per-user disclosure budget

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** PRV-10

## Context
A per-query approval threshold was bypassed by paging through results in small batches (finding A2).

## Decision
Track personal-data rows returned per user and data domain over a rolling 24 hours. A result that would exceed the budget (default 60) is held for approval. Approved runs count but aren't held.

## Consequences
- Paging no longer avoids approval.
- Users with legitimate high-volume needs request approval or a policy change.

## Alternatives considered
| Option | Why not |
|---|---|
| Per-query thresholds only | Bypassed |
