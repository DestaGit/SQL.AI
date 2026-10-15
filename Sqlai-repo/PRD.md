# SQL.AI — Product Requirements Document

**Product:** SQL.AI, the governed analytics workbench
**Document type:** Product Requirements Document (PRD)
**Version:** 1.1 (draft for review)
**Status:** Draft
**Date:** 2026-10-14
**Owner:** [Desta Ensermu]
**Reviewers:** Engineering lead, Security lead, Data platform lead, Legal and compliance, Design

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-07 |  [Desta Ensermu] | Brainstorm, mind map and security-first reprioritization |
| 0.2 | 2026-10-12 |  [Desta Ensermu]| Phased build plan |
| 1.0 | 2026-10-14 |  [Desta Ensermu]| First full PRD |
| 1.1 | 2026-10-14 |  [Desta Ensermu]| Workbench audit fixes: column lineage, group-size suppression, disclosure budget, cost guard, purpose, export control; new rules P-12–P-15; new requirements for access requests, trust card, notifications, schedules, alerts |

---

## Table of contents

1. Summary
2. Problem statement
3. Vision and principles
4. Goals, non-goals and success metrics
5. Users and personas
6. Scope by release
7. User journeys
8. Functional requirements
9. Policy engine specification
10. AI requirements
11. Non-functional requirements
12. Compliance requirements
13. Data and integration requirements
14. UX and accessibility requirements
15. Analytics and telemetry
16. Release criteria
17. Dependencies
18. Risks and mitigations
19. Open questions
20. Glossary
21. Appendix: requirement traceability

---

## 1. Summary

SQL.AI lets employees ask questions of company data in plain English and get trustworthy answers, without giving the AI or the user more access than policy allows.

A question is turned into SQL by a language model that sees only the schema the user's role permits. Every query, whether AI-drafted or hand-written, passes a single **policy gate** before it runs. The gate enforces identity, access, privacy, cost and compliance rules. Sensitive requests are held for human approval. Every step is written to a tamper-evident audit log.

**North star:** No query runs, and no data leaves, unless policy says it can.

The product is security-first. Controls ship before analytics features, and no analytics feature may bypass the gate.

## 2. Problem statement

| Who | Problem today | Consequence |
|---|---|---|
| Business users and analysts | New questions become tickets for the data team | Answers take days; decisions are made without data |
| Data teams | Repeatedly write similar ad-hoc queries | Engineering time spent on low-value work; inconsistent metric logic |
| Security teams | Most text-to-SQL tools connect with a broad service account | The AI and its users can read data they shouldn't; leakage risk |
| Compliance and audit | Little record of who queried what and who allowed it | Audit evidence takes weeks to assemble, or doesn't exist |
| Leadership | Different teams report different numbers for the same metric | Low trust in data |

The core gap: **self-serve speed and enterprise control are treated as a trade-off.** SQL.AI's job is to deliver both.

## 3. Vision and principles

**Vision:** Every employee can be a confident data user, and the data team never has to worry about what they can reach.

**Product principles (in priority order):**

1. **Deny by default.** Anything not explicitly allowed is blocked.
2. **Least privilege.** The AI never sees more than the person asking. It inherits their permissions and nothing more.
3. **Data minimization.** The model receives schema and metadata, not row data.
4. **One gate.** AI-drafted and hand-written SQL go through the same policy enforcement point. There is no side door.
5. **Explainable.** Every answer shows its SQL, the tables touched, the rules applied and a plain-English explanation.
6. **Provable.** Every decision is logged immutably and can be exported as evidence.
7. **Human in the loop where it matters.** Routine queries flow freely; sensitive ones need a second person.
8. **Warehouse-native.** Data stays in the customer's warehouse. SQL.AI doesn't copy it out.

## 4. Goals, non-goals and success metrics

### 4.1 Goals

- G1. Let authorized users answer data questions in minutes without a data-team ticket.
- G2. Ensure that no query exceeds the asking user's permissions, enforced at every layer of the gate.
- G3. Give security and compliance teams complete, verifiable evidence of data access.
- G4. Make AI-generated SQL accurate enough that users trust it, and transparent enough that they can check it.
- G5. Reduce repetitive ad-hoc query work for data teams.

