"""Verification of the SIM-02A Revision A supplementary tools (SIM-02A review, closeout action 2).

* ``tools/sim02a_criterion_margin.py``: plateau detection, knife-edge detection, the reproduction
  self-check, byte comparison, snapshot provenance and an end-to-end run on the smoke configuration.
* ``tools/check_sim02a_claims.py``: the 59 Revision A checks are preserved and pass on the run of record,
  and the checker fails on the Revision 0 documents (it must discriminate in both directions).
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
RUN_SIM02A = REPO / "results/sim02a/20261107T214846Z_c56c0048_31da01b"
RUN_SIM01 = REPO / "results/sim01/20261107T203522Z_d64d297c_8043684"
REV0 = Path(__file__).resolve().parent / "fixtures" / "sim02a_rev0"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


margin = _load("sim02a_criterion_margin")
claims = _load("check_sim02a_claims")

needs_runs = pytest.mark.skipif(not (RUN_SIM02A / "tables").exists() or not (RUN_SIM01 / "tables").exists(),
                                reason="run-of-record tables not present")


# ------------------------------------------------------------------------------------------- plateau
def test_plateau_finds_longest_constant_run_and_its_span():
    f = np.arange(10.0)
    v = np.array([-20, -12, -6.0206, -6.0206, -6.0206, -6.0206, -4, -7.77, -7.77, -7.77])
    level, f0, f1 = margin.plateau(f, v)
    assert level == pytest.approx(-6.0206) and (f0, f1) == (2.0, 5.0)


def test_plateau_requires_minimum_points_and_respects_tolerance():
    f = np.arange(6.0)
    assert margin.plateau(f, np.array([-9, -8, -8, -7, -6, -5.0])) is None  # two equal points only
    tol = margin.PLATEAU_TOL_DB
    v = np.array([-9, -8, -8 + 0.9 * tol, -8 + 1.8 * tol, -5, -4.0])  # neighbors within tolerance
    assert margin.plateau(f, v)[1:] == (1.0, 3.0)
    v2 = np.array([-9, -8, -8 + 1.1 * tol, -8, -5, -4.0])  # a step larger than the tolerance breaks the run
    assert margin.plateau(f, v2) is None


def test_plateau_ignores_non_finite_values():
    f = np.arange(6.0)
    v = np.array([np.nan, np.nan, np.nan, -3, -2, -1.0])
    assert margin.plateau(f, v) is None


# ------------------------------------------------------------------------------------------- knife edges
def _band_row(aid, ratios):
    row = {"array_id": aid}
    for L, r in ratios.items():
        row[f"guaranteed_{margin._lvl(L)}_ratio"] = r
    return row


def test_knife_edge_flags_only_large_changes_across_the_interval():
    flat = {-2.9: 1.29, -3.0: 1.28, -3.1: 1.27, -5.9: 2.81, -6.0: 2.80, -6.1: 2.79, -9.9: 1.33, -10.0: 1.32,
            -10.1: 1.32}
    edge = {**flat, -5.9: 2.38, -6.0: 2.37, -6.1: 1.65}
    out = margin.knife_edges([_band_row("FLAT", flat), _band_row("EDGE", edge)])
    assert len(out) == 1 and out[0].startswith("EDGE at -6 dB")


def test_knife_edge_skips_empty_bands():
    row = _band_row("V", {L: float("nan") for L in margin.levels_for()})
    assert margin.knife_edges([row]) == []


def test_levels_for_default_mode():
    assert margin.levels_for() == [-2.9, -3.0, -3.1, -5.9, -6.0, -6.1, -9.9, -10.0, -10.1]


# ------------------------------------------------------------------------------------------- self-check
def _summ_row(aid, value):
    r = {"array_id": aid}
    for L in margin.NOMINAL:
        lv = margin._lvl(L)
        for k in ("guaranteed_{}_lo_hz", "guaranteed_{}_hi_hz", "guaranteed_{}_ratio", "median_{}_ratio"):
            r[k.format(lv)] = value
    return r


def test_reproduction_check_passes_identical_and_fails_on_any_difference():
    summ = {"X": _summ_row("X", 1234.5)}
    ref = {"X": {k: str(v) for k, v in _summ_row("X", 1234.5).items()}}
    assert margin.check_reproduction(summ, ref) == 12
    bad = {"X": dict(ref["X"], guaranteed_m6db_hi_hz="1234.6")}
    with pytest.raises(RuntimeError, match="self-check failed"):
        margin.check_reproduction(summ, bad)
    with pytest.raises(RuntimeError, match="candidate sets differ"):
        margin.check_reproduction(summ, {**ref, "Y": ref["X"]})


def test_reproduction_check_treats_empty_bands_consistently():
    summ = {"X": _summ_row("X", float("nan"))}
    ref = {"X": {k: ("" if k != "array_id" else "X") for k in _summ_row("X", 0)}}
    assert margin.check_reproduction(summ, ref) == 12


def test_compare_outputs_is_byte_exact(tmp_path):
    (tmp_path / "a_bands.csv").write_bytes(b"x,y\n1,2\n")
    (tmp_path / "b_bands.csv").write_bytes(b"x,y\n1,2\n")
    assert margin.compare_outputs(str(tmp_path / "a"), str(tmp_path / "b")) == []
    (tmp_path / "b_bands.csv").write_bytes(b"x,y\n1,2.0\n")
    assert margin.compare_outputs(str(tmp_path / "a"), str(tmp_path / "b"))
    assert margin.compare_outputs(str(tmp_path / "a"), str(tmp_path / "missing"))


def test_provenance_text_distinguishes_snapshot_from_checkout():
    assert "source snapshot" in margin.provenance_text({"git_commit": None, "git_dirty": None})
    assert margin.provenance_text({"git_commit": "abcdef0123", "git_dirty": False}) == \
        "Code commit `abcdef0` (clean tree)"
    assert "DIRTY" in margin.provenance_text({"git_commit": "abcdef0123", "git_dirty": True})


@pytest.mark.slow
def test_generator_end_to_end_on_smoke_configuration_is_deterministic(tmp_path):
    """Build a run-like directory from the smoke configuration, run the generator twice, compare."""
    from picket_sim.experiments.sim02a import Sim02AStudy

    cfg = yaml.safe_load(open(REPO / "configs/sim02a/sim02a_smoke.yaml"))
    study = Sim02AStudy(cfg, lambda m: None)
    _, alias = study.geometry_table()
    rows = study.threshold_summary(study.thresholds(), alias)
    run = tmp_path / "run"
    (run / "tables").mkdir(parents=True)
    with open(run / "tables" / "thresholds_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    software = {"picket_sim": "test", "python": "test", "numpy": "test"}
    (run / "record.json").write_text(json.dumps({"config_resolved": cfg, "config_sha256": "0" * 64,
                                                 "software": software}))
    a, b = tmp_path / "a", tmp_path / "b"
    assert margin.main([str(run), "--out", str(a), "--allow-dirty"]) == 0
    assert (tmp_path / "a_bands.csv").exists() and (tmp_path / "a.md").exists()
    assert margin.main([str(run), "--out", str(b), "--allow-dirty", "--expect", str(a)]) == 0
    text = (tmp_path / "a.md").read_text()
    assert "Self-check" in text and "Knife-edge cases" in text
    # custom levels mode: nominal levels added automatically, bands only
    c = tmp_path / "c"
    assert margin.main([str(run), "--out", str(c), "--allow-dirty", "--levels", "-6.0206", "-6.5"]) == 0
    hdr = (tmp_path / "c_bands.csv").read_text().splitlines()[0]
    assert "guaranteed_m6p0206db_ratio" in hdr and "guaranteed_m3db_ratio" in hdr
    assert not (tmp_path / "c_psl.csv").exists()
    # a tampered run table must stop the generator
    tampered = [dict(r) for r in rows]
    tampered[0]["guaranteed_m3db_ratio"] = float(tampered[0]["guaranteed_m3db_ratio"]) * 1.01 \
        if math.isfinite(float(tampered[0]["guaranteed_m3db_ratio"])) else 1.0
    with open(run / "tables" / "thresholds_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(tampered)
    with pytest.raises(RuntimeError, match="self-check failed"):
        margin.main([str(run), "--out", str(tmp_path / "d"), "--allow-dirty"])


# ------------------------------------------------------------------------------------------- claims checker
@needs_runs
def test_claims_checker_preserves_and_passes_all_59_revision_a_checks():
    assert claims.main([str(RUN_SIM02A)], quiet=True) == 0
    assert len(claims.RESULTS) == 59
    assert all(ok for ok, *_ in claims.RESULTS)
    labels = [r[1] for r in claims.RESULTS]
    assert len(set(labels)) == 59
    for key in ("P6-C guaranteed ratio at -5.9 / -6.0 / -6.1 dB", "knife-edge candidates (ratio change > 10 % across +/- 0.1 dB)",
                "P8-C E3 15 kHz gross-error rate over target azimuths (%)", "message: quotes every checked value"):
        assert key in labels


@needs_runs
def test_claims_checker_fails_on_revision_0_documents():
    rc = claims.main([str(RUN_SIM02A), "--report", str(REV0 / "SIM-02A_engineering_report_rev0.md"),
                      "--transmittal", str(REV0 / "SIM-02A_transmittal_rev0.md"),
                      "--message", str(REV0 / "SIM-02A_reviewer_message_rev0.md")], quiet=True)
    assert rc == 1
    failed = sorted(label for ok, label, *_ in claims.RESULTS if not ok)
    assert failed == sorted(f"{d}: {c}" for d in ("report", "transmittal", "message")
                            for c in ("quotes every checked value", "contains no Rev 0 error phrase or em dash"))
    assert sum(ok for ok, *_ in claims.RESULTS) == 53


@needs_runs
def test_claims_checker_detects_a_changed_number(tmp_path):
    text = (REPO / "reports/SIM-02A_reviewer_message.md").read_text()
    bad = tmp_path / "msg.md"
    bad.write_text(text.replace("65 to 81 percent", "65 to 80 percent"))
    assert claims.main([str(RUN_SIM02A), "--message", str(bad)], quiet=True) == 1
    failed = [label for ok, label, *_ in claims.RESULTS if not ok]
    assert failed == ["message: quotes every checked value"]
