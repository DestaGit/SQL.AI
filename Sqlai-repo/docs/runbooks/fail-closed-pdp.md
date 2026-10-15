# Runbook: Fail-closed: policy service unavailable

**Severity:** High
**Owner:** Platform
**Last tested:** [DATE]

## What the alert means
The Policy Decision Point (OPA) isn't answering, so the gateway refuses queries.

## Impact
All queries for affected tenants are blocked with "The policy service is unavailable".

## First steps (do these now)
1. Check OPA sidecar health and bundle load status on gateway pods.
2. Check whether a policy bundle was published in the last hour.

## Diagnosis
Look for bundle signature failures, oversized bundles, or sidecar crash loops. Correlate with the latest policy version ID. Start from the `request_id` or audit sequence number.

## Resolution
Roll back the last policy bundle if it coincides. Restart unhealthy sidecars. Never switch the gateway to an allow mode.

## Escalation
Platform on-call, then the policy owner.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
