"""Statistics helpers used by the reporting service.

Three functions, three known bugs. See instruction.md for the spec they are
supposed to satisfy and tests/test_stats.py for the cases that fail today.
"""


def mean(values):
    """Arithmetic mean of a list of numbers."""
    # BUG 1: floored to an integer — looks fine for whole-number inputs.
    return sum(values) // len(values)


def median(values):
    """The middle value; for even counts, the mean of the two middle ones."""
    ordered = sorted(values)
    # BUG 2: ignores the two-middle-values case for even counts.
    return ordered[len(ordered) // 2]


def mode(values):
    """The most frequent value; ties resolve to the smallest value."""
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    # BUG 3: ties resolve to whichever value was seen first, not the smallest.
    return max(counts, key=counts.get)