### 4.2 Non-goals (v1)

- Writing to warehouses (inserts, updates, deletes, schema changes). SQL.AI is read-only.
- Replacing BI tools for pixel-perfect reporting.
- ETL, data pipelines or data modeling.
- Training or fine-tuning models on customer data.
- Consumer or individual-user plans.
- On-device or offline use.

### 4.3 Success metrics

Targets are proposals for the first 12 months after general availability and will be confirmed with design partners.

| Area | Metric | Target |
|---|---|---|
| Security | Policy violations leaked (data returned that policy should have blocked) | 0 |
| Security | Share of executed queries with a complete audit record | 100% |
| Security | Red-team prompts that extract masked or out-of-scope data | 0 |
| Compliance | Time to produce an access evidence pack for one quarter | Under 1 hour |
| Privacy | Share of sensitive columns auto-classified before steward review | ≥ 90% |
| Accuracy | Generated SQL judged correct on the internal benchmark | ≥ 85% at GA, ≥ 92% at 12 months |
| Adoption | Weekly active users as a share of licensed seats | ≥ 50% |
| Efficiency | Share of questions answered without a data-team ticket | ≥ 60% |
| Speed | Median time from question to answer (excluding approvals) | Under 15 seconds |
| Trust | Share of answers that use certified metrics where one exists | ≥ 80% |
| Approvals | Median time to approval decision | Under 4 business hours |

**Guardrail metrics** (must not regress): false-block rate below 3% of legitimate queries, p95 gate latency below 300 ms, warehouse cost per query within budget.

## 5. Users and personas

| Persona | Role | Goals | Key permissions |
|---|---|---|---|
| **Ana, Business analyst** | Regional analyst | Fast answers within her region | Read regional customer, order and ticket data; PII masked |
| **Sam, Business manager** | Sales or ops manager | Team performance; approves team requests | Read regional data with fewer masks; approver |
| **Priya, HR partner** | People team | Headcount and compensation analysis | Employee data only; national ID masked |
| **Dana, Data admin** | Data platform team | Connect warehouses, manage policies, approve | All regions; restricted columns masked or rounded; approver; policy admin |
| **Sofia, Security officer** | Security and compliance | Prove control; investigate incidents | Read audit log and evidence; manage security policies; no business data by default |
| **Raj, Data steward** | Domain data owner | Classify data, certify metrics | Review classifications and glossary; approver for owned datasets |
| **Auditor** | External auditor | Verify controls | Time-boxed read-only access to evidence packs |

## 6. Scope by release

The release plan follows the security-first roadmap. Each phase has exit criteria (section 16).

| Phase | Name | Timing (estimate) | Scope |
|---|---|---|---|
| 1 | Foundation | Months 1–3 | SSO and MFA, roles, one warehouse connector (read-only), query gateway, deny-by-default guardrails, immutable audit log, manual SQL editor |
| 2 | Privacy and AI safety | Months 3–6 | Data classification, masking, row-level security, NL-to-SQL, prompt-injection filter, approval workflows, output controls |
| 3 | Compliance | Months 6–9 | Framework control mapping, evidence packs, residency, retention and erasure, SOC 2 Type I |
| 4 | Governed analytics | Months 9–12+ | Semantic layer and certified metrics, dashboards, notebooks, sharing, more warehouses, scheduled insights |

Requirement priorities use **MoSCoW**: **M** = must, **S** = should, **C** = could, **W** = won't (this release).

## 7. User journeys

### 7.1 Ask a question (routine)

1. Ana signs in with SSO.
2. She types "Average CSAT by ticket category this quarter."
3. SQL.AI screens the prompt, then drafts SQL using only the tables Ana can see.
4. Ana reviews the SQL and explanation, then clicks **Run under policy**.
5. The gate passes the query, applies her region filter and masks, and runs it.
6. Ana sees a chart, a table, the rules that were applied and a "within policy" badge.
7. The audit log records the prompt, the draft, the decision, the rules applied and the row count.

### 7.2 Request sensitive data (approval)

