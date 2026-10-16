"""Rubric for the `weighted-rubric` example.

Three independent checks, each worth 1.0 on its own, combined by the rubric
into a *weighted* aggregate:

    mean    0.4
    median  0.4
    mode    0.2

`eval.toml` sets `pass_threshold = 0.7`, and the reference agent fixes mean
and median but not mode — so the aggregate is 0.8 and the run passes. That is
the pattern this example exists to show: item weights live in the rubric, the
pass mark lives in the manifest, and partial work gets partial credit.

Shipyard runs the rubric with cwd = the eval directory and the input JSON on
stdin; this rubric grades the workspace only (and consumes stdin so the pipe
closes):

    SHIPYARD_WORKDIR         the agent's working directory (workdir/)
    SHIPYARD_PASS_THRESHOLD  aggregate score needed to pass (0.7 here)
    SHIPYARD_ROLLOUTS_DIR    where the rollout writes its artifacts

It prints one JSON object (RubricsResult) on stdout and exits 0 when passed,
1 when not.
"""

import json
import os
import subprocess
import sys

# Every probe grades one function against the spec in instruction.md, and
# answers with a clean message (never an exception name) when the workspace
# is absent — `shipyard validate` runs the rubric before any sandbox exists.

MEAN_PROBE = r"""
import json, os, sys
workdir = sys.argv[1]
if not os.path.isfile(os.path.join(workdir, "src", "stats.py")):
    print(json.dumps({"ok": False, "detail": "no src/stats.py under %s" % workdir}))
    sys.exit(0)
try:
    sys.path.insert(0, workdir)
    from src.stats import mean

    problems = []
    cases = [([1, 2, 4], 7 / 3), ([5], 5.0), ([2, 3], 2.5)]
    for values, expected in cases:
        got = mean(values)
        if abs(got - expected) > 1e-9:
            problems.append("mean(%r) = %r, expected %r" % (values, got, expected))
    detail = "; ".join(problems) if problems else "all %d cases matched" % len(cases)
    print(json.dumps({"ok": not problems, "detail": detail}))
except Exception as exc:  # noqa: BLE001
    print(json.dumps({
        "ok": False,
        "detail": "importing src.stats failed: %s: %s" % (type(exc).__name__, exc),
    }))
"""

MEDIAN_PROBE = r"""
import json, os, sys
workdir = sys.argv[1]
if not os.path.isfile(os.path.join(workdir, "src", "stats.py")):
    print(json.dumps({"ok": False, "detail": "no src/stats.py under %s" % workdir}))
    sys.exit(0)
try:
    sys.path.insert(0, workdir)
    from src.stats import median

    problems = []
    cases = [([7, 1, 3], 3), ([1, 2, 3, 4], 2.5), ([4, 3, 2, 1], 2.5)]
    for values, expected in cases:
        got = median(values)
        if got != expected:
            problems.append("median(%r) = %r, expected %r" % (values, got, expected))
    detail = "; ".join(problems) if problems else "all %d cases matched" % len(cases)
    print(json.dumps({"ok": not problems, "detail": detail}))
except Exception as exc:  # noqa: BLE001
    print(json.dumps({
        "ok": False,
        "detail": "importing src.stats failed: %s: %s" % (type(exc).__name__, exc),
    }))
"""

MODE_PROBE = r"""
import json, os, sys
workdir = sys.argv[1]
if not os.path.isfile(os.path.join(workdir, "src", "stats.py")):
    print(json.dumps({"ok": False, "detail": "no src/stats.py under %s" % workdir}))
    sys.exit(0)
try:
    sys.path.insert(0, workdir)
    from src.stats import mode

    problems = []
    cases = [([2, 2, 1], 2), ([3, 1, 3, 1], 1), ([5], 5)]
    for values, expected in cases:
        got = mode(values)
        if got != expected:
            problems.append("mode(%r) = %r, expected %r" % (values, got, expected))
    detail = "; ".join(problems) if problems else "all %d cases matched" % len(cases)
    print(json.dumps({"ok": not problems, "detail": detail}))
except Exception as exc:  # noqa: BLE001
    print(json.dumps({
        "ok": False,
        "detail": "importing src.stats failed: %s: %s" % (type(exc).__name__, exc),
    }))
"""

# Item weights. The rubric contract has no `weight` field — the rubric *is*
# the aggregation function, so the weights are this table and the aggregate
# is computed from it below.
WEIGHTS = {
    "mean": 0.4,
    "median": 0.4,
    "mode": 0.2,
}


def run_probe(script, workdir, timeout=60):
    """Run a probe subprocess and parse its JSON verdict; never raises."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script, workdir],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"probe timed out after {timeout}s"
    except Exception as exc:  # noqa: BLE001
        return False, f"could not run probe: {type(exc).__name__}: {exc}"

    output = (proc.stdout or "").strip()
    if not output:
        tail = (proc.stderr or "").strip().splitlines()
        return False, "probe produced no verdict: " + (
            tail[-1] if tail else f"exit code {proc.returncode}"
        )
    try:
        verdict = json.loads(output.splitlines()[-1])
    except Exception as exc:  # noqa: BLE001
        return False, f"probe output was not JSON ({type(exc).__name__}): {output[:300]}"
    return bool(verdict.get("ok")), str(verdict.get("detail", ""))


def score():
    try:
        json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        pass

    workdir = os.environ.get("SHIPYARD_WORKDIR", ".")
    threshold = float(os.environ.get("SHIPYARD_PASS_THRESHOLD", "1.0"))

    items = []
    for name, probe in (("mean", MEAN_PROBE), ("median", MEDIAN_PROBE), ("mode", MODE_PROBE)):
        ok, detail = run_probe(probe, workdir)
        items.append({
            "name": name,
            "score": 1.0 if ok else 0.0,
            "threshold": 1.0,
            "passed": ok,
            "description": f"weight {WEIGHTS[name]}: {detail}",
        })

    aggregate = sum(item["score"] * WEIGHTS[item["name"]] for item in items)
    passed = aggregate >= threshold

    result = {
        "eval_name": "weighted-rubric",
        "items": items,
        "aggregate_score": round(aggregate, 2),
        "passed": passed,
    }

    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    # `shipyard validate` probes the rubric with `--help`; answer cleanly
    # instead of running the scoring path.
    if "--help" in sys.argv[1:]:
        print(__doc__)
        raise SystemExit(0)
    sys.exit(score())
