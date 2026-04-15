# Inference Boundary Markers

> role: diagnostic-governance
> use when: the response draws on more than one file, extends the file content, or risks overclaiming
> do not use when: every material claim is directly grounded and no metadiscursive marking is needed
> output: source-status labels that separate anchored skill content from model-added reasoning

This file governs the difference between what the repository says, what multiple files jointly
support, what the model is inferring, and what remains speculative.

## Marker Set

- `[anchored]` Directly grounded in a loaded file or in the explicit governing thesis of the skill.
- `[synthesis]` Drawn by combining multiple loaded files without adding a new thesis.
- `[inference]` A model-level inference extending beyond what the loaded files explicitly state.
- `[speculative]` A tentative extension, hypothesis, or extrapolation that should not govern the case unless confirmed.

## Rules

- Do not present `[inference]` or `[speculative]` material as though it were `[anchored]`.
- If a key move depends on `[synthesis]`, name the files or distinctions being joined.
- If a response depends materially on `[inference]`, state what evidence would confirm or weaken it.
- Reserve `[speculative]` for rare cases where the extension is useful enough to expose openly.
- If most of the case read would need `[inference]`, shrink the claim or mark the diagnosis underdetermined.

## Default Priority

Prefer this order when building a response:

1. `[anchored]`
2. `[synthesis]`
3. `[inference]`
4. `[speculative]`

The further down the list a claim sits, the more proportion, tentativeness, and explicit marking it requires.
