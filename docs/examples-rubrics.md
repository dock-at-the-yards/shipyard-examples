# Rubrics & Gates

## The rubric contract

`[tests]` in `eval.toml` names the rubric and the pass mark:

```toml
[tests]
rubric = "tests/rubric.py"
entrypoint = "score"
pass_threshold = 1.0
```

The rubric runs inside the same sandbox the agent ran in, with cwd set to
the eval directory, and prints **one JSON object** on stdout:

```json
{
  "eval_name": "python-agent",
  "items": [
    {
      "name": "slugify_behavior",
      "score": 1.0,
      "threshold": 1.0,
      "passed": true,
      "description": "all 7 cases matched"
    }
  ],
  "aggregate_score": 1.0,
  "passed": true
}
```

Alongside `[tests]`, Shipyard provides three environment variables:

| Variable | Meaning |
| :--- | :--- |
| `SHIPYARD_WORKDIR` | The agent's workspace (the eval's `workdir/`). |
| `SHIPYARD_PASS_THRESHOLD` | The configured pass mark, so the rubric and the manifest cannot disagree silently. |
| `SHIPYARD_ROLLOUTS_DIR` | The current rollout directory. |

A rubric that ignores its stdin and grades only the workspace keeps working
forever; a rubric that asserts on tool calls and the conversation reads the
rollout JSON from **stdin** (keys `tool_calls` and `conversation`).

## Pattern: workspace assertions

[`python-agent`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/python-agent)
is the worked example: one table-driven probe imports the fixed module and
runs the spec's cases, one runs the workspace's own unittest suite, and the
two items average into the aggregate. Every probe answers with a clean
message when the workspace is absent, because `shipyard validate` runs the
rubric before any sandbox exists — that probe is what catches a broken rubric
before tokens are spent.

## Pattern: weighted items and partial credit

The rubric *is* the aggregation function, so weights live in the rubric —
not in the item schema. [`weighted-rubric`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/weighted-rubric)
weights three checks `0.4 / 0.4 / 0.2`, and its reference agent deliberately
fixes only the first two. The aggregate lands at `0.80` against a
`pass_threshold` of `0.7`: the run passes, `rubrics.json` still shows the
failed item, and the score is real — partial work, partial credit,
deterministically.

## Repeats and statistics

`--repeat K` (or `repeat =` in the manifest) runs each eval K times and
aggregates: `pass@k`, `pass^k`, mean and sigma, and flake detection. The
per-repeat artifacts live in `repeat-1/` … `repeat-K/` under the rollout,
with the suite-level `results.json` and `aggregate.json` at the run root. A
flake — repeats that disagree — is visible in both the verdict and the gate.

## Baselines and the compare gate

A baseline is a committed `baselines/<name>.json` taken from a completed run:

```bash
shipyard baseline save . --name main    # from the newest run under rollouts/
shipyard compare .                      # newest run vs baselines/main.json
```

`compare` labels every eval `improved | same | regressed | flaked | errored`
and exits:

| Exit | Meaning |
| :--- | :--- |
| `0` | Gate passed — no regressions, flakes, or infra errors. |
| `1` | Gate blocked. |
| `2` | Usage error (suite mismatch without `--allow-suite-mismatch`, missing inputs). |

The baseline records the suite digest it was taken from; comparing a
different suite is refused unless you pass `--allow-suite-mismatch`. Only
`main` regenerates baselines — the workflow enforces that rule, not the
command.

## Gate policy

What `compare` treats as blocking is the `[gate]` block, written out in the
examples rather than left implicit:

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `max_score_drop_pct` | `2.0` | Score-drop budget; negative disables score gating. |
| `max_cost_increase_pct` | `0` | Cost gate; `0` is off. |
| `block_on_flake` | `true` | Block when repeats disagree. |
| `min_k_noise_floor` | `3` | With k ≥ 3, a drop must exceed both the budget and the 95% t-interval noise margin. |
| `confidence` | `0.95` | Confidence level for that interval. |

Infra errors fail closed and are labeled `infra`; a pass → fail flip always
blocks.

## Reports

`run --report markdown,json,junit` writes reports next to the rollout, and
`shipyard report <path>` re-renders them from an existing `results.json` — so
running and reporting can be separate CI jobs:

```bash
shipyard report . --format markdown,json,junit --out reports/
```
