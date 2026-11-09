# Reproduction entry points (see README.md)
PY ?= python

.PHONY: install test test-fast sim01 sim01-smoke sim02a sim02a-smoke sim02a-margin sim02a-margin-check sim02a-criteria-d06 sim02a-claims sim02a-repro-check sim02b1 sim02b1-smoke sim02b1-claims sim02b1-calibration sim02b2a sim02b2a-smoke validate

install:
	$(PY) -m pip install -r requirements.lock && $(PY) -m pip install -e . --no-deps

test:            ## full verification suite (includes end-to-end reproducibility, ~1 min)
	$(PY) -m pytest -q

test-fast:       ## unit verification only
	$(PY) -m pytest -q -m "not slow"

validate:
	$(PY) -m picket_sim validate configs/sim01/sim01_baseline.yaml
	$(PY) -m picket_sim validate configs/sim02a/sim02a_baseline.yaml
	$(PY) -m picket_sim validate configs/sim02b/sim02b1_baseline.yaml
	$(PY) -m picket_sim validate configs/sim02b/sim02b2a_baseline.yaml

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

sim02a-repro-check: ## rerun SIM-02A into a new build/ run and require every table byte-identical to the run of record (~6 min)
	$(PY) -m picket_sim run configs/sim02a/sim02a_baseline.yaml --allow-dirty --no-figures --output-root build/sim02a_repro
	$(PY) tools/compare_run_tables.py $(SIM02A_RUN) $$(ls -d build/sim02a_repro/2* | tail -1)

sim02b1: test     ## SIM-02B.1 study of record into a NEW run directory (~100 min on 4 cores; clean tree)
	$(PY) -m picket_sim run configs/sim02b/sim02b1_baseline.yaml

SIM02B1_RUN ?= results/sim02b1/20261108T125126Z_1c70e065_8dbe019

sim02b1-claims:   ## recheck every quantitative claim in the SIM-02B.1 report, transmittal and reviewer message
	$(PY) tools/check_sim02b1_claims.py $(SIM02B1_RUN)

sim02b1-calibration: ## exact false-alarm calibration test of the SIM-02B.1 run of record
	$(PY) tools/sim02b1_calibration_check.py $(SIM02B1_RUN)

sim02b1-smoke:    ## fast SIM-02B.1 pipeline check into results/_scratch (not for engineering use)
	$(PY) -m picket_sim run configs/sim02b/sim02b1_smoke.yaml --allow-dirty

sim02b2a: test    ## SIM-02B.2-A study of record into a NEW run directory (about 2.5 h on 4 cores; clean tree)
	$(PY) -m picket_sim run configs/sim02b/sim02b2a_baseline.yaml

sim02b2a-smoke:   ## fast SIM-02B.2-A pipeline check into results/_scratch (not for engineering use)
	$(PY) -m picket_sim run configs/sim02b/sim02b2a_smoke.yaml --allow-dirty
