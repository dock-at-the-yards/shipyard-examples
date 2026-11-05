"""Slug utilities used by the publishing pipeline.

This is the file the agent is asked to fix. The placeholder below is the
naive version that was shipped first: it replaces spaces but does not
lowercase, collapse runs, or strip edges — see instruction.md for the spec
the fix has to satisfy.
"""


def slugify(text: str) -> str:
    """Turn a title into a URL slug."""
    return text.replace(" ", "-")
