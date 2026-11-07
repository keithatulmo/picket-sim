"""SIM-02A model verification: provenance, acquisition chain, noise fields, errors, statistics, gain."""

import numpy as np
import pytest

from conftest import C, manifold
from picket_sim.acoustics import steering_vectors
from picket_sim.avs import first_order_di_db, first_order_di_numeric_db
from picket_sim.beamforming import beampattern_power
from picket_sim.config import build_array
from picket_sim.conventions import fibonacci_sphere, unit_vector
from picket_sim.errors import ErrorModel
from picket_sim.geometry import envelope_volumetric, uniform_circular, uniform_linear
from picket_sim.noise import directivity_index_db
from picket_sim.noisefields import (
    NoiseField,
    NoiseModelError,
    bessel_j0,
    check_covariance,
    coherence_directional,
    coherence_exponential,
    coherence_far_field,
    coherence_horizontal,
    coherence_spherical,
    density_upward,
    density_uniform,
    near_field_vector,
)
from picket_sim.params import BOLTZMANN_J_PER_K, ParamError, parse_param
from picket_sim.rag import horizontal_scan_with_errors, rag_db, rag_with_errors_db
from picket_sim.sensor import ADC, AcquisitionChain, Hydrophone, Preamplifier, PowerLawSpectrum, band_power
from picket_sim.stats import case_rng, mean_ci, quantile_ci, wilson_ci

A = "assumed"
SRC = "test value, assumed for verification only"


# ============================================================ provenance
def test_provenance_is_enforced():
    p = parse_param("capacitance_f", {"value": 1e-9, "provenance": A, "source": SRC})
    assert p.unit == "F" and p.provenance == "assumed"
    with pytest.raises(ParamError):
        parse_param("capacitance_f", {"value": 1e-9, "provenance": "guessed", "source": SRC})
    with pytest.raises(ParamError):
        parse_param("capacitance_f", {"value": 1e-9, "provenance": A, "source": ""})
    with pytest.raises(ParamError):
        parse_param("capacitance_f", {"value": 1e-9, "provenance": A})
    with pytest.raises(ParamError):  # unit error: sensitivity in V/Pa instead of dB re 1 V/uPa
        parse_param("sensitivity_db_re_1v_per_upa", {"value": 0.001, "provenance": A, "source": SRC})
    with pytest.raises(ParamError):
        parse_param("not_a_key_hz", {"value": 1.0, "provenance": A, "source": SRC})


def test_boltzmann_is_the_si_defined_value():
    assert BOLTZMANN_J_PER_K == 1.380649e-23


# ============================================================ acquisition chain
def chain(bits=24, fs=96000.0, bw=(10.0, 30000.0), g_db=20.0, en=2e-9, i_n=1e-15, fc=0.0):
    return AcquisitionChain("T", Hydrophone(-190.0, 5e-9, 0.01, 290.0),
                            Preamplifier(g_db, en, i_n, fc, 10.0), ADC(bits, 2.5, fs), bw[0], bw[1])


def test_hydrophone_thermal_noise_hand_calculation():
    h = Hydrophone(-190.0, 5e-9, 0.01, 290.0)
    f = 1000.0
    w, c, t = 2 * np.pi * f, 5e-9, 0.01
    re_z = t / (w * c * (1 + t * t))  # Re{1 / (j w C (1 - j tan d))}
    assert np.real(h.impedance_ohm(f)) == pytest.approx(re_z, rel=1e-12)
    assert h.thermal_noise_v2_per_hz(f) == pytest.approx(4 * 1.380649e-23 * 290.0 * re_z, rel=1e-12)
    # input-referred: divide by M^2, M = 10^(-190/20) V/uPa
    ch = chain()
    assert ch.thermal_upa2_per_hz(f) == pytest.approx(h.thermal_noise_v2_per_hz(f) / 10 ** (-19.0), rel=1e-12)


def test_preamp_and_adc_noise_and_clip_level():
    ch = chain(bits=16, fs=48000.0, bw=(10.0, 20000.0), g_db=40.0, en=4e-9, i_n=0.0, fc=100.0)
    f = 50.0
    assert ch.preamp.input_noise_v2_per_hz(f, 1.0) == pytest.approx((4e-9) ** 2 * 3.0)  # 1 + 100/50
    lsb = 5.0 / 2 ** 16
    assert ch.adc.quantization_psd_v2_per_hz == pytest.approx(lsb ** 2 / 12 / 24000.0)
    m, g = 10 ** (-190 / 20), 100.0
    assert ch.adc_upa2_per_hz(f) == pytest.approx(lsb ** 2 / 12 / 24000.0 / (g * m) ** 2)
    assert ch.clip_pressure_upa_peak == pytest.approx(2.5 / (g * m))
    assert ch.clipping_stage == "adc"


