# Examples

Every directory here is a self-contained evaluation: an `eval.toml` manifest,
an instruction for the agent, a workspace, and a rubric. Examples are grouped
by the infrastructure each one needs, so `scripts/e2e.sh --tier <name>` maps
exactly onto what CI can run.

| Tier | Needs | Runs in CI |
|---|---|---|
| [`offline/`](offline/) | `python3` | every push |
| [`node/`](node/) | Node.js ≥ 20 | every push |
| [`docker/`](docker/) | A Docker daemon | every push |
| [`keys/`](keys/) | A provider API key | `workflow_dispatch` with secrets |
| [`harness/`](harness/) | The CLI agent on `PATH` | `workflow_dispatch` with secrets |

## Anatomy of an example

```
<example>/
├── eval.toml            # the manifest: agent, environment, tests, gate
├── instruction.md       # the prompt the agent receives
├── agent.py             # deterministic reference agent (where the tier allows)
├── tests/rubric.py      # the scorer: prints one RubricsResult JSON object
├── workdir/             # the agent's workspace (restored after each run)
├── baselines/           # optional: committed baselines for `compare`
└── README.md            # tier, plugin, environment, needs, how to run
```

## Adding one

- Keep it deterministic when the tier allows — that is what makes it gatable.
- Add a `README.md` next to `eval.toml`: tier, plugin, environment, what it
  needs, and how to look at the result.
- If it needs a key or endpoint, add the variable to the top-level
  `.env.example`.
- Run `scripts/e2e.sh --tier <tier>` before opening the PR; CI runs the same
  script.
