"""Tail probabilities for quadratic forms and maxima of correlated Gaussian magnitudes (ADR-0020).

* ``hypoexp_sf``: exact survival of Q = sum_i lambda_i E_i (E_i independent unit exponentials, lambda_i >= 0), the
  law of the incoherent per-bin statistic under the oracle model, by the matrix exponential of the bidiagonal phase
  generator (stable for repeated or nearly equal weights).
* ``conditional_max_sf``: probability that the maximum over a set of unit-variance correlated complex Gaussian
  components exceeds eta in magnitude squared, by conditional Monte Carlo (Adler, Blanchet and Liu, 2012): pick a
  component with probability proportional to its marginal tail, sample conditional on its exceedance, and average
  the reciprocal number of exceedances. Unbiased with bounded relative error.
"""

from __future__ import annotations

import math

import numpy as np

__all__ = ["expm_small", "hypoexp_sf", "conditional_max_sf", "ConditionalMax"]


def expm_small(a: np.ndarray) -> np.ndarray:
    """Matrix exponential of a stack of small matrices (..., n, n): scaling and squaring with a degree-12 Taylor
    series. Accurate to about 1e-14 relative for the generators used here."""
    a = np.asarray(a, dtype=float)
    norm = np.max(np.sum(np.abs(a), axis=-1), axis=-1)
    s = np.maximum(0, np.ceil(np.log2(np.maximum(norm, 1e-300) / 0.5))).astype(int)
    smax = int(s.max()) if s.size else 0
    scaled = a / (2.0 ** s)[..., None, None]
    n = a.shape[-1]
    eye = np.broadcast_to(np.eye(n), a.shape)
    out = eye.copy()
    term = eye.copy()
    for j in range(1, 13):
        term = term @ scaled / j
        out = out + term
    for i in range(smax):
        sq = out @ out
        mask = (s > i)[..., None, None]
        out = np.where(mask, sq, out)
    return out


def hypoexp_sf(x: float, lam: np.ndarray, rel_floor: float = 1e-12) -> np.ndarray:
    """P(sum_i lambda_i E_i > x) for each row of ``lam`` (..., n). Weights below rel_floor x max are dropped
    (their contribution to the tail is below that relative size)."""
    lam = np.atleast_2d(np.asarray(lam, dtype=float))
    if np.any(lam < 0):
        raise ValueError("weights must be non-negative")
    lead = lam.shape[:-1]
    flat = lam.reshape(-1, lam.shape[-1])
    out = np.empty(flat.shape[0])
    for i, row in enumerate(flat):
        w = row[row > rel_floor * row.max()]
        if w.size == 0:
            out[i] = 0.0 if x > 0 else 1.0
            continue
        rates = 1.0 / w
        n = w.size
        gen = np.diag(-rates) + np.diag(rates[:-1], 1)
        e = expm_small(gen * x)
        out[i] = float(np.clip(e[0].sum(), 0.0, 1.0))
    return out.reshape(lead)


def conditional_max_sf(eta: float, cov: np.ndarray, n: int, rng: np.random.Generator) -> tuple[float, float]:
    """P(max_j |z_j|^2 > eta) for z ~ CN(0, cov) with unit diagonal (cov S x S, possibly singular).

    Returns (estimate, standard error). Uses the conditional Monte Carlo estimator: p = S e^-eta E[1 / N_eta | pick j
    uniformly, |z_j|^2 > eta], N_eta the number of components above eta.
    """
    cov = np.asarray(cov)
    s = cov.shape[0]
    if not np.allclose(np.real(np.diag(cov)), 1.0, atol=1e-9):
        raise ValueError("components must have unit variance")
    ev, vec = np.linalg.eigh(0.5 * (cov + cov.conj().T))
    fac = vec * np.sqrt(np.clip(ev, 0.0, None))  # cov = fac fac^H
    j = rng.integers(0, s, n)
    mag2 = eta + rng.exponential(size=n)  # |z_j|^2 | exceedance (memoryless)
    zj = np.sqrt(mag2) * np.exp(2j * np.pi * rng.uniform(size=n))
    u = (rng.standard_normal((n, fac.shape[1])) + 1j * rng.standard_normal((n, fac.shape[1]))) / np.sqrt(2)
    z_free = u @ fac.T  # unconditional draws (n, S)
    # condition on component j: z = z_free + cov[:, j] (zj - z_free_j) (cov[j, j] = 1)
    zfj = z_free[np.arange(n), j]
    z = z_free + cov[:, j].T * (zj - zfj)[:, None]
    cnt = np.sum(np.abs(z) ** 2 > eta, axis=1)
    cnt = np.maximum(cnt, 1)  # component j itself exceeds by construction
    vals = s * math.exp(-eta) / cnt
    return float(vals.mean()), float(vals.std(ddof=1) / math.sqrt(n))


class ConditionalMax:
    """Conditional Monte Carlo estimator of P(max_j |z_j|^2 > eta) with fixed random draws (common random numbers),
    so that a threshold search sees no sampling noise between trial thresholds (the estimate is piecewise continuous
    in eta and dominated by its exp(-eta) factor)."""

    def __init__(self, cov: np.ndarray, n: int, rng: np.random.Generator):
        cov = np.asarray(cov)
        if not np.allclose(np.real(np.diag(cov)), 1.0, atol=1e-9):
            raise ValueError("components must have unit variance")
        self.s = cov.shape[0]
        ev, vec = np.linalg.eigh(0.5 * (cov + cov.conj().T))
        fac = vec * np.sqrt(np.clip(ev, 0.0, None))
        self.j = rng.integers(0, self.s, n)
        self.e = rng.exponential(size=n)
        self.ph = np.exp(2j * np.pi * rng.uniform(size=n))
        u = (rng.standard_normal((n, fac.shape[1])) + 1j * rng.standard_normal((n, fac.shape[1]))) / np.sqrt(2)
        z_free = u @ fac.T
        self.zfj = z_free[np.arange(n), self.j]
        self.z_free = z_free
        self.col = cov[:, self.j].T  # (n, S)
        self.n = n

    def sf(self, eta: float) -> tuple[float, float]:
        zj = np.sqrt(eta + self.e) * self.ph
        z = self.z_free + self.col * (zj - self.zfj)[:, None]
        cnt = np.maximum(np.sum(np.abs(z) ** 2 > eta, axis=1), 1)
        vals = self.s * math.exp(-eta) / cnt
        return float(vals.mean()), float(vals.std(ddof=1) / math.sqrt(self.n))