1. Ana asks for a customer contact list.
2. The gate detects a row-level pull of personal data over the threshold and holds it.
3. An approval request goes to eligible approvers (not Ana).
4. Sam reviews the SQL, the row count and the columns, enters a reason and approves.
5. Ana gets a notification and runs the approved query once. The run is linked to the approval in the audit log.

### 7.3 Blocked query

1. Ana asks for average salary by department.
2. The gate blocks the query: her role has no access to the employee table.
3. She sees why it was blocked and how to request access.
4. The block is logged.

### 7.4 Prove control (audit)

1. Sofia opens the audit log, filters to Q3 and to the `customers` table.
2. She verifies the hash chain is intact.
3. She exports an evidence pack (access log, approvals, policy changes, access reviews) for the auditor.

### 7.5 Change a policy

1. Dana proposes a new masking rule.
2. The policy test suite runs against known queries and shows the impact.
3. A second admin approves the change.
4. The new policy version is published, and the change is logged.

## 8. Functional requirements

Each requirement has an ID, priority and phase. Acceptance criteria are in *italics*.

### 8.1 Identity and access (IAM)

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| IAM-01 | Support SSO via SAML 2.0 and OIDC. *A user can sign in through the customer's identity provider; local passwords are disabled for org accounts.* | M | 1 |
| IAM-02 | Enforce MFA through the identity provider, with a fallback MFA option for break-glass admin accounts. | M | 1 |
| IAM-03 | Provision and deprovision users and groups via SCIM 2.0. *A user removed in the IdP loses access within 5 minutes.* | M | 1 |
| IAM-04 | Role-based access control (RBAC) with custom roles. | M | 1 |
| IAM-05 | Attribute-based rules (ABAC) using IdP attributes such as department, region and clearance. | M | 2 |
| IAM-06 | Map each SQL.AI user to a scoped warehouse identity so queries run with that user's effective permissions, not a shared superuser. | M | 1 |
| IAM-07 | Configurable session timeout and idle timeout. | M | 1 |
| IAM-08 | Quarterly access review workflow: owners confirm or revoke each user's role. | S | 3 |
| IAM-09 | Just-in-time elevated access with expiry and approval. | C | 4 |
| IAM-10 | Request access from a block message. On approval, grant read access to that table for 24 hours with every personal and restricted column redacted and the requester's row filters kept. *The grant expires automatically and appears in the access simulator and evidence pack.* | S | 2 |

### 8.2 Query gateway

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| GW-01 | All queries, from any surface (editor, AI, API, dashboards, schedules), pass through one gateway. *No code path can execute SQL against a warehouse without a gateway decision.* | M | 1 |
| GW-02 | Parse SQL into an abstract syntax tree (AST) before any decision. Reject unparseable SQL. | M | 1 |
| GW-03 | Allow only a single read statement (`SELECT` or `WITH … SELECT`). | M | 1 |
| GW-04 | Block comments, multiple statements, file I/O, external stages, procedure calls, session or role switching and cross-database references not explicitly allowed. | M | 1 |
| GW-05 | Enforce per-role query timeouts and scan-cost limits using warehouse estimates. | M | 1 |
| GW-06 | Return a structured decision: allow, allow-with-modifications, hold-for-approval or block, with every rule evaluated and its result. | M | 1 |
| GW-07 | Rewrite queries to apply row filters and masking (or apply them through warehouse-native policies where available). | M | 2 |
| GW-08 | Cache results only per identical policy context (same user scope and policy version). | S | 4 |
| GW-09 | Estimate work before running from the query plan; refuse unconstrained joins and queries over the role's cost limit (rule P-14). | M | 1 |
| GW-10 | Use one message for unknown and ungranted tables so access checks don't reveal which tables exist. | S | 1 |

### 8.3 Policy management

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| POL-01 | Policies are defined as code (versioned, reviewable) with an admin UI on top. | M | 1 |
| POL-02 | Every policy change requires a second admin's approval. | M | 2 |
| POL-03 | Policy test suite: known-good and known-bad queries run on every change; a change that lets a known-bad query through cannot be published. | M | 2 |
| POL-04 | Impact preview: show which recent queries would have been decided differently. | S | 3 |
| POL-05 | Roll back to any previous policy version. | M | 2 |
| POL-06 | Policy decisions record the policy version used. | M | 1 |

