# Changelog

All notable changes to SQL.AI. Format follows [DOCUMENTATION_GUIDELINES.md §12.6](DOCUMENTATION_GUIDELINES.md#126-release-notes). Versions follow semantic versioning.

## Service 0.2.0 — 2026-10-15

### New
- **Web workbench served by the service** at `/`: local sign-in, SQL editor with role-aware examples and purpose, the server's policy gate decisions rule by rule, results with masked, rounded and suppressed values labelled, bar charts, the trust card, held and blocked explanations, data catalog, and the audit log with verify and checkpoint for security and data admins. Every decision is made on the server.
- `GET /v1/me` and, in local development only, `GET /v1/dev/users`.
- Security headers on every response: strict content-security policy with no inline or third-party scripts, no framing, `nosniff`, no referrer, `no-store` on the API, HSTS outside local.
- 6 new tests (95 total), including one that every rule result carries its name.

### Fixed
- Flaky checkpoint test; static rule results now include rule names in API responses.

### Changed
- Policy roles carry display titles.

## Service 0.1.0 and demo 1.1.1 — 2026-10-15

### New
- **SQL.AI service 0.1.0 (Phase 1)**: the server-side gateway in Python. sqlglot AST rules, column lineage, cost guard, rewrite-based row filters and masks, group-size suppression, purpose, approval decisions with fallback approver, disclosure budget, read-only DuckDB executor with HMAC gate tickets, append-only hash-chained audit with signed checkpoints, FastAPI, 89 tests, CI workflow and Dockerfile. See the service README.
- ADR-012: Phase 1 ships as a modular monolith.

### Fixed
- A15 in the demo: `MIN`/`MAX` and other value-revealing aggregates over personal data are row-level (purpose and approval apply).
- A14 and A16 in the service (see AUDIT.md §7). A16 remains open in the demo, planned for 1.2.

## 1.1.0 — 2026-10-14

### New
- **Column lineage** decides personal-data, masking and approval checks, through aliases, expressions, CTEs and derived tables (PRV-09).
- **Group-size suppression**: every aggregate from a group under k rows is suppressed, however it's named or computed (P-08, PRV-12).
- **Personal-data disclosure budget**: 60 rows per data domain per 24 hours before approval is needed (P-13, PRV-10).
- **Cost guard**: unconstrained joins and queries over the work limit are refused before running (P-14, GW-09).
- **Purpose required** for queries returning personal data row by row; marketing use always needs approval (P-15, PRV-08).
- **Aggregate-then-protect**: averages and sums of rounded numeric columns use true values, then round (PRV-11).
- **Request 24-hour access** to a table from a block message; approved grants keep personal columns redacted (IAM-10).
- **Approver preview**: 3 rows as the requester would see them (APR-09).
- **Fallback approver**: the security officer decides when no other domain approver exists (APR-10).
- **Trust card** under each result: certified metric, data freshness, scope, masks, suppression, rules, policy, purpose, audit entry (WB-09).
- **Certified metrics** in the catalog and in drafting.
- **Follow-up questions** in the built-in engine and Claude prompt (WB-10).
- **Saved query schedules** (daily or weekly), re-checked every run (WB-11).
- **Notifications** with an unread bell (WB-12).
- **Access simulator** on the Policies tab (WB-13).
- **Security alerts** for repeated blocks, repeated injection attempts, high budget use and chain failures (AUD-10).
- **Evidence pack** export (Markdown) from the Audit log tab (AUD-07).
- Policy settings for disclosure budget and cost limit; golden tests extended to 12.

### Changed
- Approval rule P-09 now applies to any result showing personal data row by row, including through `GROUP BY`.
- Same block message for unknown and ungranted tables (GW-10).
- Prompt-injection filter normalizes spacing, symbols and look-alike digits.
- Publishing a policy version cancels approvals made under the previous version (APR-11).
- `?` parameters are blocked by P-03.
- Grouped queries must include every `GROUP BY` column in `SELECT` so group sizes can be checked.

### Fixed
- A1–A11 and A13 from the workbench audit (see [AUDIT.md](AUDIT.md)).
- Audit queue stalled if a write completed after sign-out.

### Security
- Personal data (emails, phone numbers, ID numbers) is redacted from questions and SQL before it's written to the audit log (AUD-09).

### Breaking
- Queries returning personal data row by row are blocked until a purpose is chosen.
- Some grouped queries that ran in 1.0.0 are now refused until the grouping columns are added to `SELECT`.

## 1.0.0 — 2026-10-14

### New
- Standalone single-file workbench with five demo accounts, 12 policy rules, offline and AI drafting, approvals, two-person policy changes, hash-chained audit log and governed export.
- PRD, architecture, developer manual, user manual, README, documentation guidelines and investor pitch.
