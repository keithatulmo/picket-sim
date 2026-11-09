"""SIM-02B.2-A configuration, data-partition, scenario-generator and pipeline tests."""

from __future__ import annotations

import copy
import csv
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from picket_sim import noise_estimation as ne
from picket_sim.config import ConfigError
from picket_sim.experiments import sim02b2a
from picket_sim.experiments.sim02b2a import CalCase, EvalCase, Sim02B2AStudy, apply_normalizer

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "configs/sim02b/sim02b2a_baseline.yaml"
SMOKE = REPO / "configs/sim02b/sim02b2a_smoke.yaml"


@pytest.fixture(scope="module")
def base_cfg():
    return yaml.safe_load(open(BASE))


@pytest.fixture(scope="module")
def study(base_cfg):
    return Sim02B2AStudy(copy.deepcopy(base_cfg), log=lambda m: None)


def _ks_two_sample(a, b):
    """Two-sample Kolmogorov-Smirnov statistic and its asymptotic 0.1 % critical value (independent of scipy)."""
    a, b = np.sort(a), np.sort(b)
    x = np.concatenate([a, b])
    d = np.max(np.abs(np.searchsorted(a, x, side="right") / a.size - np.searchsorted(b, x, side="right") / b.size))
    crit = 1.95 * math.sqrt((a.size + b.size) / (a.size * b.size))
    return d, crit


# ------------------------------------------------------------------------------------------- configuration
def test_baseline_configuration_builds_expected_cases(study):
    assert [c for c in study.b1.cand_specs] == ["A0", "A1", "P8-C", "A4"]
    assert len(study.cal_cases()) == 12
    ev = study.eval_cases()
    assert len(ev) == 48
    for sc in study.scen:  # A0 is evaluated in every scenario and cell where an array is
        for cell in study.scen[sc]["cells"]:
            assert {c.cand for c in ev if c.scenario == sc and c.cell == cell} == {"A0", "A1", "P8-C", "A4"}
    assert study.alias == {"TREF-CA16-G8": "TREF-CA16"}
    assert [n["M"] for n in study.a0_extra] == [4, 8, 32, 64]
    assert study.pfa == [0.01, 0.001, 0.0001]
    assert study.classes("C1", "CONTAM") == ("tone", "broadband")
    assert sim02b2a.history_needed(study.norms) == 18
    assert sim02b2a.history_needed(study.norms + study.cnorms) == 24
    assert study.excluded({"type": "fref_os"}, "energy") and not study.excluded({"type": "tref_ca"}, "energy")


def test_invalid_configurations_fail_visibly(base_cfg):
    def bad(edit, match):
        cfg = copy.deepcopy(base_cfg)
        edit(cfg["sim02b2a"])
        with pytest.raises(ConfigError, match=match):
            Sim02B2AStudy(cfg, log=lambda m: None)

    bad(lambda s: s["normalizers"].append({"id": "X", "type": "median_magic"}), "unknown normalizer type")
    bad(lambda s: s["normalizers"].append(dict(s["normalizers"][2])), "unique")
    bad(lambda s: s["scenarios"][0].update(reference="N-NOPE"), "unknown noise scenario")
    bad(lambda s: s["scenarios"][0].update(cells=["C9"]), "unknown cell")
    bad(lambda s: s.update(nominal_scenario="N-NOPE"), "nominal")
    bad(lambda s: s["contamination_normalizers"].append({"id": "Y", "type": "tref_ca", "M": 5, "guard": 1}),
        "no calibrated normalizer")
    cfg = copy.deepcopy(base_cfg)
    cfg["sim02b2a"]["normalizers"][5]["L"] = 6  # frequency-reference normalizers must share one bin layout
    st = Sim02B2AStudy(cfg, log=lambda m: None)
    with pytest.raises(ConfigError, match="share L and G"):
        st._detector("C2")


def test_generated_configuration_is_reproducible_from_its_generator(base_cfg):
    """The committed YAML is exactly what tools/make_sim02b2a_config.py writes (edit the generator, not the file)."""
    import subprocess
    import sys

    before = (BASE.read_bytes(), SMOKE.read_bytes())
    subprocess.run([sys.executable, str(REPO / "tools/make_sim02b2a_config.py")], check=True, capture_output=True)
    assert (BASE.read_bytes(), SMOKE.read_bytes()) == before


