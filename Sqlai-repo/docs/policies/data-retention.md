# SQL.AI — Data Retention and Deletion Policy

**Audience:** Customers, security and compliance teams, engineering
**Version:** 1.0 (draft — requires legal review before publication)
**Date:** 2026-10-14
**Owner:** [PRIVACY OWNER NAME]

> **Draft for counsel.** This describes how the product is designed to handle data. It isn't a contract and must be reviewed by legal before customers rely on it.

## 1. Principles

- **Customer data stays in the customer's warehouse.** SQL.AI reads it to answer queries and does not keep copies beyond the short-lived items below.
- **Keep the minimum, for the minimum time.**
- **Erasure reaches everything SQL.AI holds**, including caches, saved results, exports it stores and, through crypto-shredding, audit records.

## 2. What SQL.AI holds and for how long

| Data | Example | Default retention | Configurable | Deletion method |
|---|---|---|---|---|
| Query results cache | Rows behind a recent answer | Minutes to hours; purged on policy change | Yes (shorter only) | Automatic expiry; purge on erasure request |
| Query history | SQL text and decision per user | 90 days | 0–365 days | Automatic deletion |
| Saved queries and schedules | SQL, name, purpose, schedule | Until deleted by the user or account closure | — | User deletion; account closure |
| Notifications | Approval and alert messages | 90 days | 30–365 days | Automatic deletion |
| Approval and access requests | Requester, reason, purpose, decision | Same as audit log | Same as audit log | With audit records |
| Audit log | Actor, action, outcome, rules, SQL hash, row count | 7 years | 1–10 years | Expiry after retention; crypto-shredding for erasure |
| Classification tags | Column → PII/Restricted | While the connection exists | — | Deleted with the connection |
| Model prompts and responses | Question, visible schema, drafted SQL | Not retained by providers (zero data retention) | — | Provider terms; SQL.AI stores only the audit record |
| Account and identity data | Name, email, roles from your IdP | Duration of contract + 30 days | — | Deleted after contract end |

## 3. Personal data in the audit log

- Emails, phone numbers and ID numbers typed into questions or SQL are redacted before writing (AUD-09).
- Where personal values must be logged, they're encrypted with a per-subject key. Erasure deletes the key, making the values unreadable without breaking the hash chain (ADR-008).

## 4. Erasure requests

1. The customer submits the request (subject identifier and scope) through the admin console or API.
2. SQL.AI purges matching cached results, saved results and stored exports within 24 hours (PRV-06) and shreds the subject's audit key.
3. SQL.AI confirms completion with an audit record and a report to the customer.
4. Data in the customer's own warehouse is the customer's responsibility to erase.

## 5. Account closure

On contract end, SQL.AI deletes customer configuration, saved queries, history and caches within 30 days, and exports the audit log to the customer on request before deletion at the end of its retention period or earlier if the contract requires.

## 6. Backups

Backups follow the same retention periods plus a maximum of 35 days. Erasure is reapplied if a backup is restored.

## 7. Review

Reviewed at least annually and whenever a new data store is added.
