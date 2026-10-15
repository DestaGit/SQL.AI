# Runbook: AI accuracy drop in nightly evaluation

**Severity:** Medium
**Owner:** AI
**Last tested:** [DATE]

## What the alert means
The nightly accuracy, refusal or injection suite fell below its gate.

## Impact
Drafts may be less accurate; the gate still protects data.

## First steps (do these now)
1. Compare prompt version, model version and retriever changes since the last passing run.

## Diagnosis
Re-run the failing suite against the previous versions to isolate the change. Start from the `request_id` or audit sequence number.

## Resolution
Roll back the feature flag for the prompt or model. Add failing cases to the regression suite.

## Escalation
AI on-call.

## After the incident
Hold a post-incident review, add any missing golden tests or monitors, update this runbook, and follow the incident response plan for customer communication.
