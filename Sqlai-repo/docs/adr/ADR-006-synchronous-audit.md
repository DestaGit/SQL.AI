# ADR-006: Write the audit record before returning results

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** AUD-01–AUD-03

## Context
Evidence with gaps is weak evidence.

## Decision
The gateway returns results only after the audit service acknowledges a replicated write. If the write fails, the result is discarded.

## Consequences
- Complete evidence by construction.
- Audit store availability directly affects query availability.

## Alternatives considered
| Option | Why not |
|---|---|
| Asynchronous logging | Gaps under failure |