# ------------------------------------------------------------------------------------------- ground-truth isolation
def test_adaptive_normalizers_never_read_model_backgrounds(study):
    """ADR-0019: adaptive estimates are functions of stream data only. Feeding NaN as the model background must
    leave every adaptive statistic unchanged and poison only the ORACLE and NOMINAL paths."""
    rng = np.random.default_rng(1)
    t, H, S, K = 5, 18, 3, 181
    y = ((rng.standard_normal((t, S, K)) + 1j * rng.standard_normal((t, S, K))) / np.sqrt(2)).astype(np.complex64)
    hp = rng.exponential(size=(t, H, S, K)).astype(np.float32)
    dets, detector, ref, fidx, _ = study._detector("C2")
    good = {"oracle": np.ones((S, K)), "nominal": np.ones((S, K))}
    poison = {"oracle": np.full((S, K), np.nan), "nominal": np.full((S, K), np.nan)}
    a = study.all_stats(y, hp, good, study.norms, dets, "max", detector, ref, fidx)
    with np.errstate(invalid="ignore", divide="ignore"):  # NaN is meant to propagate on the model paths
        b = study.all_stats(y, hp, poison, study.norms, dets, "max", detector, ref, fidx)
    for n in study.norms:
        for d in a[n["id"]]:
            if n["type"] in sim02b2a.ADAPTIVE:
                np.testing.assert_array_equal(a[n["id"]][d], b[n["id"]][d])
            else:
                assert np.all(np.isnan(b[n["id"]][d]))
    for n in study.norms:  # and the adaptive path accepts no model at all
        if n["type"] in sim02b2a.ADAPTIVE:
            apply_normalizer(n, np.abs(y) ** 2, hp, fidx, None)


def test_time_reference_uses_the_windows_after_the_guard():
    t, H, S, K = 2, 24, 1, 4
    age = np.arange(1, H + 1, dtype=float)  # history index h holds age h + 1
    hp = np.broadcast_to(age[None, :, None, None], (t, H, S, K)).copy()
    g = apply_normalizer({"type": "tref_ca", "M": 16, "guard": 2}, None, hp, None)
    np.testing.assert_allclose(g, np.mean(age[2:18]))  # ages 3..18
    g = apply_normalizer({"type": "tref_ca", "M": 16, "guard": 8}, None, hp, None)
    np.testing.assert_allclose(g, np.mean(age[8:24]))  # ages 9..24
    g = apply_normalizer({"type": "tref_os", "M": 16, "r": 12, "guard": 2}, None, hp, None)
    np.testing.assert_allclose(g, age[2 + 11])  # 12th smallest of ages 3..18
    with pytest.raises(ValueError, match="not enough reference windows"):
        apply_normalizer({"type": "tref_ca", "M": 16, "guard": 9}, None, hp, None)


def test_frequency_reference_excludes_the_test_bin(study):
    """A tone confined to one bin must not enter its own frequency-reference estimate (guard G >= 1)."""
    K = 181
    p = np.ones((1, 1, K))
    p[..., 90] = 1e6
    fidx = ne.fref_index(K, 8, 2)
    for spec in study.norms:
        if spec["type"] in ("fref_ca", "fref_os"):
            assert apply_normalizer(spec, p, None, fidx)[0, 0, 90] == pytest.approx(1.0)


# ------------------------------------------------------------------------------------------- scenario generators
def test_interference_enters_reference_windows_only_with_the_stated_probability(study):
    n, H = 400, 18
    rng = np.random.default_rng(5)
    xt_i, xh_i = study.synth("A0", "C2", "INTERF", n, rng, H)
    xt_s, xh_s = study.synth("A0", "C2", "STAT", n, np.random.default_rng(6), H)
    g = study._ctx("A0", "C2", "STAT")["g_true"]
    win = np.mean(np.abs(xh_i[..., 0]) ** 2 / g, axis=-1)  # (n, H) window power / nominal
    hit = win > 4.0  # +10 dB band interferer: about 11 x; clean windows: 1 +/- 0.08
    p = float(study.scen["INTERF"]["interference"]["probability"])
    assert abs(hit.mean() - p) < 4 * math.sqrt(p * (1 - p) / hit.size)
    assert np.all(win[~hit] < 1.5)
    tw_i = np.mean(np.abs(xt_i[..., 0]) ** 2 / g, axis=-1)
    tw_s = np.mean(np.abs(xt_s[..., 0]) ** 2 / g, axis=-1)
    assert tw_i.max() < 1.5 and abs(tw_i.mean() - tw_s.mean()) < 0.02  # test window is never interfered
    assert np.mean(np.abs(xh_s[..., 0]) ** 2 / g) == pytest.approx(1.0, abs=0.01)