### 8.4 Privacy

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| PRV-01 | Automatically classify columns (PII, PHI, financial, restricted, public) from names, types and sampled values. Sampling runs inside the customer's environment. | M | 2 |
| PRV-02 | Data stewards review and confirm classifications. Unreviewed sensitive columns default to masked. | M | 2 |
| PRV-03 | Column masking methods: full redaction, partial (e.g. last 4), initials, hashing, tokenization, rounding or banding. Configurable per role and column. | M | 2 |
| PRV-04 | Row-level security from user attributes (e.g. region, business unit). | M | 2 |
| PRV-05 | Small-group suppression: aggregate counts below a configurable threshold (default 5) display as "<5". | M | 2 |
| PRV-06 | Erasure requests propagate to caches, saved results and exports within a configurable period (default 24 hours). | M | 3 |
| PRV-07 | Data residency: processing and logs pinned to the customer's chosen region. | M | 3 |
| PRV-08 | A purpose is required for any query that returns personal data row by row, and is recorded in the audit log (rule P-15). Purposes listed as high-risk (default: marketing) always need approval. | M | 2 |
| PRV-09 | **Column lineage.** Classify each output column by the source columns it derives from, through aliases, expressions, CTEs and derived tables. Personal-data, masking and approval decisions use lineage, not column names. *Renaming or grouping by a personal-data column doesn't change how it's treated.* | M | 2 |
| PRV-10 | **Disclosure budget.** Limit the personal-data rows each person can see per data domain in 24 hours (default 60). Exceeding it requires approval (rule P-13). | M | 2 |
| PRV-11 | **Aggregate, then protect.** For numeric columns masked by rounding, compute AVG and SUM on true values and round the result; MIN, MAX and row-level output stay masked. | S | 2 |
| PRV-12 | **Group-size suppression.** For aggregate results, compute each group's row count; suppress every aggregate in a group under k, and any count-like value under k regardless of name or expression. Queries whose groups can't be checked are refused. | M | 2 |

### 8.5 AI: natural language to SQL

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| AI-01 | Translate a question into SQL for the connected warehouse's dialect. | M | 2 |
| AI-02 | The model context contains only schema, descriptions, glossary terms and certified metric definitions visible to the asking user. No row data. | M | 2 |
| AI-03 | Screen prompts for injection and policy-evasion attempts before any model call. | M | 2 |
| AI-04 | Every draft passes the same gateway as hand-written SQL. The model can never execute SQL directly. | M | 2 |
| AI-05 | Show a plain-English explanation of what the SQL does, and label drafts "review before running." | M | 2 |
| AI-06 | If the question can't be answered within the user's scope, decline and say why, without revealing hidden tables or columns. | M | 2 |
| AI-07 | Prefer certified metrics from the semantic layer over freshly written logic. | S | 4 |
| AI-08 | Self-correction: when a draft fails to parse or run, retry once with the error, then stop. | S | 2 |
| AI-09 | Model providers must offer zero data retention and no training on customer data. | M | 2 |
| AI-10 | Users can rate drafts; ratings feed the accuracy benchmark (without customer data leaving the tenant). | S | 2 |

### 8.6 Approvals

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| APR-01 | Hold queries that meet approval rules (default: row-level result over 25 rows containing personal data). | M | 2 |
| APR-02 | Route requests to eligible approvers by data domain and requester's management chain. | M | 2 |
| APR-03 | Separation of duties: requesters can't approve their own requests. | M | 2 |
| APR-04 | Approvers must enter a reason; approve or deny is logged with the reason. | M | 2 |
| APR-05 | Approvals are single-use and bound to the exact SQL and policy version. Any change requires a new approval. | M | 2 |
| APR-06 | Approvals expire if unused (default 72 hours). | S | 2 |
| APR-07 | Notifications via email and chat integrations. | S | 2 |
| APR-08 | Escalation when a request is pending longer than a set time. | C | 3 |
| APR-09 | Approvers with access to the data see a 3-row preview exactly as the requester would see it; others decide on metadata only. | S | 2 |
| APR-10 | Every request has an eligible approver: if no domain approver other than the requester exists, the security officer decides. | M | 2 |
| APR-11 | A policy change invalidates outstanding approvals made under the previous version. | M | 2 |

