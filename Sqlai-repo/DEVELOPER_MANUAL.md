# SQL.AI — Developer Manual

**Audience:** Engineers building, testing and operating SQL.AI
**Version:** 1.1 (draft)
**Date:** 2026-10-14
**Owner:** [ENGINEERING LEAD NAME]
**Related:** PRD v1.0, Model and Architecture v1.0

> This manual describes the codebase as designed in the architecture document. Paths, commands and endpoints are the agreed conventions; update this manual in the same pull request whenever any of them change.

---

## Table of contents

1. The rules that never bend
2. Getting started
3. Repository layout
4. Configuration
5. Running locally
6. Service guide
7. API reference
8. Working with policies
9. Working with the AI service
10. Adding a warehouse connector
11. Database and migrations
12. Testing
13. Coding standards
14. Security practices for developers
15. CI/CD and releases
16. Observability and debugging
17. Runbooks
18. Troubleshooting
19. Contributing checklist
20. Glossary

---

## 1. The rules that never bend

Read these before writing any code. Code review rejects any change that breaks them.

1. **Every query goes through the Query Gateway.** No service except the executor opens a warehouse connection. New surfaces (API, dashboards, schedules) call the gateway.
2. **Fail closed.** If you can't get a policy decision, a classification or an audit acknowledgement, refuse the request.
3. **No audit, no result.** Results are returned only after the audit service acknowledges the record.
4. **The model sees schema, never rows.** Don't pass query results, sample values or user data into prompts.
5. **The model never executes anything.** It returns text. No tool calls, no execution adapters.
6. **Never log row data or unmasked values.** Not in logs, traces, metrics, error messages or test fixtures copied from customers.
7. **Analyze the AST, not the string.** Regex is a prefilter only.
8. **Policies are code.** Every policy change has tests and a second reviewer.

## 2. Getting started

### 2.1 Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Git | 2.40+ | Source control |
| Docker and Docker Compose | Docker 25+ | Local dependencies |
| Python | 3.12 | Analyzer, AI service, workers |
| uv | latest | Python dependency management |
| Go | 1.22+ | Edge gateway, executor |
| Node.js | 20 LTS | Web app |
| pnpm | 9+ | Web dependencies |
| OPA CLI | 0.68+ | Policy tests |
| make | any | Task runner |
| pre-commit | 3+ | Git hooks |

### 2.2 First-day setup

```bash
git clone git@github.com:[ORG]/sqlai.git
cd sqlai
make bootstrap        # installs toolchains, pre-commit hooks, dependencies
cp .env.example .env  # local settings; never commit .env
make up               # starts Postgres, Redis, Kafka, OPA, MinIO, Vault (dev mode), DuckDB warehouse stub
make seed             # creates a demo tenant, four users, sample data and the default policy bundle
make dev              # runs all services with hot reload
```

Open `http://localhost:5173` and sign in through the local mock IdP as one of the seeded users:

| User | Role | Password (local only) |
|---|---|---|
| ana@demo.local | analyst_eu | `demo` |
| sam@demo.local | sales_manager_na (approver) | `demo` |
| priya@demo.local | hr_partner | `demo` |
| dana@demo.local | data_admin (approver, access approver, policy admin, security) | `demo` |
| sofia@demo.local | security_officer (fallback approver, policy admin, sees all audit; no business data) | `demo` |

### 2.3 Verify your setup

```bash
make test-fast      # unit tests for all services (< 2 min)
make policy-test    # policy golden tests
make check          # lint, type checks, format
```

## 3. Repository layout

