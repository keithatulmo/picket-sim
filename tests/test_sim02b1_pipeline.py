"""SIM-02B.1 configuration, provenance and pipeline tests."""

from __future__ import annotations

import copy
import csv
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from picket_sim.environment import CoatesWenz, spectrum_from_config
from picket_sim.experiments import sim02b1
from picket_sim.params import ParamError

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "configs/sim02b/sim02b1_baseline.yaml"
SMOKE = REPO / "configs/sim02b/sim02b1_smoke.yaml"


@pytest.fixture(scope="module")
def base_cfg():
    return yaml.safe_load(open(BASE))


def test_baseline_configuration_validates_and_builds_expected_cases(base_cfg):
    st = sim02b1.Sim02B1Study(copy.deepcopy(base_cfg), log=lambda m: None)
    cases = st.cases()
    prim = [c for c in cases if c.experiment == "PRIMARY"]
    assert {c.cand for c in prim} == {"A0", "A1", "A2", "P6-C", "P8-C", "A4"}
    assert {c.T for c in prim} == {0.1, 1.0, 10.0}
    assert all(c.truth == c.assumed for c in prim)
    assert {c.experiment for c in cases if c.kind == "mismatch"} == {"MM-LEVEL+1", "MM-LEVEL+3", "MM-SHAPE",
                                                                      "MM-COH-FLOW", "MM-COH-WHITE"}
    # chirps only in 0.1 and 1 s windows; tone also in the 60 s experiment
    assert "chirp" not in st.classes_for("B2", 10.0) and "chirp" in st.classes_for("B2", 1.0)
    assert st.classes_for("B1", 60.0) == ("tone",)


def test_coates_spectrum_matches_hand_arithmetic_and_refuses_extrapolation(base_cfg):
    cw = CoatesWenz(0.5, 5.0)
    # at 1 kHz (f = 1 in kHz): Nt 17, Ns 40 - 60 log 1.03, Nw 50 + 7.5 sqrt 5 - 40 log 1.4, Nth -15
    terms = [17.0, 40.0 - 60 * math.log10(1.03), 50.0 + 7.5 * math.sqrt(5.0) - 40 * math.log10(1.4), -15.0]
    expect = 10 * math.log10(sum(10 ** (t / 10) for t in terms))
    assert 10 * math.log10(cw(1000.0)) == pytest.approx(expect, abs=1e-12)
    params = []
    g = spectrum_from_config("AMB-WENZ", base_cfg["spectra"]["AMB-WENZ"], {}, params)
    with pytest.raises(ParamError):
        g(np.array([10.0, 100.0]))  # below the stated range
    eq = [p for p in params if p.name == "coates_wenz_equations"][0]
    assert eq.provenance == "published" and "Stojanovic" in eq.source and eq.uncertainty and eq.applicability


def test_published_values_require_d01_fields(base_cfg):
    cfg = copy.deepcopy(base_cfg)
    cfg["noise_scenarios"][1]["components"][0]["coherence"]["correlation_length_m"] = {
        "value": 0.1, "provenance": "published", "source": "a citation without the D01 fields"}
    with pytest.raises(ParamError, match="ADR-0017"):
        sim02b1.Sim02B1Study(cfg, log=lambda m: None)


def test_invalid_configurations_fail_visibly(base_cfg):
    cfg = copy.deepcopy(base_cfg)
    cfg["noise_scenarios"][0]["components"][0]["spectrum"] = "NOPE"
    with pytest.raises(Exception, match="unknown spectrum"):
        sim02b1.Sim02B1Study(cfg, log=lambda m: None)
    cfg = copy.deepcopy(base_cfg)
    cfg["bands"][0]["f_hi_hz"] = 600.0  # above Nyquist of fs = 1000
    with pytest.raises(Exception, match="fs/2"):
        sim02b1.Sim02B1Study(cfg, log=lambda m: None)
    cfg = copy.deepcopy(base_cfg)
    cfg["candidates"] = [c for c in cfg["candidates"] if c["id"] != "A0"]
    with pytest.raises(Exception, match="A0"):
        sim02b1.Sim02B1Study(cfg, log=lambda m: None)


