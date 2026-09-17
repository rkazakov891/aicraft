---
id: FEAT-001
title: <Feature name>
status: draft
spec_issue: <null | TBD | issue number>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Feature name>

<!-- What and why. State user-visible behavior, business rules, and acceptance
     criteria. Keep implementation detail only when it is a genuine external
     constraint. Delete sections that do not apply and delete these comments. -->

## Sources

- `<canonical repository-relative PRD or plan path, or canonical GitHub issue URL>`

<!-- Record exactly one accepted source. Never write an absolute local path. -->

## Summary

<One paragraph: the capability being added.>

## Problem

<The user or business problem this feature addresses.>

## Goals

- ...

## Non-goals

- ...

## User scenarios

### Scenario: <Name or stable SC-ID>

<User, goal, preconditions, actions, observable outcome, and material alternatives. For Discovery intake, link the canonical SC file rather than copying it.>

## Functional requirements

- FR-001: When <event>, the system shall <observable response>.
- FR-002: If <unwanted condition>, then the system shall <observable response>.

<!-- Use the applicable EARS pattern; do not invent events or conditions for always-active requirements. Link SC/DEC sources for Discovery intake. -->

## Quality requirements

<Keep only real performance, security, access, or reliability constraints.>

- NFR-001: ...

## Edge cases

<State applicable invalid-input, duplicate, concurrency, timeout, partial- completion, and stale-reference behavior precisely.>

## Acceptance criteria

- [ ] AC-001: <Observable condition demonstrating success.>
- [ ] AC-002: ...

## Assumptions

- ...

## Open questions

- ...

<!-- Optional when real: Business rules (BR-NNN), State model, Dependencies,
     and Rollout constraints. -->
