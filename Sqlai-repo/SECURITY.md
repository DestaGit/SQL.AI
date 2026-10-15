# Security policy

## Reporting a vulnerability

Email **[SECURITY CONTACT]** with:
- what you found and where (component, version, URL or file),
- steps to reproduce,
- the impact you believe it has,
- whether you've shared it with anyone else.

Please don't open a public issue, post details publicly or test against other customers' data.

**What to expect:**

| Step | Target time |
|---|---|
| Acknowledgement | 2 business days |
| Initial assessment and severity | 5 business days |
| Fix or mitigation for critical issues | 7 days |
| Fix or mitigation for high issues | 30 days |
| Public disclosure (coordinated with you) | After a fix is available |

These are targets, not contractual commitments. We'll keep you updated and credit you if you'd like.

## Scope

| In scope | Out of scope |
|---|---|
| The SQL.AI service and API (once live) | Findings in third-party services we don't control |
| The standalone demo's policy logic (`index.html`), where it misrepresents how the product protects data | That the demo can be changed by its own user: the demo enforces policy in the browser by design (see below) |
| Documentation that misstates a security control | Social engineering, physical attacks, denial-of-service testing |

## Supported versions

| Version | Supported |
|---|---|
| 1.1.x | Yes |
| 1.0.x | No (contains findings A1–A13 fixed in 1.1.0) |

## Security model in brief

- **One gate:** every query passes the policy gate; in production only the executor service holds warehouse credentials.
- **Deny by default and fail closed:** if policy, classification or audit is unavailable, queries are refused.
- **Least privilege:** queries run under the user's scoped identity; the AI sees only the schema the user can see, never rows.
- **Defense in depth:** checks on the SQL (static), in the data layer (row filters, masks) and on the output (group-size suppression, approvals, budget, caps).
- **Lineage-based decisions:** personal-data rules follow where each output column comes from, not its name.
- **Evidence:** a hash-chained, append-only audit log, with signed checkpoints in write-once storage in production.

Full detail: [ARCHITECTURE.md §11](ARCHITECTURE.md#11-security-architecture) and [AUDIT.md](AUDIT.md).

## About the standalone demo

`index.html` runs the policy gate in the browser to show how SQL.AI behaves. A browser can't enforce policy against its own user, so the demo is **not a security boundary**: anyone can pick any account, and stored data can be edited. All demo data is fictional. Don't load real data into it.
