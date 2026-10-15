# Architecture decision records

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-single-query-gateway.md) | Single Query Gateway for all surfaces | Accepted |
| [ADR-002](ADR-002-ast-based-analysis.md) | Analyze SQL as an AST, not text | Accepted |
| [ADR-003](ADR-003-defense-in-depth.md) | Enforce on the SQL, in the data layer and on the output | Accepted |
| [ADR-004](ADR-004-opa-rego-yaml-dsl.md) | OPA/Rego for decisions, YAML for authoring | Accepted |
| [ADR-005](ADR-005-schema-only-model-context.md) | The model sees schema only and has no tools | Accepted |
| [ADR-006](ADR-006-synchronous-audit.md) | Write the audit record before returning results | Accepted |
| [ADR-007](ADR-007-customer-side-classification.md) | Run classification inside the customer's environment | Accepted |
| [ADR-008](ADR-008-crypto-shredding.md) | Crypto-shredding for erasure in audit data | Proposed |
| [ADR-009](ADR-009-lineage-based-classification.md) | Classify output columns by lineage | Accepted |
| [ADR-010](ADR-010-group-size-suppression.md) | Group-size suppression with a companion count query | Accepted |
| [ADR-011](ADR-011-disclosure-budget.md) | Rolling per-user disclosure budget | Accepted |
| [ADR-012](ADR-012-modular-monolith-first.md) | Ship Phase 1 as a modular monolith | Accepted |

New ADRs use the template in [DOCUMENTATION_GUIDELINES.md §15.1](../../DOCUMENTATION_GUIDELINES.md#151-architecture-decision-record).
