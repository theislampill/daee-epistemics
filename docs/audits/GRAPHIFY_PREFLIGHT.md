# Graphify Preflight - 2026-05-31

Status: `READY_NAVIGATION_ONLY`

Graphify is available for this repository as an ignored, local, read-only
navigation aid. It is not proof, not CI, not release evidence, not a checker
substitute, and not a runtime dependency.

## Install Detection

| Field | Result |
|---|---|
| PATH command | Not found by `Get-Command graphify` |
| Local command | `.daee/repo-graph/20260524-205010/venv/Scripts/graphify.exe` |
| Version | `graphify 0.8.18` |
| Python package location | local Graphify venv under `.daee/repo-graph/20260524-205010/venv/` |
| Repo config path | No project Graphify config file found |
| Cache/artifact roots | `.daee/repo-graph/`; `graphify-out/` |
| Hook/watch/MCP/Neo4j/CI integration | None detected; not installed or enabled |
| Update check | `pip index versions graphify` found no PyPI distribution; no update performed |

## Fresh Graph Build

A bounded local graph refresh was run against a copied tracked-file corpus under
`.daee/repo-graph/20260531-095400/code-corpus/`.

The corpus was built from `git ls-files`, so ignored/local-only directories such
as `.daee/`, `.release/`, `build/`, and `graphify-out/` were not copied from the
working tree into the corpus. The current dirty status at graph time was one
tracked audit-ledger file: `docs/audits/v0.4.3.0-open-work-ledger.md`.

| Field | Value |
|---|---|
| Graph timestamp | `20260531-095400` |
| Graph source HEAD | `ab4e5b3e01496ba90c928945249f2601edccb56f` |
| Branch | `main` |
| Worktree status rows at build | `1` |
| Tracked files at build | `957` |
| Indexed code files | `538` |
| Word count | `~238,435` |
| Nodes | `5320` |
| Edges | `4792` |
| Communities | `600` |
| Extraction | `100% EXTRACTED`, `0% INFERRED`, `0% AMBIGUOUS` |
| Token cost | `0 input`, `0 output` |
| HTML rendering | Skipped by Graphify because the graph exceeded the 5000-node HTML limit |

Command:

```powershell
.daee\repo-graph\20260524-205010\venv\Scripts\graphify.exe update .daee\repo-graph\20260531-095400\code-corpus --force
```

## Artifact Manifest

| Artifact | Size | SHA256 | Purpose |
|---|---:|---|---|
| `.daee/repo-graph/20260531-095400/graph.json` | `4251891` | `4BAF3D97BF426219EF2FD8E01C2D12FC71976DB97B1E0BCB35556CCF4139C33A` | Current navigation graph |
| `.daee/repo-graph/20260531-095400/GRAPH_REPORT.md` | `112939` | `71EB90A3F86CCB9EBB074F59CC27764581979E590BCA6E51EC6E8A8DE3AFEE55` | Current graph report |
| `.daee/repo-graph/20260531-095400/source-state.txt` | `156` | `344DC8D9533F6A1DC9E09F5497F57FACAC69FEF3DED94C014299A0A54C85007F` | Graph source-state record |

Prior useful graph artifacts remain available, but are stale against the current
HEAD:

| Artifact root | Notes |
|---|---|
| `.daee/repo-graph/20260524-205010/` | Original ledger-navigation spike; includes local Graphify venv |
| `.daee/repo-graph/20260531-040733/` | Earlier v0.4.3.5 relationship snapshot |
| `.daee/repo-graph/20260531-052658/` | Earlier docs/proofing action-map snapshot |
| `.daee/repo-graph/20260531-063824/` | Earlier refresh at commit `956ac9f7` with dirty 49-row source state |

## Exclusion / Secret Safety

The fresh corpus was copied from tracked files only. Ignored local-only paths
were not copied from the worktree. The tracked-file inventory had no exact
`.env`, private-key, database dump, or backup filename hits.

Strict secret-pattern scan over the fresh Graphify outputs returned no hits for
private-key blocks, AWS access-key shape, GitHub token shape, Slack token shape,
or OpenAI key shape.

Future Graphify rebuilds should continue to exclude:

- `.env*`
- private keys and certificates
- auth, cookie, and token dumps
- database dumps and backups
- `.daee/` except the selected output directory
- `.release/`
- `build/`
- `node_modules/`, vendor, cache, and runtime junk
- huge generated artifacts unless explicitly needed for a bounded audit

## Usage Decision

Codex/Hermes may consult:

- `.daee/repo-graph/20260531-095400/GRAPH_REPORT.md`
- `.daee/repo-graph/20260531-095400/graph.json`

Use them only for candidate links and navigation. Verify every claim with live
source files, checker files, fixture paths, smoke artifacts, hashes, command
results, or orchestrator evidence.

Do not use Graphify to prove runtime behavior, proof-corpus validity, Output
Grapher correctness, release readiness, docs truthfulness, package provenance,
or ledger row closure.
