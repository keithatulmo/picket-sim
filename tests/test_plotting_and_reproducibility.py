"""Plot data orientation/normalization checks and bitwise reproducibility of a full (smoke) run."""

import json

import numpy as np
import pytest

from conftest import SMOKE, manifold
from picket_sim.beamforming import beampattern_power
from picket_sim.conventions import horizontal_cut, unit_vector, vertical_cut
from picket_sim.grids import cut_offsets_deg
from picket_sim.plotting import (
    cone_curve_az_el,
    cut_for_plot,
    equirect_grid,
    to_display_db,
    vertical_front_for_plot,
)

GAM = cut_offsets_deg(3600)


def test_display_db_floor_and_normalization_guard():
    d = to_display_db(np.array([1.0, 0.5, 1e-9, 0.0]), -40.0)
    np.testing.assert_allclose(d, [0.0, 10 * np.log10(0.5), -40.0, -40.0])
    with pytest.raises(ValueError):
        to_display_db(np.array([1.2]))


@pytest.mark.parametrize("az0", [-170.0, -90.0, 0.0, 60.0, 175.0])
def test_horizontal_cut_plot_peak_at_steering_and_no_seam(candidates, az0):
    man = manifold(candidates["A3"])
    p = beampattern_power(man, 1500.0, unit_vector(az0, 0), horizontal_cut(az0, 0, GAM))
    az, d = cut_for_plot(GAM, p, az0)
    assert np.all(np.diff(az) > 0) and az[0] >= -180 and az[-1] < 180  # sorted, no wrap-around segment
    assert az[np.argmax(d)] == pytest.approx(az0, abs=0.1 + 1e-9)


def test_vertical_cut_plot_peak_at_steering(candidates):
    man = manifold(candidates["A4"])
    p = beampattern_power(man, 600.0, unit_vector(60, -20), vertical_cut(60, -20, GAM))
    el, d = vertical_front_for_plot(GAM, p, -20.0)
    assert el.min() >= -90 and el.max() <= 90
    assert el[np.argmax(d)] == pytest.approx(-20.0, abs=0.1 + 1e-9)


def test_sphere_map_orientation(candidates):
    az, el, u = equirect_grid(1.0)
    assert u.shape == (el.size, az.size, 3)  # rows = elevation, columns = azimuth (pcolormesh(az, el, C))
    p = beampattern_power(manifold(candidates["A4"]), 400.0, unit_vector(60, -20), u)
    i, j = np.unravel_index(np.argmax(p), p.shape)
    assert az[j] == pytest.approx(60.0) and el[i] == pytest.approx(-20.0)


def test_cone_curve_passes_through_target():
    u0 = unit_vector(60, -20)
    a, e = cone_curve_az_el(np.array([1.0, 0, 0]), u0)
    d = np.min(np.hypot(a - 60, e + 20))
    assert d < 1.0


@pytest.mark.slow
def test_full_pipeline_is_bitwise_reproducible(tmp_path):
    from picket_sim.experiments import sim01

    quiet = lambda *a, **k: None  # noqa: E731
    r1 = sim01.run(SMOKE, output_root=tmp_path / "a", allow_dirty=True, log=quiet)
    r2 = sim01.run(SMOKE, output_root=tmp_path / "b", allow_dirty=True, log=quiet)
    o1 = {o["path"]: o["sha256"] for o in json.loads((r1 / "record.json").read_text())["outputs"]}
    o2 = {o["path"]: o["sha256"] for o in json.loads((r2 / "record.json").read_text())["outputs"]}
    assert o1.keys() == o2.keys()
    assert any(k.startswith("figures/") for k in o1) and any(k.startswith("tables/") for k in o1)
    diff = sorted(k for k in o1 if o1[k] != o2[k] and k != "summary.md")
    assert diff == [], f"outputs differ between identical runs: {diff}"
    rec = json.loads((r1 / "record.json").read_text())
    assert rec["self_checks"]["di_closed_form_vs_quadrature_max_abs_db"] < 1e-6
    assert rec["self_checks"]["normalization_max_abs_error"] < 1e-12
