# ADR-009: Classify output columns by lineage

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** PRV-09

## Context
The 1.0 workbench audit showed that checks based on column names were bypassed by aliases (`phone AS contact`), by `GROUP BY` on personal data and by renaming through `WITH` queries (findings A1, A8, A13).

## Decision
For every output column, record its source columns (resolving aliases through CTEs and derived tables) and whether each sits inside an aggregate. Personal-data, masking-label and approval decisions use this lineage.

## Consequences
- Renaming or regrouping no longer changes how personal data is treated.
- Every new SQL feature must be covered by lineage tests.

## Alternatives considered
| Option | Why not |
|---|---|
| Column-name matching | Bypassed in the audit |
