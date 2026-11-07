"""Metric definitions against independent analytic or brute-force calculations."""

import numpy as np
import pytest

from conftest import C, bisect, dirichlet_power, manifold
from picket_sim.analysis import AnalysisSettings, Steering, analyze_frequency, steering_thresholds
from picket_sim.beamforming import beampattern_power
from picket_sim.conventions import horizontal_cut, unit_vector
from picket_sim.geometry import uniform_linear, uniform_rectangular
from picket_sim.grids import SphereGrid, cut_offsets_deg, log_frequency_grid
from picket_sim.metrics import (
    aliasing_onset_hz,
    circular_profile_metrics,
    first_crossing_frequency,
    observable_lobe_metrics,
)

GAM = cut_offsets_deg(3600)


# ---------------------------------------------------------------- circular cut metric on synthetic profiles
def test_cut_metrics_cos_squared_profile():
    p = np.cos(np.deg2rad(GAM)) ** 2  # half power at +-45, minima at +-90, mirror lobe at 180
    m = circular_profile_metrics(GAM, p)
    assert m.hpbw_deg == pytest.approx(90.0, abs=1e-3)
    assert m.mainlobe_left_deg == pytest.approx(90.0) and m.mainlobe_right_deg == pytest.approx(90.0)
    assert m.max_outside == pytest.approx(1.0) and abs(m.max_outside_gamma_deg) == pytest.approx(180.0)


def test_cut_metrics_flat_profile_is_undefined():
    m = circular_profile_metrics(GAM, np.ones_like(GAM))
    assert np.isnan(m.hpbw_deg) and m.hpbw_reason
    assert np.isnan(m.max_outside) and m.outside_reason


def test_cut_metrics_single_lobe_without_sidelobes():
    p = np.exp(-((GAM / 20.0) ** 2))
    m = circular_profile_metrics(GAM, p)
    assert m.hpbw_deg == pytest.approx(2 * 20 * np.sqrt(np.log(2)), abs=2e-3)
    assert np.isnan(m.max_outside)  # minima meet at 180 deg: no outside region


def test_cut_metrics_reject_profile_not_peaked_at_steering():
    with pytest.raises(ValueError):
        circular_profile_metrics(GAM, np.cos(np.deg2rad(GAM - 30.0)) ** 2 * 0.5 + 0.25 + 0.25 * (GAM > 0))


# ---------------------------------------------------------------- ULA beamwidth and sidelobes
def test_ula_broadside_hpbw_matches_independent_root():
    n, d, f = 4, 0.15, 5000.0
    k = 2 * np.pi * f / C
    x_h = bisect(lambda x: dirichlet_power(n, np.array([x]))[0] - 0.5, 1e-9, 2 * np.pi / n)
    expected = 2 * np.rad2deg(np.arcsin(x_h / (k * d)))
    man = manifold(uniform_linear(n, d))
    m = circular_profile_metrics(GAM, beampattern_power(man, f, unit_vector(90, 0), horizontal_cut(90, 0, GAM)))
    assert m.hpbw_deg == pytest.approx(expected, abs=0.01)
    # classical large-N approximation 0.886 lambda/(N d) rad is within ~5 % for N = 4
    assert m.hpbw_deg == pytest.approx(np.rad2deg(0.886 * (C / f) / (n * d)), rel=0.06)


def test_ula_psl_matches_brute_force_and_textbook_value():
    n, d, f = 4, 0.15, 5000.0
    man = manifold(uniform_linear(n, d))
    lm = observable_lobe_metrics(man, f, unit_vector(90, 0))
    p = np.linspace(-1, 1, 2_000_001)
    pw = dirichlet_power(n, 2 * np.pi * f / C * d * p)
    brute = 10 * np.log10(pw[np.abs(p) > (C / f) / (n * d)].max())  # beyond the first nulls at |p| = lambda/(N d)
    assert lm.psl_db == pytest.approx(brute, abs=1e-6)
    assert lm.psl_db == pytest.approx(-11.30, abs=0.01)  # N = 4 uniform line array first sidelobe


def test_aperture_increases_resolution_and_gain():
    f = 2000.0
    widths = []
    for n in (2, 3, 4, 6, 8):
        m = analyze_frequency(manifold(uniform_linear(n, 0.15)), f, [Steering("b", 90.0, 0.0)],
                              AnalysisSettings(SphereGrid(31, 60), use_sphere_for_rank1=False))[0]
        widths.append(m["hpbw_h_deg"])
    w = np.array(widths, dtype=float)
    assert np.all(np.isfinite(w[2:])) and np.all(np.diff(w[np.isfinite(w)]) < 0)
    widths_d = []
    for d in (0.1, 0.2, 0.3):  # all below c/(2 f) = 0.375 m
        m = circular_profile_metrics(GAM, beampattern_power(manifold(uniform_linear(4, d)), f, unit_vector(90, 0),
                                                            horizontal_cut(90, 0, GAM)))
        widths_d.append(m.hpbw_deg)
    assert widths_d[0] > widths_d[1] > widths_d[2]


