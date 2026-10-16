#!/usr/bin/env bash
#
# End-to-end runner for shipyard-examples.
#
# Runs each example of the selected tiers against a real shipyard binary, in
# a temp copy so the repository tree stays clean, and asserts:
#
#   - `shipyard validate` exits 0
#   - `shipyard run --run-name e2e` exits 0 and the rollout's results.json
#     reports a clean, passing verdict
#   - when the example commits baselines/main.json, `shipyard compare`
#     exits 0 against it
#   - negative cases fail exactly the way their case.json says they must
#
# Tiers:
#   offline    python3 only                 (hermetic: runs in CI on every push)
#   node       Node.js >= 20                (hermetic)
#   docker     a Docker daemon              (hermetic)
#   negative   deliberately broken evals    (hermetic)
#   keys       a provider key in the env    (never implied; spends money)
#   harness    a CLI agent on PATH          (never implied; spends money)
#
# `--tier all` is the four hermetic tiers. A tier that is part of `all` and
# cannot run — no Docker daemon, no examples yet — is skipped with a notice;
# a tier named explicitly must run.
#
# Usage:
#   scripts/e2e.sh [--tier <name>]... [--bin <path>] [--keep]
#                  [--strict-version] [--list]
#
# The binary is resolved from --bin, then $SHIPYARD_BIN, then PATH.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPECTED_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"

TIER_ORDER="offline node docker negative keys harness"
EXPLICIT=" "
IMPLIED=" "
BIN="${SHIPYARD_BIN:-}"
KEEP=0
STRICT_VERSION=0
LIST=0

PASSED=0
FAILED=0
SKIPPED=0

usage() {
  sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
}

say()  { printf '%s\n' "$*"; }
note() { printf '  note: %s\n' "$*"; }

is_in() { case " $1 " in *" $2 "*) return 0 ;; *) return 1 ;; esac; }
add_tier() { if ! is_in "$1" "$2"; then eval "$1=\"\${$1}$2 \""; fi; }

while [ $# -gt 0 ]; do
  case "$1" in
    --tier)   tier="${2:?--tier requires a value}"; shift 2 ;;
    --tier=*) tier="${1#*=}"; shift ;;
    --bin)    BIN="${2:?--bin requires a value}"; shift 2 ;;
    --bin=*)  BIN="${1#*=}"; shift ;;
    --keep)   KEEP=1; shift ;;
    --strict-version) STRICT_VERSION=1; shift ;;
    --list)   LIST=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) say "unknown argument: $1"; usage >&2; exit 2 ;;
  esac

  if [ "${tier:-}" != "" ]; then
    IFS=, read -ra parts <<< "$tier"
    for part in "${parts[@]}"; do
      case "$part" in
        all|"")
          add_tier IMPLIED offline
          add_tier IMPLIED node
          add_tier IMPLIED docker
          add_tier IMPLIED negative
          ;;
        offline|node|docker|negative|keys|harness)
          add_tier EXPLICIT "$part"
          ;;
        *)
          say "unknown tier '$part' (offline, node, docker, negative, keys, harness, all)"
          exit 2
          ;;
      esac
    done
    tier=""
  fi
done

if [ "$LIST" -eq 1 ]; then
  for t in $TIER_ORDER; do
    say "tier: $t"
    if [ "$t" = "negative" ]; then
      while IFS= read -r case; do
        [ -n "$case" ] || continue
        say "  $(basename "$(dirname "$case")")"
      done <<< "$(find "$ROOT/negative" -mindepth 2 -maxdepth 2 -name case.json 2>/dev/null | sort)"
    else
      while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        say "  $(basename "$dir")"
      done <<< "$(find "$ROOT/examples/$t" -mindepth 2 -maxdepth 2 -name eval.toml -print 2>/dev/null | sort | sed 's|/eval.toml||')"
    fi
  done
  exit 0
fi

# No explicit tier means the fast, hermetic default.
if [ "$EXPLICIT" = " " ] && [ "$IMPLIED" = " " ]; then
  add_tier EXPLICIT offline
fi

# ------------------------------------------------------------------ binary --

