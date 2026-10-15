# Runbook: Fail-closed: audit service unavailable

**Severity:** High
**Owner:** Platform
**Last tested:** [DATE]

## What the alert means
The audit ledger isn't acknowledging writes, so results are withheld.

## Impact
All queries are refused until audit writes succeed.

## First steps (do these now)
1. Check Postgres primary and synchronous replica health.
2. Check audit service error rates and disk space.

## Diagnosis
Replication lag, failover in progress, storage exhaustion, or connection pool limits. Start from the `request_id` or audit sequence number.

## Resolution
Restore the primary or complete failover. Confirm the chain verifies across the outage window.

## Escalation
Platform on-call, then the database owner.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
