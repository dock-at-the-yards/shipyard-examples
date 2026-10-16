# offline

**Needs:** `python3`. No Docker, no API keys, no network. This is the tier
that gates every push.

| Example | Demonstrates |
|---|---|
| [`python-agent`](python-agent/) | The `python` runtime plugin and the `local` environment: a deterministic agent script edits the workspace and a rubric scores it. |
| [`weighted-rubric`](weighted-rubric/) | Weighted rubric items, `pass_threshold < 1.0` (partial credit), and the committed-baseline `compare` gate. |

```bash
scripts/e2e.sh --tier offline
```
