# verdict

- fixture class: hard
- final classification: hard-pass
- status: PASS
- output bytes: 23712
- burden-cycle count: 3
- depth is runtime-licensed: runtime-licensed hard depth
- fixture-contamination terms detected: no
- static render/governance expectation: output.md must pass render, recursive, and smoke-artifact checker functions
- common-sense audit result: PASS: hard fixture meets depth, no contamination, no boilerplate, no fake recursion, and burden transitions are materially different
- fail if: scaffold/test language appears in output.md, fixture-specific language leaks across families, TTPs are named without operation, state re-read lacks claim-state change, or a hard fixture is under 20 KB.
