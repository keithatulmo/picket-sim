"""Sound-speed mismatch bias versus the closed-form result."""

import numpy as np
import pytest

from picket_sim.geometry import from_coordinates, uniform_linear, uniform_rectangular
from picket_sim.grids import SphereGrid
from picket_sim.mismatch import mismatch_peak

SPH = SphereGrid(91, 180)


@pytest.mark.parametrize("c_true", [1450.0, 1550.0])
@pytest.mark.parametrize("az", [0.0, 20.0, 45.0, 75.0, 90.0])
def test_line_array_cone_angle_bias(c_true, az):
    r = mismatch_peak(uniform_linear(4, 0.15), 1000.0, c_true, 1500.0, az, 0.0, SPH)
    assert r["cone_angle_error_deg"] == pytest.approx(r["cone_angle_pred_error_deg"], abs=0.02)
    if az == 90.0:
        assert abs(r["cone_angle_error_deg"]) < 0.02  # broadside is unbiased


def test_line_array_bias_value_example():
    # c_assumed/c_true = 1500/1450: cos(psi_est) = 1.0345 cos(30 deg) -> psi_est = 26.39 deg
    r = mismatch_peak(uniform_linear(4, 0.30), 800.0, 1450.0, 1500.0, 30.0, 0.0, SPH)
    assert r["cone_angle_est_deg"] == pytest.approx(np.rad2deg(np.arccos(1500 / 1450 * np.cos(np.deg2rad(30)))), abs=0.02)


@pytest.mark.parametrize("c_true", [1450.0, 1550.0])
@pytest.mark.parametrize("el", [0.0, -10.0, -30.0])
def test_horizontal_plane_azimuth_unbiased_elevation_biased(c_true, el):
    r = mismatch_peak(uniform_rectangular(2, 2, 0.3, 0.3), 1000.0, c_true, 1500.0, 60.0, el, SPH)
    assert abs(r["az_error_deg"]) < 0.05
    assert r["abs_el_error_deg"] == pytest.approx(r["abs_el_pred_error_deg"], abs=0.05)


def test_regular_tetrahedron_direction_nearly_unbiased():
    e = 0.3
    tet = e / np.sqrt(8) * np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]])
    for az, el in ((0, 0), (60, -20), (135, 40)):
        r = mismatch_peak(from_coordinates(tet), 300.0, 1450.0, 1500.0, az, el, SPH)
        assert r["direction_error_deg"] < 0.1
