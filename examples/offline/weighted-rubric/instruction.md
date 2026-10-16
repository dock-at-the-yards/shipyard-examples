# Fix the reporting service's three statistics bugs

`src/stats.py` backs the reporting service. Three functions are wrong;
`tests/test_stats.py` has the failing cases.

## The spec

| Function | Requirement |
|---|---|
| `mean(values)` | The arithmetic mean, not floored: `mean([1, 2, 4]) == 7/3`. |
| `median(values)` | The middle value; for **even** counts, the mean of the two middle ones: `median([1, 2, 3, 4]) == 2.5`. |
| `mode(values)` | The most frequent value; **ties resolve to the smallest value**: `mode([3, 1, 3, 1]) == 1`. |

## Your task

Fix all three, and keep the public API unchanged:
`from src.stats import mean, median, mode`.

## Definition of done

- `python3 -m unittest discover -s tests` passes from your working directory.
- Each function satisfies the spec table, including the even-count median and
  the tied mode.
