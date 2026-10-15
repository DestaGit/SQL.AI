# ADR-002: Analyze SQL as an AST, not text

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Engineering lead, Security lead
**Related requirements:** GW-02, GW-03

## Context
Text matching on SQL is easy to evade with formatting, comments, aliases and nesting.

## Decision
Parse every query into an abstract syntax tree (sqlglot in production) and run static rules on it. Regular expressions are allowed only as a fast prefilter.

## Consequences
- Rules are robust to formatting and nesting.
- Multi-dialect support depends on the parser's coverage; unsupported syntax is refused.

## Alternatives considered
| Option | Why not |
|---|---|
| Regex only | Evasion |
| Warehouse EXPLAIN only | Dialect gaps; no column-level facts |
