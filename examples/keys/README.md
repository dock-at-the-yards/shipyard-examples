# keys

**Needs:** A provider API key (see the top-level `.env.example`).

Examples for the real LLM plugins — `openai`, `anthropic`, `gemini`,
`deepseek`, `ollama`, `opencode-api` — and the Remote VPC worker protocol
(`remote`). These run spend money and their outputs vary between runs, so CI
runs them only via `workflow_dispatch` with secrets, and `scripts/e2e.sh
--tier all` never includes them: name the tier explicitly.