# ---------------------------------------------------------------- aliasing
def test_grating_lobe_at_half_wavelength_criterion():
    n, d = 4, 0.15
    man = manifold(uniform_linear(n, d))
    f_g = C / (2 * d)  # 5 kHz
    back = unit_vector(180, 0)[None, :]
    assert beampattern_power(man, f_g, unit_vector(0, 0), back)[0] == pytest.approx(1.0, abs=1e-12)
    assert beampattern_power(man, 0.95 * f_g, unit_vector(0, 0), back)[0] < 0.9
    lm = observable_lobe_metrics(man, f_g, unit_vector(0, 0))
    assert lm.psl_db == pytest.approx(0.0, abs=1e-9) and lm.n_lobes_ge[-1.0] == 1
    assert observable_lobe_metrics(man, 4000.0, unit_vector(0, 0)).psl_db < -1.0
    # broadside steering at d = lambda: grating lobes at both endfire directions
    lm = observable_lobe_metrics(man, C / d, unit_vector(90, 0))
    assert lm.n_lobes_ge[-1.0] == 2 and lm.psl_db == pytest.approx(0.0, abs=1e-9)


def test_worst_case_aliasing_onset_line_array_independent():
    n, d = 4, 0.15
    out = aliasing_onset_hz(uniform_linear(n, d), C, (-1.0, -3.0), 10_000.0)
    for L in (-1.0, -3.0):
        x_l = bisect(lambda x: dirichlet_power(n, np.array([x]))[0] - 10 ** (L / 10), 1e-9, 2 * np.pi / n)
        q = (2 * np.pi - x_l) / d  # edge of the grating lobe centred at q d = 2 pi
        assert out[L] == pytest.approx(C * q / (4 * np.pi), rel=2e-3)
    assert out[-1.0] < C / (2 * d)


def test_worst_case_aliasing_onset_square_brute_force():
    d = 0.30
    out = aliasing_onset_hz(uniform_rectangular(2, 2, d, d), C, (-1.0, -3.0), 10_000.0, n_dirs_2d=2880)
    q = np.arange(-25.0, 25.0, 0.01)
    qx, qy = np.meshgrid(q, q)
    w2 = np.cos(qx * d / 2) ** 2 * np.cos(qy * d / 2) ** 2
    outside = np.maximum(np.abs(qx), np.abs(qy)) >= np.pi / d  # mainlobe of the separable 2x2 factor
    r = np.hypot(qx, qy)
    for L in (-1.0, -3.0):
        qmin = r[outside & (w2 >= 10 ** (L / 10))].min()
        assert out[L] == pytest.approx(C * qmin / (4 * np.pi), rel=3e-3)


def test_single_sensor_aliasing_undefined(candidates):
    out = aliasing_onset_hz(candidates["A0"], C)
    assert out[-1.0] is None and "single sensor" in out["reason"]


def test_planar_psl_on_sphere_matches_disk_brute_force(sphere):
    d, f = 0.30, 2000.0
    g = uniform_rectangular(2, 2, d, d)
    k = 2 * np.pi * f / C
    p0 = np.array([np.cos(np.deg2rad(30)), np.sin(np.deg2rad(30))])
    lm = observable_lobe_metrics(manifold(g), f, unit_vector(30, 0), sphere=sphere)
    x = np.linspace(-1, 1, 4001)
    px, py = np.meshgrid(x, x)
    inside = px ** 2 + py ** 2 <= 1
    qx, qy = k * (px - p0[0]), k * (py - p0[1])
    w2 = np.cos(qx * d / 2) ** 2 * np.cos(qy * d / 2) ** 2
    outside = np.maximum(np.abs(qx), np.abs(qy)) >= np.pi / d
    brute = 10 * np.log10(w2[inside & outside].max())
    assert lm.psl_db == pytest.approx(brute, abs=0.02)


