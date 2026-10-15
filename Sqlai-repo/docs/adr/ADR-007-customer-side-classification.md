# ADR-007: Run classification inside the customer's environment

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** PRV-01

## Context
Detecting personal data requires sampling values.

## Decision
The classification agent runs in the customer's warehouse compute or a customer-hosted agent; only tags and confidence leave.

## Consequences
- Sampled values never leave the customer.
- Deployment is more involved for customers.

## Alternatives considered
| Option | Why not |
|---|---|
| Vendor-side sampling | Data leaves the customer |
