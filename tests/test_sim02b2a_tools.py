"""Verification of the SIM-02B.2-A supplementary tools.

* ``tools/d02_collection_design.py``: Golomb spacing set, coherence values from the study functions, the MSC formulas
  (the tool itself refuses to write if Monte Carlo disagrees), deterministic output.
* ``tools/sim02b2a_b1_regression.py``: verdict arithmetic on constructed tables.
* ``tools/sim02b2a_repro_check.py``: detects a changed row.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


d02 = _load("d02_collection_design")
reg = _load("sim02b2a_b1_regression")
rep = _load("sim02b2a_repro_check")


def test_golomb_marks_give_distinct_spacings_and_cover_the_candidates():
    diffs = sorted(abs(i - j) for i in d02.MARKS for j in d02.MARKS if i < j)
    assert len(diffs) == len(set(diffs)) == 21
    assert min(diffs) * d02.UNIT_M <= 0.15 and max(diffs) * d02.UNIT_M >= 1.07  # candidate spacings 0.15 to 1.07 m


def test_msc_null_law_and_variance_by_independent_simulation():
    import numpy as np

    rng = np.random.default_rng(3)
    n, alpha = 32, 0.05
    x = d02.msc_hat(n, 0.0, rng, 40000)
    thr = 1 - alpha ** (1 / (n - 1))
    assert abs(np.mean(x > thr) - alpha) < 4 * math.sqrt(alpha * (1 - alpha) / x.size)
    assert np.mean(x) == pytest.approx(1 / n, rel=0.03)  # E[MSC_hat | g = 0] = 1/n
    y = d02.msc_hat(256, 0.5, rng, 20000)
    assert np.std(y) == pytest.approx(math.sqrt(2 * 0.5 * 0.25 / 256), rel=0.1)


@pytest.mark.slow
def test_d02_design_tables_are_deterministic(tmp_path):
    d02.main(["--out", str(tmp_path / "a")])
    d02.main(["--out", str(tmp_path / "b")])
    for t in ("spacings", "coherence", "msc", "timing", "candidates"):
        assert (tmp_path / f"a_{t}.csv").read_bytes() == (tmp_path / f"b_{t}.csv").read_bytes()
    coh = {(float(r["f_hz"]), float(r["spacing_m"])): r for r in csv.DictReader(open(tmp_path / "a_coherence.csv"))}
    r = coh[(100.0, 0.08)]
    k = 2 * math.pi * 100 / 1500
    assert float(r["spherical"]) == pytest.approx(math.sin(k * 0.08) / (k * 0.08), abs=1e-9)
    assert float(r["exponential_L0p1"]) == pytest.approx(math.exp(-0.8), abs=1e-9)


def _write(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_regression_verdicts(tmp_path):
    run, b1 = tmp_path / "run", tmp_path / "b1"
    (run / "tables").mkdir(parents=True)
    (b1 / "tables").mkdir(parents=True)
    (run / "record.json").write_text(json.dumps({"config_resolved": {"sim02b2a": {"cells": [
        {"id": "C1", "band": "B2", "window_s": 1.0}]}}}))
    base = {"scenario": "STAT", "normalizer": "ORACLE", "cell": "C1", "candidate": "A0", "mode": "single",
            "class": "tone", "pfa_target": "0.001", "status": "ok", "threshold_method": "exact",
            "binom_lo_db": "", "binom_hi_db": "", "threshold_lo_db": "", "threshold_hi_db": ""}
    rows = [dict(base, pd_target="0.5", snr_req_db="10.0", binom_lo_db="9.7", binom_hi_db="10.3"),   # hw 0.3 & 0.4
            dict(base, pd_target="0.9", snr_req_db="12.0", binom_lo_db="11.7", binom_hi_db="12.3")]
    _write(run / "tables/snr_required.csv", rows)
    b = {"experiment": "PRIMARY", "scenario": "N-AMB", "band": "B2", "window_s": "1", "candidate": "A0",
         "mode": "single", "class": "tone", "pfa_target": "0.001", "threshold_method": "exact", "status": "ok"}
    _write(b1 / "tables/snr_required.csv",
           [dict(b, pd_target="0.5", snr_req_db="10.4", snr_req_lo="10.0", snr_req_hi="10.8"),   # diff 0.4, hw 0.5
            dict(b, pd_target="0.9", snr_req_db="12.7", snr_req_lo="12.3", snr_req_hi="13.1")])  # diff 0.7, hw 0.5
    reg.main([str(run), "--b1", str(b1), "--out", str(tmp_path / "out")])
    v = {r["pd_target"]: r["verdict"] for r in csv.DictReader(open(tmp_path / "out.csv"))}
    assert v == {"0.5": "consistent", "0.9": "marginal"}


def test_repro_comparison_detects_a_changed_value():
    run_rows = [{"candidate": "A0", "cell": "C2", "normalizer": "ORACLE", "mode": "single", "detector": "tonal",
                 "pfa_target": "0.001", "eta": "12.5", "method": "exact"}]
    same = [dict(run_rows[0])]
    n, prob = rep.compare("thresholds.csv", run_rows, same, {"candidate": "A0", "cell": "C2"})
    assert n == 1 and prob == []
    changed = [dict(run_rows[0], eta="12.50000001")]
    _, prob = rep.compare("thresholds.csv", run_rows, changed, {"candidate": "A0", "cell": "C2"})
    assert prob and "eta" in prob[0]
    _, prob = rep.compare("thresholds.csv", run_rows, [], {"candidate": "A0", "cell": "C2"})
    assert prob and "row keys differ" in prob[0]
