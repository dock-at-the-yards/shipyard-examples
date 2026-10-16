#!/usr/bin/env python3
"""Deterministic reference agent for the `python-agent` example.

It needs no model and no API keys: it reads $SHIPYARD_WORKDIR, rewrites
`src/slugify.py` with an implementation that satisfies the spec, and prints a
short summary. Running it twice is a no-op the second time, so repeats are
reproducible.

    SHIPYARD_WORKDIR=/tmp/copy-of-workdir python3 agent.py
"""

import os
import sys
from pathlib import Path

FIXED_SOURCE = '''\
"""Slug utilities used by the publishing pipeline."""

import re

_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn a title into a URL slug.

    Lowercases, collapses every run of non-slug characters into a single
    dash, and strips leading and trailing dashes.
    """
    return _NON_SLUG.sub("-", text.lower()).strip("-")
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
        if (candidate / "src" / "slugify.py").is_file():
            return candidate
    return Path(env) if env else Path.cwd()


def main() -> int:
    workdir = resolve_workdir()
    target = workdir / "src" / "slugify.py"

    if not target.is_file():
        print(f"reference-agent: no src/slugify.py under {workdir}", file=sys.stderr)
        return 1

    if target.read_text() == FIXED_SOURCE:
        print(f"reference-agent: {target} is already fixed; nothing to do")
        return 0

    target.write_text(FIXED_SOURCE)
    print(f"reference-agent: rewrote {target} with a spec-compliant slugify")
    print("reference-agent: verify with python3 -m unittest discover -s tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