def test_level_step_raises_only_the_test_window(study):
    ctx = study._ctx("A0", "C2", "STEP+3")
    np.testing.assert_allclose(ctx["g_true"] / study._ctx("A0", "C2", "STAT")["g_true"], 10 ** 0.3, rtol=1e-12)
    np.testing.assert_allclose(np.real(ctx["c_ref"][:, 0, 0]), study._ctx("A0", "C2", "STAT")["g_true"], rtol=1e-12)


def test_contamination_occupies_windows_after_onset_with_a_phase_continuous_tone(study):
    """Independent check: synthesize the tone in the time domain across consecutive windows, take each window's
    DFT, and compare with the history-window bins used for contaminated reference windows."""
    cell = "C2"
    grid = study.grid(cell)
    ctx = study._ctx("A0", cell, "STAT")
    src = study.b1.source_params("tone", "B1", 1.0, 2, grid)
    case = EvalCase("A0", cell, "CONTAM")
    sig = study._signal_fn("tone", case, ctx, src, np.array([0, 1]), np.array([0, 3]))
    for h in (1, 2, 3, 4):
        x = sig(h)
        assert np.all(x[0] == 0)  # onset 0: the signal starts in the test window
        assert (np.any(x[1] != 0)) == (h <= 3)  # onset 3: ages 1..3 contain the signal
    i = 1
    f0, ph = src["f0"][i], src["phase"][i]
    A = math.sqrt(2.0 * float(np.interp(f0, grid.f, ctx["g_true"])))
    n = grid.n_samples
    for h in (0, 1, 3):
        m = np.arange(-h * n, -h * n + n)
        xt = A * np.cos(2 * np.pi * f0 * m / grid.fs + ph)
        X = np.fft.fft(xt)[grid.k] / grid.scale
        np.testing.assert_allclose(sig(h)[1, :, 0], X, atol=1e-9 * np.max(np.abs(X)))


def test_contaminated_tone_masks_itself_in_time_reference_estimates(study):
    """With the target present in every reference window, the time-reference estimate at the tone bin is about
    the signal-plus-noise power, so the normalized test statistic collapses (the mechanism CONTAM measures)."""
    cell = "C2"
    grid = study.grid(cell)
    ctx = study._ctx("A0", cell, "STAT")
    src = study.b1.source_params("tone", "B1", 1.0, 1, grid)
    sig = study._signal_fn("tone", EvalCase("A0", cell, "CONTAM"), ctx, src, np.array([0]), np.array([24]))
    a = 10.0  # 20 dB per-element SNR re 1 Hz
    hist = np.stack([a * sig(h + 1) for h in range(18)], axis=1)  # (1, 18, K, 1)
    hp = np.abs(study.to_streams(hist, "single", None)) ** 2
    yt = study.to_streams(a * sig(0), "single", None)
    k = int(np.argmax(np.abs(yt[0, 0])))
    g_tref = apply_normalizer({"type": "tref_ca", "M": 16, "guard": 2}, None, hp, None)
    u = np.abs(yt[0, 0, k]) ** 2 / g_tref[0, 0, k]
    assert 0.5 < u < 2.0  # signal-only data: the tone bin is normalized by its own power
    assert np.abs(yt[0, 0, k]) ** 2 / ctx["g_true"][k] > 50


# ------------------------------------------------------------------------------------------- calibration methods
def test_a0_fast_null_simulation_matches_full_synthesis(study):
    """The A0 exact-in-distribution shortcut (Gamma and Beta reference draws) against full window synthesis."""
    st = Sim02B2AStudy(copy.deepcopy(study.cfg), log=lambda m: None)
    fast = st.a0_fast_null(CalCase("A0", "C2"), 4000)
    full, _ = st.null_stats("A0", "C2", st.nominal, 4000, "ks-test", st.norms)
    for nid in ("TREF-CA16", "TREF-OS16", "FREF-OS8", "ORACLE"):
        for d in ("tonal", "energy", "harmonic", "mf"):
            if (nid, d) not in fast:
                continue
            ks, crit = _ks_two_sample(fast[(nid, d)], full[(nid, "single", d)])
            assert ks < crit, (nid, d, ks, crit)


