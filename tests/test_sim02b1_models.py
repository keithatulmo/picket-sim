"""Independent verification of the SIM-02B.1 signal, synthesis, detector and threshold models.

Reviewer requirements (SIM-02A review, section 6): broadband signal generation, spectral power, covariance,
acquisition gain, detector null distributions, false-alarm calibration, TDOA sign conventions and
timing-error propagation. Reference values are computed independently of the code under test (direct
time-domain DFTs, closed forms, plain NumPy statistics).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import yaml

from picket_sim import detection as dt
from picket_sim.detectors import Detectors, beam_sigma, beam_weights, harmonic_index, normalize
from picket_sim.noisefields import NoiseModelError, coherence_exponential, coherence_horizontal, coherence_spherical
from picket_sim.sensor import chain_from_config
from picket_sim.signals import (Grid, SignalError, broadband_bins, chirp_bins, chirp_reference, delays_s,
                                harmonic_bins, tone_bins)
from picket_sim.stats import wilson_ci
from picket_sim.synthesis import (CoherenceSpec, NoiseScenario, check_covariance_stack, coherence_bins,
                                  covariance_factor, draw_noise, steering_bins, to_waveform, welch_csd)

C = 1500.0
RNG = np.random.default_rng(20261108)
SQUARE = np.array([[0.15, 0.15, 0], [-0.15, 0.15, 0], [-0.15, -0.15, 0], [0.15, -0.15, 0.0]])


def _band_dft(x: np.ndarray, grid: Grid) -> np.ndarray:
    """Reference: direct DFT of sampled waveforms, band bins, normalized units."""
    return np.fft.rfft(np.atleast_2d(x), axis=1)[:, grid.k] / grid.scale


# ------------------------------------------------------------------------------------------- grid
def test_grid_rejects_invalid_configurations():
    with pytest.raises(SignalError):
        Grid(1.0, 1000.0, 20.0, 600.0)  # band edge above Nyquist
    with pytest.raises(SignalError):
        Grid(0.1234567, 1000.0, 20.0, 200.0)  # non-integer number of samples
    g = Grid(1.0, 1000.0, 20.0, 200.0)
    assert g.K == 181 and g.f[0] == 20.0 and g.f[-1] == 200.0 and g.n_samples == 1000


# ------------------------------------------------------------------------------------------- signals
@pytest.mark.parametrize("f0", [123.4567, 150.0, 21.3])
def test_tone_bins_match_direct_dft_of_delayed_sampled_tone(f0):
    g = Grid(0.5, 1000.0, 20.0, 200.0)
    tau = np.array([0.0, 1.234e-4, -3.3e-4])
    A, ph = 2.5, 0.7
    t = np.arange(g.n_samples) / g.fs
    x = A * np.cos(2 * np.pi * f0 * (t[None, :] - tau[:, None]) + ph)
    np.testing.assert_allclose(tone_bins(g, f0, A, ph, tau), _band_dft(x, g), atol=1e-9 * A * g.n_samples / g.scale)


def test_harmonic_bins_are_the_sum_of_their_tones():
    g = Grid(1.0, 1000.0, 20.0, 200.0)
    tau = np.array([0.0, 2e-4])
    t = np.arange(g.n_samples) / g.fs
    amps, phs, f0 = np.array([1.0, 0.5, 0.25]), np.array([0.1, 1.2, -2.0]), 31.7
    x = sum(a * np.cos(2 * np.pi * h * f0 * (t[None, :] - tau[:, None]) + p)
            for h, (a, p) in enumerate(zip(amps, phs), start=1))
    np.testing.assert_allclose(harmonic_bins(g, f0, amps, phs, tau), _band_dft(x, g), atol=1e-9)


def test_tone_energy_convention_equals_power_times_window():
    """sum |x_k|^2 / G = P T / G for an on-bin tone (ADR-0015): normalized units carry PSD scaling."""
    g = Grid(2.0, 4000.0, 200.0, 1800.0)
    A = 3.0
    xk = tone_bins(g, 500.0, A, 0.3, np.zeros(1))
    assert np.sum(np.abs(xk) ** 2) == pytest.approx((A * A / 2) * g.T, rel=1e-9)


def test_chirp_reference_matches_shifted_time_domain_pulse_and_parseval():
    g = Grid(0.2, 10000.0, 200.0, 2000.0)
    ref = chirp_reference(g, 500.0, 1500.0, 0.05, 0.2)
    shift = 137  # integer samples: band-limited delay equals the circular shift exactly
    n_p = int(round(0.05 * g.fs))
    t = np.arange(n_p) / g.fs
    from picket_sim.signals import tukey
    pulse = tukey(n_p, 0.2) * np.cos(2 * np.pi * (500.0 * t + 0.5 * (1000.0 / 0.05) * t * t))
    x = np.zeros(g.n_samples)
    x[shift:shift + n_p] = pulse
    got = chirp_bins(g, ref, 1.0, shift / g.fs, np.zeros(1))
    np.testing.assert_allclose(got, _band_dft(x, g), atol=1e-8)
    energy = np.sum(pulse ** 2) / g.fs
    assert np.sum(np.abs(ref) ** 2) == pytest.approx(energy, rel=2e-3)  # in-band energy (>= 99.9 %)


def test_chirp_outside_band_or_too_long_fails_visibly():
    g = Grid(0.1, 10000.0, 200.0, 2000.0)
    with pytest.raises(SignalError):
        chirp_reference(g, 100.0, 1500.0, 0.05, 0.2)
    with pytest.raises(SignalError):
        chirp_reference(g, 500.0, 1500.0, 0.2, 0.2)


def test_broadband_power_and_cross_channel_phase():
    g = Grid(1.0, 10000.0, 200.0, 2000.0)
    psd = 7.0
    tau = np.array([0.0, 3e-4])
    acc = np.zeros(g.K)
    for _ in range(400):
        b = broadband_bins(g, psd, tau, RNG)
        acc += np.abs(b[0]) ** 2
        np.testing.assert_allclose(b[1], b[0] * np.exp(-2j * np.pi * g.f * 3e-4), atol=1e-12)
    assert acc.mean() / 400 == pytest.approx(psd, rel=0.02)


# ------------------------------------------------------------------------------------------- coherence and covariance
def test_vectorized_coherence_matches_sim02a_functions():
    f = np.array([37.0, 410.0, 2250.0])
    for kind, ref in (("spherical", lambda k: coherence_spherical(SQUARE, k)),
                      ("horizontal", lambda k: coherence_horizontal(SQUARE, k))):
        got = coherence_bins(CoherenceSpec(kind), SQUARE, f, C)
        for i, fi in enumerate(f):
            np.testing.assert_allclose(got[i], ref(2 * np.pi * fi / C).real, atol=1e-12)
    got = coherence_bins(CoherenceSpec("exponential", 0.1), SQUARE, f, C)
    np.testing.assert_allclose(got[1], coherence_exponential(SQUARE, 0.1).real, atol=1e-14)


def test_covariance_check_rejects_invalid_stacks():
    c = np.repeat(np.eye(3)[None], 4, axis=0)
    check_covariance_stack(c)
    bad = c.copy()
    bad[2, 0, 0] = -1.0
    with pytest.raises(NoiseModelError):
        check_covariance_stack(bad)
    asym = c.copy()
    asym[1, 0, 1] = 0.5
    with pytest.raises(NoiseModelError):
        check_covariance_stack(asym)
    with pytest.raises(NoiseModelError):
        CoherenceSpec("exponential")


def _scenario():
    amb = lambda f: 1e4 * (f / 1000.0) ** -1.7  # noqa: E731
    return NoiseScenario("test", [(amb, CoherenceSpec("spherical"))], self_noise=lambda f: 0.1 * amb(f))


def test_synthesized_bins_have_the_model_covariance():
    g = Grid(0.2, 10000.0, 200.0, 2000.0)
    cmat = _scenario().covariance(SQUARE, g.f, C)
    x = draw_noise(covariance_factor(cmat), RNG, 4000)  # (t, K, N)
    for k in (0, g.K // 2, g.K - 1):
        est = np.einsum("tn,tm->nm", x[:, k], x[:, k].conj()) / x.shape[0]
        # relative standard error ~ 1/sqrt(4000); allow 6 standard errors on the diagonal scale
        assert np.max(np.abs(est - cmat[k])) < 6 * cmat[k, 0, 0] / np.sqrt(4000)


def test_waveform_cross_spectral_density_matches_model_and_variance_matches_band_power():
    g = Grid(20.0, 2000.0, 200.0, 800.0)
    sc = _scenario()
    cmat = sc.covariance(SQUARE, g.f, C)
    x = draw_noise(covariance_factor(cmat), RNG, 1)[0].T  # (N, K)
    w = to_waveform(x, g)
    assert w.shape == (4, g.n_samples)
    band_power = np.sum(sc.element_psd(g.f)) * g.df
    assert np.var(w[0]) == pytest.approx(band_power, rel=0.05)
    nper = 400
    fw, gw, nseg = welch_csd(w, g.fs, nper)
    sel = (fw > 260) & (fw < 740)
    model = sc.covariance(SQUARE, fw[sel], C)
    rel = np.abs(gw[sel] - model) / model[:, :1, :1].real  # relative to the element PSD
    assert np.median(rel) < 3.0 / np.sqrt(nseg)
    assert np.max(rel) < 8.0 / np.sqrt(nseg)


# ------------------------------------------------------------------------------------------- acquisition chain
def test_acquisition_chain_input_referral_and_quantization_noise():
    cfg = yaml.safe_load(open("configs/sim02a/sim02a_baseline.yaml"))
    chain, _ = chain_from_config(cfg["sensor_scenarios"][0])
    f = np.array([100.0, 1000.0, 5000.0])
    m = chain.hydrophone.sensitivity_v_per_upa
    g = chain.preamp.gain
    z = chain.hydrophone.impedance_ohm(f)
    out_v2 = ((chain.hydrophone.thermal_noise_v2_per_hz(f) + chain.preamp.input_noise_v2_per_hz(f, z)) * g * g
              + chain.adc.quantization_psd_v2_per_hz)
    np.testing.assert_allclose(out_v2 / (g * m) ** 2, chain.self_noise_upa2_per_hz(f), rtol=1e-12)
    # quantization noise of an actual rounding quantizer (time domain) matches Delta^2 / 12 over fs / 2
    lsb = chain.adc.lsb_v
    v = RNG.standard_normal(200000) * 50 * lsb
    e = np.round(v / lsb) * lsb - v
    assert np.var(e) == pytest.approx(lsb * lsb / 12, rel=0.02)
    assert chain.adc.quantization_psd_v2_per_hz == pytest.approx(lsb * lsb / 12 / (chain.adc.sample_rate_hz / 2))


# ------------------------------------------------------------------------------------------- TDOA and timing
def test_tdoa_sign_convention_by_cross_correlation():
    """A source in direction +x reaches the element at +x first: its waveform leads (ADR-0003, ADR-0016)."""
    g = Grid(1.0, 8000.0, 200.0, 2000.0)
    d = 15 / g.fs * C  # 15 samples of travel time
    pos = np.array([[0.0, 0, 0], [d, 0, 0]])
    tau = delays_s(pos, np.array([1.0, 0, 0]), C)
    assert tau[1] == pytest.approx(-15 / g.fs)
    w = to_waveform(broadband_bins(g, 1.0, tau, RNG), g)
    xc = np.fft.irfft(np.fft.rfft(w[1]) * np.conj(np.fft.rfft(w[0])), n=g.n_samples)
    lag = int(np.argmax(xc))
    lag = lag - g.n_samples if lag > g.n_samples // 2 else lag
    assert lag == -15
    # steering_bins uses the same sign: exp(-j 2 pi f tau)
    np.testing.assert_allclose(steering_bins(pos, [1.0, 0, 0], g.f, C)[:, 1], np.exp(-2j * np.pi * g.f * tau[1]))


def test_timing_error_propagation_matches_closed_form():
    """Random per-channel timing errors sigma_t reduce the coherent beam power to
    [N + N(N-1) exp(-sigma^2)] / N^2 with sigma = 2 pi f sigma_t (SIM-02A closed form)."""
    g = Grid(1.0, 10000.0, 1900.0, 2100.0)
    n, f0, sig_t = 8, 2000.0, 40e-6
    pos = np.c_[0.2 * np.cos(2 * np.pi * np.arange(n) / n), 0.2 * np.sin(2 * np.pi * np.arange(n) / n), np.zeros(n)]
    u = np.array([1.0, 0, 0])
    tau = delays_s(pos, u, C)
    w = steering_bins(pos, u, g.f, C) / n
    k0 = int(np.argmin(np.abs(g.f - f0)))
    p = []
    for _ in range(3000):
        x = tone_bins(g, f0, 1.0, 0.0, tau + RNG.normal(0, sig_t, n))
        p.append(abs(np.sum(w[k0].conj() * x[:, k0])) ** 2)
    ref = abs(np.sum(w[k0].conj() * tone_bins(g, f0, 1.0, 0.0, tau)[:, k0])) ** 2
    s2 = (2 * np.pi * f0 * sig_t) ** 2
    expected = (n + n * (n - 1) * math.exp(-s2)) / n ** 2
    assert np.mean(p) / ref == pytest.approx(expected, abs=4 * np.std(p) / ref / np.sqrt(len(p)))


# ------------------------------------------------------------------------------------------- detectors
def test_normalized_streams_are_unit_variance_and_white_under_matched_noise():
    g = Grid(0.5, 10000.0, 200.0, 2000.0)
    cmat = _scenario().covariance(SQUARE, g.f, C)
    x = draw_noise(covariance_factor(cmat), RNG, 600)
    us = np.array([[1.0, 0, 0], [0, 1.0, 0]])
    w = beam_weights(SQUARE, us, g.f, C)
    for mode, kw in (("single", {}), ("incoherent", {}),
                     ("beam_search", {"search_w": w, "search_sigma": beam_sigma(w, cmat)}),
                     ("beam_known", {"positions_m": SQUARE, "f_hz": g.f, "c_mps": C,
                                     "look_u": np.repeat(us[:1], 600, axis=0)})):
        z = normalize(x, mode, cmat, **kw)
        p = np.abs(z) ** 2
        assert p.mean() == pytest.approx(1.0, abs=0.02), mode
        # adjacent bins uncorrelated
        r = np.mean(z[..., 1:] * z[..., :-1].conj())
        assert abs(r) < 0.02, mode


def test_normalization_reports_mismatch_as_a_level_change():
    g = Grid(0.5, 10000.0, 200.0, 2000.0)
    cmat = _scenario().covariance(SQUARE, g.f, C)
    x = draw_noise(covariance_factor(2.0 * cmat), RNG, 400)  # truth 3 dB above the assumption
    assert (np.abs(normalize(x, "single", cmat)) ** 2).mean() == pytest.approx(2.0, rel=0.03)


def test_detector_null_distributions_match_exact_forms():
    n, K = 40000, 50
    z = (RNG.standard_normal((n, 1, K)) + 1j * RNG.standard_normal((n, 1, K))) / np.sqrt(2)
    det = Detectors()
    st = det.power_stats(np.abs(z) ** 2, "max", ("tonal", "energy"))
    for p in (0.1, 0.01):
        for name, thr in (("tonal", dt.maxexp_isf(p, K)), ("energy", dt.erlang_isf(p, K))):
            k = int(np.sum(st[name] > thr))
            # four simultaneous checks: use a 4-standard-error band rather than four 95 % intervals
            assert abs(k - n * p) <= 4 * math.sqrt(n * p * (1 - p)), (name, p, k)


def test_matched_filter_null_is_unit_exponential_per_lag_and_finds_the_arrival():
    g = Grid(0.2, 10000.0, 200.0, 2000.0)
    ref = chirp_reference(g, 500.0, 1500.0, 0.05, 0.2)
    det = Detectors(replica=ref[None, :], oversample=2)
    z = (RNG.standard_normal((2000, 1, g.K)) + 1j * RNG.standard_normal((2000, 1, g.K))) / np.sqrt(2)
    m = det.mf_lags(z)
    assert np.mean(np.abs(m) ** 2) == pytest.approx(1.0, abs=0.01)
    t0 = 0.0731
    s = chirp_bins(g, ref, 1.0, t0, np.zeros(1))  # unit noise, strong signal
    q = np.abs(det.mf_lags((s * 50)[None]))[0, 0] ** 2
    lag_s = np.argmax(q) * g.T / q.size
    assert abs(lag_s - t0) <= 0.5 * g.T / q.size + 1e-12


def test_harmonic_index_keeps_all_harmonics_in_band():
    g = Grid(1.0, 1000.0, 20.0, 200.0)
    idx = harmonic_index(g, 4)
    assert idx.shape[1] == 4 and idx.min() >= 0 and idx.max() < g.K
    # fundamental grid step is df / H: consecutive fundamentals differ by a quarter bin
    f0 = (idx[:, 0] + g.k[0]) / g.T
    assert np.all(np.diff(f0) >= 0)


# ------------------------------------------------------------------------------------------- thresholds and statistics
def test_threshold_preference_and_empirical_quantile():
    x = RNG.exponential(size=20000)
    assert dt.choose_threshold(1e-3, x, exact=6.9)["method"] == "exact"
    e = dt.choose_threshold(1e-3, x)
    assert e["method"] == "empirical" and e["eta_lo"] <= e["eta"] <= e["eta_hi"]
    assert int(np.sum(x > e["eta"])) == pytest.approx(20, abs=1)
    assert dt.choose_threshold(1e-4, x, bound=9.9)["method"] == "bound"
    assert dt.choose_threshold(1e-4, x)["method"] == "not estimated"


def test_false_alarm_calibration_on_independent_evaluation_set():
    cal, ev = RNG.exponential(size=20000), RNG.exponential(size=20000)
    thr = dt.choose_threshold(1e-2, cal)
    r = dt.realized_pfa(ev, thr["eta"])
    assert r["lo"] <= 1e-2 <= r["hi"]


def test_pd_interval_contains_estimate_and_snr_interpolation():
    pos = RNG.exponential(size=500) * 3
    thr = {"eta": 3.0, "eta_lo": 2.8, "eta_hi": 3.2}
    pd = dt.pd_with_interval(pos, thr)
    assert pd["lo"] <= pd["pd"] <= pd["hi"]
    assert dt.snr_at_pd(np.array([0.0, 2.0, 4.0]), np.array([0.1, 0.3, 0.7]), 0.5) == (3.0, "ok")
    assert dt.snr_at_pd(np.array([0.0, 2.0]), np.array([0.6, 0.9]), 0.5)[1] == "below grid"
    assert dt.snr_at_pd(np.array([0.0, 2.0]), np.array([0.1, 0.2]), 0.5)[1] == "above grid"


def test_incoherent_bound_is_conservative_for_correlated_channels():
    """q_k = mean over channels of |z_n|^2 with correlated channels: the eigenvalue bound must not under-cover."""
    n_ch, K, n = 4, 40, 40000
    pos = SQUARE
    f = np.linspace(100.0, 2000.0, K)
    r = coherence_bins(CoherenceSpec("spherical"), pos, f, C)  # strongly correlated at low frequency
    fac = covariance_factor(r)
    z = draw_noise(fac, RNG, n)  # unit-variance channels
    q = (np.abs(z) ** 2).mean(axis=2).max(axis=1)
    lam = np.linalg.eigvalsh(r)[:, -1]
    for p in (0.1, 0.01):
        x = dt.incoherent_tonal_bound(p, lam, n_ch)
        k = int(np.sum(q > x))
        assert k <= n * p + 4 * math.sqrt(n * p), (p, k / n)
    # white channels: the bound reduces to the exact Gamma(N)/N maximum and is then tight
    lam_w = np.ones(K)
    zw = (RNG.standard_normal((n, K, n_ch)) + 1j * RNG.standard_normal((n, K, n_ch))) / np.sqrt(2)
    qw = (np.abs(zw) ** 2).mean(axis=2).max(axis=1)
    x = dt.incoherent_tonal_bound(0.01, lam_w, n_ch)
    assert abs(int(np.sum(qw > x)) - n * 0.01) <= 4 * math.sqrt(n * 0.01)
