"""Rubric for the `python-agent` example.

Shipyard runs this inside the same sandbox as the agent, with cwd = the eval
directory and the rubric input JSON on stdin (this rubric grades the
workspace only, and consumes stdin so the pipe closes). Environment:

    SHIPYARD_WORKDIR         the agent's working directory (workdir/)
    SHIPYARD_PASS_THRESHOLD  aggregate score needed to pass (default 1.0)
    SHIPYARD_ROLLOUTS_DIR    where the rollout writes its artifacts

It prints one JSON object (RubricsResult) on stdout and exits 0 when passed,
1 when not.
"""

import json
import os
import subprocess
import sys

# Probe: the slugify spec, as a table. It runs with cwd = the workdir so
# `from src.slugify import slugify` resolves.
BEHAVIOR_PROBE = r"""
import json, os, sys
workdir = sys.argv[1]
cases = [
    ("Hello World", "hello-world"),
    ("a  --  b", "a-b"),
    ("Hello? World!", "hello-world"),
    ("--hello--", "hello"),
    ("Shipyard v0.0.2!", "shipyard-v0-0-2"),
    ("!!!", ""),
    ("", ""),
]
try:
    # `shipyard validate` runs this rubric with --help before any sandbox
    # exists, so answer with a clean message — never an exception name. The
    # probe's stdout is scanned for load failures.
    if not os.path.isfile(os.path.join(workdir, "src", "slugify.py")):
        print(json.dumps({
            "ok": False,
            "detail": "no src/slugify.py under %s" % workdir,
        }))
        sys.exit(0)
    sys.path.insert(0, workdir)
    from src.slugify import slugify

    problems = []
    for text, expected in cases:
        got = slugify(text)
        if got != expected:
            problems.append("%r -> %r, expected %r" % (text, got, expected))
    detail = "; ".join(problems) if problems else "all %d cases matched" % len(cases)
    print(json.dumps({"ok": not problems, "detail": detail}))
except Exception as exc:  # noqa: BLE001 - any failure is a failed probe
    print(json.dumps({
        "ok": False,
        "detail": "importing src.slugify failed: %s: %s" % (type(exc).__name__, exc),
    }))
"""


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
    except Exception as exc:  # noqa: BLE001 - report anything as a failed probe
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


def run_unit_tests(workdir, timeout=60):
    """Run the workdir's own unittest suite with `sys.executable`."""
    if not os.path.isdir(os.path.join(workdir, "tests")):
        return False, f"no tests/ directory under {workdir}"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"unittest discover timed out after {timeout}s"
    except Exception as exc:  # noqa: BLE001
        return False, f"could not run unittest discover: {type(exc).__name__}: {exc}"

    if proc.returncode == 0:
        tail = (proc.stdout or "").strip().splitlines()
        return True, "python3 -m unittest discover -s tests passed" + (
            f" ({tail[-1]})" if tail else ""
        )
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, "unittest discover failed: " + (
        detail[-1] if detail else f"exit code {proc.returncode}"
    )


def score():
    try:
        json.load(sys.stdin)
    except Exception:  # noqa: BLE001 - an absent or non-JSON stdin is fine
        pass

    workdir = os.environ.get("SHIPYARD_WORKDIR", ".")
    threshold = float(os.environ.get("SHIPYARD_PASS_THRESHOLD", "1.0"))

    items = []

    ok, detail = run_probe(BEHAVIOR_PROBE, workdir)
    items.append({
        "name": "slugify_behavior",
        "score": 1.0 if ok else 0.0,
        "threshold": 1.0,
        "passed": ok,
        "description": detail,
    })

    ok, detail = run_unit_tests(workdir)
    items.append({
        "name": "unit_tests",
        "score": 1.0 if ok else 0.0,
        "threshold": 1.0,
        "passed": ok,
        "description": detail,
    })

    aggregate = sum(item["score"] for item in items) / len(items)
    passed = aggregate >= threshold

    result = {
        "eval_name": "python-agent",
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
