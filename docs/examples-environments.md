# Environments

The sandbox an example runs in is declared in `[environment]` in `eval.toml`.
Shipyard supports three types, and the examples cover all of them:

| `type` | What it is | Notable keys |
| :--- | :--- | :--- |
| `local` | This machine. No container runtime involved. | `workdir` |
| `docker` | A container: built from a `dockerfile`, or pulled as an `image`. | `dockerfile`, `image`, `workdir`, `persistent`, `container_name`, `env_vars` |
| `custom` | `local` plus lifecycle hooks you define. | `setup_command`, `teardown_command` |

## `local` — the offline tier's sandbox

[`python-agent`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/python-agent)
declares the smallest possible environment:

```toml
[environment]
type = "local"
workdir = "workdir"
```

The agent runs on the host with `workdir/` as its workspace
(`$SHIPYARD_WORKDIR`), the rubric runs in the same place, and no Docker
daemon is required — which is exactly why the offline tier gates every push
in CI. If a docker-based example is broken on a machine without Docker,
`--env local` re-points the run at the host.

## `docker` — reproducible sandboxes

Docker environments give the agent a reproducible machine:

- **`dockerfile`** builds an image from the eval's Dockerfile before each
  run — the right default when the agent needs packages the host does not
  have;
- **`image`** pulls a pinned tag instead of building;
- **`persistent = true`** keeps the container alive across runs (pair it
  with `container_name`), which is useful when setup is expensive;
- **`env_vars`** injects environment variables into the container, and the
  `[redaction]` block treats their values as secrets in captured artifacts.

The eval directory is mounted into the container and the workspace is
`workdir`. `shipyard run --dry-run` prints the resolved image and mounts
before anything starts.

## `custom` — local with hooks

A custom environment wraps `local` and runs commands around it, configured
under `[environment.options]`:

```toml
[environment]
type = "custom"

[environment.options]
setup_command = "python3 prepare.py"
teardown_command = "python3 cleanup.py"
```

`setup_command` runs once before the agent; `teardown_command` runs after
the rubric unless the environment is persistent. A failing setup command
fails the run before the agent ever starts.

## Workspace hygiene

Two guarantees make examples safe to run repeatedly in a shared checkout:

- the workspace is restored between repeats and after the run — pass
  `--keep-workdir` to inspect the agent's changes instead, or `--keep-env`
  to also leave a container running for debugging;
- rollouts are run output: `rollouts/` is gitignored in the examples repo,
  while `baselines/` is committed on purpose (it is what `compare` gates
  against).

## Where the examples live

| Environment | Example |
| :--- | :--- |
| `local` | [`examples/offline/python-agent`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/offline/python-agent) |
| `docker` (dockerfile, image, persistent) | [`examples/docker/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/docker) |
| `custom` | [`examples/docker/`](https://github.com/dock-at-the-yards/shipyard-examples/tree/main/examples/docker) |
