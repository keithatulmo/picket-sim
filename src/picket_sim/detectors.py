"""SIM-02B.1 conventional detectors and processing modes (SIM-02B plan section 3, ADR-0015).

Every detector works on *normalized* bins z (trials, streams, K): for a stream with weights w,
z_k = w^H x_k / sqrt(w^H C_assumed(f_k) w). Under matched noise the z_k are independent unit circular complex
Gaussians, so the per-bin powers are unit exponentials.

Processing modes (``streams``):
  single       one element (A0)
  beam_known   one DAS beam steered at the true source direction (upper bound: direction assumed known)
  beam_search  DAS beams at the configured horizon azimuths; statistic = maximum over beams
  incoherent   every element normalized separately; per-bin powers averaged over elements (no beamforming)

Detectors (statistic per window):
  tonal      max over bins of |z_k|^2
  harmonic   max over fundamentals of the sum of |z|^2 at the bins nearest to h f0, h = 1..H
  energy     sum over bins of |z_k|^2
  mf         max over lags of |sum_k z_k s_k^* exp(j 2 pi f_k tau)|^2 / sum_k |s_k|^2 (whitened replica s)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .signals import Grid
from .synthesis import steering_bins

__all__ = ["MODES", "DETECTORS", "harmonic_index", "beam_weights", "normalize", "Detectors"]

MODES = ("single", "beam_known", "beam_search", "incoherent")
DETECTORS = ("tonal", "harmonic", "energy", "mf")


def harmonic_index(grid: Grid, n_harmonics: int) -> np.ndarray:
    """Relative bin indices (F, H) of the harmonic sum for fundamentals on a grid of step df / H."""
    if n_harmonics < 1:
        raise ValueError("n_harmonics must be >= 1")
    step = grid.df / n_harmonics
    f0 = np.arange(grid.f_lo, grid.f_hi / n_harmonics + 1e-9, step)
    h = np.arange(1, n_harmonics + 1)
    idx = np.rint(np.outer(f0, h) * grid.T).astype(int) - int(grid.k[0])
    ok = np.all((idx >= 0) & (idx < grid.K), axis=1)
    if not np.any(ok):
        raise ValueError("no fundamental has all harmonics inside the band")
    return idx[ok]


def beam_weights(positions_m: np.ndarray, us: np.ndarray, f_hz: np.ndarray, c_mps: float) -> np.ndarray:
    """DAS weights a/N for each look direction, shape (K, N, B)."""
    us = np.atleast_2d(us)
    n = np.asarray(positions_m).shape[0]
    return np.stack([steering_bins(positions_m, u, f_hz, c_mps) for u in us], axis=-1) / n


def beam_sigma(w: np.ndarray, c: np.ndarray) -> np.ndarray:
    """sqrt(w^H C w) per bin and beam; w (K, N, B), C (K, N, N)."""
    v = np.einsum("knb,knm,kmb->kb", w.conj(), c, w).real
    if np.any(v <= 0):
        raise ValueError("beam noise power must be positive")
    return np.sqrt(v)


def normalize(x: np.ndarray, mode: str, c_assumed: np.ndarray, positions_m=None, f_hz=None, c_mps=None,
              look_u=None, search_w=None, search_sigma=None) -> np.ndarray:
    """Normalized streams z (t, S, K) from noise-plus-signal bins x (t, K, N).

    ``look_u`` (t, 3): true direction per trial for beam_known. ``search_w``/``search_sigma``: precomputed
    beam-search weights (K, N, B) and normalizations (K, B).
    """
    if mode == "single":
        return (x[..., 0] / np.sqrt(c_assumed[:, 0, 0])[None, :])[:, None, :]
    if mode == "incoherent":
        sig = np.sqrt(np.einsum("knn->kn", c_assumed))  # (K, N)
        return np.swapaxes(x / sig[None], 1, 2)  # (t, N, K)
    if mode == "beam_search":
        y = np.einsum("tkn,knb->tbk", x, search_w.conj())
        return y / search_sigma.T[None]
    if mode == "beam_known":
        look_u = np.atleast_2d(look_u)
        tau = -(look_u @ np.asarray(positions_m, dtype=float).T) / c_mps  # (t, N)
        w = np.exp(-2j * np.pi * f_hz[None, :, None] * tau[:, None, :]) / tau.shape[1]  # (t, K, N)
        y = np.einsum("tkn,tkn->tk", x, w.conj())
        v = np.einsum("tkn,knm,tkm->tk", w.conj(), c_assumed, w).real
        return (y / np.sqrt(v))[:, None, :]
    raise ValueError(f"unknown mode {mode!r}")


@dataclass
class Detectors:
    """Statistics of the four detectors on normalized streams.

    ``harmonic_idx`` (F, H) relative bins; ``replica`` (S, K) whitened replica per stream for the matched
    filter (or (1, K) broadcast); ``oversample`` lag oversampling of the matched filter.
    """

    harmonic_idx: np.ndarray | None = None
    replica: np.ndarray | None = None
    oversample: int = 2

    def power_stats(self, p: np.ndarray, combine: str, which) -> dict:
        """Tonal, harmonic and energy statistics from per-bin powers p (t, S, K)."""
        if combine == "mean":
            p = p.mean(axis=1, keepdims=True)
        out = {}
        if "tonal" in which:
            out["tonal"] = p.max(axis=2).max(axis=1)
        if "energy" in which:
            out["energy"] = p.sum(axis=2).max(axis=1)
        if "harmonic" in which:
            hs = p[:, :, self.harmonic_idx].sum(axis=-1)  # (t, S, F)
            out["harmonic"] = hs.max(axis=2).max(axis=1)
        return out

    def mf_lags(self, z: np.ndarray, replica: np.ndarray | None = None) -> np.ndarray:
        """Complex matched-filter output over lags, normalized to unit noise variance: (t, S, L)."""
        s = self.replica if replica is None else replica
        L = self.oversample * z.shape[-1]
        norm = np.sqrt(np.sum(np.abs(s) ** 2, axis=-1))  # (S,) or (t, S)
        m = np.fft.ifft(z * s.conj(), n=L, axis=-1) * L
        return m / norm[..., None]

    @staticmethod
    def mf_stat(m: np.ndarray, combine: str) -> np.ndarray:
        q = np.abs(m) ** 2
        if combine == "mean":
            q = q.mean(axis=1, keepdims=True)
        return q.max(axis=2).max(axis=1)