### 8.7 Output controls

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| OUT-01 | Cap rows returned to the UI (default 500) and to exports (configurable per role). | M | 2 |
| OUT-02 | Export permissions by role; exports of sensitive data require approval. | M | 2 |
| OUT-03 | Watermark exports and shared views with user and timestamp. | S | 3 |
| OUT-04 | Block copy and download for selected classifications. | C | 3 |
| OUT-05 | Exports keep all masks and suppression; personal data shown row by row can only be exported from an approved run (rule P-12). | M | 2 |

### 8.8 Audit and evidence

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| AUD-01 | Log every sign-in, prompt, draft, gate decision, execution, approval, policy change and admin action. | M | 1 |
| AUD-02 | Each log record includes actor, time, action, outcome, rules evaluated, policy version, SQL, tables, row count and request ID. | M | 1 |
| AUD-03 | The log is append-only and tamper-evident (hash-chained, stored in write-once storage). | M | 1 |
| AUD-04 | Verify the hash chain on demand and on a schedule; alert on a break. | M | 1 |
| AUD-05 | Filter and search the log; export as CSV and JSON. | M | 1 |
| AUD-06 | Stream logs to the customer's SIEM. | S | 2 |
| AUD-07 | Evidence packs per framework and period. | M | 3 |
| AUD-08 | Retention configurable per customer (default 7 years, minimum 1 year). | M | 3 |
| AUD-09 | Redact personal data patterns (emails, phone numbers, national IDs) from questions and SQL before they're written to the audit log. | M | 2 |
| AUD-10 | Security alerts for unusual activity: repeated blocks, repeated injection attempts, personal-data budget over 80%, failed chain verification. Alerts go to the security team and the audit log. | S | 3 |

### 8.9 Workbench

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| WB-01 | SQL editor with syntax highlighting, autocomplete limited to visible schema, and run shortcut. | M | 1 |
| WB-02 | Results table with masked and suppressed values visibly labelled. | M | 1 |
| WB-03 | Policy gate panel showing each rule and its result for the current query. | M | 1 |
| WB-04 | Automatic chart for suitable results (bar, line); user can switch chart types. | S | 2 |
| WB-05 | Data catalog showing tables, columns, classifications and what the current user sees. | M | 2 |
| WB-06 | Saved queries and history (subject to the same policies when re-run). | S | 2 |
| WB-07 | Dashboards and notebooks; each viewer sees results under their own permissions. | S | 4 |
| WB-08 | Sharing re-checks the viewer's permissions; shared links never carry the sharer's access. | M | 4 |
| WB-09 | **Trust card** under every result: certified metric (if any), data freshness, rows in scope, masks, suppressed values, rules applied, policy version, purpose and audit entry. | S | 2 |
| WB-10 | **Follow-up questions** ("now by month", "only enterprise") refine the previous question. | S | 2 |
| WB-11 | **Scheduled reports** from saved queries (daily or weekly). Every run re-checks the owner's permissions under the current policy and is audited. | S | 4 |
| WB-12 | **Notifications** for approval requests and decisions, policy proposals, schedules and security alerts; in-app, plus email, Slack and Teams in production. | S | 2 |
| WB-13 | **Access simulator:** show what any role sees in any table, and who can see any column. | S | 3 |

### 8.10 Semantic layer

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| SEM-01 | Define certified metrics (name, definition, SQL, owner, grain). | S | 4 |
| SEM-02 | Business glossary mapping terms to tables and columns. | S | 4 |
| SEM-03 | "Certified" badge on answers that use certified metrics. | S | 4 |
| SEM-04 | Import definitions from dbt and similar tools. | C | 4 |

### 8.11 Administration

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| ADM-01 | Connect warehouses with read-only credentials stored in a secrets vault. | M | 1 |
| ADM-02 | Health checks for connectors and identity sync. | M | 1 |
| ADM-03 | Usage and cost dashboards per team. | S | 3 |
| ADM-04 | Public API for queries, audit export and policy management, with the same gateway and scoped tokens. | S | 3 |

