"""First-order directivity of an ideal acoustic vector sensor (feasibility support only).

An ideal co-located pressure + 3-axis particle-velocity sensor can form any first-order pattern
b(theta) = alpha + (1 - alpha) cos(theta) steered to any direction. Its directivity factor against
spherically isotropic noise is

    D = 1 / (alpha^2 + (1 - alpha)^2 / 3)

(alpha = 1 omnidirectional, D = 1; alpha = 0 dipole, D = 3; alpha = 1/2 cardioid, D = 3;
alpha = 1/4 hypercardioid, D = 4, the first-order maximum). This assumes ideal, noise-free,
perfectly calibrated channels and is not a model of any device (docs/avs_feasibility.md).
"""

from __future__ import annotations

import numpy as np

__all__ = ["first_order_di_db", "first_order_di_numeric_db", "optimal_first_order_alpha"]


def first_order_di_db(alpha: float) -> float:
    a = float(alpha)
    return float(10 * np.log10(1.0 / (a * a + (1 - a) ** 2 / 3.0)))


def first_order_di_numeric_db(alpha: float, n: int = 8) -> float:
    """Independent check: D = 4 pi |b(0)|^2 / integral |b|^2 dOmega, Gauss-Legendre in mu = cos theta
    (exact for the quadratic integrand)."""
    mu, w = np.polynomial.legendre.leggauss(n)
    b2 = (alpha + (1 - alpha) * mu) ** 2
    integral = 2 * np.pi * np.sum(w * b2)
    return float(10 * np.log10(4 * np.pi * 1.0 / integral))


def optimal_first_order_alpha() -> float:
    """alpha maximizing D: minimize alpha^2 + (1 - alpha)^2 / 3 -> alpha = 1/4."""
    return 0.25
