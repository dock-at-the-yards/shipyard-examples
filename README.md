# Shipyard Examples ⚓

One runnable example per Shipyard feature.

Every directory under `examples/` is a real evaluation you can point
`shipyard run` at today — nothing to fill in first. Examples are grouped by
the infrastructure each one needs, which is also how CI runs them:

| Tier | What it needs | What it demonstrates |
| :--- | :--- | :--- |
| [`examples/offline/`](examples/offline) | `python3` | Deterministic agents and rubrics. No model, no API keys, no Docker. |
| [`examples/node/`](examples/node) | Node.js ≥ 20 | The `javascript`, `typescript`, and `langchain-js` runtimes. |
| [`examples/docker/`](examples/docker) | A Docker daemon | Dockerfile builds, pinned images, persistent sandboxes, custom environments. |
| [`examples/keys/`](examples/keys) | A provider API key | Real LLM agents: `openai`, `anthropic`, `gemini`, `deepseek`, `ollama`, `opencode-api`, and the Remote VPC worker protocol. |
| [`examples/harness/`](examples/harness) | A CLI agent on `PATH` | `claude-code`, `codex`, `opencode`, `gemini-cli`, `aider`. |
| [`negative/`](negative) | nothing extra | Deliberately broken evals, one per failure mode, with the exact error code each must produce. They are meant to fail. |

---

## Quick start

```bash
# Install the CLI (macOS / Linux). This repo is validated against the release
# named in VERSION, currently v0.0.2.
curl -fsSL https://raw.githubusercontent.com/dock-at-the-yards/shipyard-cli/main/install.sh | sh

# Pick an example and lint it before anything runs. `validate` is static:
# no containers, no tokens, no spend.
cd examples/offline/python-agent
shipyard validate .

# Run it. The offline tier needs only python3: no Docker, no keys.
shipyard run .
```

The rollout lands under the example's `rollouts/` directory (`run.json`,
`results.json`, the rubric's itemized verdict). One line below shows the
same loop on an evalset with repeats, a committed baseline, and the delta
gate:

```bash
shipyard run examples/offline/expected-failure --repeat 3
shipyard compare examples/offline/expected-failure
```

## Repository layout

```
examples/
  offline/           deterministic — python3 only, no keys, no Docker
  node/              Node.js runtimes (javascript, typescript, langchain-js)
  docker/            Docker sandboxes (dockerfile, image, persistent, custom)
  keys/              real LLM providers (spends money; workflow_dispatch only)
  harness/           CLI coding agents (needs the agent installed)
negative/            deliberately broken evals; the expected error code is
                     documented per case
docs/                the pages shipyard-web imports for the site's Examples
                     section — single source, never copied
scripts/
  docs-check.py      validates docs/manifest.json and every link it carries
                     (the build-time import contract)
  e2e.sh             runs every example of a tier against a real binary
  validate-static.sh manifest / path / fixture / compile checks — what CI's
                     static job runs
fixtures/            committed sample results for gate and report demos
```

## Running the whole suite

`scripts/e2e.sh` is the end-to-end runner. It copies each example to a temp
directory, runs it against a real `shipyard` binary, and asserts on exit
codes and artifacts — the repo tree stays clean.

```bash
SHIPYARD_BIN=/path/to/shipyard scripts/e2e.sh --tier offline

# `all` is offline + node + docker — the hermetic tiers. The keys/ and
# harness/ tiers spend money, so they are never implied; name them.
scripts/e2e.sh --tier all
scripts/e2e.sh --tier keys
```

A tier whose prerequisites are missing is skipped with a notice when it is
part of `all`, and is a hard error when named explicitly.

## Versioning

`VERSION` names the Shipyard CLI release this repo is validated against, and
`shipyard-examples` is released in lockstep with `shipyard-cli` and
`shipyard-web`: the same `vX.Y.Z` tag is cut on all three during a release
wave. CI installs the released binary for `v$(cat VERSION)` and runs the
hermetic tiers against it, so a tag means "these examples were exercised
against this CLI release". The docs site imports the pages under `docs/`
from that same tag.

## Repositories in the Shipyard family

| Repository | Visibility | Role |
| :--- | :--- | :--- |
| [`shipyard-core`](https://github.com/dock-at-the-yards/shipyard-core) | private | The evaluation engine and sandbox implementations. |
| [`shipyard-cli`](https://github.com/dock-at-the-yards/shipyard-cli) | public | The `shipyard` binary, commands, and release pipeline. |
| [`shipyard-ci`](https://github.com/dock-at-the-yards/shipyard-ci) | public | Reusable CI templates that gate evals in GitHub Actions, Argo, Jenkins, and GitLab. |
| **`shipyard-examples`** (this repo) | public | One runnable example per feature, kept green end to end. |
| [`shipyard-registry`](https://github.com/dock-at-the-yards/shipyard-registry) | private | Pre-made evalsets and reference agents. |
| [`shipyard-web`](https://github.com/dock-at-the-yards/shipyard-web) | private | The documentation site. |

## License

Source-available; see [LICENSE](LICENSE).