def test_sources_are_shared_across_candidates(base_cfg):
    """Common random numbers: every candidate sees the same source parameters (paired comparison)."""
    st = sim02b1.Sim02B1Study(copy.deepcopy(base_cfg), log=lambda m: None)
    grid = st.grid("B2", 1.0)
    s1 = st.source_params("tone", "B2", 1.0, 50, grid)
    st2 = sim02b1.Sim02B1Study(copy.deepcopy(base_cfg), log=lambda m: None)
    s2 = st2.source_params("tone", "B2", 1.0, 50, grid)
    np.testing.assert_array_equal(s1["f0"], s2["f0"])
    g_true = st.scenarios["N-AMB"].element_psd(grid.f)
    a0 = st.signal_unit("tone", "B2", grid, s1, [3], st.geoms["A0"].positions_m, g_true)
    p8 = st.signal_unit("tone", "B2", grid, s1, [3], st.geoms["P8-C"].positions_m, g_true)
    # same source: the array element powers equal the A0 power (plane wave, equal sensitivity) to within the
    # phase-dependent interference of the finite window's positive- and negative-frequency terms
    assert np.sum(np.abs(p8[0]) ** 2, axis=0) == pytest.approx(np.full(8, np.sum(np.abs(a0[0, :, 0]) ** 2)), rel=1e-3)
    # unit SNR convention: tone power over element PSD at the tone frequency is 1 (0 dB re 1 Hz)
    f0 = s1["f0"][3]
    power = np.sum(np.abs(a0[0, :, 0]) ** 2) / grid.T
    assert power / np.interp(f0, grid.f, g_true) == pytest.approx(1.0, rel=0.02)


def test_detection_gain_arithmetic():
    rows = [{"experiment": "X", "candidate": "A0", "band": "B2", "window_s": 1.0, "scenario": "N", "class": "tone",
             "pfa_target": 1e-3, "pd_target": 0.5, "snr_req_db": 10.0, "snr_req_lo": 9.5, "snr_req_hi": 10.6,
             "status": "ok", "threshold_method": "exact", "mode": "single"},
            {"experiment": "X", "candidate": "P8-C", "band": "B2", "window_s": 1.0, "scenario": "N", "class": "tone",
             "pfa_target": 1e-3, "pd_target": 0.5, "snr_req_db": 7.0, "snr_req_lo": 6.4, "snr_req_hi": 7.5,
             "status": "ok", "threshold_method": "empirical", "mode": "beam_search"}]
    g = sim02b1.detection_gain_rows(rows)[0]
    assert (g["gain_db"], g["gain_lo_db"], g["gain_hi_db"]) == pytest.approx((3.0, 2.0, 4.2))


@pytest.mark.slow
def test_smoke_run_is_complete_and_independent_of_worker_count(tmp_path):
    a = sim02b1.run(SMOKE, output_root=tmp_path / "a", allow_dirty=True, make_figures=False, log=lambda m: None,
                    workers=1)
    b = sim02b1.run(SMOKE, output_root=tmp_path / "b", allow_dirty=True, make_figures=False, log=lambda m: None,
                    workers=2)
    for name in ("thresholds_and_pfa.csv", "snr_required.csv", "detection_gain_vs_a0.csv", "roc_curves.csv",
                 "covariance_validation.csv"):
        assert (a / "tables" / name).read_bytes() == (b / "tables" / name).read_bytes(), name
    rec = yaml.safe_load((a / "record.json").read_text())
    assert rec["status"] == "complete"
    assert rec["self_checks"]["covariance_validation_worst_median_error_in_se"] < 3
    thr = list(csv.DictReader(open(a / "tables" / "thresholds_and_pfa.csv")))
    # the white-coherence assumption under isotropic truth must break false-alarm control for the array (B1)
    mm = [r for r in thr if r["experiment"] == "MM-COH-WHITE" and r["candidate"] == "P8-C"
          and r["mode"] == "beam_search" and r["detector"] == "tonal" and r["pfa_target"] == "0.01"]
    assert mm and float(mm[0]["realized_pfa"]) > 0.5
    a0 = [r for r in thr if r["experiment"] == "MM-COH-WHITE" and r["candidate"] == "A0"
          and r["detector"] == "tonal" and r["pfa_target"] == "0.01"]
    assert a0 and float(a0[0]["realized_pfa"]) < 0.05  # one element sees the same PSD: unaffected
    assert any((a / "waveforms").iterdir())