if [ -z "$BIN" ]; then
  BIN="$(command -v shipyard || true)"
fi
if [ -z "$BIN" ] || [ ! -x "$BIN" ]; then
  say "error: no shipyard binary found (--bin PATH, \$SHIPYARD_BIN, or PATH)"
  say "       install one: curl -fsSL https://raw.githubusercontent.com/dock-at-the-yards/shipyard-cli/main/install.sh | sh"
  exit 2
fi

ACTUAL_VERSION="$("$BIN" version 2>/dev/null | head -n1 | awk '{print $NF}')"
if [ "$ACTUAL_VERSION" != "$EXPECTED_VERSION" ]; then
  if [ "$STRICT_VERSION" -eq 1 ]; then
    say "error: binary is $ACTUAL_VERSION but VERSION pins $EXPECTED_VERSION (--strict-version)"
    exit 2
  fi
  say "warning: binary is $ACTUAL_VERSION; VERSION pins $EXPECTED_VERSION"
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/shipyard-examples-e2e.XXXXXX")"
cleanup() {
  if [ "$KEEP" -eq 1 ] || [ "$FAILED" -gt 0 ]; then
    say "kept: $WORKDIR"
  else
    rm -rf "$WORKDIR"
  fi
}
trap cleanup EXIT

say "shipyard $ACTUAL_VERSION  ($BIN)"
say "workdir:  $WORKDIR"
say ""

# ----------------------------------------------------------------- helpers --

run_capture() {
  # Run a command quietly; on failure print the output tail.
  local log="$WORKDIR/last.log"
  if ! "$@" >"$log" 2>&1; then
    say "    command failed: $*"
    tail -n 30 "$log" | sed 's/^/    | /'
    return 1
  fi
  return 0
}

pass() { PASSED=$((PASSED + 1)); say "  PASS  $1"; }
fail() { FAILED=$((FAILED + 1)); say "  FAIL  $1"; }
skip() { SKIPPED=$((SKIPPED + 1)); note "$1"; }

examples_for_tier() {
  find "$ROOT/examples/$1" -mindepth 2 -maxdepth 2 -name eval.toml -print 2>/dev/null \
    | sort | sed 's|/eval.toml||'
}

tier_prereq_ok() {
  case "$1" in
    offline|negative) return 0 ;;
    node)    command -v node >/dev/null 2>&1 ;;
    docker)  docker info >/dev/null 2>&1 ;;
    keys)
      [ "${SHIPYARD_E2E_KEYS_OK:-}" = "1" ] && return 0
      for var in OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY DEEPSEEK_API_KEY SHIPYARD_REMOTE_AGENT_URL; do
        eval "value=\"\${$var:-}\""
        [ -n "$value" ] && return 0
      done
      return 1
      ;;
    harness)
      [ "${SHIPYARD_E2E_HARNESS_OK:-}" = "1" ] && return 0
      for bin in claude codex opencode gemini aider; do
        command -v "$bin" >/dev/null 2>&1 && return 0
      done
      return 1
      ;;
    *) return 1 ;;
  esac
}

# --------------------------------------------------------------- examples --

run_example() {
  local tier="$1" dir="$2"
  local base copy results
  base="$(basename "$dir")"
  copy="$WORKDIR/$tier-$base"

  rm -rf "$copy"
  cp -R "$dir" "$copy"

  say "  $tier/$base"
  if ! run_capture "$BIN" validate "$copy"; then fail "$tier/$base (validate)"; return; fi
  if ! run_capture "$BIN" run "$copy" --run-name e2e; then fail "$tier/$base (run)"; return; fi

  results="$copy/rollouts/e2e/results.json"
  if [ ! -f "$results" ]; then
    fail "$tier/$base (no rollouts/e2e/results.json)"
    return
  fi
  if ! python3 - "$results" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
totals = doc.get("totals", {})
if doc.get("verdict") != "passed" or totals.get("failed", 0) or totals.get("errored", 0):
    sys.exit("verdict=%s totals=%s" % (doc.get("verdict"), totals))
PY
  then
    fail "$tier/$base (results.json not a clean pass)"
    return
  fi

  if [ -f "$copy/baselines/main.json" ]; then
    if ! run_capture "$BIN" compare "$copy"; then fail "$tier/$base (compare)"; return; fi
  fi

  pass "$tier/$base"
}

