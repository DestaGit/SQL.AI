# Runbook: Personal-data budget alert

**Severity:** Medium
**Owner:** Security
**Last tested:** [DATE]

## What the alert means
A user has used more than 80% of their 24-hour personal-data budget in a domain.

## Impact
None yet. The next large pull will be held for approval.

## First steps (do these now)
1. Check the user's recent runs and stated purposes in the audit log.
2. Check whether the pattern matches their role.

## Diagnosis
Look for many small row-level queries (paging) or unusual purposes. Start from the `request_id` or audit sequence number.

## Resolution
If legitimate, no action, or a policy change through the normal review. If not, notify the user's manager and the data owner.

## Escalation
Security on-call; the data owner.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