def test_dynamic_range_for_a_tone_is_clip_minus_3db_minus_noise():
    ch = chain()
    r = ch.dynamic_range_db(100.0, 1000.0, crest_factor_db=20 * np.log10(np.sqrt(2)))
    noise_db = 10 * np.log10(band_power(ch.self_noise_upa2_per_hz, 100.0, 1000.0))
    assert r["dr_over_self_noise_db"] == pytest.approx(20 * np.log10(ch.clip_pressure_upa_peak) - 3.0103 - noise_db,
                                                       abs=1e-3)


def test_band_power_matches_analytic_power_law():
    s = PowerLawSpectrum("x", 60.0, 1000.0, -20.0)  # S = 10^6 (f/1000)^-2
    exact = 1e6 * 1000.0 ** 2 * (1 / 100.0 - 1 / 1000.0)
    assert band_power(s, 100.0, 1000.0) == pytest.approx(exact, rel=1e-5)
    flat = PowerLawSpectrum("y", 0.0, 1000.0, 0.0)
    assert band_power(flat, 10.0, 20.0) == pytest.approx(10.0, rel=1e-6)


def test_acquisition_rejects_nyquist_and_bandwidth_violations():
    with pytest.raises(ParamError):  # declared band at Nyquist
        chain(fs=40000.0, bw=(10.0, 20000.0))
    ch = chain(fs=48000.0, bw=(20.0, 20000.0))
    with pytest.raises(ParamError):
        ch.check_band(10.0, 200.0)  # below declared low edge
    with pytest.raises(ParamError):
        ch.check_band(10000.0, 24000.0)  # at Nyquist
    assert ch.covers(20.0, 200.0) and not ch.covers(10000.0, 22000.0)


# ============================================================ noise fields
def test_bessel_j0_tabulated_values():
    assert bessel_j0(np.array(0.0)) == pytest.approx(1.0, abs=1e-15)
    assert bessel_j0(np.array(1.0)) == pytest.approx(0.7651976865579666, abs=1e-14)
    assert bessel_j0(np.array(2.404825557695773)) == pytest.approx(0.0, abs=1e-14)
    assert bessel_j0(np.array(10.0)) == pytest.approx(-0.2459357644513483, abs=1e-14)
    assert bessel_j0(np.array(300.0)) == pytest.approx(np.sqrt(2 / (np.pi * 300)) * np.cos(300 - np.pi / 4), abs=2e-4)


@pytest.mark.parametrize("key", ["A1", "A3", "A4"])
def test_coherence_models_are_psd_with_unit_diagonal(candidates, key):
    pos = candidates[key].positions_m
    for f in (100.0, 2000.0, 15000.0):
        k = 2 * np.pi * f / C
        for g in (coherence_spherical(pos, k), coherence_horizontal(pos, k), coherence_exponential(pos, 0.2),
                  coherence_far_field(pos, k, unit_vector(30, -10))):
            check_covariance(g)
            np.testing.assert_allclose(np.diag(g), 1.0, atol=1e-12)


def test_uniform_directional_density_reproduces_sinc(candidates):
    pos = candidates["A4"].positions_m
    k = 2 * np.pi * 3000.0 / C
    np.testing.assert_allclose(coherence_directional(pos, k, density_uniform), coherence_spherical(pos, k), atol=1e-8)


def test_horizontal_coherence_equals_ring_average():
    pos = uniform_circular(6, 0.9).positions_m + np.array([[0, 0, 0.0], [0, 0, 0.3], [0, 0, -0.2],
                                                          [0, 0, 0.1], [0, 0, 0], [0, 0, 0.05]])
    k = 2 * np.pi * 2500.0 / C
    az = np.linspace(-180, 180, 7200, endpoint=False)
    a = np.exp(1j * k * (unit_vector(az, 0.0) @ pos.T))
    ring = a.T @ a.conj() / len(az)
    np.testing.assert_allclose(coherence_horizontal(pos, k), ring, atol=1e-10)


def test_upward_density_against_independent_fibonacci_quadrature(candidates):
    pos = candidates["A3"].positions_m + np.array([[0, 0, 0.0], [0, 0, 0.2], [0, 0, -0.1], [0, 0, 0.05]])
    k = 2 * np.pi * 1500.0 / C
    dens = density_upward(2.0)
    u = fibonacci_sphere(400_000)
    w = dens(u)
    a = np.exp(1j * k * (u @ pos.T))
    ref = (a.T * w) @ a.conj() / w.sum()
    np.testing.assert_allclose(coherence_directional(pos, k, dens), ref, atol=2e-4)
    assert np.abs(coherence_directional(pos, k, dens)[0, 1].imag) > 1e-3  # vertical asymmetry -> complex


