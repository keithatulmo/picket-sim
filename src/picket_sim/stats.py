"""Monte Carlo statistics with explicit uncertainty (ADR-0012)."""

from __future__ import annotations

import hashlib

import numpy as np

__all__ = ["Z95", "case_rng", "mean_ci", "quantile_ci", "wilson_ci", "MIN_TRIALS"]

Z95 = 1.959963984540054
MIN_TRIALS = 200


def case_rng(base_seed: int, *key) -> np.random.Generator:
    """Generator for one Monte Carlo case, independent of loop order (stable hash of the key)."""
    h = int.from_bytes(hashlib.sha256(repr(key).encode("utf-8")).digest()[:8], "little")
    return np.random.default_rng(np.random.SeedSequence([int(base_seed), h]))


def _check(x, minimum=MIN_TRIALS):
    x = np.asarray(x, dtype=float)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if x.size < minimum:
        raise ValueError(f"need at least {minimum} samples for the normal-approximation interval, got {x.size}")
    if not np.all(np.isfinite(x)):
        raise ValueError("non-finite Monte Carlo samples")
    return x


def mean_ci(x) -> dict:
    x = _check(x)
    m = float(np.mean(x))
    se = float(np.std(x, ddof=1) / np.sqrt(x.size))
    return {"mean": m, "lo": m - Z95 * se, "hi": m + Z95 * se, "se": se, "n": int(x.size)}


def quantile_ci(x, q: float) -> dict:
    """Quantile with a distribution-free 95 % interval from order statistics (binomial, normal approx.)."""
    x = np.sort(_check(x))
    n = x.size
    est = float(np.quantile(x, q))
    half = Z95 * np.sqrt(n * q * (1 - q))
    lo_rank = int(np.clip(np.floor(n * q - half), 1, n))
    hi_rank = int(np.clip(np.ceil(n * q + half), 1, n))
    return {"q": q, "est": est, "lo": float(x[lo_rank - 1]), "hi": float(x[hi_rank - 1]), "n": n}


def wilson_ci(k: int, n: int) -> dict:
    if n < 1 or not 0 <= k <= n:
        raise ValueError("require 0 <= k <= n, n >= 1")
    p = k / n
    z2 = Z95 * Z95
    den = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / den
    half = Z95 * np.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    # The Wilson interval always contains p; enforce it against floating-point rounding at p = 0 or 1.
    lo, hi = min(max(0.0, centre - half), p), max(min(1.0, centre + half), p)
    return {"p": p, "lo": lo, "hi": hi, "k": int(k), "n": int(n)}
