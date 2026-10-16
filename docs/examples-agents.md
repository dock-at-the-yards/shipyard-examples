# Agent Plugins

The subject of an evaluation is declared as one or more `[[agent]]` blocks in
`eval.toml`. Every example is built the same way — a plugin, optionally an
entrypoint or command, and a role:

```toml
[[agent]]
name = "reference-agent"
role = "target"
plugin = "python"
entrypoint = "agent.py"
```

`role` is `target`, `assistant`, or `critic`, and multiple blocks compose
multi-agent workflows. The plugin names below are the complete built-in set.

## The plugin families

| Family | Plugins | What actually runs |
| :--- | :--- | :--- |
| Runtime | `python`, `javascript`, `typescript`, `custom` | A script in the eval directory, executed inside the sandbox. |
| LLM APIs | `api`, `openai`, `anthropic`, `gemini`, `deepseek`, `ollama`, `opencode-api` | A model conversation driven through the provider's API. |
| CLI harnesses | `cli`, `claude-code`, `codex`, `opencode`, `gemini-cli`, `aider` | An executable already installed in the environment. |
| Frameworks | `langchain`, `langgraph`, `pydantic-ai`, `langchain-js` | A framework adapter entrypoint. |
| Remote | `remote`, `bridge`, `vpc-agent` | A rollout executed by a worker over the Remote Agent Protocol. |

## The runtime plugins, up close

Runtime plugins are how the offline tier stays deterministic: a script reads
its workspace from `$SHIPYARD_WORKDIR`, does its work, and exits — no model,
no keys. [`python-agent`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/python-agent)
is the worked example: `plugin = "python"` resolves `entrypoint` against the
eval directory and runs `python3 agent.py` inside the sandbox.

`javascript` and `typescript` follow the same contract with a Node.js
interpreter, and `custom` runs the `command` string with no interpreter
assumptions — the escape hatch for anything the built-ins do not cover.

Because the eval is agent-agnostic, every runtime example doubles as a
fixture for a real agent: `shipyard run . --agent claude-code` swaps the
subject without touching the manifest.

## Where each family's examples live

| Family | Tier | Why there |
| :--- | :--- | :--- |
| Runtime — `python` | [`examples/offline/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline) | Deterministic reference agents; no keys needed. |
| Runtime — `javascript`, `typescript` | [`examples/node/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/node) | Node.js runtimes. |
| Runtime — `custom` | [`examples/docker/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/docker) | Command-string agents, usually paired with a sandbox. |
| LLM APIs + remote | [`examples/keys/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/keys) | Real providers; runs spend money. |
| CLI harnesses | [`examples/harness/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/harness) | The agent binary must be installed. |
| Frameworks | `keys/` (Python) and `node/` (`langchain-js`) | Follow their runtime. |

## Overriding the agent without editing

All of these win over `eval.toml`, which is what makes `staging` runs of the
same example against different subjects meaningful:

| Flag | Effect |
| :--- | :--- |
| `--agent <name>` | Replace the plugin / alias (e.g. `claude-code`, `langgraph`, `codex`). |
| `--command "<cmd>"` | Replace the entrypoint command. |
| `--model`, `--provider` | Select the model and API provider for LLM plugins. |
| `--env <type>` | Override the environment (see [Environments](./examples-environments.md)). |

`shipyard run --dry-run` prints the resolved plan — agent command, image,
mounts, config hash — without executing anything, which is the fastest way
to confirm what a plugin resolution produced.
