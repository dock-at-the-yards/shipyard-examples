# python-agent

**Tier:** offline · **Plugin:** `python` · **Environment:** `local` · **Needs:** `python3`

The smallest complete loop: a deterministic agent script edits the workspace,
a rubric scores the workspace, and the verdict lands in `rollouts/`. No model,
no API keys, no Docker — which is what makes it a test you can gate on.

```bash
shipyard validate .   # static lint: manifests, paths, rubric probe
shipyard run .        # the reference agent fixes src/slugify.py
```

## What to look at

| File | Why |
|---|---|
| `eval.toml` | The whole manifest: one `[[agent]]`, a `local` environment, one rubric. |
| `agent.py` | The `python` plugin contract: Shipyard runs `python3 agent.py` and the script edits `$SHIPYARD_WORKDIR`. |
| `tests/rubric.py` | The workspace-assertion pattern: a table-driven behavior probe plus the workdir's own unit tests. |
| `rollouts/<run-id>/` | `results.json`, `rubrics.json`, `run.json` — the run's artifacts. |

The workspace is restored when the run finishes. To inspect the agent's
changes instead, run with `--keep-workdir`.

## Swapping the subject agent

The reference agent exists so the example runs offline; the eval itself is
agent-agnostic. Point it at a real harness without editing anything:

```bash
shipyard run . --agent claude-code
```
