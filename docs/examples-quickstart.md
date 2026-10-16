# Running the Examples

## 1. Install the CLI

The examples are validated against the release named in the repository's
`VERSION` file — `v0.0.2` today. The installer's `stable` channel serves that
same release:

```bash
curl -fsSL https://raw.githubusercontent.com/dock-at-the-yards/shipyard-cli/main/install.sh | sh
shipyard version
```

To pin the exact release this repository names:

```bash
curl -fsSL https://raw.githubusercontent.com/dock-at-the-yards/shipyard-cli/main/install.sh \
  | sh -s -- --version v0.0.2
```

Then clone the examples:

```bash
git clone https://github.com/dock-at-the-yards/shipyard-examples
cd shipyard-examples
```

## 2. Lint before you run

`validate` is static: it parses every manifest, resolves every referenced
file, sanity-checks the gate policy, and probes the rubric — no container
starts and no tokens are spent.

```bash
cd examples/offline/python-agent
shipyard validate .
```

## 3. Run it

```bash
shipyard run .
```

The offline tier needs only `python3` — no Docker, no API keys — and the
reference agent is deterministic, so this is also what CI gates on. The run
writes a rollout under `rollouts/<run-id>/` (`--run-name` picks the id):

| File | Contents |
| :--- | :--- |
| `results.json` | Suite totals: verdicts, scores, k, digests. |
| `metrics.json` | Verdict, usage, timing for the eval. |
| `rubrics.json` | The rubric's itemized scoring result. |
| `run.json` | Provenance: what produced the score. |
| `trajectory.json` | The agent's steps in ATIF form. |

The workspace is restored after the run. To inspect the agent's changes
instead, run with `--keep-workdir`.

## 4. Swap the subject agent

The deterministic reference agent exists so the example runs offline; the
eval itself is agent-agnostic. Point it at a real harness without editing
anything:

```bash
shipyard run . --agent claude-code
```

`--model` and `--provider` do the same for the LLM plugins, and `--command`
replaces the entrypoint. Runtime overrides win over `eval.toml`.

## 5. Gate a change against the baseline

`weighted-rubric` commits a baseline, so the full loop is visible in three
commands:

```bash
cd ../weighted-rubric
shipyard run .          # 0.80 — two of the three bugs are fixed on purpose
shipyard compare .      # delta table vs baselines/main.json; exit 0 when the gate passes
shipyard report .       # markdown / json / junit rendering of the same rollout
```

## Which tier do I need?

| You want to… | Use |
| :--- | :--- |
| Try anything with no setup | `examples/offline/` |
| Exercise the Node.js runtimes | `examples/node/` (Node.js ≥ 20) |
| Exercise sandboxing | `examples/docker/` (Docker running) |
| Exercise a real LLM | `examples/keys/` (a provider key in `.env`) |
| Exercise a coding agent | `examples/harness/` (the agent installed) |

## Running the whole suite locally

`scripts/e2e.sh` copies each example to a temp directory, runs it against a
real binary, and asserts on exit codes and artifacts — the repository tree
stays clean:

```bash
SHIPYARD_BIN=/path/to/shipyard scripts/e2e.sh --tier offline

# `all` is the hermetic tiers — offline, node, docker, negative. The paid
# tiers are never implied; name them, with their keys exported.
scripts/e2e.sh --tier all
scripts/e2e.sh --tier keys
```

A tier whose prerequisites are missing is skipped with a notice when it is
part of `all`, and is a hard error when named explicitly.