def test_worst_case_onset_bounds_steering_specific_onsets(candidates):
    sph = SphereGrid(61, 120)
    s = AnalysisSettings(sph, cut_points=720, reduced_1d_points=1601)
    fg = log_frequency_grid(100, 10000, 20)
    for key in ("A1", "A3", "A4"):
        worst = aliasing_onset_hz(candidates[key], C, (-3.0,), 10_000.0)[-3.0]
        for az in (0.0, 50.0, 90.0):
            t = steering_thresholds(manifold(candidates[key]), Steering("h", az, 0.0), fg, s)
            if t["f_amb_m3db_status"] == "ok":
                assert worst <= t["f_amb_m3db_hz"] * 1.01


# ---------------------------------------------------------------- thresholds and undefined metrics
def test_first_sidelobe_onset_line_array_broadside():
    n, d = 4, 0.15
    s = AnalysisSettings(SphereGrid(31, 60), use_sphere_for_rank1=False)
    t = steering_thresholds(manifold(uniform_linear(n, d)), Steering("b", 90.0, 0.0),
                            log_frequency_grid(100, 10000, 30), s, rel_tol=1e-5)
    assert t["f_sl_hz"] == pytest.approx(C / (n * d), rel=2e-3)  # first null reaches endfire: N d = lambda


def test_half_power_onset_two_element_endfire():
    d = 0.30
    s = AnalysisSettings(SphereGrid(31, 60), use_sphere_for_rank1=False)
    t = steering_thresholds(manifold(uniform_linear(2, d)), Steering("e", 0.0, 0.0),
                            log_frequency_grid(100, 10000, 30), s, rel_tol=1e-6)
    # P(p) = cos^2(k d (p - 1)/2), minimum at p = -1: cos^2(k d) = 1/2 -> k d = pi/4 -> f = c/(8 d)
    assert t["f_hp_hz"] == pytest.approx(C / (8 * d), rel=1e-4)


def test_rank1_hpsf_exact_and_sphere_grid(sphere):
    d = 0.30
    f = C / (2 * d)  # k d = pi
    man = manifold(uniform_linear(2, d))
    lm = observable_lobe_metrics(man, f, unit_vector(90, 0))
    # P = cos^2(pi p / 2) >= 1/2  <=>  |p| <= 1/2 ; u.axis is uniform on [-1, 1] -> fraction 1/2
    assert lm.hpsf == pytest.approx(0.5, abs=1e-3)
    row = analyze_frequency(man, f, [Steering("b", 90.0, 0.0)], AnalysisSettings(sphere))[0]
    assert row["hpsf_sphere_grid"] == pytest.approx(0.5, abs=0.01)


def test_single_hydrophone_metrics_are_undefined_not_numbers(candidates, sphere):
    row = analyze_frequency(manifold(candidates["A0"]), 5000.0, [Steering("h", 10.0, 0.0)], AnalysisSettings(sphere))[0]
    assert row["di_db"] == 0.0 and row["hpsf"] == 1.0
    for k in ("hpbw_h_deg", "hpbw_v_deg", "psl_obs_db", "max_outside_h_db"):
        assert np.isnan(row[k]), k
    assert row["psl_obs_reason"] and row["hpbw_h_reason"]


def test_line_array_vertical_cut_at_broadside_is_undefined(candidates, sphere):
    row = analyze_frequency(manifold(candidates["A2"]), 5000.0, [Steering("h", 90.0, 0.0)], AnalysisSettings(sphere))[0]
    assert np.isnan(row["hpbw_v_deg"])  # cone ambiguity: the vertical great circle lies on the cone
    assert row["max_outside_h_db"] == pytest.approx(0.0, abs=1e-9)  # left/right mirror on the horizontal cut


def test_first_crossing_frequency_bisection():
    fg = log_frequency_grid(100, 10000, 10)
    f, s = first_crossing_frequency(lambda f: f >= 1234.5, fg, rel_tol=1e-7)
    assert s == "ok" and f == pytest.approx(1234.5, rel=1e-6)
    assert first_crossing_frequency(lambda f: True, fg)[1] == "below_grid"
    f, s = first_crossing_frequency(lambda f: False, fg)
    assert s == "not_reached" and np.isnan(f)


def test_metrics_depend_only_on_f_over_c(candidates, sphere):
    s = AnalysisSettings(sphere, cut_points=720)
    st = [Steering("h", 40.0, 0.0)]
    for key in ("A2", "A3", "A4"):
        r1 = analyze_frequency(manifold(candidates[key], 1500.0), 2000.0, st, s)[0]
        r2 = analyze_frequency(manifold(candidates[key], 1450.0), 2000.0 * 1450 / 1500, st, s)[0]
        for k in ("di_db", "hpsf", "hpbw_h_deg", "psl_obs_db"):
            if np.isfinite(r1[k]):
                assert r2[k] == pytest.approx(r1[k], abs=1e-6), (key, k)