def test_a0_exact_thresholds_agree_with_fast_simulation(study):
    st = Sim02B2AStudy(copy.deepcopy(study.cfg), log=lambda m: None)
    st.cal = dict(st.cal, a0_fast_samples=20000)
    st.pfa = [0.01]
    rows, _ = st._calibrate_a0(CalCase("A0", "C2"))
    exact = [r for r in rows if r["method"] == "exact"]
    assert {r["normalizer"] for r in exact if r["detector"] == "tonal"} >= {"ORACLE", "NOMINAL", "TREF-CA16",
                                                                            "TREF-OS16", "TREF-CA4-A0"}
    for r in exact:  # 20000 samples at Pfa 0.01: 200 expected exceedances
        assert abs(r["check_fast_pfa"] - 0.01) < 4 * math.sqrt(0.01 * 0.99 / 20000), r
    assert all(r["method"] == "fast null simulation" for r in rows if r["normalizer"].startswith("FREF"))


def test_sequential_calibration_stopping_rule(base_cfg):
    cfg = copy.deepcopy(base_cfg)
    s = cfg["sim02b2a"]
    s["pfa"] = [0.1]
    s["calibration"] = dict(s["calibration"], batch=100, max_trials={"C1": 1000, "C2": 1000, "C3": 1000},
                            tolerance_db=10.0, cmc_samples_per_bin=4)
    st = Sim02B2AStudy(cfg, log=lambda m: None)
    rows, extra = st._calibrate_array(CalCase("A1", "C2"))
    assert extra["n_sequential"] == 100 and extra["stop"].startswith("interval <= 10.0 dB")
    s["calibration"]["tolerance_db"] = 1e-6  # unattainable: runs to the cap and says so
    s["calibration"]["max_trials"] = {"C1": 300, "C2": 300, "C3": 300}
    st = Sim02B2AStudy(cfg, log=lambda m: None)
    rows, extra = st._calibrate_array(CalCase("A1", "C2"))
    assert extra["n_sequential"] == 300 and extra["stop"] == "cap"
    assert {r["n"] for r in rows if r["method"] == "empirical"} == {300}
    meth = {(r["normalizer"], r["mode"], r["detector"]): r["method"] for r in rows}
    assert meth[("ORACLE", "incoherent", "tonal")] == "exact quadratic form"
    assert meth[("ORACLE", "beam_search", "tonal")] == "conditional Monte Carlo"
    assert meth[("NOMINAL", "beam_search", "tonal")] == "conditional Monte Carlo"  # nominal = design model


def test_unreachable_pfa_is_reported_not_estimated(base_cfg):
    cfg = copy.deepcopy(base_cfg)
    s = cfg["sim02b2a"]
    s["pfa"] = [0.001]
    s["calibration"] = dict(s["calibration"], batch=100, max_trials={"C1": 200, "C2": 200, "C3": 200},
                            cmc_samples_per_bin=4)
    st = Sim02B2AStudy(cfg, log=lambda m: None)
    rows, extra = st._calibrate_array(CalCase("A1", "C2"))
    adaptive = [r for r in rows if r["normalizer"].startswith(("TREF", "FREF"))]
    assert adaptive and all(r["method"] == "not estimated" and math.isnan(r["eta"]) for r in adaptive)


def test_exact_tails_match_binomial_and_beta_binomial_laws():
    """Exact thresholds: binomial tails. Empirical thresholds: beta-binomial tails, wider than binomial (the
    threshold's own sampling error), so the same count is less surprising."""
    up, low = sim02b2a.exact_tails({"method": "exact"}, 3, 1000, 0.001)
    p0 = math.exp(-1) * (1 + 1 + 0.5)  # Poisson(1) approximation of P(K <= 2)
    assert up == pytest.approx(1 - p0, abs=2e-3)
    assert low == pytest.approx(p0 + math.exp(-1) / 6, abs=2e-3)
    up_e, _ = sim02b2a.exact_tails({"method": "empirical", "n": 20000}, 25, 10000, 0.001)
    up_x, _ = sim02b2a.exact_tails({"method": "exact"}, 25, 10000, 0.001)
    assert up_x < up_e < 1


