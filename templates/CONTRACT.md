# Contract: {{unit}}

One logical contract per work unit, scaled to the work. Every heading must be
present; a small task may answer each in a sentence. Lines of the form
`Key: value` are read by the tools. Inputs cite documents listed in
DOCUMENTS.md and decisions by D-number.

## Purpose and relationship
Why this matters, its parent if any, and the outcome it supports.

## Scope and return
Deliverable, exclusions, affected interfaces, and where the result is accepted.

Reserved: {{choices that return to Jules, or "none"}}

## Authoritative inputs
Requirements, decisions (by D-number), source references, and unresolved questions with their triggers.

## Execution arrangement
Role, model, context list, workspace, and permitted actions.

Model: {{model}}

## Effort and stopping
Allowance, experiment and repair limits, escalation triggers, allowed delegation.

Turns: {{per-dispatch turn cap}}
Repairs: {{failed repairs of one finding before the unit stops}}

## Acceptance and closure
Observable criteria, evidence, test procedure, review, integration, and cleanup obligations.

Tests: {{command run in the worktree; its output goes to the reviewer and must pass on the merged result}}
