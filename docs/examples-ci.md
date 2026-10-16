# CI & Negative Cases

## Generated pipelines

`shipyard init ci` scaffolds a gated pipeline wired to the released
`shipyard-ci` templates:

```bash
shipyard init ci --provider github --target evalsets/demo
shipyard init ci --provider gitlab --target evalsets/demo
shipyard init ci --provider jenkins --target evalsets/demo
shipyard init ci --provider argo --target evalsets/demo
```

| Provider | Writes | Uses |
| :--- | :--- | :--- |
| `github` | `.github/workflows/shipyard.yml` | The `dock-at-the-yards/shipyard-ci` action |
| `gitlab` | A job file to `include` from `.gitlab-ci.yml` | The shared `shipyard-ci` templates |
| `jenkins` | A `Jenkinsfile` | The `shipyard-ci` shared library |
| `argo` | An Argo `Workflow` | The released `shipyard-eval-runner` template |

The GitHub workflow it generates is a nine-line job around the action:

```yaml
- uses: actions/checkout@v4
- uses: dock-at-the-yards/shipyard-ci@v1   # pin a version in production
  with:
    path: "evalsets/demo"
    repeat: "3"
    baseline: "baselines/main.json"
    post-comment: "true"
```

The action posts a sticky delta comment on the PR, annotates regressions,
and uploads JUnit results and rollout artifacts. `init ci` also creates
`baselines/` (with a README explaining the discipline) and appends the
v0.0.2 `[gate]` policy to an evalset that has none — so a scaffolded suite
gates from its first PR.

The two rules the scaffolding cannot enforce on its own:

- **only `main` regenerates a baseline** — run `baseline save` on a main
  build and commit the result; PRs compare against it, never refresh it;
- **`staging` is where paid tiers run** — the hermetic tiers gate every push,
  the `keys/` and `harness/` tiers run deliberately, by a person.

## Scaffolds

`shipyard init eval <name>` and `shipyard init evalset <name>` generate the
starting manifests, instruction, Dockerfile, rubric stub and workspace that
every example in this section is shaped like. The committed scaffold outputs
are kept as examples so you can diff the generator's behavior release over
release.

## Negative cases

The `negative/` directory in the examples repository holds deliberately
broken evals — one per failure mode — and the exact failure each must
produce:

```json
{
  "command": "validate",
  "args": [],
  "expect_exit": 1,
  "expect_message": "instruction"
}
```

`scripts/e2e.sh --tier negative` runs every case, asserts the expected
failure, and fails when a case fails *differently* — or stops failing at
all. That is how the CLI's error paths are exercised end to end; the
[error-code directory](https://shipyard.shivamja.in/docs/error-codes) is the
checklist of codes to cover.

## This repository's CI

The examples repository runs its own suite on every push — static validation,
the docs check, and the hermetic e2e tiers (offline, node, docker, negative)
against the exact CLI release named in the repository's `VERSION` file. The
paid tiers run on `workflow_dispatch` with secrets. Tags run the full
hermetic suite before the documentation site imports this section.
