# PACK-SPEC — Spec Authoring Pack

## Purpose

PACK-SPEC keeps repo contracts precise without turning ordinary prose into legal machinery. Use it
when a document or tool defines behavior that another file, checker, release step, package, runtime,
or maintainer must conform to.

## Scope

Use PACK-SPEC for spec-like docs, contracts, schemas, checkers, release gates, smoke gates, package
gates, runtime contracts, implementation requirements, and acceptance criteria.

Do not use it to force every explanation, audit narrative, theory note, or design rationale into
RFC form. If a file is mainly context, history, or rationale, add a short pointer to the normative
owner instead of rewriting the whole file.

## Normal mode

- Use RFC 2119/8174-style requirement levels when the file is normative.
- Uppercase `MUST`, `SHOULD`, and `MAY` only when the sentence is intentionally normative.
- Normative requirements should include examples, counterexamples, compatibility notes where useful,
  and conformance tests.
- Acceptance: uppercase requirement words are intentional and normative.
- Verification: schema, contract, or checker examples pass.

## Strict mode

Use strict mode for release gates, package gates, smoke-promotion gates, destructive actions,
generated-runtime freshness, provenance checks, and public artifact updates.

- Avoid ambiguous requirement words such as "good enough" or "basically" in normative rules.
- Unsafe, unsupported, or unauthorized paths stop and report the stop reason.
- Done when the unsafe, unsupported, or unauthorized path is stopped and the stop reason is recorded.
- Verification names the denied action or the smallest passing check.

## Exploratory mode

Use exploratory mode before changing source ownership, schema shape, checker policy, generated-doc
architecture, runtime entrypoint behavior, or release proof boundaries.

- Draft requirement levels before implementation.
- Name the owner, risk, and next verification step before mutation.
- Report the inspection basis.

Done when owner, risk, next verification, and inspection basis are named before mutation.

## RFC 2119/8174 usage

Uppercase requirement words are reserved for normative clauses:

- `MUST` and `MUST NOT` define required conformance.
- `SHOULD` and `SHOULD NOT` define default conformance with a named exception path.
- `MAY` defines permitted behavior, not a vague possibility.

Lowercase "must", "should", and "may" can remain in explanatory prose when the file is not acting
as a normative spec, but do not mix casual and normative usage inside the same requirement block.

## Examples

Normative example:

```text
The current-release smoke manifest MUST NOT count `pending-live-output` as PASS evidence.
```

Exploratory example:

```text
Owner: docs/index generator
Risk: changing generated display order may erase source-owned notation
Next verification: build_docs_index.py --check + notation-preservation rg
Inspection basis: runtime-architecture.json and generated index.html
```

## Counterexamples

Counterexample:

```text
The current-release smoke manifest should be good enough.
```

Why it fails: "should be good enough" names neither conformance, evidence, exception path, nor a
checker.

## Compatibility matrix pattern

Use a compact matrix when old and new behavior must coexist:

```text
Surface | Current rule | Compatibility allowance | Checker
--- | --- | --- | ---
Generated runtime | Atomics source wins | Old atomized paths may resolve through compiled-module-map.json | check_compiled_runtime_freshness.py
Smoke evidence | Current package SHA required | Historical regression evidence allowed only when marked non-current | check_smoke_artifacts.py
```

Keep compatibility notes close to the requirement they qualify. A compatibility allowance is not an
unbounded exception.

## Conformance test pattern

Every durable requirement should name the smallest meaningful check:

```text
Requirement: Current-release PASS evidence uses current package filename/SHA and `current-release evidence: yes`.
Positive check: python tools/check_smoke_artifacts.py --require-current-release-smokes
Negative check: a `pending-live-output` PASS fixture fails with "pending-live-output cannot be PASS or PARTIAL evidence".
Owner: tools/check_smoke_artifacts.py plus docs/package-smoke-readiness.md
```

If no automated check exists, name the manual inspection basis and whether a checker is P0, P1, or
deferred.

Low-noise prose checker pattern:

```text
Checker: python tools/check_spec_authoring_pack.py
Scope: allowlisted spec-like files only
Exclusions: ordinary theory prose, case-library prose, fenced examples, and explanatory counterexamples
Failure type: high-risk ambiguous requirement phrases such as "good enough" or "best effort"
```

Do not broaden this into a global prose linter. Add a file to the allowlist only when it behaves as
a contract, gate, schema, runtime requirement, package rule, or checker policy.

## Stop reason pattern

Stop reasons make strict-mode denial auditable:

```text
STOP: release upload denied because current-release smoke checker failed.
Denied action: updating GitHub Release assets.
Smallest passing check: python tools/check_smoke_artifacts.py --require-current-release-smokes
```

Use this for release uploads, package publication, tag movement, generated artifact mutation,
schema migration, or any action the current task forbids.

## When not to use PACK-SPEC

Do not use PACK-SPEC to:

- rewrite theory prose into legalistic syntax when no conformance surface exists;
- duplicate the full owner file inside `AGENTS.md` or `SKILL.md`;
- block tiny safe fixes with process theater;
- make noisy checkers that punish ordinary explanatory prose;
- replace Gemba inspection of the actual file, checker output, generated page, smoke output, or
  package artifact.
