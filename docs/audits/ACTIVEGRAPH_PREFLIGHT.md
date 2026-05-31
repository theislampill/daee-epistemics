# ActiveGraph Preflight - 2026-05-31

Status: `READY_EXPERIMENTAL_SIDECAR`

ActiveGraph is owner-approved for bounded local IMPLEMENTAUDIT provenance
experiments. It is installed only in ignored `.daee` scratch space and is not a
runtime, CI, package, release, provenance, or canonical-ledger dependency.

## Detection

| Field | Result |
|---|---|
| PATH command | `activegraph` not found |
| Current Python environment | `activegraph` not installed |
| Graphify venv | `activegraph` not installed |
| Global npm package | no `activegraph` package detected |
| Isolated install path | `.daee/activegraph/20260531-095847/venv/` |
| Installed version | `activegraph 1.0.5.post2` |
| Repo-local service/path | none detected |
| User-profile state path | no obvious `.activegraph` / ActiveGraph directory detected |
| Config/state/event-log path | `.daee/activegraph/20260531-095847/scratch/implementaudit-preflight.sqlite` |
| Graph storage path | same SQLite scratch database |
| Runtime/CI/release hook | none detected |

## Install / Smoke Result

ActiveGraph was installed into an isolated ignored venv:

```powershell
python -m venv .daee\activegraph\20260531-095847\venv
.daee\activegraph\20260531-095847\venv\Scripts\python.exe -m pip install activegraph==1.0.5.post2
.daee\activegraph\20260531-095847\venv\Scripts\activegraph.exe --version
```

Installed dependencies:

```text
activegraph==1.0.5.post2
annotated-types==0.7.0
click==8.4.1
colorama==0.4.6
pydantic==2.13.4
pydantic_core==2.46.4
typing-inspection==0.4.2
typing_extensions==4.15.0
```

A scratch IMPLEMENTAUDIT event run was created in SQLite:

| Field | Value |
|---|---|
| Run ID | `implementaudit_preflight` |
| Objects | `2` |
| Relations | `1` |
| Events | `4` |
| Event types | `object.created`, `object.created`, `relation.created`, `runtime.idle` |
| Replay result | loaded graph returned `2` objects, `1` relation, `4` events |
| CLI inspect result | run state `idle`, queue depth `0`, events processed `4` |

Artifacts:

| Artifact | SHA256 |
|---|---|
| `.daee/activegraph/20260531-095847/install-state.txt` | `D790256044DF42305D8309E709F5BD553769330FFC1FEBF630AC1F181D0F3968` |
| `.daee/activegraph/20260531-095847/scratch/implementaudit-preflight.sqlite` | `68092258C7DB04CF60B7954586416F7EC0493417971F89641E05DEB2B9395EDD` |
| `.daee/activegraph/20260531-095847/scratch/smoke-output.txt` | `88B86A0A48276BEA6DFF2CB501CB32BA94C2E50B5C16DF7902947F738F220F02` |
| `.daee/activegraph/20260531-095847/scratch/inspect-output.txt` | `809D2742ECE3CE118C9A8A59919F3F6B9654E54AADEE0D015CD8FE4E9DEDAD1E` |
| `.daee/activegraph/20260531-095847/scratch/trace.jsonl` | `4CEEAB660A0301800163EC54E5AC10B03F94261228EA28E1EAC00F034E05D631` |

## Classification

`READY_EXPERIMENTAL_SIDECAR`

ActiveGraph may be used for bounded local sidecar events during future
IMPLEMENTAUDIT runs when explicitly authorized. It should record provenance
metadata and dependency edges only; it must not replace checker evidence or the
Markdown proof ledger.

## Boundaries

- Do not make ActiveGraph the canonical ledger.
- Do not migrate the orchestrator into ActiveGraph.
- Do not add a daemon, service, hook, CI step, release gate, or runtime
  dependency.
- Do not treat ActiveGraph events as proof of behavior.
- Do not write subagent cleanup or D.8 closure events until D.8 has explicit
  ID-level owner approval.
