# Runbook: Audit chain verification failed

**Severity:** Critical
**Owner:** Security
**Last tested:** [DATE]

## What the alert means
A recomputed hash didn't match a stored audit record, or a record's previous-hash link is wrong. An audit entry may have been altered or removed.

## Impact
Evidence for the affected tenant can't be trusted until resolved. Customer notification may be required.

## First steps (do these now)
1. Freeze writes for the tenant: `make audit-freeze TENANT=<id>` (queries for that tenant fail closed).
2. Page the security on-call and the audit service owner.
3. Record the first broken sequence number and the time of the last successful verification.
4. Do not attempt to repair or rehash the chain.

## Diagnosis
Compare the ledger range against the signed Merkle checkpoints in write-once storage. A mismatch only in the ledger points to database tampering or corruption; a mismatch in both points to a signing or software defect. Check database access logs and recent deployments. Start from the `request_id` or audit sequence number.

## Resolution
Restore the affected range from write-once storage if the ledger was altered. If a software defect caused it, fix, then re-verify the full chain. Unfreeze only after a full verification passes.

## Escalation
Security incident commander; legal and the customer's security contact per the incident response plan.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
