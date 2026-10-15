# ADR-012: Ship Phase 1 as a modular monolith

**Status:** Accepted
**Date:** 2026-10-15
**Deciders:** Engineering lead, Security lead
**Related requirements:** GW-01, ADR-001

## Context
The architecture describes separate services (gateway, analyzer, executor, output, audit). Building and operating them separately before the first design partner adds network hops, deployment work and new trust boundaries without improving the controls.

## Decision
Phase 1 ships as one Python package whose modules keep the service boundaries: `analyzer`, `gateway`, `executor`, `audit`, `policy`, `identity`, `api`. The executor accepts only HMAC-signed gate tickets minted by the gateway for the exact SQL, so the one-gate guarantee holds inside the process. The YAML policy bundle is evaluated in-process; compiling it to Rego for OPA follows when services split.

## Consequences
- Faster delivery and simpler testing; the full pipeline runs in one test process.
- Module boundaries must stay clean so services can be split later without rewriting logic.
- A compromise of the process compromises all modules; production hardening (separate executor process and credentials, network policy) is required before regulated customers.

## Alternatives considered
| Option | Why not |
|---|---|
| Microservices from day one | Operational cost before product validation |
| Single module without boundaries | Hard to split later; weakens the executor guarantee |