```
sqlai/
├── apps/
│   └── web/                    # React + TypeScript workbench, admin console
├── services/
│   ├── edge/                   # Go: API gateway, auth middleware, rate limits
│   ├── query-gateway/          # Python: orchestration pipeline
│   ├── analyzer/               # Python: sqlglot parsing, static rules, rewrite
│   ├── ai/                     # Python: prompt screen, context builder, drafting
│   ├── executor/               # Go: scoped warehouse sessions (only credential holder)
│   ├── output/                 # Python: suppression, caps, approval check
│   ├── approvals/              # Python: requests, routing, tokens
│   ├── audit/                  # Go: ledger, hash chain, checkpoints, SIEM stream
│   ├── catalog/                # Python: schema cache, classifications, semantic layer
│   └── auth/                   # Go: SSO, SCIM, sessions
├── workers/
│   ├── classifier-agent/       # Customer-side classification job
│   └── evidence/               # Evidence pack builder
├── policy/
│   ├── dsl/                    # YAML policy schema and compiler
│   ├── rego/                   # Rego library (sqlai.query, sqlai.approval)
│   ├── bundles/default/        # Default policy bundle
│   └── tests/                  # Golden queries and expected decisions
├── connectors/
│   ├── base/                   # Connector interface
│   ├── snowflake/
│   ├── bigquery/
│   └── duckdb/                 # Local development stub
├── packages/
│   ├── py-common/              # Shared Python: context models, errors, telemetry
│   ├── go-common/              # Shared Go
│   └── ts-sdk/                 # Public TypeScript SDK
├── evals/
│   ├── accuracy/               # NL-to-SQL benchmark
│   ├── refusal/                # Out-of-scope questions
│   └── injection/              # Red-team prompts
├── db/
│   └── migrations/             # SQL migrations (golang-migrate)
├── deploy/
│   ├── helm/                   # Charts per service
│   └── argocd/                 # Environment manifests
├── docs/                       # PRD, architecture, manuals, ADRs
├── demo/
│   └── index.html              # Standalone browser demo (not a security boundary)
├── Makefile
└── docker-compose.yml
```

**Ownership** is defined in `CODEOWNERS`. Changes under `policy/`, `services/executor/`, `services/audit/` and `services/ai/prompts/` need a security team reviewer.

## 4. Configuration

All services read configuration from environment variables, validated at start-up. A missing required value stops the service (fail closed).

| Variable | Service | Example | Notes |
|---|---|---|---|
| `SQLAI_ENV` | all | `local`, `staging`, `prod` | |
| `SQLAI_REGION` | all | `us-east-1` | Data residency pin |
| `DATABASE_URL` | most | `postgres://...` | Metadata store |
| `REDIS_URL` | edge, gateway | `redis://...` | |
| `KAFKA_BROKERS` | audit, notify | `localhost:9092` | |
| `OPA_URL` | gateway, analyzer, ai | `http://localhost:8181` | PDP sidecar |
| `VAULT_ADDR` | executor | `http://localhost:8200` | Only the executor needs it |
| `AUDIT_URL` | gateway, approvals | `http://localhost:7300` | |
| `AUDIT_FAIL_MODE` | gateway | `closed` | Must be `closed` outside `local` |
| `LLM_PROVIDER` | ai | `primary` | Provider key from the model registry |
| `LLM_FALLBACK` | ai | `secondary` | Optional |
| `PROMPT_VERSION` | ai | `nl2sql-v7` | Pinned template version |
| `RESULT_CAP` | output | `500` | Policy may lower it |
| `SMALL_GROUP_K` | output | `5` | Policy may raise it |
| `APPROVAL_TTL_HOURS` | approvals | `72` | |

Secrets (API keys, warehouse credentials, signing keys) come from Vault at runtime. They never appear in `.env` files outside local development.

## 5. Running locally

| Command | What it does |
|---|---|
| `make up` / `make down` | Start or stop local dependencies |
| `make dev` | Run all services with hot reload |
| `make dev SERVICE=analyzer` | Run one service |
| `make seed` | Reset and seed the demo tenant |
| `make logs SERVICE=query-gateway` | Tail a service's logs |
| `make psql` | Open a shell on the metadata database |
| `make policy-build` | Compile YAML policies to Rego bundles |
| `make policy-test` | Run golden policy tests |
| `make eval SUITE=accuracy` | Run an AI evaluation suite (uses a local or stub model) |
| `make test` | Full test suite |
| `make check` | Lint, types, format |

The local warehouse is DuckDB with the same synthetic data as the browser demo, so behavior matches between them.

## 6. Service guide

### 6.1 Query Gateway (`services/query-gateway`)

Pipeline stages live in `pipeline/stages/` and run in this order:

```python
PIPELINE = [
    resolve_identity,       # roles, attributes, policy version
    screen_prompt,          # P-01, AI requests only
    analyze_static,         # P-02..P-05 via analyzer, plus column lineage
    estimate_cost,          # P-14 cost guard
    check_purpose,          # P-15, when lineage shows row-level personal data
    decide_policy,          # PDP decision + obligations
    rewrite,                # row filters and masks (P-06, P-07), aggregate-then-protect
    execute,                # executor call
    post_checks,            # P-08 group sizes, P-09 approval, P-13 budget, P-10 cap
    write_audit,            # synchronous; raises on failure
]
```

