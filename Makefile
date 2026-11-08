# Reproduction entry points (see README.md)
PY ?= python

.PHONY: install test test-fast sim01 sim01-smoke sim02a sim02a-smoke sim02a-margin sim02a-margin-check sim02a-criteria-d06 sim02a-claims validate

install:
	$(PY) -m pip install -r requirements.lock && $(PY) -m pip install -e . --no-deps

test:            ## full verification suite (includes end-to-end reproducibility, ~1 min)
	$(PY) -m pytest -q

test-fast:       ## unit verification only
	$(PY) -m pytest -q -m "not slow"

validate:
	$(PY) -m picket_sim validate configs/sim01/sim01_baseline.yaml
	$(PY) -m picket_sim validate configs/sim02a/sim02a_baseline.yaml

sim01: test      ## regenerate all SIM-01 results into a NEW run directory (requires a clean git tree)
	$(PY) -m picket_sim run configs/sim01/sim01_baseline.yaml

sim01-smoke:     ## fast pipeline check into results/_scratch (not for engineering use)
	$(PY) -m picket_sim run configs/sim01/sim01_smoke.yaml --allow-dirty

sim02a: test     ## regenerate all SIM-02A results into a NEW run directory (requires a clean git tree)
	$(PY) -m picket_sim run configs/sim02a/sim02a_baseline.yaml

sim02a-smoke:    ## fast SIM-02A pipeline check into results/_scratch (not for engineering use)
	$(PY) -m picket_sim run configs/sim02a/sim02a_smoke.yaml --allow-dirty

SIM02A_RUN ?= results/sim02a/20261107T214846Z_c56c0048_31da01b

sim02a-margin:   ## regenerate the criterion-margin supplement in reports/ (~5 min; clean tree in a git checkout)
	$(PY) tools/sim02a_criterion_margin.py $(SIM02A_RUN) --out reports/SIM-02A_criterion_margin

sim02a-margin-check: ## regenerate the supplement into build/ and require byte-identical CSVs (~5 min; safe in a snapshot)
	mkdir -p build
	$(PY) tools/sim02a_criterion_margin.py $(SIM02A_RUN) --out build/SIM-02A_criterion_margin --allow-dirty \
	    --expect reports/SIM-02A_criterion_margin

sim02a-criteria-d06: ## D06 criterion sensitivity (-6.0206 dB and +/-0.5, +/-1 dB around each criterion; ~10 min)
	$(PY) tools/sim02a_criterion_margin.py $(SIM02A_RUN) --out reports/SIM-02A_criteria_D06 \
	    --levels -2 -2.5 -3.5 -4 -5 -5.5 -6.0206 -6.5 -7 -9 -9.5 -10.5 -11

sim02a-claims:   ## recheck every quantitative claim in the SIM-02A findings, transmittal and reviewer message
	$(PY) tools/check_sim02a_claims.py $(SIM02A_RUN)
