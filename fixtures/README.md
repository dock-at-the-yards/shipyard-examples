# Fixtures

Committed sample results used by the gate and report examples.

`rollouts/` is run output and is gitignored; a fixture is the opposite — a
`results.json` (or a fragment of one) small enough to commit, stable enough
to assert on, and used where a live run would be slow or nondeterministic:

- `shipyard compare --candidate fixtures/<name>/results.json` — the delta
  gate against a known candidate, no run required;
- `shipyard report --results fixtures/<name>/results.json` — re-rendering a
  report from captured output.

Nothing has landed here yet; fixtures arrive with the examples that need
them.