Each stage takes and returns a `QueryContext`. A stage that blocks sets `ctx.decision = Decision.BLOCKED` and the runner stops, then still runs `write_audit`.

**Adding a stage:** add it to `PIPELINE`, record a `RuleResult` for every outcome, add unit tests and update the pipeline invariant test.

### 6.2 Analyzer (`services/analyzer`)

- `parse.py`: dialect-aware parse with sqlglot; rejects multiple statements.
- `facts.py`: extracts tables, columns, aggregates and `SELECT *` usage from the AST.
- `rules/`: one module per static rule (`p02_read_only.py`, …). Each exports `evaluate(ast, facts, ctx) -> RuleResult`.
- `rewrite.py`: applies obligations by wrapping tables in filtered, masked subqueries; then re-parses and re-checks.

### 6.3 Executor (`services/executor`)

- Gets short-lived credentials from Vault for the user's scoped role.
- Sets read-only mode, statement timeout and row ceiling.
- Has no public route. Only the gateway can call it (mTLS + network policy).

### 6.4 Audit (`services/audit`)

- `POST /internal/records` appends a record and returns `{seq, hash}` after a replicated commit.
- `POST /internal/verify` recomputes a range of the chain.
- Checkpointer job writes signed Merkle roots to object storage every 5 minutes.

### 6.5 Other services

| Service | Entry point | Notes |
|---|---|---|
| ai | `services/ai/app.py` | See section 9 |
| output | `services/output/app.py` | Count columns detected from AST aggregates, not names |
| approvals | `services/approvals/app.py` | Enforces P-11 in code and in the DB constraint |
| catalog | `services/catalog/app.py` | Schema cache refresh every 15 minutes or on demand |
| auth | `services/auth/cmd/main.go` | SAML/OIDC, SCIM 2.0 endpoints |

### 6.6 Lineage, suppression and budget (since 1.1)

These three mechanisms replaced name-based checks after the 1.0 workbench audit (see `AUDIT.md`). Never reintroduce checks that depend on column names or SQL text.

| Mechanism | Where | Key function | Tests |
|---|---|---|---|
| Column lineage | `services/analyzer/lineage.py` | `analyze(ast, refs) -> [OutputColumn]` with `sources`, `in_aggregate`, `count_like`, `masked_by` | `tests/lineage/` incl. CTE and derived-table aliases |
| Group-size suppression | `services/output/groups.py` | `group_sizes(ast, scoped_tables) -> {group_key: n}` via a companion `COUNT(*)` query | `tests/suppression/` incl. renamed counts and `SUM(CASE…)` |
| Disclosure budget | `services/output/budget.py` | `budget_used(user, domain, window=24h)` | `tests/budget/` incl. paging attempts |

Adding a new aggregate function? Decide whether it's count-like (`COUNT`, `SUM` of constants), value-revealing (`MIN`, `MAX`: never computed on unmasked data), or smoothing (`AVG`, `SUM`: eligible for aggregate-then-protect), and add it to `lineage.AGG_KINDS` with tests.

## 7. API reference

Base URL: `https://api.[DOMAIN]/v1`. All requests need `Authorization: Bearer <token>`. Tokens are scoped (`query:run`, `query:draft`, `audit:read`, `approvals:decide`, `policy:admin`).

### 7.1 Draft SQL from a question

`POST /v1/questions`

```json
{ "question": "Average CSAT by ticket category this quarter" }
```

Response `200`:

```json
{
  "request_id": "req_01J9...",
  "status": "drafted",
  "sql": "SELECT category, ROUND(AVG(csat), 2) AS avg_csat FROM tickets WHERE ...",
  "explanation": "Averages the satisfaction score for rated tickets this quarter, per category.",
  "source": "ai",
  "model": { "prompt_version": "nl2sql-v7" }
}
```

Other statuses: `blocked` (prompt screen), `declined` (out of scope, with `reason`).

### 7.2 Run a query

`POST /v1/queries`

```json
{
  "sql": "SELECT category, ROUND(AVG(csat), 2) AS avg_csat FROM tickets GROUP BY category",
  "approval_id": null,
  "purpose": "quarterly-review"
}
```

Response `200`:

```json
{
  "request_id": "req_01J9...",
  "decision": "modified",
  "rules": [
    { "id": "P-02", "state": "pass",    "detail": "Single SELECT statement." },
    { "id": "P-06", "state": "applied", "detail": "Rows limited to region EU." }
  ],
  "columns": [
    { "name": "category", "type": "text" },
    { "name": "avg_csat", "type": "number" }
  ],
  "rows": [["Billing", 2.73], ["Bug", 3.13]],
  "row_count": 5,
  "masked_columns": [],
  "policy_version": "pv_2026-10-14.3",
  "audit": { "seq": 18234, "hash": "c07e..." }
}
```

