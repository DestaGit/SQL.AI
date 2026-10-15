# ADR-003: Enforce on the SQL, in the data layer and on the output

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** GW-07, PRV-03–PRV-05

## Context
A single enforcement layer is a single point of failure.

## Decision
Apply static checks to the SQL, row filters and masks in the data layer (rewrite plus warehouse-native policies where available), and post-checks on results.

## Consequences
- A failure in one layer doesn't leak data.
- More moving parts to test; each layer has its own test suite.

## Alternatives considered
| Option | Why not |
|---|---|
| Warehouse-native policies only | Not available on every warehouse; no output checks |
