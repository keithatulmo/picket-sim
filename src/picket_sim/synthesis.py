"""SIM-02B.1 frequency-domain multichannel noise synthesis and waveform access (ADR-0016).

Noise bins of one window are drawn independently per bin as x_k ~ CN(0, C(f_k)), where C is the
cross-spectral density matrix (uPa^2/Hz) of the noise scenario at the array:

    C(f) = sum_i G_i(f) Gamma_i(f)  (+ G_self(f) I)

with Gamma_i a closed-form spatial coherence (spherically isotropic, horizontally isotropic, exponential
flow-like, white). Every matrix is checked Hermitian positive semidefinite before it is factored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .noisefields import NoiseModelError, bessel_j0
from .signals import Grid

__all__ = ["CoherenceSpec", "NoiseScenario", "coherence_bins", "check_covariance_stack", "covariance_factor",
           "draw_noise", "to_waveform", "welch_csd", "steering_bins"]

COHERENCE_KINDS = ("white", "spherical", "horizontal", "exponential")


@dataclass(frozen=True)
class CoherenceSpec:
    kind: str
    correlation_length_m: float | None = None

    def __post_init__(self):
        if self.kind not in COHERENCE_KINDS:
            raise NoiseModelError(f"coherence kind must be one of {COHERENCE_KINDS}, got {self.kind!r}")
        if self.kind == "exponential" and not (self.correlation_length_m and self.correlation_length_m > 0):
            raise NoiseModelError("exponential coherence needs a positive correlation length")


def coherence_bins(spec: CoherenceSpec, positions_m: np.ndarray, f_hz: np.ndarray, c_mps: float,
                   chunk: int = 4096) -> np.ndarray:
    """Real coherence matrices Gamma(f_k), shape (K, N, N), for the closed-form fields."""
    r = np.asarray(positions_m, dtype=float)
    n = r.shape[0]
    f = np.asarray(f_hz, dtype=float)
    out = np.empty((f.size, n, n))
    d = r[:, None, :] - r[None, :, :]
    if spec.kind == "white":
        out[:] = np.eye(n)
        return out
    if spec.kind == "exponential":
        out[:] = np.exp(-np.linalg.norm(d, axis=-1) / spec.correlation_length_m)
        return out
    if spec.kind == "spherical":
        dist = np.linalg.norm(d, axis=-1)
        out[:] = np.sinc(2.0 * f[:, None, None] * dist[None] / c_mps)
        return out
    # horizontal: J0(k rho) on unique pairs, chunked over frequency (quadrature cost grows with k rho)
    rho = np.hypot(d[..., 0], d[..., 1])
    iu = np.triu_indices(n, 1)
    for s in range(0, f.size, chunk):
        kk = 2 * np.pi * f[s:s + chunk] / c_mps
        vals = bessel_j0(kk[:, None] * rho[iu][None, :])
        blk = np.empty((kk.size, n, n))
        blk[:, iu[0], iu[1]] = vals
        blk[:, iu[1], iu[0]] = vals
        blk[:, np.arange(n), np.arange(n)] = 1.0
        out[s:s + chunk] = blk
    return out


@dataclass(frozen=True)
class NoiseScenario:
    """Noise at the array: spatially structured components plus independent per-element self-noise.

    ``components`` is a list of (psd, coherence) pairs, psd a callable G(f) in uPa^2/Hz; ``self_noise`` is a
    callable G_self(f) applied independently at every element (sensor and electronics referred to input).
    """

    name: str
    components: list = field(default_factory=list)
    self_noise: Callable | None = None

    def element_psd(self, f_hz) -> np.ndarray:
        """Total one-sided PSD at one element (uPa^2/Hz): the SNR reference of ADR-0015."""
        f = np.asarray(f_hz, dtype=float)
        g = np.zeros_like(f)
        for psd, _ in self.components:
            g = g + psd(f)
        if self.self_noise is not None:
            g = g + self.self_noise(f)
        return g

    def covariance(self, positions_m: np.ndarray, f_hz: np.ndarray, c_mps: float) -> np.ndarray:
        """Cross-spectral density matrices C(f_k), shape (K, N, N), real symmetric for these fields."""
        r = np.asarray(positions_m, dtype=float)
        f = np.asarray(f_hz, dtype=float)
        c = np.zeros((f.size, r.shape[0], r.shape[0]))
        for psd, coh in self.components:
            g = psd(f)
            if np.any(~np.isfinite(g)) or np.any(g < 0):
                raise NoiseModelError(f"{self.name}: component PSD must be finite and non-negative")
            c += g[:, None, None] * coherence_bins(coh, r, f, c_mps)
        if self.self_noise is not None:
            g = self.self_noise(f)
            if np.any(~np.isfinite(g)) or np.any(g < 0):
                raise NoiseModelError(f"{self.name}: self-noise PSD must be finite and non-negative")
            c += g[:, None, None] * np.eye(r.shape[0])[None]
        return c


def check_covariance_stack(c: np.ndarray, name: str = "covariance", rtol: float = 1e-10) -> np.ndarray:
    """Vectorized form of ``noisefields.check_covariance`` over a stack (K, N, N); returns eigenpairs."""
    if c.ndim != 3 or c.shape[1] != c.shape[2]:
        raise NoiseModelError(f"{name}: expected a (K, N, N) stack")
    if not np.all(np.isfinite(c)):
        raise NoiseModelError(f"{name}: non-finite entries")
    tr = np.maximum(np.real(np.trace(c, axis1=1, axis2=2)), 1e-300)
    asym = np.max(np.abs(c - np.conj(np.swapaxes(c, 1, 2))), axis=(1, 2))
    if np.any(asym > rtol * tr):
        raise NoiseModelError(f"{name}: not Hermitian at {int(np.sum(asym > rtol * tr))} bins")
    ev, vec = np.linalg.eigh(0.5 * (c + np.conj(np.swapaxes(c, 1, 2))))
    bad = ev[:, 0] < -rtol * tr
    if np.any(bad):
        i = int(np.argmax(bad))
        raise NoiseModelError(f"{name}: not positive semidefinite at {int(bad.sum())} bins "
                              f"(first: min eigenvalue {ev[i, 0]:.3e}, trace {tr[i]:.3e})")
    return ev, vec


def covariance_factor(c: np.ndarray, name: str = "covariance") -> np.ndarray:
    """F with F F^H = C per bin, after the PSD check. Eigenvalues within round-off of zero are set to zero."""
    ev, vec = check_covariance_stack(c, name)
    return vec * np.sqrt(np.maximum(ev, 0.0))[:, None, :]


def draw_noise(factor: np.ndarray, rng: np.random.Generator, n_trials: int, dtype=np.complex128) -> np.ndarray:
    """Noise bins for ``n_trials`` independent windows, shape (n_trials, K, N)."""
    k, n, _ = factor.shape
    z = (rng.standard_normal((n_trials, k, n)) + 1j * rng.standard_normal((n_trials, k, n))) * np.sqrt(0.5)
    return np.einsum("knm,tkm->tkn", factor, z).astype(dtype, copy=False)


def steering_bins(positions_m: np.ndarray, u: np.ndarray, f_hz: np.ndarray, c_mps: float) -> np.ndarray:
    """Plane-wave bin factors exp(-j 2 pi f tau_n) = exp(+j k u . r_n), shape (K, N) (ADR-0003)."""
    tau = -(np.asarray(positions_m, dtype=float) @ np.asarray(u, dtype=float)) / c_mps
    return np.exp(-2j * np.pi * np.asarray(f_hz)[:, None] * tau[None, :])


def to_waveform(bins: np.ndarray, grid: Grid) -> np.ndarray:
    """Real multichannel time series (channels, N samples) from band bins (channels, K)."""
    b = np.atleast_2d(bins)
    X = np.zeros((b.shape[0], grid.n_samples // 2 + 1), dtype=complex)
    X[:, grid.k] = b * grid.scale
    return np.fft.irfft(X, n=grid.n_samples, axis=1)


def welch_csd(x: np.ndarray, fs: float, nperseg: int) -> tuple[np.ndarray, np.ndarray, int]:
    """One-sided cross-spectral density matrix by Welch's method (Hann, 50 % overlap).

    Returns (f, G of shape (F, N, N), number of segments). G[f, i, j] = 2 E[X_i X_j^*] / (fs sum w^2).
    """
    x = np.atleast_2d(np.asarray(x, dtype=float))
    n_ch, n = x.shape
    step = nperseg // 2
    starts = np.arange(0, n - nperseg + 1, step)
    if starts.size < 2:
        raise ValueError("signal too short for Welch averaging")
    w = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(nperseg) / nperseg)  # periodic Hann
    acc = np.zeros((nperseg // 2 + 1, n_ch, n_ch), dtype=complex)
    for s in starts:
        X = np.fft.rfft(x[:, s:s + nperseg] * w, axis=1)  # (N, F)
        acc += np.einsum("if,jf->fij", X, X.conj())
    g = acc / starts.size * 2.0 / (fs * np.sum(w * w))
    g[0] /= 2.0
    if nperseg % 2 == 0:
        g[-1] /= 2.0
    return np.fft.rfftfreq(nperseg, 1.0 / fs), g, int(starts.size)