def test_near_field_vector_level_and_far_field_limit():
    pos = uniform_linear(4, 0.3).positions_m
    k = 2 * np.pi * 1000.0 / C
    xs = np.array([-3.0, 0.0, 1.0])
    h = near_field_vector(pos, k, xs)
    rho = np.linalg.norm(xs - pos, axis=1)
    np.testing.assert_allclose(np.abs(h), np.linalg.norm(xs) / rho, rtol=1e-12)
    u = unit_vector(150.0, 20.0)
    hf = near_field_vector(pos, k, 1e7 * u)
    pw = np.exp(1j * k * (pos @ u))
    np.testing.assert_allclose(hf / hf[0], pw / pw[0], atol=1e-5)
    with pytest.raises(NoiseModelError):
        near_field_vector(pos, k, pos[0] + 0.01)


def test_invalid_covariances_and_fields_fail_visibly():
    with pytest.raises(NoiseModelError):
        check_covariance(np.array([[1.0, 2.0], [2.0, 1.0]]))  # eigenvalue -1
    with pytest.raises(NoiseModelError):
        check_covariance(np.array([[1.0, 0.5j], [0.5j, 1.0]]))  # not Hermitian
    with pytest.raises(NoiseModelError):
        NoiseField.from_config({"id": "bad", "components": [{"type": "spherical", "fraction": 0.7}]})
    with pytest.raises(NoiseModelError):
        coherence_exponential(np.zeros((2, 3)) + [[0, 0, 0], [1, 0, 0]], 0.0)


# ============================================================ realized array gain
def test_rag_limits(candidates):
    u = np.stack([unit_vector(a, 0) for a in (0, 40, 90)])
    for key in ("A1", "A3", "A4"):
        g = candidates[key]
        for f in (200.0, 3000.0):
            k = 2 * np.pi * f / C
            white = rag_db(g.positions_m, f, C, u, np.eye(4))
            np.testing.assert_allclose(white, 10 * np.log10(4), atol=1e-12)
            iso = rag_db(g.positions_m, f, C, u, coherence_spherical(g.positions_m, k))
            np.testing.assert_allclose(iso, directivity_index_db(manifold(g), f, u), atol=1e-10)  # SIM-01 DI
            big = rag_db(g.positions_m, f, C, u, coherence_spherical(g.positions_m, k), eta=1e6)
            np.testing.assert_allclose(big, 10 * np.log10(4), atol=1e-4)
    a0 = candidates["A0"]
    assert rag_db(a0.positions_m, 1000.0, C, u[:1], np.eye(1), eta=0.3)[0] == pytest.approx(0.0, abs=1e-12)


def test_rag_with_interferer_in_a_null():
    g = uniform_linear(2, 0.375)
    f = C / (2 * 0.375)  # k d = pi: a broadside-steered pair has its nulls at endfire
    gam = np.eye(2)
    h = steering_vectors(g.positions_m, unit_vector(0, 0), f, C)
    base = rag_db(g.positions_m, f, C, unit_vector(90, 0)[None, :], gam)[0]
    with_int = rag_db(g.positions_m, f, C, unit_vector(90, 0)[None, :], gam, hnr=100.0, host_vector=h)[0]
    assert with_int - base == pytest.approx(10 * np.log10(101.0), abs=1e-9)  # array rejects it, A0 does not


# ============================================================ channel errors and Monte Carlo
@pytest.mark.parametrize("em", [
    ErrorModel("phase", 0.0, 15.0, 0.0, 0.0),
    ErrorModel("gain", 1.5, 0.0, 0.0, 0.0),
    ErrorModel("position", 0.0, 0.0, 0.01, 0.0),
    ErrorModel("timing", 0.0, 0.0, 0.0, 20e-6),
    ErrorModel("combined", 0.7, 5.0, 0.004, 5e-6),
])
def test_mainlobe_and_null_power_match_closed_form(em):
    n, f = 6, 3000.0
    g = uniform_circular(n, 0.45)
    rng = case_rng(1234, "unit", em.scenario_id)
    draw = em.sample(rng, 4000, n)
    p = horizontal_scan_with_errors(g.positions_m, f, C, 30.0, np.array([30.0]), draw)[:, 0]
    s = mean_ci(p)
    expect = em.expected_mainlobe_power(n, f, C)
    assert abs(s["mean"] - expect) < 4 * s["se"]
    # null filling at an exact null of a uniform line (endfire source, broadside look at k d = pi ... use ULA null)
    ula = uniform_linear(4, 0.25)
    fn = C / (4 * 0.25)  # first null at u_x = lambda/(N d) = 1 for broadside steering -> source at endfire
    draw4 = em.sample(case_rng(99, "null", em.scenario_id), 4000, 4)
    pn = horizontal_scan_with_errors(ula.positions_m, fn, C, 0.0, np.array([90.0]), draw4)[:, 0]
    sn = mean_ci(pn)
    assert abs(sn["mean"] - em.expected_null_power(4, fn, C)) < 4 * sn["se"] + 1e-12


