"""Numerical grids: frequency grids, Gauss-Legendre sphere quadrature, 1-D observable grids, cuts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import numpy as np

from .conventions import unit_vector

__all__ = [
    "log_frequency_grid",
    "SphereGrid",
    "gauss_legendre_sphere",
    "cut_offsets_deg",
]


def log_frequency_grid(f_min_hz: float, f_max_hz: float, points_per_decade: int) -> np.ndarray:
    """Logarithmically spaced frequencies including both end points."""
    if not (0 < f_min_hz < f_max_hz):
        raise ValueError("require 0 < f_min_hz < f_max_hz")
    decades = np.log10(f_max_hz / f_min_hz)
    n = int(round(decades * points_per_decade)) + 1
    return np.logspace(np.log10(f_min_hz), np.log10(f_max_hz), n)


@dataclass(frozen=True)
class SphereGrid:
    """Product grid: Gauss-Legendre nodes in mu = sin(el) times uniform azimuth.

    Quadrature ``sum(f * weights_sr)`` approximates ``integral f dOmega`` and is exact for
    spherical harmonics of degree < min(2 n_el, n_az). ``n_el`` odd places a node on the horizon
    (el = 0); ``n_az`` must be even so that the grid is symmetric across each pole.
    """

    n_el: int
    n_az: int

    def __post_init__(self):
        if self.n_az % 2:
            raise ValueError("n_az must be even")
        if self.n_el < 2:
            raise ValueError("n_el must be >= 2")

    @cached_property
    def _nodes(self):
        mu, w = np.polynomial.legendre.leggauss(self.n_el)
        return mu, w

    @property
    def el_deg(self) -> np.ndarray:
        return np.rad2deg(np.arcsin(self._nodes[0]))

    @property
    def az_deg(self) -> np.ndarray:
        return -180.0 + 360.0 * np.arange(self.n_az) / self.n_az

    @cached_property
    def unit_vectors(self) -> np.ndarray:
        """``(n_el, n_az, 3)``."""
        az, el = np.meshgrid(self.az_deg, self.el_deg, indexing="xy")
        return unit_vector(az, el)

    @cached_property
    def weights_sr(self) -> np.ndarray:
        """``(n_el, n_az)`` quadrature weights in steradians, summing to 4 pi."""
        w_mu = self._nodes[1]
        return np.repeat(w_mu[:, None] * (2.0 * np.pi / self.n_az), self.n_az, axis=1)

    @property
    def flat_unit_vectors(self) -> np.ndarray:
        return self.unit_vectors.reshape(-1, 3)

    @property
    def flat_weights_sr(self) -> np.ndarray:
        return self.weights_sr.reshape(-1)

    @property
    def max_spacing_deg(self) -> float:
        """Largest angular spacing between neighbouring nodes (azimuth spacing on the horizon)."""
        el = self.el_deg
        d_el = float(np.max(np.diff(el))) if el.size > 1 else 180.0
        return max(360.0 / self.n_az, d_el)

    def max_exact_degree(self) -> int:
        return min(2 * self.n_el, self.n_az) - 1


def gauss_legendre_sphere(n_el: int, n_az: int) -> SphereGrid:
    return SphereGrid(n_el=n_el, n_az=n_az)


def cut_offsets_deg(n_points: int) -> np.ndarray:
    """Offsets in [-180, 180) with exactly 0 included (``n_points`` even)."""
    if n_points % 2:
        raise ValueError("n_points must be even")
    return -180.0 + 360.0 * np.arange(n_points) / n_points
