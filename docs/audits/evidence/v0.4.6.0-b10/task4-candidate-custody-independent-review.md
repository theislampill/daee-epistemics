# Task 4 independent candidate-custody review

Verdict: `ACCEPT`

- Critical findings: `0`
- Important findings: `0`
- Review scope: the exact stable Task 4 paths and SHA-256 identities recorded in `task4-candidate-custody-owner-report.md`.
- Review method: independent read-only source inspection, mutation probes at archive publication, bound-reference revalidation, extraction-receipt publication, and readiness-marker publication, plus fresh focused contract/self-test execution.

The review initially identified four Important custody defects, then two residual archive/readiness defects, then one final readiness-publication race. Every finding was repaired test-first and independently replayed. Final verification established:

- one frozen archive identity is shared by extraction receipt, candidate record, and final readback;
- references are checked before build, before publish, and during readiness consumption;
- authorization-bound archive, extracted-byte, and entry ceilings are independent and enforced;
- extraction uses a stable candidate-relative locator;
- readiness is a separate create-once marker emitted only after final verification;
- the custody writer lock covers final verification, marker publication/readback, live readiness validation, cleanup, and return;
- a marker-publication mutation cannot leave an identity-valid readiness marker or yield a successful candidate.

Bounded nonclaim: this review approves Task 4 engineering bytes only. It does not approve candidate maturity, exact-SHA CI, deterministic closure, model execution, smoke success, or owner acceptance.