def test_derived_rows_arithmetic(study):
    base = {"cell": "C1", "scenario": "STAT", "class": "tone", "pfa_target": 1e-3, "pd_target": 0.5,
            "threshold_method": "exact"}
    rows = [dict(base, candidate="A0", normalizer="ORACLE", mode="single", snr_req_db=10.0, status="ok"),
            dict(base, candidate="A0", normalizer="TREF-CA16", mode="single", snr_req_db=11.5, status="ok"),
            dict(base, candidate="P8-C", normalizer="ORACLE", mode="beam_search", snr_req_db=2.0, status="ok"),
            dict(base, candidate="P8-C", normalizer="TREF-CA16", mode="beam_search", snr_req_db=3.25, status="ok"),
            dict(base, candidate="P8-C", normalizer="FREF-OS8", mode="beam_search", snr_req_db=float("nan"),
                 status="above grid")]
    loss, gain = sim02b2a.derived_rows(study, rows)
    lk = {(r["candidate"], r["normalizer"]): r for r in loss}
    assert lk[("A0", "TREF-CA16")]["loss_db"] == pytest.approx(1.5)
    assert lk[("P8-C", "TREF-CA16")]["loss_db"] == pytest.approx(1.25)
    assert math.isnan(lk[("P8-C", "FREF-OS8")]["loss_db"]) and "above grid" in lk[("P8-C", "FREF-OS8")]["status"]
    gk = {(r["candidate"], r["normalizer"]): r for r in gain}
    assert gk[("P8-C", "ORACLE")]["gain_db"] == pytest.approx(8.0)
    assert gk[("P8-C", "TREF-CA16")]["gain_db"] == pytest.approx(8.25)
    assert ("P8-C", "FREF-OS8") not in gk  # no A0 row with that normalizer: no gain is invented
    # with null sets: each row carries the realized false-alarm status; CONTAM borrows the STAT null and says so
    pf = [{"candidate": "P8-C", "cell": "C1", "scenario": "STAT", "normalizer": "TREF-CA16", "mode": "beam_search",
           "detector": "tonal", "pfa_target": 1e-3, "realized_pfa": 0.004, "pfa_status": "liberal"},
          {"candidate": "P8-C", "cell": "C1", "scenario": "STAT", "normalizer": "ORACLE", "mode": "beam_search",
           "detector": "tonal", "pfa_target": 1e-3, "realized_pfa": 0.001, "pfa_status": "consistent"}]
    contam = [dict(r, scenario="CONTAM", normalizer=n) for r in rows[2:4]
              for n in ([r["normalizer"]] + (["TREF-CA16-G8"] if r["normalizer"] == "TREF-CA16" else []))]
    loss, _ = sim02b2a.derived_rows(study, rows + contam, pf)
    lk = {(r["scenario"], r["normalizer"]): r for r in loss if r["candidate"] == "P8-C"}
    assert lk[("STAT", "TREF-CA16")]["pfa_status"] == "liberal" and lk[("STAT", "TREF-CA16")]["pfa_source"] == "STAT"
    assert lk[("STAT", "TREF-CA16")]["oracle_pfa_status"] == "consistent"
    assert lk[("CONTAM", "TREF-CA16-G8")]["pfa_source"] == "STAT"  # alias: same null law as TREF-CA16
    assert lk[("CONTAM", "TREF-CA16-G8")]["realized_pfa"] == 0.004
    assert lk[("STAT", "FREF-OS8")]["pfa_status"] == "no null set"