## 9. Policy engine specification

### 9.1 Default rule set

| Rule | Name | Stage | Default behavior |
|---|---|---|---|
| P-01 | Prompt-injection filter | Before drafting | Block prompts that try to override rules, unmask data or reach other systems |
| P-02 | Read-only statements | Before run | Allow only a single `SELECT`/`WITH` |
| P-03 | No file, script or system access | Before run | Block file I/O, scripts, comments, database switching |
| P-04 | Table access by role | Before run and data layer | Block tables outside the role's grants, with one message for unknown and ungranted tables |
| P-05 | No `SELECT *` on sensitive tables | Before run | Require named columns |
| P-06 | Row-level security | Data layer | Filter rows by user attributes |
| P-07 | Column masking | Data layer | Mask per role and classification; masks follow lineage; AVG and SUM of rounded numeric columns use true values, then round |
| P-08 | Small-group suppression | After run | Suppress aggregates from groups under k rows (default 5) and count-like values under k, by lineage and group size |
| P-09 | Approval for personal-data pulls | After run (pre-display) | Hold results that show personal data row by row (including through GROUP BY) over 25 rows; hold all marketing use of personal data |
| P-10 | Result cap | After run | Return at most 500 rows to the UI |
| P-11 | Separation of duties | Approvals and policy changes | No self-approval; security officer is the fallback approver |
| P-12 | Export control | Export | Row-level personal data exports only from approved runs; protections preserved |
| P-13 | Personal-data disclosure budget | After run | Hold when a person's personal-data rows in a domain would exceed the 24-hour budget (default 60) |
| P-14 | Cost guard | Before run | Refuse queries whose estimated work exceeds the limit (default 100,000 row combinations) |
| P-15 | Purpose required | Before run | Require a stated purpose for queries returning personal data row by row |

### 9.2 Decision order

1. Authenticate and resolve the user's roles, attributes and policy version.
2. Prompt rules (P-01) for AI requests.
3. Static rules on the AST (P-02 to P-05). Any block stops evaluation.
4. Apply data-layer rules (P-06, P-07) by rewriting the query or using warehouse-native policies.
5. Estimate cost (P-14); block if over limit. Check purpose (P-15) when the output's lineage includes personal data.
6. Execute with the user's scoped identity.
7. Post-execution rules (P-08 to P-10, P-13) before any result reaches the client.
8. Write the audit record. **If the audit write fails, the result is not returned (fail closed).**

### 9.3 Fail-closed behavior

If the policy service, classification service or audit store is unavailable, queries are blocked with a clear message. No degraded "allow" mode exists.

## 10. AI requirements

- **Model access:** through providers with zero data retention and contractual no-training terms. Customers can pick an approved provider or bring their own endpoint.
- **Context construction:** built per request from the user's visible schema only. Hidden tables and columns are not mentioned.
- **Output contract:** JSON with `sql` and `explanation`; empty `sql` plus a reason when the request can't be answered in scope.
- **Validation:** drafts are parsed and gated like any other query. The model has no execution tools.
- **Evaluation:** an internal benchmark of question/SQL pairs per dialect, run on every model or prompt change. Track accuracy, refusal correctness and injection resistance.
- **Red teaming:** a standing suite of adversarial prompts (instruction override, schema probing, encoding tricks, multi-turn escalation) must pass before each release.
- **Transparency:** UI marks AI-drafted SQL; the audit log records the model and prompt version used.

## 11. Non-functional requirements

### 11.1 Security

| ID | Requirement |
|---|---|
| SEC-01 | TLS 1.2+ in transit; AES-256 at rest. |
| SEC-02 | Customer-managed encryption keys (Enterprise plan). |
| SEC-03 | Private connectivity to warehouses (private link or VPC peering). |
| SEC-04 | Secrets held in a managed vault; never in logs or client code. |
| SEC-05 | Tenant isolation at the data, compute and key level. |
| SEC-06 | Independent penetration test before GA and at least annually. |
| SEC-07 | Dependency and container scanning in CI; critical vulnerabilities fixed within 7 days. |
| SEC-08 | Security incident response plan with customer notification within contractual and legal deadlines. |
| SEC-09 | Bug bounty program after GA. |

