# ADR-008: Crypto-shredding for erasure in audit data

**Status:** Proposed
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** PRV-06, AUD-03

## Context
Erasure requests conflict with an immutable, hash-chained audit log.

## Decision
Store personal values in audit records only when necessary, encrypted with a per-subject key; erasure deletes the key. Questions and SQL are redacted of personal-data patterns before writing (AUD-09).

## Consequences
- Erasure without breaking the chain.
- Key management per subject.

## Alternatives considered
| Option | Why not |
|---|---|
| Redaction in place | Breaks the chain |