run_negative_case() {
  local case_json="$1" case_dir copy command expect_exit expect_message output exit_code
  case_dir="$(dirname "$case_json")"
  copy="$WORKDIR/negative-$(basename "$case_dir")"

  # Parse the expectation. Fields are NUL-separated so values may contain
  # spaces; args are one space-separated string by design.
  local parsed
  parsed="$(python3 - "$case_json" <<'PY'
import json, sys
spec = json.load(open(sys.argv[1]))
parts = [
    spec.get("command", ""),
    str(spec.get("expect_exit", "")),
    " ".join(spec.get("args", [])),
    spec.get("expect_message", ""),
]
sys.stdout.write("\0".join(parts))
PY
)"
  local field_index=0
  command=""; expect_exit=""; local args_line=""; expect_message=""
  while IFS= read -r -d '' field; do
    case "$field_index" in
      0) command="$field" ;;
      1) expect_exit="$field" ;;
      2) args_line="$field" ;;
      3) expect_message="$field" ;;
    esac
    field_index=$((field_index + 1))
  done < <(printf '%s' "$parsed")

  rm -rf "$copy"
  cp -R "$case_dir" "$copy"

  say "  negative/$(basename "$case_dir") (expects $command -> exit $expect_exit)"
  set +e
  if [ -n "$args_line" ]; then
    output="$("$BIN" "$command" "$copy" $args_line 2>&1)"
  else
    output="$("$BIN" "$command" "$copy" 2>&1)"
  fi
  exit_code=$?
  set -e

  if [ "$exit_code" -ne "$expect_exit" ]; then
    fail "negative/$(basename "$case_dir") (exit $exit_code, expected $expect_exit)"
    printf '%s\n' "$output" | tail -n 10 | sed 's/^/    | /'
    return
  fi
  if [ -n "$expect_message" ] && ! printf '%s\n' "$output" | grep -Eq -- "$expect_message"; then
    fail "negative/$(basename "$case_dir") (output does not match /$expect_message/)"
    printf '%s\n' "$output" | tail -n 10 | sed 's/^/    | /'
    return
  fi
  pass "negative/$(basename "$case_dir")"
}

run_tier() {
  local tier="$1" dir found
  say "tier: $tier"

  if [ "$tier" = "negative" ]; then
    local cases
    cases="$(find "$ROOT/negative" -mindepth 2 -maxdepth 2 -name case.json 2>/dev/null | sort)"
    if [ -z "$cases" ]; then
      skip "no negative cases yet"
      return
    fi
    if ! tier_prereq_ok "$tier"; then
      if is_in "$EXPLICIT" "$tier"; then
        say "error: tier '$tier' is missing a prerequisite"
        exit 2
      fi
      skip "tier '$tier' cannot run here (missing prerequisite)"
      return
    fi
    while IFS= read -r case_json; do
      [ -n "$case_json" ] || continue
      run_negative_case "$case_json"
    done <<< "$cases"
    return
  fi

  found=0
  while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    found=1
    if ! tier_prereq_ok "$tier"; then
      if is_in "$EXPLICIT" "$tier"; then
        say "error: tier '$tier' is missing a prerequisite"
        exit 2
      fi
      skip "tier '$tier' cannot run here (missing prerequisite)"
      return
    fi
    run_example "$tier" "$dir"
  done <<< "$(examples_for_tier "$tier")"

  if [ "$found" -eq 0 ]; then
    skip "no examples in tier '$tier' yet"
  fi
}

# -------------------------------------------------------------------- run --

for t in $TIER_ORDER; do
  if is_in "$EXPLICIT" "$t" || is_in "$IMPLIED" "$t"; then
    run_tier "$t"
  fi
done

say ""
say "summary: $PASSED passed, $FAILED failed, $SKIPPED tier(s)/case(s) skipped"
if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