### 11.2 Performance

| Metric | Target |
|---|---|
| Gate decision latency (excluding warehouse execution) | p50 < 100 ms, p95 < 300 ms |
| AI draft latency | p50 < 5 s, p95 < 15 s |
| UI interaction latency | p95 < 200 ms |
| Audit write latency | p95 < 150 ms |

### 11.3 Availability and resilience

- Service availability: 99.9% monthly (99.95% Enterprise target).
- RPO ≤ 15 minutes for application data; audit log RPO = 0 (synchronous replicated write).
- RTO ≤ 4 hours.
- Fail closed on dependency outages (section 9.3).

### 11.4 Scalability

- 10,000 users and 1,000 concurrent queries per tenant at GA.
- Horizontal scaling of the gateway and AI services.

### 11.5 Privacy by design

- Default settings are the most protective.
- No customer row data is stored by SQL.AI outside short-lived result caches, which respect retention and erasure rules.

### 11.6 Maintainability and observability

- Structured logs, metrics and traces for every request, with the request ID shared with the audit record.
- Feature flags for every new policy and AI behavior.

## 12. Compliance requirements

SQL.AI must provide controls and evidence that support customers' obligations. Final mapping must be validated by legal and compliance.

| Framework | What SQL.AI provides |
|---|---|
| GDPR | Data minimization, purpose tags, access logs, erasure propagation, residency, DPA |
| CCPA/CPRA | Access logs, deletion propagation, restricted use of personal information |
| HIPAA | PHI classification and masking, access logs, BAA availability (Enterprise) |
| SOC 2 | Access control, change management, monitoring, incident response evidence |
| ISO/IEC 27001 | Control mapping to Annex A, evidence export |
| PCI DSS | Isolation and masking of cardholder data; access logging |
| EU AI Act | Transparency labeling of AI output, logging, human oversight through approvals |

**SQL.AI's own certifications:** SOC 2 Type I during Phase 3, Type II within 12 months of GA; ISO 27001 to follow.

## 13. Data and integration requirements

### 13.1 Warehouses

| Warehouse | Phase |
|---|---|
| Snowflake | 1 |
| BigQuery | 3 |
| Databricks SQL | 4 |
| Amazon Redshift | 4 |
| PostgreSQL | 4 |

Warehouse-native row and masking policies are used where available; otherwise, the gateway rewrites queries.

### 13.2 Other integrations

- Identity: Okta, Microsoft Entra ID, Google Workspace (SAML/OIDC, SCIM).
- SIEM: Splunk, Microsoft Sentinel, Datadog (log streaming).
- Notifications: email, Slack, Microsoft Teams.
- Metadata: dbt manifests, data catalogs (Phase 4).

### 13.3 SQL.AI's own data

| Entity | Purpose | Retention |
|---|---|---|
| Users, roles, attributes | Access decisions | Synced from IdP |
| Policies and versions | Enforcement and history | Indefinite |
| Classifications | Masking decisions | Indefinite |
| Approval requests | Workflow and evidence | Same as audit log |
| Audit records | Evidence | Default 7 years |
| Query history | User convenience | Default 90 days |
| Result caches | Speed | Minutes to hours; erasure-aware |

## 14. UX and accessibility requirements

- The policy gate is always visible beside the query and shows each rule's result in plain language.
- Masked, filtered and suppressed values are labelled; users always know when they're seeing less than everything.
- Block messages say what happened and what to do next ("Your role can't read `employees`. Ask a data admin for access.").
- AI drafts are clearly labelled and must be reviewed before running.
- WCAG 2.2 AA conformance, full keyboard operation, screen reader support.
- Light and dark themes; responsive down to tablet width for the workbench and phone width for approvals.

## 15. Analytics and telemetry

Product telemetry must never include customer row data or query results.

| Event | Properties |
|---|---|
| `question_asked` | role, draft_source, latency |
| `draft_generated` | model_version, success, refusal |
| `query_decided` | decision, rules_fired, policy_version, latency |
| `query_executed` | row_count, duration, cost_estimate |
| `approval_requested` / `approval_decided` | time_to_decision, outcome |
| `audit_verified` | entries, result |
| `draft_rated` | rating |

