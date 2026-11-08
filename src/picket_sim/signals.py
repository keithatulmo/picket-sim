"""SIM-02B.1 signal classes and observation grid (ADR-0015, ADR-0016).

A trial is one window of ``T`` seconds sampled at ``fs`` (``N = round(T fs)`` samples). Signals are returned
as DFT bins inside the analysis band in *normalized units*

    x_k = X[k] / (fs * sqrt(T / 2)),   X[k] = sum_n x[n] exp(-j 2 pi k n / N),

so that a stationary noise bin has variance equal to its one-sided PSD (uPa^2/Hz) and, for any deterministic
signal, ``sum_k |x_k|^2 / G_n(f_k)`` is the noise-weighted energy-to-noise-density ratio E/N0_eff of
ADR-0015 (for a tone of power P it is approximately P T / G_n).

Per channel, a plane wave from unit direction ``u`` arrives with delay ``tau_n = -(u . r_n) / c`` relative to
the array origin (ADR-0003). Tones and harmonics are computed exactly for the delayed sampled sinusoid
(Dirichlet kernel). Broadband and chirp signals use the ideal band-limited delay, the bin factor
``exp(-j 2 pi f_k tau_n)``, which is exact in the circular band-limited model of ADR-0016.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = ["Grid", "delays_s", "tone_bins", "harmonic_bins", "broadband_bins", "chirp_reference", "chirp_bins",
           "tukey", "SignalError"]


class SignalError(ValueError):
    pass


@dataclass(frozen=True)
class Grid:
    """DFT bins of a T-second window at sample rate fs inside the analysis band [f_lo, f_hi]."""

    T: float
    fs: float
    f_lo: float
    f_hi: float

    def __post_init__(self):
        if not (self.T > 0 and self.fs > 0 and 0 < self.f_lo < self.f_hi):
            raise SignalError("grid needs T > 0, fs > 0 and 0 < f_lo < f_hi")
        if self.f_hi >= self.fs / 2:
            raise SignalError(f"band edge {self.f_hi} Hz not below Nyquist {self.fs / 2} Hz")
        if abs(self.T * self.fs - round(self.T * self.fs)) > 1e-6:
            raise SignalError("T * fs must be an integer number of samples")
        if self.k.size < 2:
            raise SignalError("band contains fewer than two bins for this window")

    @property
    def n_samples(self) -> int:
        return int(round(self.T * self.fs))

    @property
    def k(self) -> np.ndarray:
        """Integer bin indices inside the band (inclusive)."""
        return np.arange(math.ceil(self.f_lo * self.T - 1e-9), math.floor(self.f_hi * self.T + 1e-9) + 1)

    @property
    def f(self) -> np.ndarray:
        return self.k / self.T

    @property
    def K(self) -> int:
        return int(self.k.size)

    @property
    def df(self) -> float:
        return 1.0 / self.T

    @property
    def scale(self) -> float:
        """Factor from normalized bins to raw DFT values: X[k] = scale * x_k."""
        return self.fs * math.sqrt(self.T / 2.0)


def delays_s(positions_m: np.ndarray, u: np.ndarray, c_mps: float) -> np.ndarray:
    """Arrival delay of a plane wave from direction ``u`` at each element, relative to the origin (s)."""
    return -(np.asarray(positions_m, dtype=float) @ np.asarray(u, dtype=float)) / c_mps


def _dirichlet(nu: np.ndarray, n: int) -> np.ndarray:
    """sum_{m=0}^{n-1} exp(j 2 pi nu m) for real nu (cycles per sample)."""
    nu = np.asarray(nu, dtype=float)
    out = np.empty(nu.shape, dtype=complex)
    s = np.sin(np.pi * nu)
    small = np.abs(s) < 1e-12
    out[~small] = np.exp(1j * np.pi * nu[~small] * (n - 1)) * np.sin(np.pi * nu[~small] * n) / s[~small]
    # nu integer: every term is exp(j 2 pi m * integer) = 1
    out[small] = n
    return out


def tone_bins(grid: Grid, f0: float, amplitude: float, phase: float, tau_s: np.ndarray) -> np.ndarray:
    """Exact band bins of x_n[m] = A cos(2 pi f0 (m/fs - tau_n) + phase), shape (channels, K)."""
    if not (0 < f0 < grid.fs / 2):
        raise SignalError("tone frequency must lie between 0 and Nyquist")
    tau = np.atleast_1d(np.asarray(tau_s, dtype=float))
    n = grid.n_samples
    nu_k = grid.k / n
    pos = _dirichlet(f0 / grid.fs - nu_k, n)       # (K,)
    neg = _dirichlet(-f0 / grid.fs - nu_k, n)      # (K,)
    ph = phase - 2 * np.pi * f0 * tau              # (C,)
    X = 0.5 * amplitude * (np.exp(1j * ph)[:, None] * pos[None, :] + np.exp(-1j * ph)[:, None] * neg[None, :])
    return X / grid.scale


def harmonic_bins(grid: Grid, f0: float, amplitudes: np.ndarray, phases: np.ndarray, tau_s: np.ndarray) -> np.ndarray:
    """Sum of tones at h f0 (h = 1..H) with the given amplitudes and phases."""
    out = 0
    for h, (a, p) in enumerate(zip(amplitudes, phases), start=1):
        out = out + tone_bins(grid, h * f0, a, p, tau_s)
    return out


def broadband_bins(grid: Grid, psd_upa2_per_hz: np.ndarray, tau_s: np.ndarray, rng: np.random.Generator,
                   f_band=None) -> np.ndarray:
    """Gaussian random plane wave with one-sided PSD ``psd`` on the band bins (zero outside ``f_band``)."""
    psd = np.broadcast_to(np.asarray(psd_upa2_per_hz, dtype=float), (grid.K,)).copy()
    if f_band is not None:
        psd[(grid.f < f_band[0]) | (grid.f > f_band[1])] = 0.0
    if np.any(psd < 0) or not np.all(np.isfinite(psd)):
        raise SignalError("signal PSD must be finite and non-negative")
    s = np.sqrt(psd / 2.0) * (rng.standard_normal(grid.K) + 1j * rng.standard_normal(grid.K))
    tau = np.atleast_1d(np.asarray(tau_s, dtype=float))
    return s[None, :] * np.exp(-2j * np.pi * grid.f[None, :] * tau[:, None])


def tukey(n: int, alpha: float) -> np.ndarray:
    """Tukey (tapered cosine) window of length n; alpha = 0 rectangular, 1 Hann."""
    if n < 2:
        return np.ones(n)
    if alpha <= 0:
        return np.ones(n)
    x = np.arange(n) / (n - 1)
    w = np.ones(n)
    a = min(alpha, 1.0)
    lo = x < a / 2
    hi = x > 1 - a / 2
    w[lo] = 0.5 * (1 + np.cos(np.pi * (2 * x[lo] / a - 1)))
    w[hi] = 0.5 * (1 + np.cos(np.pi * (2 * x[hi] / a - 2 / a + 1)))
    return w


def chirp_reference(grid: Grid, f1: float, f2: float, duration_s: float, taper: float) -> np.ndarray:
    """Band bins (normalized units, unit amplitude) of a tapered LFM pulse starting at t = 0.

    The pulse is sampled at fs over the window; bins outside [f_lo, f_hi] are discarded (ideal band-pass).
    Raises if more than 1e-3 of the pulse energy lies outside the analysis band.
    """
    if not (grid.f_lo <= min(f1, f2) and max(f1, f2) <= grid.f_hi):
        raise SignalError("chirp sweep must lie inside the analysis band")
    if not (0 < duration_s < grid.T):
        raise SignalError("chirp duration must be positive and shorter than the window")
    n_p = int(round(duration_s * grid.fs))
    t = np.arange(n_p) / grid.fs
    rate = (f2 - f1) / duration_s
    x = np.zeros(grid.n_samples)
    x[:n_p] = tukey(n_p, taper) * np.cos(2 * np.pi * (f1 * t + 0.5 * rate * t * t))
    X = np.fft.rfft(x)
    total = float(np.sum(np.abs(X[1:]) ** 2))
    inband = float(np.sum(np.abs(X[grid.k]) ** 2))
    if total <= 0 or (total - inband) / total > 1e-3:
        raise SignalError(f"chirp energy outside the analysis band is {(total - inband) / total:.2e} > 1e-3")
    return X[grid.k] / grid.scale


def chirp_bins(grid: Grid, reference: np.ndarray, amplitude: float, t0_s: float, tau_s: np.ndarray) -> np.ndarray:
    """Chirp arriving at the origin at t0 (s), delayed per channel by tau_n (ideal band-limited delay)."""
    tau = np.atleast_1d(np.asarray(tau_s, dtype=float))
    return amplitude * reference[None, :] * np.exp(-2j * np.pi * grid.f[None, :] * (t0_s + tau[:, None]))
