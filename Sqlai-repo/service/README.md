# SQL.AI — Phase 1 service

The governed query gateway: every query passes the policy gate before and after it runs, decisions use **column lineage** rather than column names, and nothing is returned unless the audit record was committed.

> **North star:** No query runs, and no data leaves, unless policy says it can.

| | |
|---|---|
| **Version** | 0.2.0 (Phase 1 + web app) |
| **Status** | Runs locally against a fictional DuckDB warehouse; web workbench included; 95 tests passing |
| **Design docs** | [PRD](../PRD.md), [ARCHITECTURE](../ARCHITECTURE.md), [DEVELOPER_MANUAL](../DEVELOPER_MANUAL.md), [AUDIT](../AUDIT.md) |

## Quick start

```bash
make bootstrap   # virtualenv + dependencies
make test        # 95 tests: rules, lineage regressions, audit, executor, API, web app, invariants
make dev         # seeds fictional data and serves http://127.0.0.1:8000
```

Open **http://127.0.0.1:8000** for the workbench: pick a local account, run an example, and watch the server's policy gate decide. API docs are at `/docs`.

Or call the API directly as Ana, the EU analyst:

```bash
curl -s -X POST localhost:8000/v1/queries \
  -H 'Authorization: Bearer dev-ana' -H 'Content-Type: application/json' \
  -d '{"sql": "SELECT region, ROUND(SUM(amount), 2) AS revenue FROM orders GROUP BY region"}'
```

You get only EU rows (`P-06 applied`), every rule's result, a trust summary and the audit sequence number.

**Local tokens** (development identity provider, `SQLAI_ENV=local` only): `dev-ana`, `dev-sam`, `dev-priya`, `dev-dana`, `dev-sofia`. Roles and permissions are in `policy/default.yaml`.

Requires Python 3.11+. Docker: `make docker && docker run -p 8000:8000 sqlai:phase1`.

## What Phase 1 includes

| Area | Status | Where | Requirements |
|---|---|---|---|
| Single gateway pipeline, fail closed | Done | `sqlai/gateway.py` | GW-01, GW-06, §9.3 |
| AST static rules: read-only, no system access, table access, no `SELECT *` on sensitive tables | Done | `sqlai/analyzer.py` | GW-02–GW-04, GW-10, P-02–P-05 |
| Column lineage through aliases, CTEs, derived tables and scalar sub-queries | Done | `analyzer.analyze` | PRV-09 |
| Cost guard | Done | `analyzer.estimate_cost` | GW-09, P-14 |
| Row filters and masks by rewriting each table to a scoped sub-query | Done | `analyzer.rewrite` | GW-07, PRV-03, PRV-04 |
| Aggregate-then-protect for rounded numeric masks | Done | `analyzer`, `gateway` | PRV-11 |
| Group-size suppression with a companion count query | Done | `analyzer.group_size_query`, `gateway` | PRV-12, P-08 |
| Purpose required; high-risk purposes held | Done | `gateway` | PRV-08, P-15 |
| Approval *decision* (held + eligible approvers + fallback) | Done | `gateway` | P-09, APR-01, APR-10 |
| Personal-data disclosure budget | Done | `gateway`, `audit.budget_*` | PRV-10, P-13 |
| Executor: the only warehouse session holder; HMAC gate tickets bound to the exact SQL; read-only; external access, extensions and configuration locked; timeouts; row ceiling | Done | `sqlai/executor.py` | ADR-001, IAM-06, GW-05 |
| Append-only, hash-chained audit with synchronous writes, redaction and signed Merkle checkpoints | Done | `sqlai/audit.py` | AUD-01–AUD-04, AUD-09, ADR-006 |
| Policy bundle as code with validation and golden tests | Done | `policy/`, `sqlai/policy.py` | POL-01, POL-03, POL-06 |
| Development identity provider; OIDC interface | Dev only | `sqlai/identity.py` | IAM-01 (interface) |
| API: queries, catalog, audit, verify, checkpoint, `/v1/me` | Done | `sqlai/api.py` | Subset of `openapi.yaml` |
| Web workbench served by the API: sign-in, gate panel, results, trust card, catalog, audit with verify and checkpoint | Done | `sqlai/web/` | WB-01–WB-05, WB-09 (no AI drafting yet) |
| Security headers: strict CSP (no inline or third-party scripts), no framing, nosniff, no-store on API, HSTS outside local | Done | `api.security_headers` | SEC-01 |

**Not in Phase 1** (next): OIDC/SAML and SCIM integration, the approval *workflow* (requests, decisions, single-use tokens), access requests, notifications, SIEM streaming, AI drafting, Snowflake connector, OPA/Rego compilation of the policy bundle, KMS-signed checkpoints in object storage.

## How a query flows

```
identity → P-02..P-05 static rules → lineage → P-14 cost → P-15 purpose
→ rewrite (P-06 rows, P-07 masks) → execute with a gate ticket
→ P-08 group sizes → P-09 approval / P-13 budget → P-10 cap → audit (sync) → response
```

If the audit write fails, the response is `503 AUDIT_UNAVAILABLE` and no rows are returned.

## Layout

```
sqlai/
  analyzer.py   static rules, lineage, cost, rewrite, group-size query
  gateway.py    the pipeline and decisions
  executor.py   read-only warehouse sessions, gate tickets
  audit.py      ledger, budget, checkpoints
  policy.py     bundle loading, validation, effective permissions
  identity.py   identity providers
  api.py        FastAPI app
  redact.py     personal-data redaction for logs
  demo_data.py  fictional warehouse seeding
  web/          the workbench: index.html, app.js, app.css (no inline code)
policy/
  default.yaml  roles, catalog classifications, masks, settings
  golden.yaml   policy golden tests
tests/          95 tests
```

Design decisions: [docs/adr](../docs/adr/README.md), including ADR-012 (modular monolith).

## Tests

| Suite | What it proves |
|---|---|
| `test_golden.py` | 20 policy cases from `policy/golden.yaml`, including the audit findings |
| `test_bypass_regressions.py` | Every finding A1–A13 from the workbench audit stays fixed, plus scalar sub-query, window-function, string-aggregation, row-filter-escape and inner-aggregation bypass attempts |
| `test_static_rules.py` | 22 blocked statements across P-02–P-05, plus allowed edge cases |
| `test_audit_and_executor.py` | Append-only triggers, tamper detection, checkpoint signatures, redaction, budget window; executor rejects forged or reused tickets, writes, external file access and configuration changes |
| `test_api_and_invariants.py` | Authentication, audit scoping, fail-closed responses, a reviewed route inventory, every execution has a gate ticket whose request is in the audit log, the web app's security headers, `/v1/me`, local-only dev sign-in and OIDC fail-closed in production |

## Security notes

- The web app is served with a strict content-security policy: scripts load only from the service itself, nothing can frame it, and API responses aren't cached.
- `SQLAI_ENV` other than `local` requires `SQLAI_AUDIT_KEY` (32+ characters) and refuses the development identity provider.
- Masked values are what the query sees: filtering on a masked column filters on the masked value, so it can't be used to probe real values.
- Window aggregates, `MIN`/`MAX` and string aggregation over personal data are treated as row-level.
- Aggregation inside CTEs or derived tables is refused until group sizes can be checked there.

Report vulnerabilities as described in [SECURITY.md](../SECURITY.md).