## 16. Release criteria

| Phase | Exit criteria |
|---|---|
| 1 | Independent pen test with no open critical or high findings; 100% of executions audited; no write path to any warehouse; SSO, SCIM and audit chain verification working with one design partner |
| 2 | Red-team suite passes with 0 extractions of masked or out-of-scope data; accuracy ≥ 80% on benchmark; approval flow used in production by at least one partner |
| 3 | SOC 2 Type I report issued; evidence pack accepted by a partner's auditor; residency in at least two regions |
| 4 (GA) | Accuracy ≥ 85%; availability ≥ 99.9% over 30 days; WCAG 2.2 AA audit passed; at least 3 reference customers |

## 17. Dependencies

- LLM provider(s) with zero-retention terms and suitable regional endpoints.
- Warehouse vendor APIs for scoped identities, cost estimates and native policies.
- Customer identity providers supporting SAML/OIDC and SCIM.
- Write-once storage for audit records.
- Third-party auditors for SOC 2 and penetration testing.

## 18. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI-generated SQL is wrong but plausible | High | High | Explanations, review step, certified metrics, benchmark gating, user ratings |
| Prompt injection extracts restricted data | Medium | Critical | Schema-only context, same gate for all SQL, data-layer enforcement, red-team suite |
| Gate bypass via a new surface (API, schedule) | Medium | Critical | Single gateway architecture (GW-01), integration tests that fail if any path skips the gate |
| Over-blocking frustrates users | Medium | Medium | Clear block reasons, access-request flow, false-block metric |
| Warehouse cost overruns | Medium | Medium | Cost estimates, per-role limits, caching |
| Classification misses sensitive columns | Medium | High | Unreviewed-sensitive defaults to masked; steward review; periodic rescans |
| Model provider outage or terms change | Low | High | Multi-provider support; manual SQL still works |
| Compliance claims overstated | Low | High | Legal review of all compliance messaging; "supports" not "certifies" |

## 19. Open questions

1. Which warehouse do the first design partners use? (Assumed Snowflake.)
2. Default approval threshold: 25 rows, or configurable per dataset from day one?
3. ~~Should approvers see a sample of the held results?~~ Resolved in 1.1: approvers with access see a 3-row masked preview (APR-09).
4. Bring-your-own-model in Phase 2 or later?
5. Pricing model: per seat, per query volume or platform fee? (See the investor pitch.)
6. Is a self-hosted deployment needed for regulated customers in year one?
7. Which regions are required for residency at launch?

## 20. Glossary

| Term | Meaning |
|---|---|
| Policy gate | The single enforcement point every query passes before and after execution |
| RLS | Row-level security: filtering rows by user attributes |
| Masking | Replacing or transforming sensitive values for users who shouldn't see them in full |
| Small-group suppression | Hiding small counts that could identify individuals |
| Certified metric | A metric definition reviewed and owned by a data steward |
| Evidence pack | An exported set of logs and reports supporting an audit |
| Fail closed | Blocking requests when a safety dependency is unavailable |
| Zero data retention | A provider term under which prompts and outputs are not stored |
| Column lineage | Tracing each output column back to the source columns it's computed from |
| Disclosure budget | A cap on how many personal-data rows one person can see per domain in 24 hours |
| Trust card | The panel under a result explaining how it was produced and which protections applied |

## 21. Appendix: requirement traceability

| Goal | Requirements |
|---|---|
| G1 Fast answers | AI-01–AI-08, WB-01–WB-13, SEM-01–SEM-03 |
| G2 Never exceed permissions | IAM-04–IAM-06, GW-01–GW-10, PRV-03–PRV-12, POL-03, OUT-05 |
| G3 Verifiable evidence | AUD-01–AUD-10, APR-04, APR-09–APR-11, POL-06 |
| G4 Trusted AI | AI-02–AI-06, AI-10, section 10 |
| G5 Less ad-hoc work | AI-07, SEM-01–SEM-03, WB-06 |

---

*Related documents: Model and Architecture, Developer Manual, User Manual, README, Documentation Guidelines, Investor Pitch.*
