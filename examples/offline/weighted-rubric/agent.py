#!/usr/bin/env python3
"""Deterministic reference agent for the `weighted-rubric` example.

It fixes two of the three bugs in `src/stats.py` and leaves the third, on
purpose: the rubric weights the three checks 0.4 / 0.4 / 0.2 and the eval’s
`pass_threshold` is 0.7, so the run passes with a visible 0.8 aggregate —
partial credit, demonstrated deterministically. See README.md.

No model, no API keys:

    SHIPYARD_WORKDIR=/tmp/copy-of-workdir python3 agent.py
"""

import os
import sys
from pathlib import Path

FIXED_SOURCE = '''\
"""Statistics helpers used by the reporting service."""


def mean(values):
    """Arithmetic mean of a list of numbers."""
    return sum(values) / len(values)


def median(values):
    """The middle value; for even counts, the mean of the two middle ones."""
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def mode(values):
    """The most frequent value; ties resolve to the smallest value."""
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    # Left unfixed on purpose: this example demonstrates partial credit.
    return max(counts, key=counts.get)
'''


def resolve_workdir() -> Path:
    """Find the workdir: $SHIPYARD_WORKDIR, else the eval's, else cwd."""
    env = os.environ.get("SHIPYARD_WORKDIR")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(Path(__file__).resolve().parent / "workdir")
    candidates.append(Path.cwd())
    for candidate in candidates:
        if (candidate / "src" / "stats.py").is_file():
            return candidate
    return Path(env) if env else Path.cwd()


def main() -> int:
    workdir = resolve_workdir()
    target = workdir / "src" / "stats.py"

    if not target.is_file():
        print(f"reference-agent: no src/stats.py under {workdir}", file=sys.stderr)
        return 1

    if target.read_text() == FIXED_SOURCE:
        print(f"reference-agent: {target} is already fixed; nothing to do")
        return 0

    target.write_text(FIXED_SOURCE)
    print("reference-agent: fixed mean() and median()")
    print("reference-agent: left mode()'s tie-breaking untouched (partial credit demo)")
    print("reference-agent: verify with python3 -m unittest discover -s tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
