# harness

**Needs:** The CLI agent installed and on `PATH`.

Examples for the process & CLI plugins: `claude-code`, `codex`, `opencode`,
`gemini-cli`, and `aider`. Like the `keys/` tier these cost money and are
non-deterministic, so CI runs them only via `workflow_dispatch` with secrets.
Name the tier explicitly; `--tier all` never includes it.
