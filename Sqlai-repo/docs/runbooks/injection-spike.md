# Runbook: Spike in prompt-injection blocks

**Severity:** Medium
**Owner:** Security
**Last tested:** [DATE]

## What the alert means
Many P-01 blocks from one tenant or user in a short window. Security alerts may already have fired.

## Impact
Usually none (the gate held). Could indicate a targeted attempt.

## First steps (do these now)
1. Identify the users and tenants involved from the audit log (filter: Security alerts, Blocked).
2. Check whether any related query was allowed.

## Diagnosis
Review the redacted prompts and the sequence of attempts. Check for successful runs from the same users in the same window. Start from the `request_id` or audit sequence number.

## Resolution
If a gap is found, add a golden test and fix the rule. Notify the customer's security contact if the activity looks deliberate.

## Escalation
Security on-call.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
