#!/usr/bin/env bash
#
# Static validation — what CI's `validate` job runs and what `make check`
# runs locally. Nothing here starts a container or spends a token:
#
#   1. every eval.toml parses and every path it references exists
#   2. every negative case.json is a well-formed expectation
#   3. every JSON file parses (docs/manifest.json and baselines included)
#   4. every Python file byte-compiles
#   5. every TypeScript file parses (Node 22+, nothing installed)
#   6. no committed .env and no key-shaped strings in the tree

set -euo pipefail

cd "$(dirname "$0")/.."

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  tracked() { git ls-files "$1"; }
else
  tracked() { find . -path ./.git -prune -o -name "$1" -print | sed 's|^\./||'; }
fi

echo "== manifests and referenced paths"
python3 - <<'PY'
import glob, os, sys, tomllib

manifests = sorted(glob.glob("examples/**/eval.toml", recursive=True))
if not manifests:
    sys.exit("no manifests found; the glob is probably wrong")

problems = []

for path in manifests:
    base = os.path.dirname(os.path.abspath(path))
    print(f"\n{path}")
    try:
        with open(path, "rb") as fh:
            doc = tomllib.load(fh)
    except Exception as exc:
        problems.append(f"{path}: TOML does not parse: {exc}")
        continue

    for key in ("name", "version", "description"):
        if key not in doc:
            problems.append(f"{path}: missing required key '{key}'")
        else:
            print(f"  {key}: {doc[key]}")

    def check(ref, label):
        """Resolve a manifest-relative path and confirm it exists."""
        if not isinstance(ref, str) or not ref:
            return
        target = os.path.normpath(os.path.join(base, ref))
        if os.path.exists(target):
            print(f"  ok  {label}: {ref}")
        else:
            problems.append(
                f"{path}: {label} points at '{ref}', which does not exist "
                f"(resolved to {os.path.relpath(target, base)})"
            )
            print(f"  BAD {label}: {ref}")

    check(doc.get("instruction"), "instruction")

    for agent in doc.get("agent", []):
        entry = agent.get("entrypoint")
        # A bare plugin name or built-in command is not a repository file.
        if entry and not entry.endswith((".py", ".ts", ".js", ".sh")):
            print(f"  ok  agent {agent.get('name')}: entrypoint '{entry}' (built-in)")
            continue
        check(entry, f"agent {agent.get('name', '?')} entrypoint")

    env = doc.get("environment", {})
    if isinstance(env, dict):
        etype = env.get("type")
        if etype and etype not in ("local", "docker", "custom"):
            problems.append(f"{path}: environment.type '{etype}' is not one of local, docker, custom")
        check(env.get("dockerfile"), "environment.dockerfile")
        check(env.get("workdir"), "environment.workdir")

    check(doc.get("tests", {}).get("rubric") if isinstance(doc.get("tests"), dict) else None, "tests.rubric")

print("\n" + "=" * 60)
if problems:
    for p in problems:
        print(f"FAIL  {p}")
    sys.exit(f"\n{len(problems)} problem(s)")
print(f"OK    {len(manifests)} manifests validated")
PY

echo
echo "== negative cases"
python3 - <<'PY'
import glob, json, re, sys

cases = sorted(glob.glob("negative/*/case.json"))
problems = []
for path in cases:
    try:
        spec = json.load(open(path))
    except Exception as exc:
        problems.append(f"{path}: does not parse: {exc}")
        continue
    if spec.get("command") not in ("validate", "run"):
        problems.append(f"{path}: command must be 'validate' or 'run'")
    if not isinstance(spec.get("expect_exit"), int):
        problems.append(f"{path}: expect_exit must be an integer")
    message = spec.get("expect_message")
    if message is not None:
        try:
            re.compile(message)
        except re.error as exc:
            problems.append(f"{path}: expect_message is not a valid regex: {exc}")

if problems:
    for p in problems:
        print(f"FAIL  {p}")
    sys.exit(f"\n{len(problems)} problem(s)")
if cases:
    print(f"OK    {len(cases)} negative case(s) well-formed")
else:
    print("SKIP  no negative cases yet (they land with the first error-path example)")
PY

echo
echo "== JSON files"
python3 - <<'PY'
import glob, json, os, sys

files = [f for f in sorted(glob.glob("**/*.json", recursive=True))
         if "node_modules" not in f
         and os.path.basename(f) != "package-lock.json"]
if not files:
    sys.exit("no JSON files found; the glob is probably wrong")

bad = 0
for f in files:
    try:
        json.load(open(f))
    except Exception as exc:
        bad += 1
        print(f"  FAIL  {f}: {exc}")
if bad:
    sys.exit(f"{bad} invalid JSON file(s)")
print(f"  {len(files)} JSON files parsed")
PY

echo
echo "== Python sources"
n=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  python3 -m py_compile "$f"
  n=$((n + 1))
done < <(tracked '*.py')
echo "  $n Python files compile"

echo
echo "== TypeScript sources"
ts_files="$(tracked '*.ts' || true)"
if [ -z "$ts_files" ]; then
  echo "  no TypeScript files yet"
else
  node_major="$(node --version | sed -E 's/^v([0-9]+).*/\1/')"
  if [ "$node_major" -lt 22 ]; then
    echo "FAIL  Node 22+ required to parse TypeScript, found $(node --version)"
    exit 1
  fi
  n=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    node --experimental-strip-types --check "$f" \
      || { echo "FAIL  $f does not parse"; exit 1; }
    n=$((n + 1))
  done <<< "$ts_files"
  echo "  $n TypeScript files parse"
fi

echo
echo "== secrets"
if git ls-files --error-unmatch '**/.env' >/dev/null 2>&1; then
  echo "FAIL  a .env file is tracked; it must not be"
  exit 1
fi

# .env.example files are placeholders: a real value on a credential-shaped
# name is the mistake this catches.
bad=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  while IFS= read -r line; do
    case "$line" in
      *KEY=*|*TOKEN=*|*SECRET=*|*PASSWORD=*|*PAT=*)
        value="${line#*=}"
        value="${value%%#*}"
        value="$(printf '%s' "$value" | tr -d '[:space:]')"
        if [ -n "$value" ]; then
          echo "FAIL  $f: '$line' looks like a real value on a credential-shaped name"
          bad=1
        fi
        ;;
    esac
  done < "$f"
done < <(tracked '*.env.example')

# Key-shaped strings anywhere in tracked text files.
pattern='(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})'
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git grep -nEI "$pattern" -- . >/dev/null 2>&1; then
  echo "FAIL  a key-shaped string is committed:"
  git grep -nEI "$pattern" -- . || true
  bad=1
fi
if [ "$bad" -eq 0 ]; then
  echo "  no committed .env, no key-shaped strings"
fi
exit "$bad"
