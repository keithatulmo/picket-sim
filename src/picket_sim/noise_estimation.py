"""SIM-02B.2-A adaptive background estimation (ADR-0019) and exact CFAR laws (ADR-0020).

Estimators take *data only*: reference-window powers of a stream (time references) or the test window's own
powers (frequency references). They never receive the true covariance, scenario labels or signal information.

Shapes: powers are real arrays with bins on the last axis. Time-reference inputs have the reference-window axis
second to last: (..., M, K) -> (..., K).
"""

from __future__ import annotations

import math

import numpy as np

__all__ = ["tref_ca", "tref_os", "fref_index", "fref_ca", "fref_os", "ca_cfar_sf", "ca_cfar_isf", "os_cfar_sf",
           "os_cfar_isf", "per_bin_pfa", "cfar_loss_db"]


# ------------------------------------------------------------------------------------------- estimators
def tref_ca(ref_powers: np.ndarray) -> np.ndarray:
    """Cell-averaging over reference windows: mean of the M reference powers per bin."""
    r = np.asarray(ref_powers)
    if r.ndim < 2 or r.shape[-2] < 1:
        raise ValueError("reference powers need a window axis (..., M, K)")
    return r.mean(axis=-2)


def tref_os(ref_powers: np.ndarray, r: int) -> np.ndarray:
    """Ordered statistic over reference windows: the r-th smallest of the M reference powers per bin (1-based r)."""
    x = np.asarray(ref_powers)
    m = x.shape[-2]
    if not 1 <= r <= m:
        raise ValueError(f"order r must be in 1..{m}")
    return np.partition(x, r - 1, axis=-2).take(r - 1, axis=-2)


def fref_index(K: int, L: int, G: int) -> np.ndarray:
    """Reference-bin indices (K, 2L): L bins on each side beyond G guard bins; at band edges all 2L bins are taken
    from the inner side so every cell has exactly 2L references."""
    if L < 1 or G < 0 or K < 2 * (L + G) + 1:
        raise ValueError("band too narrow for the reference-bin layout")
    idx = np.empty((K, 2 * L), dtype=int)
    for k in range(K):
        left = [j for j in range(k - G - L, k - G) if j >= 0]
        right = [j for j in range(k + G + 1, k + G + L + 1) if j < K]
        need = 2 * L - len(left) - len(right)
        if need > 0 and len(left) < L:  # near the lower edge: extend to the right
            right = list(range(k + G + 1, k + G + 1 + len(right) + need))
        elif need > 0:  # near the upper edge: extend to the left
            left = list(range(k - G - len(left) - need, k - G))
        idx[k] = left + right
    if idx.min() < 0 or idx.max() >= K:
        raise ValueError("reference-bin layout out of range")
    return idx


def fref_ca(powers: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Cell-averaging over reference bins of the same window: (..., K) -> (..., K)."""
    return np.asarray(powers)[..., idx].mean(axis=-1)


def fref_os(powers: np.ndarray, idx: np.ndarray, r: int) -> np.ndarray:
    """Ordered statistic over reference bins: the r-th smallest of the 2L reference powers."""
    x = np.asarray(powers)[..., idx]
    if not 1 <= r <= x.shape[-1]:
        raise ValueError("order r out of range")
    return np.partition(x, r - 1, axis=-1)[..., r - 1]


# ------------------------------------------------------------------------------------------- exact laws
def ca_cfar_sf(eta, M: int):
    """P(|y|^2 / G_hat > eta) for G_hat the mean of M independent reference powers (exponential noise)."""
    return (1.0 + np.asarray(eta, dtype=float) / M) ** (-M)


def ca_cfar_isf(p: float, M: int) -> float:
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    return M * math.expm1(-math.log(p) / M)


def os_cfar_sf(eta, M: int, r: int):
    """P(|y|^2 > eta x_(r)) for x_(r) the r-th smallest of M reference powers (Rohling 1983)."""
    e = np.asarray(eta, dtype=float)
    out = np.ones_like(e)
    for i in range(r):
        out = out * (M - i) / (M - i + e)
    return out


def os_cfar_isf(p: float, M: int, r: int) -> float:
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    lo, hi = 0.0, 1.0
    while os_cfar_sf(hi, M, r) > p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if os_cfar_sf(mid, M, r) > p:
            lo = mid
        else:
            hi = mid
    return hi


def per_bin_pfa(p_window: float, K: int) -> float:
    """Per-bin false-alarm probability giving window probability p for a maximum over K independent bins."""
    return -math.expm1(math.log1p(-p_window) / K)


def cfar_loss_db(p_window: float, K: int, M: int) -> float:
    """Threshold ratio TREF-CA / ORACLE for a tonal maximum over K bins, in dB (large-SNR detection loss)."""
    pb = per_bin_pfa(p_window, K)
    return 10.0 * math.log10(ca_cfar_isf(pb, M) / -math.log(pb))