Decisions: `allowed`, `modified`, `held` (with `approval_request_id`), `blocked` (with the blocking rule), `error`.

Requests that may return personal data must include `"purpose"`; without it the gate blocks with rule P-15. Responses include `"trust"` (certified metrics, data freshness, masks, suppressed count, rules applied, policy version, audit sequence).

### 7.3 Approvals

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/v1/approvals?status=pending` | `approvals:read` | Requests visible to you |
| POST | `/v1/approvals/{id}/approve` | `approvals:decide` | Body `{ "note": "..." }` (required) |
| POST | `/v1/approvals/{id}/deny` | `approvals:decide` | Body `{ "note": "..." }` (required) |
| POST | `/v1/access-requests` | `access:request` | Body `{ "table": "employees", "reason": "..." }`; approval grants 24-hour redacted access |
| GET | `/v1/notifications` | `notifications:read` | Your notifications |
| GET | `/v1/simulate?user=&table=` | `policy:read` | What a user sees in a table (access simulator) |

### 7.4 Audit

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/v1/audit?from=&to=&user=&outcome=&table=` | `audit:read` | Search records (paginated) |
| POST | `/v1/audit/verify` | `audit:read` | Verify the chain for a range |
| POST | `/v1/audit/exports` | `audit:export` | Start a CSV/JSON export or evidence pack |

### 7.5 Errors

```json
{ "error": { "code": "POLICY_UNAVAILABLE", "message": "The policy service is unavailable, so the query was not run.", "request_id": "req_..." } }
```

| Code | HTTP | Meaning |
|---|---|---|
| `UNAUTHENTICATED` | 401 | Missing or expired token |
| `FORBIDDEN_SCOPE` | 403 | Token lacks the scope |
| `POLICY_BLOCKED` | 200 | Decision is `blocked` (not an HTTP error; the gate worked) |
| `POLICY_UNAVAILABLE` | 503 | Fail-closed: PDP down |
| `AUDIT_UNAVAILABLE` | 503 | Fail-closed: audit down |
| `APPROVAL_INVALID` | 409 | Token used, expired, or SQL/policy changed |
| `WAREHOUSE_TIMEOUT` | 504 | Query exceeded its time limit |
| `RATE_LIMITED` | 429 | Back off and retry later |

### 7.6 SDK example (TypeScript)

```ts
import { SqlAi } from "@sqlai/sdk";

const client = new SqlAi({ token: process.env.SQLAI_TOKEN! });

const draft = await client.questions.draft("Revenue by region in Q3 2026");
if (draft.status !== "drafted") throw new Error(draft.reason);

const run = await client.queries.run({ sql: draft.sql });
if (run.decision === "held") {
  console.log(`Waiting for approval ${run.approvalRequestId}`);
} else if (run.decision === "blocked") {
  console.log(run.rules.find(r => r.state === "blocked")?.detail);
} else {
  console.table(run.rows);
}
```

## 8. Working with policies

### 8.1 Where they live

- Authoring schema: `policy/dsl/schema.json`
- Default bundle: `policy/bundles/default/policy.yaml`
- Rego library: `policy/rego/`
- Golden tests: `policy/tests/*.yaml`

### 8.2 Golden test format

```yaml
- name: analyst cannot read employees
  user: { roles: [analyst_eu], attrs: { region: [EU] } }
  sql: SELECT department, AVG(salary) AS avg_salary FROM employees GROUP BY department
  expect:
    decision: blocked
    rule: P-04

- name: analyst sees EU rows with masked email
  user: { roles: [analyst_eu], attrs: { region: [EU] } }
  sql: SELECT customer_id, email FROM customers WHERE tier = 'Pro'
  expect:
    decision: modified
    obligations:
      row_filters: { customers: "region IN ('EU')" }
      masks: { customers.email: partial_email }
```

### 8.3 Adding a rule (example: block cross-region joins)

1. Add the rule to the DSL schema (`policy/dsl/schema.json`) and compiler.
2. Implement it in Rego (`policy/rego/query/cross_region.rego`) with a new ID (next free `P-xx`).
3. If it needs new facts, extend `services/analyzer/facts.py`.
4. Add golden tests: at least one allow, one block and one edge case.
5. Add the rule to the gate panel copy in `apps/web/src/gate/rules.ts` (plain-language name and messages).
6. Update the PRD's rule table and this manual.
7. Open a PR with a security reviewer.

