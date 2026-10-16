# Examples

One runnable example per Shipyard feature. Every example is a complete
evaluation — a manifest, an instruction, an agent, a workspace, and a rubric —
that you can point `shipyard run` at without editing anything first.

The examples live in the public
[`shipyard-examples`](https://github.com/dock-at-the-yards/shipyard-examples)
repository. This whole section is imported from that repository's `docs/`
directory when the site is built — there is no second copy to keep in sync.

## Tiers

Examples are grouped by the infrastructure each one needs, which is also how
CI runs them:

| Tier | Needs | Demonstrates | In CI |
| :--- | :--- | :--- | :--- |
| `examples/offline/` | `python3` | Deterministic agents and rubrics — no model, no API keys, no Docker. | Every push. |
| `examples/node/` | Node.js ≥ 20 | The `javascript`, `typescript`, and `langchain-js` runtimes. | Every push. |
| `examples/docker/` | A Docker daemon | Dockerfile builds, pinned images, persistent sandboxes, custom environments. | Every push. |
| `examples/keys/` | A provider API key | Real LLM agents: `openai`, `anthropic`, `gemini`, `deepseek`, `ollama`, `opencode-api`, and the Remote VPC worker protocol. | Manual (`workflow_dispatch`) — runs spend money. |
| `examples/harness/` | A CLI agent on `PATH` | `claude-code`, `codex`, `opencode`, `gemini-cli`, `aider`. | Manual (`workflow_dispatch`) — runs spend money. |

The deliberately broken evals in `negative/` are the other half of the suite:
one per failure mode, each with the exact failure it must produce. They are
meant to fail.

## The loop every example teaches

Every example is runnable as its own target, and the same four commands work
on all of them:

```bash
shipyard validate .   # static lint: manifests, paths, rubric probe — no containers
shipyard run .        # execute the agent inside the sandbox, then score it
shipyard compare .    # gate the newest run against the committed baseline
shipyard report .     # re-render markdown / JSON / JUnit from the rollout
```

## What ships today

| Example | Tier | Demonstrates |
| :--- | :--- | :--- |
| [`python-agent`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/python-agent) | offline | The `python` runtime plugin in a `local` environment, scored by a workspace rubric. |
| [`weighted-rubric`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/weighted-rubric) | offline | Weighted rubric items, `pass_threshold < 1.0` (partial credit), and a committed baseline gated with `compare`. |

The suite grows with each release. [`examples/README.md`](https://github.com/dock-at-the-yards/shipyard-examples/blob/main/examples/README.md)
records the layout rules every new example follows.

## One version, pinned

`VERSION` in the examples repository names the CLI release it is validated
against, and CI installs exactly that binary (`v0.0.2` today) before running
the hermetic tiers. The repository is released in lockstep with the CLI: the
same `vX.Y.Z` tag is cut on both, and this documentation section is imported
from that tag.
