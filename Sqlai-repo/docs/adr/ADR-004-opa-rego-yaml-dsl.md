# ADR-004: OPA/Rego for decisions, YAML for authoring

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** POL-01

## Context
Policies must be versioned, testable and reviewable, and readable by non-engineers.

## Decision
Admins author policies in a YAML DSL; it compiles to signed Rego bundles evaluated by Open Policy Agent sidecars.

## Consequences
- Readable authoring and a proven engine.
- A compiler to maintain; Cedar remains an option for formal analysis.

## Alternatives considered
| Option | Why not |
|---|---|
| Cedar | Strong option; revisit for analyzability |
| Custom engine | Cost and risk |
