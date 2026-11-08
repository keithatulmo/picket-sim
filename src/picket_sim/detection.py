"""SIM-02B.1 thresholds, false-alarm verification and detection statistics (ADR-0015).

Exact null distributions (matched noise, single normalized stream):
  energy detector over K bins:  Gamma(K, 1) (Erlang); survival via P(Poisson(x) <= K - 1)
  tonal maximum over K bins:    P(max > x) = 1 - (1 - exp(-x))^K
Union bounds: Bonferroni across correlated streams, lags or fundamentals; exact products across
independent bins.
"""

from __future__ import annotations

import math

import numpy as np

from .stats import Z95, wilson_ci

__all__ = ["erlang_logsf", "erlang_isf", "erlang_sf_small", "maxexp_isf", "exp_isf", "empirical_threshold",
           "choose_threshold", "realized_pfa", "pd_with_interval", "snr_at_pd", "incoherent_tonal_bound",
           "MIN_EXCEEDANCES"]

#: Minimum expected number of calibration exceedances (n_cal * Pfa) for an empirical threshold.
MIN_EXCEEDANCES = 10


def erlang_logsf(x: float, k: int) -> float:
    """log P(Gamma(k, 1) > x) for integer k >= 1."""
    if k < 1:
        raise ValueError("shape must be >= 1")
    if x <= 0:
        return 0.0
    i = np.arange(k)
    lgam = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, k, dtype=float)))))  # log(i!)
    t = i * math.log(x) - x - lgam
    m = float(np.max(t))
    return m + math.log(float(np.sum(np.exp(t - m))))


def erlang_isf(p: float, k: int) -> float:
    """x with P(Gamma(k, 1) > x) = p, by bisection on the log survival function."""
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    target = math.log(p)
    lo, hi = 0.0, k + 40.0 * math.sqrt(k) + 60.0
    while erlang_logsf(hi, k) > target:
        hi *= 2
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if erlang_logsf(mid, k) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10 * max(1.0, hi):
            break
    return 0.5 * (lo + hi)


def erlang_sf_small(y: np.ndarray, k: int) -> np.ndarray:
    """P(Gamma(k, 1) > y), vectorized over y, for small integer k (closed-form Poisson sum)."""
    y = np.asarray(y, dtype=float)
    term = np.ones_like(y)
    acc = np.ones_like(y)
    for i in range(1, k):
        term = term * y / i
        acc = acc + term
    return np.exp(-y) * acc


def incoherent_tonal_bound(p: float, lam_max: np.ndarray, n: int) -> float:
    """Conservative threshold for max over bins of q_k = (1/n) sum_i lam_ik E_ik (incoherent power).

    Uses q_k <= (lam_max,k / n) Gamma(n, 1) per bin and the exact product over independent bins.
    """
    lam = np.asarray(lam_max, dtype=float)

    def pfa(x):
        b = np.minimum(erlang_sf_small(n * x / lam, n), 1.0)
        return -np.expm1(np.sum(np.log1p(-b)))

    lo, hi = 0.0, 1.0
    while pfa(hi) > p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if pfa(mid) > p:
            lo = mid
        else:
            hi = mid
    return hi


def exp_isf(p: float) -> float:
    return -math.log(p)


def maxexp_isf(p: float, m: int) -> float:
    """x with P(max of m iid unit exponentials > x) = p."""
    if not 0 < p < 1 or m < 1:
        raise ValueError("need 0 < p < 1 and m >= 1")
    q = -math.expm1(math.log1p(-p) / m)  # per-variable exceedance
    return -math.log(q)


def empirical_threshold(null_stats: np.ndarray, p: float) -> dict:
    """Order-statistic threshold with exceedance fraction ~p and its 95 % order-statistic interval."""
    x = np.sort(np.asarray(null_stats, dtype=float))
    n = x.size
    if not np.all(np.isfinite(x)):
        raise ValueError("non-finite null statistics")
    m = int(math.ceil(n * (1 - p)))  # 1-indexed rank of the threshold
    m = min(max(m, 1), n)
    half = Z95 * math.sqrt(n * p * (1 - p))
    lo_rank = int(min(max(math.floor(n * (1 - p) - half), 1), n))
    hi_rank = int(min(max(math.ceil(n * (1 - p) + half), 1), n))
    return {"eta": float(x[m - 1]), "eta_lo": float(x[lo_rank - 1]), "eta_hi": float(x[hi_rank - 1]),
            "method": "empirical", "n_cal": n}


def choose_threshold(p: float, null_cal: np.ndarray | None, exact: float | None = None,
                     bound: float | None = None) -> dict:
    """Threshold by preference: exact, then empirical (n p >= MIN_EXCEEDANCES), then union bound."""
    if exact is not None and math.isfinite(exact):
        return {"eta": exact, "eta_lo": exact, "eta_hi": exact, "method": "exact", "n_cal": 0}
    if null_cal is not None and len(null_cal) * p >= MIN_EXCEEDANCES:
        return empirical_threshold(null_cal, p)
    if bound is not None and math.isfinite(bound):
        return {"eta": bound, "eta_lo": bound, "eta_hi": bound, "method": "bound", "n_cal": 0}
    return {"eta": float("nan"), "eta_lo": float("nan"), "eta_hi": float("nan"), "method": "not estimated",
            "n_cal": 0 if null_cal is None else len(null_cal)}


def realized_pfa(null_eval: np.ndarray, eta: float) -> dict:
    """Exceedance fraction of an independent evaluation null set, with its Wilson interval."""
    x = np.asarray(null_eval, dtype=float)
    if not math.isfinite(eta):
        return {"p": float("nan"), "lo": float("nan"), "hi": float("nan"), "k": 0, "n": int(x.size)}
    return wilson_ci(int(np.sum(x > eta)), int(x.size))


def pd_with_interval(pos: np.ndarray, thr: dict) -> dict:
    """Pd at the threshold; interval = Wilson interval widened over the threshold's own interval."""
    x = np.asarray(pos, dtype=float)
    n = x.size
    if not math.isfinite(thr["eta"]):
        return {"pd": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": n}
    k = int(np.sum(x > thr["eta"]))
    k_hi = int(np.sum(x > thr["eta_lo"]))
    k_lo = int(np.sum(x > thr["eta_hi"]))
    return {"pd": k / n, "lo": wilson_ci(k_lo, n)["lo"], "hi": wilson_ci(k_hi, n)["hi"], "n": n}


def snr_at_pd(snr_db: np.ndarray, pd: np.ndarray, target: float) -> tuple[float, str]:
    """SNR (dB) at which the Pd curve first reaches ``target`` (linear interpolation in dB).

    Returns (value, status) with status 'ok', 'above grid' (never reached) or 'below grid' (reached at the
    first grid point). Censored values are nan.
    """
    s = np.asarray(snr_db, dtype=float)
    p = np.asarray(pd, dtype=float)
    if np.all(~np.isfinite(p)):
        return float("nan"), "not estimated"
    if p[0] >= target:
        return float("nan"), "below grid"
    above = np.nonzero(p >= target)[0]
    if above.size == 0:
        return float("nan"), "above grid"
    i = int(above[0])
    s0, s1, p0, p1 = s[i - 1], s[i], p[i - 1], p[i]
    return float(s0 + (target - p0) * (s1 - s0) / (p1 - p0)), "ok"
