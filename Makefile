# Reproduction entry points (see README.md)
PY ?= python

.PHONY: install test test-fast sim01 sim01-smoke validate

install:
	$(PY) -m pip install -r requirements.lock && $(PY) -m pip install -e . --no-deps

test:            ## full verification suite (includes end-to-end reproducibility, ~1 min)
	$(PY) -m pytest -q

test-fast:       ## unit verification only
	$(PY) -m pytest -q -m "not slow"

validate:
	$(PY) -m picket_sim validate configs/sim01/sim01_baseline.yaml

sim01: test      ## regenerate all SIM-01 results into a NEW run directory (requires a clean git tree)
	$(PY) -m picket_sim run configs/sim01/sim01_baseline.yaml

sim01-smoke:     ## fast pipeline check into results/_scratch (not for engineering use)
	$(PY) -m picket_sim run configs/sim01/sim01_smoke.yaml --allow-dirty
