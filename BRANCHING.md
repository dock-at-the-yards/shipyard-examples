# Branching strategy

Three long-lived branches, one per environment. Code moves up exactly one tier
at a time, and never down.

```
  feature/*  ──PR──▶  develop  ──PR──▶  staging  ──PR──▶  main
             dev         dev              test          prod
```

| Branch | Environment | Purpose |
|---|---|---|
| `develop` | integration | day-to-day work lands here |
| `staging` | pre-production | examples exercised end to end (the `keys/` and `harness/` tiers included) |
| `main` | production | what CI runs on release tags, and what the docs site imports |

## What "production" means here

Nothing is deployed as an artifact, but `main` is consumed twice: CI runs the
hermetic tiers against it on every release tag, and `shipyard-web` imports the
pages under `docs/` from that tag into the documentation site. A broken example
on `main` is a broken build for anyone pointing `shipyard run` at it, and a
broken `docs/manifest.json` is a broken docs deploy.

That shapes what the tiers are for. `staging` is where a change gets run
against a real agent — including the paid `keys/` and `harness/` tiers — before
`main` carries it. CI on every tier statically validates manifests, resolves
every path they reference, and runs the hermetic e2e tiers; it cannot run the
paid tiers on every push, which is exactly why they are `staging` work.

## Working on a change

```bash
git checkout develop && git pull
git checkout -b feat/node-runtime-example
# ... work ...
git push -u origin feat/node-runtime-example
gh pr create --base develop
```

Feature branches are throwaway. Nothing long-lived forks from `main`.

## Promoting

```bash
# develop -> staging
gh workflow run promote.yml --repo dock-at-the-yards/shipyard-examples -f target=staging

# staging -> main
gh workflow run promote.yml --repo dock-at-the-yards/shipyard-examples -f target=production
```

The workflow refuses to skip a tier, so `develop` cannot reach `main` directly.

## Versioning and releases

`VERSION` names the CLI release these examples are validated against, and it
moves in lockstep with `shipyard-cli` and `shipyard-web`: during a release wave
the same `vX.Y.Z` tag is cut on all three.

The ordering is deliberate:

1. `shipyard-cli` tags `vX.Y.Z` (the release that CI will install),
2. bump `VERSION` here and merge to `main`,
3. tag `shipyard-examples` `vX.Y.Z` on `main`.

The tag push runs the full hermetic e2e suite (offline, node, docker) before
anything downstream consumes it. `shipyard-web` then imports `docs/` from this
tag, and its release gate checks that this tag exists before its own
production promotion can merge.

## CI, and where it runs

CI runs on GitHub-hosted runners. The hermetic tiers need nothing but
`python3`, Node, and the Docker daemon that `ubuntu-latest` already provides,
so a self-hosted runner buys nothing here.

| Check | What it catches |
|---|---|
| Static validation | a manifest that does not parse, or a path it references that does not exist |
| Docs check | a `docs/manifest.json` page whose file or link target is missing — the failure that would surface as a broken docs deploy |
| E2E `offline` | a deterministic example that no longer passes against the pinned CLI release |
| E2E `node` | same, for the Node.js runtimes |
| E2E `docker` | same, for the Docker sandboxes |
| E2E `negative` | a deliberately broken eval that no longer fails, or fails for the wrong reason |
| E2E `keys` / `harness` | same, for the paid tiers — `workflow_dispatch` only, secrets required |

The paid tiers are never part of a push build: they need API credentials,
spend money per run, and an LLM's output varies between runs, so a flaky CI
gate would train everyone to ignore red. They belong in `staging`,
deliberately and by a person, which is what the tier is for.

## Branch protection

`main` and `staging` require a pull request and a passing CI run, with no
force-push and no deletion. `develop` allows direct pushes, since that is
where work lands, but still blocks force-push and deletion.
