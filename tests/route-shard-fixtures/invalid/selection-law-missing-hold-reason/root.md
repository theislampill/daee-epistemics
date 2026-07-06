# Fixture Root

Preamble text unrelated to the addendum.

Load path for substantive cases:

1. `references/runtime-core-routing.md`

Dispatch Index (route shards - load on selection, not eagerly):

| trigger signal | shard | load when |
| --- | --- | --- |
| trigger one | `references/runtime-shard-alpha.md` | when alpha fires |
| trigger two | `references/runtime-shard-beta.md` | when beta fires |

Selection law:

- Load one shard when the trigger is unambiguous.
- If still ambiguous, load ALL candidate shards (cap 3) or route HOLD/PARTIAL with reason
  `route-ambiguous`.
- Live pressure with 0 candidate shards means route HOLD/PARTIAL with reason
  `owner-not-available`.
- Record `shards_loaded` in the state capsule when available.

Known aliases (OSM discipline - same surface never means same hidden state):

- Surface "source" aliases source-order vs authority-order vs hidden-support.
- "definition-discipline" is a route label, not a callable operation unless mapped.
- proof-method-audit applies only when the tribunal/burden role is body-backed.

Use `references/omnibus/*.md` only after V1, Phase 2, and the Diagnostic IR authorize the original source module owner.

Trailer text unrelated to the addendum.
