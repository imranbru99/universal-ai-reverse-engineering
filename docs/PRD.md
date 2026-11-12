# PRD — REVERSEFORGE AI

## Problem

Teams need to reconstruct specifications and independent implementations from authorized application evidence without illegally copying proprietary internals or guessing silently.

## Goals

- Authorized multi-source evidence intake
- Observable behavior mapping (state graph)
- Provenance-tagged inference with human review
- Independent code generation for one primary stack
- Exportable, testable reconstruction artifacts

## Non-goals (v1)

- Unauthorized testing or attack tooling
- Guaranteed complete recovery of private schemas
- Multi-stack generation parity

## Personas

- Security-conscious engineering lead
- Analyst performing migration discovery
- Developer reviewing generated reconstruction

## Success metrics

- Acceptance criteria path completes on bundled demo
- Cross-tenant denial rate 100% in tests
- Out-of-scope navigations blocked and logged
- Pipeline resumes after worker restart
