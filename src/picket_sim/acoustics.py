"""Idealized narrowband far-field acoustics (ADR-0003, ADR-0004).

Model: a plane wave of frequency f from direction u (unit vector toward the source) in a
homogeneous, lossless, unbounded medium of sound speed c. Time convention exp(+j omega t).

* wavelength          lambda = c / f                        [m]
* wavenumber          k = 2 pi f / c                        [rad/m]
* arrival-time offset tau_n = -(u . r_n) / c                [s]  (relative to the frame origin;
                                                                  negative = arrives earlier)
* steering vector     a_n(u, f) = exp(+j k u . r_n)         [dimensionless]

A sensor's signal is s(t - tau_n); its Fourier coefficient (NumPy forward-FFT convention,
X(f) = sum x(t) exp(-j 2 pi f t)) is S(f) exp(-j 2 pi f tau_n) = S(f) a_n(u, f).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .geometry import ArrayGeometry

__all__ = [
    "NOMINAL_SOUND_SPEED_MPS",
    "wavelength_m",
    "wavenumber_rad_per_m",
    "arrival_time_offsets_s",
    "steering_vectors",
    "PlaneWaveManifold",
    "validate_sound_speed",
]

#: Nominal sound speed assumed by SIM-01 (handoff Step 3). Configurable everywhere.
NOMINAL_SOUND_SPEED_MPS = 1500.0

#: Plausibility band for liquid-water sound speed in m/s. Values outside are almost always unit
#: errors (km/s, ft/s). Seawater spans roughly 1440-1560 m/s; fresh water ~1400-1550 m/s.
SOUND_SPEED_PLAUSIBLE_MPS = (1300.0, 1700.0)


def validate_sound_speed(c_mps: float) -> float:
    c = float(c_mps)
    lo, hi = SOUND_SPEED_PLAUSIBLE_MPS
    if not np.isfinite(c) or not (lo <= c <= hi):
        raise ValueError(
            f"sound speed {c_mps!r} m/s is outside the plausible water range [{lo}, {hi}] m/s; "
            "check units (expected metres per second)"
        )
    return c


def _check_frequency(f_hz) -> np.ndarray:
    f = np.asarray(f_hz, dtype=float)
    if np.any(~np.isfinite(f)) or np.any(f < 0):
        raise ValueError("frequency must be finite and non-negative (Hz)")
    return f


def wavelength_m(f_hz, c_mps: float = NOMINAL_SOUND_SPEED_MPS) -> np.ndarray:
    f = _check_frequency(f_hz)
    with np.errstate(divide="ignore"):
        return np.where(f > 0, float(c_mps) / np.where(f > 0, f, 1.0), np.inf)


def wavenumber_rad_per_m(f_hz, c_mps: float = NOMINAL_SOUND_SPEED_MPS) -> np.ndarray:
    f = _check_frequency(f_hz)
    if c_mps <= 0:
        raise ValueError("sound speed must be positive")
    return 2.0 * np.pi * f / float(c_mps)


def arrival_time_offsets_s(positions_m, u, c_mps: float = NOMINAL_SOUND_SPEED_MPS) -> np.ndarray:
    """Plane-wave arrival time at each sensor relative to the origin, shape ``u.shape[:-1] + (N,)``."""
    r = np.asarray(positions_m, dtype=float)
    u = np.asarray(u, dtype=float)
    return -(u @ r.T) / float(c_mps)


def steering_vectors(positions_m, u, f_hz: float, c_mps: float = NOMINAL_SOUND_SPEED_MPS) -> np.ndarray:
    """Plane-wave steering vectors ``exp(+j k u . r_n)``, shape ``u.shape[:-1] + (N,)``."""
    k = float(wavenumber_rad_per_m(f_hz, c_mps))
    r = np.asarray(positions_m, dtype=float)
    u = np.asarray(u, dtype=float)
    return np.exp(1j * k * (u @ r.T))


ElementResponse = Callable[[np.ndarray, float], np.ndarray]
"""Optional element response hook: ``(u (...,3), f_hz) -> (..., N)`` complex gains."""


@dataclass(frozen=True)
class PlaneWaveManifold:
    """Array manifold for plane waves on a given geometry (extension point, ADR-0007).

    ``element_response`` (optional) multiplies the ideal steering vectors by per-element,
    direction- and frequency-dependent complex gains (directivity, baffling, calibration). SIM-01
    uses ideal omnidirectional, identical elements (``None``).
    """

    geometry: ArrayGeometry
    c_mps: float = NOMINAL_SOUND_SPEED_MPS
    element_response: ElementResponse | None = None

    def __post_init__(self):
        validate_sound_speed(self.c_mps)

    @property
    def n_elements(self) -> int:
        return self.geometry.n_elements

    def vectors(self, u, f_hz: float) -> np.ndarray:
        a = steering_vectors(self.geometry.positions_m, u, f_hz, self.c_mps)
        if self.element_response is not None:
            a = a * self.element_response(np.asarray(u, dtype=float), f_hz)
        return a

    def wavenumber(self, f_hz: float) -> float:
        return float(wavenumber_rad_per_m(f_hz, self.c_mps))