# ------------------------------------------------------------------------------------------- end to end
def _tiny_cfg(tmp_path):
    cfg = yaml.safe_load(open(SMOKE))
    s = cfg["sim02b2a"]
    s["cells"] = [{"id": "C2", "band": "B1", "window_s": 1.0}]
    s["calibration"] = {"a0_fast_samples": 3000, "batch": 300, "max_trials": {"C2": 600}, "tolerance_db": 0.25,
                        "cmc_samples_per_bin": 8}
    s["evaluation"] = {"null_trials": {"STAT": 600, "default": 600}, "positive_trials": 24}
    s["scenarios"] = [
        {"id": "STAT", "cells": ["C2"], "reference": "N-AMB", "test": "N-AMB"},
        {"id": "STEP+3", "cells": ["C2"], "reference": "N-AMB", "test": "N-AMB", "test_offset_db": 3.0},
        {"id": "INTERF", "cells": ["C2"], "reference": "N-AMB", "test": "N-AMB",
         "interference": {"probability": 0.25, "level_db": 10.0, "spectrum": "AMB-WENZ"}},
        {"id": "CONTAM", "cells": ["C2"], "reference": "N-AMB", "test": "N-AMB",
         "contamination": {"max_onset_windows": 24}, "classes": ["tone", "broadband"]}]
    s["pfa"] = [0.01]
    p = tmp_path / "tiny.yaml"
    p.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return p


@pytest.mark.slow
def test_tiny_run_is_complete_and_independent_of_worker_count(tmp_path):
    cfgp = _tiny_cfg(tmp_path)
    a = sim02b2a.run(cfgp, output_root=tmp_path / "a", allow_dirty=True, make_figures=False, log=lambda m: None,
                     workers=1, repo_dir=REPO)
    b = sim02b2a.run(cfgp, output_root=tmp_path / "b", allow_dirty=True, make_figures=False, log=lambda m: None,
                     workers=2, repo_dir=REPO)
    for name in ("thresholds.csv", "realized_pfa.csv", "estimation_error.csv", "snr_required.csv",
                 "detection_loss_vs_oracle.csv", "gain_vs_a0.csv"):
        assert (a / "tables" / name).read_bytes() == (b / "tables" / name).read_bytes(), name
    rec = yaml.safe_load((a / "record.json").read_text())
    assert rec["status"] == "complete" and rec["self_checks"]["stat_calibration_rows"] > 0
    pfa = list(csv.DictReader(open(a / "tables" / "realized_pfa.csv")))

    def realized(sc, nid):
        r = [x for x in pfa if x["scenario"] == sc and x["candidate"] == "A0" and x["normalizer"] == nid
             and x["detector"] == "tonal"]
        assert len(r) == 1
        return float(r[0]["realized_pfa"])
    # a +3 dB step in the test window: the design-model and time-reference normalizers lose false-alarm control,
    # the oracle and the frequency reference (estimated inside the test window) keep it
    assert realized("STEP+3", "NOMINAL") > 0.3 and realized("STEP+3", "TREF-CA16") > 0.1
    assert realized("STEP+3", "ORACLE") < 0.05 and realized("STEP+3", "FREF-OS8") < 0.05
    # interference in the reference windows inflates time-reference estimates: conservative, never liberal
    assert realized("INTERF", "TREF-CA16") <= 0.01
    assert not any(x["scenario"] == "CONTAM" for x in pfa)  # contamination affects positive trials only
    snr = list(csv.DictReader(open(a / "tables" / "snr_required.csv")))
    g8 = [x for x in snr if x["scenario"] == "CONTAM" and x["normalizer"] == "TREF-CA16-G8"]
    assert g8 and all(x["threshold_method"] for x in g8)  # aliased thresholds were found
    assert {x["pfa_status"] for x in pfa} <= {"liberal", "conservative", "consistent"}
    assert {x["pfa_status_exact"] for x in pfa} <= {"liberal", "conservative", "consistent"}
    for x in pfa:  # the exact status follows the exact predictive tails at the stated level
        up, low = float(x["p_upper_exact"]), float(x["p_lower_exact"])
        assert x["pfa_status_exact"] == ("liberal" if up < 1e-3 else "conservative" if low < 1e-3 else "consistent")
    assert [x["pfa_status_exact"] for x in pfa if x["scenario"] == "STEP+3" and x["candidate"] == "A0"
            and x["normalizer"] == "NOMINAL" and x["detector"] == "tonal"] == ["liberal"]
    assert [x["pfa_status"] for x in pfa if x["scenario"] == "STEP+3" and x["candidate"] == "A0"
            and x["normalizer"] == "NOMINAL" and x["detector"] == "tonal"] == ["liberal"]
    fref_energy = [x for x in pfa if x["normalizer"].startswith("FREF") and x["detector"] == "energy"]
    assert not fref_energy  # excluded combination (configuration states why)