def test_ideal_draw_reproduces_error_free_results(candidates):
    g = candidates["A4"]
    em = ErrorModel("ideal", 0, 0, 0, 0)
    draw = em.sample(case_rng(0, "ideal"), 3, 4)
    scan_az = np.linspace(-180, 180, 73)
    p = horizontal_scan_with_errors(g.positions_m, 800.0, C, 50.0, scan_az, draw)
    ref = beampattern_power(manifold(g), 800.0, unit_vector(scan_az, 0.0), unit_vector(50.0, 0.0)[None, :])[:, 0]
    np.testing.assert_allclose(p[0], ref, atol=1e-12)  # symmetric in steering/look for unit-modulus DAS
    k = 2 * np.pi * 800.0 / C
    r1 = rag_with_errors_db(g.positions_m, 800.0, C, unit_vector(50, 0), draw, eta_th=0.2, eta_el=0.3)
    r2 = rag_db(g.positions_m, 800.0, C, unit_vector(50, 0)[None, :], coherence_spherical(g.positions_m, k), eta=0.5)
    np.testing.assert_allclose(r1, r2[0], atol=1e-10)


def test_error_model_validation():
    with pytest.raises(ParamError):
        ErrorModel("bad", -0.1, 0, 0, 0)
    with pytest.raises(ParamError):
        ErrorModel("bad", 0, float("nan"), 0, 0)


def test_statistics_helpers():
    w = wilson_ci(0, 10)
    assert w["lo"] == 0.0 and w["hi"] == pytest.approx(0.2775, abs=1e-4)
    hits = 0
    for i in range(400):
        x = case_rng(7, "cov", i).normal(0.0, 1.0, 300)
        s = mean_ci(x)
        hits += s["lo"] <= 0.0 <= s["hi"]
    assert 0.92 <= hits / 400 <= 0.98  # nominal 95 % coverage
    q = quantile_ci(case_rng(8, "q").normal(0, 1, 2000), 0.5)
    assert q["lo"] <= 0.0 <= q["hi"]
    with pytest.raises(ValueError):
        mean_ci(np.zeros(50))  # below the minimum sample size


def test_case_rng_is_order_independent_and_reproducible():
    a = case_rng(1, "A3", 1000.0, "E2").normal(size=5)
    case_rng(1, "other").normal(size=100)
    b = case_rng(1, "A3", 1000.0, "E2").normal(size=5)
    np.testing.assert_array_equal(a, b)
    assert not np.allclose(a, case_rng(1, "A3", 1000.0, "E3").normal(size=5))


# ============================================================ geometry and AVS support
def test_new_geometries_and_a4_regression(baseline_cfg):
    u6 = uniform_circular(6, 0.45)
    assert u6.aperture_m == pytest.approx(0.45) and u6.observability.rank == 2
    assert u6.min_spacing_m == pytest.approx(0.45 * np.sin(np.pi / 6))
    a4 = build_array(next(a for a in baseline_cfg["arrays"] if a["id"] == "A4"))
    np.testing.assert_allclose(envelope_volumetric(1.0, 0.85, 0.75).positions_m, a4.positions_m, atol=1e-15)
    assert envelope_volumetric(4.0, 2.0, 0.25).observability.rank == 3


def test_first_order_vector_sensor_directivity():
    for alpha, d in ((1.0, 1.0), (0.0, 3.0), (0.5, 3.0), (0.25, 4.0)):
        assert first_order_di_db(alpha) == pytest.approx(10 * np.log10(d), abs=1e-12)
        assert first_order_di_numeric_db(alpha) == pytest.approx(10 * np.log10(d), abs=1e-6)
    grid = np.linspace(0, 1, 1001)
    assert grid[np.argmax([first_order_di_db(a) for a in grid])] == pytest.approx(0.25)
