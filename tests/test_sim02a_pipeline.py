"""SIM-02A pipeline: configuration validation and bitwise reproducibility."""

import copy
import json
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from picket_sim.experiments.sim02a import Sim02AStudy
from picket_sim.params import ParamError

SMOKE2 = REPO / "configs" / "sim02a" / "sim02a_smoke.yaml"
BASE2 = REPO / "configs" / "sim02a" / "sim02a_baseline.yaml"


def _cfg(path=BASE2):
    return yaml.safe_load(Path(path).read_text())


def test_baseline_config_builds_and_tags_every_parameter():
    st = Sim02AStudy(_cfg(), log=lambda *a, **k: None)
    rows = st.provenance_rows()
    assert all(r["provenance"] in ("published", "measured", "assumed") for r in rows)
    assert all(len(r["source"]) >= 8 for r in rows)
    assert not any(r["provenance"] == "measured" for r in rows)  # SIM-02A has no measured values
    assert {s["id"] for s, _ in st.cands} >= {"A0", "A1", "A2", "A3", "A4", "P6-C", "P8-C", "P6-E", "P8-E"}


def test_invalid_provenance_fails_visibly():
    c = _cfg()
    c["sensor_scenarios"][0]["hydrophone"]["capacitance_f"]["provenance"] = "typical"
    with pytest.raises(ParamError):
        Sim02AStudy(c, log=lambda *a, **k: None)
    c = _cfg()
    c["error_sweeps"].pop("source")
    with pytest.raises(ParamError):
        Sim02AStudy(c, log=lambda *a, **k: None)


def test_nyquist_inconsistent_sensor_fails_visibly():
    c = _cfg()
    c["sensor_scenarios"][1]["adc"]["sample_rate_hz"]["value"] = 30000.0  # declared band to 20 kHz
    with pytest.raises(ParamError):
        Sim02AStudy(c, log=lambda *a, **k: None)


@pytest.mark.slow
def test_sim02a_smoke_is_bitwise_reproducible(tmp_path):
    from picket_sim.experiments import sim02a

    quiet = lambda *a, **k: None  # noqa: E731
    r1 = sim02a.run(SMOKE2, output_root=tmp_path / "a", allow_dirty=True, log=quiet)
    r2 = sim02a.run(SMOKE2, output_root=tmp_path / "b", allow_dirty=True, log=quiet)
    o1 = {o["path"]: o["sha256"] for o in json.loads((r1 / "record.json").read_text())["outputs"]}
    o2 = {o["path"]: o["sha256"] for o in json.loads((r2 / "record.json").read_text())["outputs"]}
    assert o1.keys() == o2.keys()
    diff = sorted(k for k in o1 if o1[k] != o2[k] and k != "summary.md")
    assert diff == [], diff
    rec = json.loads((r1 / "record.json").read_text())
    sc = rec["self_checks"]
    assert sc["rag_white_vs_10logN_max_abs_db"] < 1e-9
    assert sc["rag_iso_no_sensor_noise_vs_sim01_DI_max_abs_db"] < 1e-9
    assert sc["mc_mainlobe_vs_closed_form_max_abs_z"] < 5
    assert sc["parameters_by_provenance"]["measured"] == 0


def test_line_array_mirror_is_an_unresolved_tie_not_a_gross_error():
    """A line's scanned response is symmetric in azimuth for any channel errors (nominal steering vectors
    depend only on cos az), so target and mirror tie exactly; this must be reported as a tie."""
    st = Sim02AStudy(_cfg(), log=lambda *a, **k: None)
    em = next(e for e in st.errors if e.scenario_id.startswith("E1"))
    line = next(g for s, g in st.cands if s["id"] == "A1")
    r = st._mc_case(line, 5000.0, 30.0, em, 300, ("test", "A1"))
    assert r["closed_mainlobe"] and r["unresolved_tie_rate"] == 1.0 and r["gross_error_rate"] == 0.0
    assert r["fine_rms_error_deg"] < 2.0
    planar = next(g for s, g in st.cands if s["id"] == "P8-C")
    r = st._mc_case(planar, 2000.0, 30.0, em, 300, ("test", "P8-C"))
    assert r["unresolved_tie_rate"] == 0.0


def test_cut_statistics_undefined_without_half_power_discrimination():
    st = Sim02AStudy(_cfg(), log=lambda *a, **k: None)
    em = next(e for e in st.errors if e.scenario_id.startswith("E2"))
    a4 = next(g for s, g in st.cands if s["id"] == "A4")
    r = st._mc_case(a4, 100.0, 30.0, em, 300, ("test", "A4"))  # A4 f_HP is about 270 Hz
    assert not r["closed_mainlobe"] and "p_amb_ge_m6db" not in r and "undefined" in r["status"]
