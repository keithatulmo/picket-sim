"""Acoustic primitives: units, delay sign, steering vectors against independent calculations."""

import numpy as np
import pytest

from picket_sim.acoustics import (
    PlaneWaveManifold,
    arrival_time_offsets_s,
    steering_vectors,
    validate_sound_speed,
    wavelength_m,
    wavenumber_rad_per_m,
)
from picket_sim.conventions import unit_vector
from picket_sim.geometry import uniform_linear


def test_units_wavelength_wavenumber():
    assert wavelength_m(1500.0, 1500.0) == pytest.approx(1.0)  # 1 m at 1.5 kHz
    assert wavelength_m(100.0, 1500.0) == pytest.approx(15.0)
    assert wavelength_m(10_000.0, 1500.0) == pytest.approx(0.15)
    assert wavenumber_rad_per_m(1500.0, 1500.0) == pytest.approx(2 * np.pi)
    assert wavenumber_rad_per_m(1000.0, 1500.0) == pytest.approx(2 * np.pi / 1.5)


def test_arrival_time_sign_and_units():
    # element 1 m along +x, source along +x: the wavefront reaches it 1/1500 s EARLIER than the origin
    tau = arrival_time_offsets_s([[0, 0, 0], [1, 0, 0]], unit_vector(0, 0), 1500.0)
    np.testing.assert_allclose(tau, [0.0, -1.0 / 1500.0], rtol=0, atol=1e-18)
    # broadside: simultaneous arrival
    tau = arrival_time_offsets_s([[0, 0, 0], [1, 0, 0]], unit_vector(90, 0), 1500.0)
    np.testing.assert_allclose(tau, [0.0, 0.0], atol=1e-18)


@pytest.mark.parametrize(
    "az, el, expected_second",
    [
        (0, 0, 1j),  # endfire toward +x: phase +k d = +pi/2
        (180, 0, -1j),  # endfire from -x: -pi/2
        (90, 0, 1.0),  # broadside
        (60, 0, (1 + 1j) / np.sqrt(2)),  # cos 60 = 1/2 -> pi/4
        (0, 60, (1 + 1j) / np.sqrt(2)),  # cos(el) cos(az) = 1/2 -> pi/4
    ],
)
def test_two_element_steering_vector_hand_computed(az, el, expected_second):
    # d = 0.375 m, f = 1000 Hz, c = 1500 m/s -> k d = 2 pi * 1000 * 0.375 / 1500 = pi / 2 exactly
    a = steering_vectors([[0, 0, 0], [0.375, 0, 0]], unit_vector(az, el), 1000.0, 1500.0)
    np.testing.assert_allclose(a, [1.0, expected_second], atol=1e-14)


def test_steering_vector_on_y_and_z_axes():
    pos = [[0, 0.375, 0], [0, 0, 0.375]]
    np.testing.assert_allclose(steering_vectors(pos, unit_vector(90, 0), 1000.0, 1500.0), [1j, 1.0], atol=1e-14)
    np.testing.assert_allclose(steering_vectors(pos, unit_vector(-90, 0), 1000.0, 1500.0), [-1j, 1.0], atol=1e-14)
    np.testing.assert_allclose(steering_vectors(pos, unit_vector(0, 90), 1000.0, 1500.0), [1.0, 1j], atol=1e-14)


def test_far_field_limit_of_spherical_wave():
    """Independent physics: a point source at range R has phase exp(-j k (|R u - r| - R)) relative to the origin."""
    rng = np.random.default_rng(4)
    pos = rng.uniform(-0.5, 0.5, size=(6, 3))
    f, c, R = 2000.0, 1500.0, 1.0e7
    k = 2 * np.pi * f / c
    for _ in range(20):
        u = rng.normal(size=3)
        u /= np.linalg.norm(u)
        rho = np.linalg.norm(R * u - pos, axis=1)
        exact = np.exp(-1j * k * (rho - R))
        np.testing.assert_allclose(steering_vectors(pos, u, f, c), exact, atol=1e-5)  # error ~ k r^2 / 2R


def test_time_domain_delay_matches_steering_vector():
    """Delay pulses in the time domain, FFT them (NumPy convention), compare inter-channel phase to a(u)."""
    c, fs, n = 1500.0, 200_000.0, 16384
    t = np.arange(n) / fs
    pos = np.array([[0, 0, 0], [0.2, 0, 0], [0.05, 0.3, -0.1]])
    u = unit_vector(35.0, -15.0)
    tau = arrival_time_offsets_s(pos, u, c)
    t0, sig, f0 = 0.04, 0.00025, 3000.0  # 0.25 ms envelope: usable spectrum ~1.5-4.5 kHz

    def pulse(tt):
        return np.exp(-(((tt - t0) / sig) ** 2)) * np.cos(2 * np.pi * f0 * (tt - t0))

    x = np.stack([pulse(t - tn) for tn in tau])  # s(t - tau_n)
    spec = np.fft.rfft(x, axis=1)
    freqs = np.fft.rfftfreq(n, 1 / fs)
    for f in (2000.0, 2500.0, 3000.0, 3500.0):
        j = int(np.argmin(np.abs(freqs - f)))
        measured = spec[:, j] / spec[0, j]
        a = steering_vectors(pos, u, freqs[j], c)
        np.testing.assert_allclose(measured, a / a[0], atol=1e-8)


def test_sound_speed_validation_catches_unit_errors():
    assert validate_sound_speed(1500.0) == 1500.0
    for bad in (1.5, 4921.0, 0.0, -1500.0, float("nan")):
        with pytest.raises(ValueError):
            validate_sound_speed(bad)
    with pytest.raises(ValueError):
        PlaneWaveManifold(uniform_linear(2, 0.1), 1.5)


def test_negative_frequency_rejected():
    with pytest.raises(ValueError):
        wavenumber_rad_per_m(-1.0, 1500.0)