### 8.4 Adding a masking method

1. Implement it as a SQL expression template per dialect in `services/analyzer/masks/` (e.g. `last4.sql.j2`).
2. Register it in `masks/registry.py` with a label for the UI.
3. Add tests for each dialect, including nulls and non-string input.
4. Add it to the DSL enum.

## 9. Working with the AI service

### 9.1 Layout

```
services/ai/
├── screen/           # P-01 patterns and classifier client
├── context/          # visible-schema builder, retriever
├── prompts/          # versioned templates (nl2sql-v7.md, ...)
├── router.py         # provider selection and fallback
├── validate.py       # JSON contract, parse, dry gate
└── app.py
```

### 9.2 Changing a prompt

1. Copy the current template to a new version (`nl2sql-v8.md`). Never edit a released version.
2. Run all three eval suites: `make eval SUITE=accuracy`, `SUITE=refusal`, `SUITE=injection`.
3. Compare against the current version: `make eval-compare FROM=nl2sql-v7 TO=nl2sql-v8`.
4. The PR must show no regression in refusal or injection results and include the accuracy delta.
5. Roll out behind a feature flag per tenant.

### 9.3 Context builder rules

- Request visible schema from the PDP for the asking user. Never read the catalog directly for prompts.
- Hidden tables and columns must not appear by name, in comments or in examples.
- Column descriptions are customer-authored text: escape them and wrap them in a clearly delimited data section so they can't act as instructions.

### 9.4 Adding a model provider

1. Confirm zero data retention, no-training terms and regional endpoints with legal.
2. Implement the provider adapter in `router.py` (text in, text out, no tools).
3. Register it in the model registry with allowed regions.
4. Run all eval suites against it.

## 10. Adding a warehouse connector

Implement the interface in `connectors/base/connector.py`:

```python
class Connector(Protocol):
    dialect: str                                  # sqlglot dialect name
    def scoped_session(self, identity: ScopedIdentity) -> Session: ...
    def set_read_only(self, session: Session) -> None: ...
    def estimate_cost(self, session: Session, sql: str) -> CostEstimate: ...
    def execute(self, session: Session, sql: str, row_ceiling: int, timeout_s: int) -> ResultStream: ...
    def list_schema(self, session: Session) -> SchemaSnapshot: ...
    def native_policies(self) -> NativePolicySupport: ...   # row access / masking support
```

Checklist:
- [ ] Read-only enforced at the session level, and verified by a test that tries `INSERT` and `DROP`.
- [ ] Timeouts and row ceiling enforced.
- [ ] Cost estimate implemented or explicitly marked unsupported (gateway then uses conservative limits).
- [ ] Contract tests pass: `make connector-test CONNECTOR=<name>`.
- [ ] Dialect added to the eval benchmark.

## 11. Database and migrations

- Migrations live in `db/migrations/` as numbered `up`/`down` SQL files.
- Create one: `make migration NAME=add_purpose_tags`.
- Apply locally: `make migrate`.
- Rules:
  - Every table has `tenant_id` and an RLS policy.
  - Never grant `UPDATE` or `DELETE` on audit tables.
  - Migrations must be backward compatible for one release (expand, then contract).

## 12. Testing

| Layer | Tooling | Location | Runs |
|---|---|---|---|
| Unit | pytest, go test, vitest | next to code | every commit |
| Policy golden tests | OPA + harness | `policy/tests/` | every commit |
| Pipeline invariant | pytest | `services/query-gateway/tests/invariant/` | every commit |
| Connector contract | pytest | `connectors/*/tests/` | every commit touching connectors |
| Integration | docker-compose stack | `tests/integration/` | every PR |
| End-to-end | Playwright | `apps/web/e2e/` | every PR |
| AI evals | eval harness | `evals/` | prompt, model or retriever changes; nightly |
| Security | SAST, dependency, container scans | CI | every PR |
| Load | k6 | `tests/load/` | weekly and before releases |

**The pipeline invariant test** enumerates every route that can reach the executor and asserts that each request produces exactly one audit record with a gate decision. A new route without a gate decision fails the build.

**Test data:** synthetic only. Never copy customer data into fixtures, even masked.

## 13. Coding standards

