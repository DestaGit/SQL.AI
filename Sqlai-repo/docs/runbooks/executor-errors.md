# Runbook: Executor errors

**Severity:** High
**Owner:** Platform
**Last tested:** [DATE]

## What the alert means
Queries fail between the gateway and the warehouse.

## Impact
Users see warehouse errors or timeouts.

## First steps (do these now)
1. Check warehouse status pages and the customer's warehouse limits.
2. Check credential issuance in the vault.
3. Check network policy and private link health.

## Diagnosis
Group errors by tenant and warehouse; distinguish auth, network and query errors. Start from the `request_id` or audit sequence number.

## Resolution
Fix the failing dependency. Never widen credentials as a workaround.

## Escalation
Platform on-call; the customer's data platform contact if their warehouse is down.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
