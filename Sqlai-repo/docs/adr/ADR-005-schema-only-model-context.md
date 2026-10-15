# ADR-005: The model sees schema only and has no tools

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** AI-02, AI-04

## Context
Giving a language model data rows or the ability to execute SQL would create a path around the gate.

## Decision
Model context contains only the asking user's visible schema, glossary and certified metric definitions. The model returns text; it never executes anything.

## Consequences
- Prompt injection can't extract rows through the model.
- Drafts may be less accurate on data-dependent questions; users review before running.

## Alternatives considered
| Option | Why not |
|---|---|
| Agentic model with an execution tool | Bypass risk |