| Language | Format | Lint | Types |
|---|---|---|---|
| Python | ruff format | ruff | mypy (strict) |
| Go | gofmt | golangci-lint | — |
| TypeScript | prettier | eslint | tsc (strict) |
| SQL | sqlfluff | sqlfluff | — |

Conventions:
- Errors carry a stable `code` and a user-facing `message` that says what happened and what to do next.
- Rule IDs (`P-xx`) are stable and never reused.
- User-facing copy for the gate lives in one place (`apps/web/src/gate/rules.ts`) and in plain language.
- Commit messages follow Conventional Commits (`feat(analyzer): detect cross-region joins`).

## 14. Security practices for developers

- **Logging:** use the shared logger; it drops fields named `rows`, `values`, `result`, `prompt_context`. Don't work around it.
- **Secrets:** never in code, tests or `.env.example`. Use Vault paths.
- **Dependencies:** new dependencies need a reason in the PR and a security reviewer for anything in the executor, audit or auth paths.
- **Input handling:** treat schema descriptions, column comments and glossary text as untrusted. They can contain injection attempts.
- **Threat modeling:** any change to a trust boundary (new external call, new data store, new surface) needs a short threat model in the PR description.
- **Reporting:** report suspected vulnerabilities to [SECURITY CONTACT], not in public issues.

## 15. CI/CD and releases

1. PR opened → lint, types, unit, policy, invariant, integration, e2e, security scans.
2. Required reviews: one code owner; plus security for protected paths.
3. Merge to `main` → images built, signed (Sigstore) and pushed with SBOMs.
4. Argo CD deploys to `staging` automatically.
5. Release to `prod` per region by canary (5% → 25% → 100%) with automatic rollback on SLO burn.
6. Policy bundles and prompt versions are released separately, with their own canary and per-tenant flags.

Versioning: services use semantic versioning; the public API is versioned in the path (`/v1`).

## 16. Observability and debugging

- Every request has a `request_id`, shared by traces, logs and the audit record. Start any investigation from it.
- Dashboards (Grafana): *Gate decisions*, *Gate latency*, *AI drafting*, *Approvals*, *Audit integrity*.
- Find a request's trace: `make trace REQUEST=req_01J9...` (local) or search by `request_id` in the tracing UI.
- To see why a query was blocked, read its `rule_results`; don't reproduce it with customer data.

## 17. Runbooks

| Alert | First steps |
|---|---|
| **Audit chain verification failed** | Critical. Freeze writes for the tenant (`make audit-freeze TENANT=`), page security, compare ledger with WORM checkpoints, do not attempt repair. |
| **Fail-closed: PDP unavailable** | Check OPA sidecar health and bundle loading; roll back the last policy bundle if it coincides. |
| **Fail-closed: audit unavailable** | Check Postgres primary and sync replica; queries stay blocked until resolved. |
| **Spike in injection blocks** | Check for a targeted attack on one tenant; notify the customer's security contact per the incident plan. |
| **AI accuracy drop (nightly eval)** | Compare prompt and model versions; roll back the flag. |
| **Executor errors** | Check warehouse status, credential issuance in Vault and network policy. |

## 18. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `make up` fails on Kafka | Port 9092 in use | Stop the other process or change `KAFKA_PORT` |
| All local queries return `AUDIT_UNAVAILABLE` | Audit service not running | `make dev SERVICE=audit` |
| Policy change has no effect | Bundle not rebuilt | `make policy-build` then restart OPA |
| AI drafts reference hidden tables | Context built from catalog directly | Use the PDP visible-schema call (section 9.3) |
| Golden test passes locally, fails in CI | Stale bundle committed | Rebuild and commit bundle, or let CI build it |

## 19. Contributing checklist

- [ ] The change keeps all eight rules in section 1.
- [ ] Tests added: unit, plus policy golden tests or evals if relevant.
- [ ] No row data, secrets or real customer data in code, tests or logs.
- [ ] User-facing messages are plain and actionable.
- [ ] Docs updated (this manual, PRD tables, API reference) in the same PR.
- [ ] Security reviewer added for protected paths.

## 20. Glossary

| Term | Meaning |
|---|---|
| Query context | The object carried through the gateway pipeline for one request |
| Obligation | Something the PDP requires the gateway to apply (row filter, mask, cap) |
| Golden test | A policy test with a fixed query and expected decision |
| Pipeline invariant | The guarantee that every execution path has a gate decision and audit record |
| Scoped identity | A warehouse identity limited to one user's or role's grants |
| Bundle | A compiled, signed set of policies loaded by the PDP |

---

*Next: User Manual.*
