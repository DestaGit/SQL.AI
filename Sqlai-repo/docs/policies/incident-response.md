# SQL.AI — Incident Response Plan

**Audience:** Engineering, security, support and leadership
**Version:** 1.0 (draft — requires legal review of notification commitments)
**Date:** 2026-10-14
**Owner:** [SECURITY LEAD NAME]

## 1. Purpose

How SQL.AI detects, responds to and learns from security and privacy incidents. Customer notification timelines depend on contracts and applicable law; legal confirms them for each incident.

## 2. Severity levels

| Level | Definition | Examples | Response start |
|---|---|---|---|
| **SEV-1** | Confirmed or likely exposure of customer data, or loss of audit integrity | Data returned beyond policy; audit chain broken; credential leak | Immediately, 24/7 |
| **SEV-2** | Control failure without confirmed exposure, or broad fail-closed outage | Gate rule regression caught in production; policy service down | Within 1 hour |
| **SEV-3** | Limited impact or a suspicious pattern | Injection spike; budget alerts for one user | Within 1 business day |
| **SEV-4** | No impact; improvement needed | Missing monitor, stale runbook | Planned work |

## 3. Roles

| Role | Responsibility |
|---|---|
| Incident commander | Owns the response, decisions and timeline |
| Technical lead | Investigation and fix |
| Communications lead | Internal updates, customer and regulator communication (with legal) |
| Scribe | Timeline and evidence log |
| Legal and privacy | Notification obligations and wording |

## 4. Process

1. **Detect.** Alerts (chain verification failure, fail-closed events, security alerts, anomaly detection), customer reports, researcher reports via [SECURITY.md](../../SECURITY.md).
2. **Triage.** Assign severity and an incident commander. Open an incident channel and timeline.
3. **Contain.** Use the relevant runbook in [docs/runbooks](../runbooks/README.md). Prefer actions that fail closed: freeze a tenant, roll back a policy bundle, revoke credentials, disable a feature flag. Never widen access to restore service.
4. **Preserve evidence.** Export affected audit ranges and checkpoints before any repair. Record every action with time and actor.
5. **Assess impact.** Which tenants, users, tables and columns; which rules failed; whether data was returned, exported or only attempted. Use audit records and the evidence pack.
6. **Notify.** Legal decides on customer, regulator and individual notification and timelines. Customer notices state what happened, what data was affected, what we've done and what they should do.
7. **Eradicate and recover.** Fix the cause, add golden tests or bypass probes that reproduce it, re-verify the audit chain, and restore normal operation.
8. **Review.** Blameless post-incident review within 5 business days for SEV-1 and SEV-2: timeline, root cause, what worked, and tracked actions. Update runbooks, tests and docs.

## 5. Communication templates

**Internal status (every 30–60 minutes for SEV-1):**
> Status: [investigating / contained / resolved] · Impact: [known scope] · Next update: [time] · Commander: [name]

**Customer notice (draft for legal):**
> On [date] we identified [what happened] affecting [scope]. [Data involved, if any]. We [containment steps]. You don't need to [or: we recommend you] [action]. We'll share our full review by [date]. Contact: [SECURITY CONTACT].

## 6. Testing the plan

- Tabletop exercise each quarter, rotating scenarios: audit chain break, gate regression, credential leak, model provider incident.
- Restore drill for audit storage twice a year.
- Track exercise findings like incident actions.
