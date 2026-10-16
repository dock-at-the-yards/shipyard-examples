# Negative examples

Deliberately broken evals, one per failure mode. Unlike everything else in
this repo, these are *supposed to fail*.

Each case is a directory containing the broken eval (or the fragment of one)
and a `case.json` describing what must happen when the CLI touches it:

```json
{
  "command": "validate",
  "args": [],
  "expect_exit": 1,
  "expect_message": "instruction"
}
```

| Field | Meaning |
|---|---|
| `command` | `validate` or `run` |
| `args` | Extra CLI arguments, in order. |
| `expect_exit` | The exit code the command must produce. |
| `expect_message` | A regular expression the combined output must match. |

`scripts/e2e.sh --tier negative` runs every case, asserts the expected
failure, and fails when a case fails *differently* — or stops failing at
all. That is how the CLI's error paths are tested end to end. The error-code
directory in the documentation site is the checklist for what to write next.

No cases have landed yet.
