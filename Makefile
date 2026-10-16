# Shipyard Examples — developer shortcuts.
#
# `make check` is what CI's static job runs; `make e2e` runs every tier this
# machine can support (offline + node + docker when the daemon is up).
# The keys/ and harness/ tiers are named explicitly and are never part of
# `all`: they spend money.

PYTHON ?= python3

.PHONY: check e2e e2e-offline e2e-keys e2e-harness

check:
	$(PYTHON) scripts/docs-check.py
	scripts/validate-static.sh

e2e:
	scripts/e2e.sh --tier all

e2e-offline:
	scripts/e2e.sh --tier offline

e2e-keys:
	scripts/e2e.sh --tier keys

e2e-harness:
	scripts/e2e.sh --tier harness
