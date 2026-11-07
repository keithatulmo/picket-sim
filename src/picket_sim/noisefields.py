"""Spatial noise-field models: coherence matrices and composite covariance (ADR-0011).

Every homogeneous component returns a Hermitian, positive semidefinite coherence matrix with unit
diagonal. Near-field point sources (host noise) return h h^H with the level defined at the array
reference point (centroid). Invalid inputs and numerically unconverged integrals raise
``NoiseModelError``; nothing is clipped or regularized.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .acoustics import steering_vectors
from .conventions import unit_vector
from .geometry import ArrayGeometry
from .grids import SphereGrid

__all__ = [
    "NoiseModelError",
    "bessel_j0",
    "coherence_white",
    "coherence_spherical",
    "coherence_horizontal",
    "coherence_exponential",
    "coherence_directional",
    "coherence_far_field",
    "near_field_vector",
    "check_covariance",
    "density_upward",
    "density_horizontal_band",
    "density_uniform",
    "FieldComponent",
    "NoiseField",
]


class NoiseModelError(ValueError):
    pass


def bessel_j0(x) -> np.ndarray:
    """J0 by the trapezoid rule on J0(x) = (1/2pi) int_0^{2pi} cos(x sin t) dt.

    The rule is exact up to terms of order J_M(x), which are negligible for M > |x| + 40.
    """
    x = np.asarray(x, dtype=float)
    m = int(2 * np.ceil((np.max(np.abs(x)) + 40.0) / 2.0)) if x.size else 2
    t = 2.0 * np.pi * np.arange(m) / m
    return np.mean(np.cos(x[..., None] * np.sin(t)), axis=-1)


def _pair_vectors(positions_m):
    r = np.asarray(positions_m, dtype=float)
    return r[:, None, :] - r[None, :, :]


def coherence_white(n: int) -> np.ndarray:
    return np.eye(n, dtype=complex)


def coherence_spherical(positions_m, k: float) -> np.ndarray:
    d = np.linalg.norm(_pair_vectors(positions_m), axis=-1)
    return np.sinc(k * d / np.pi).astype(complex)


def coherence_horizontal(positions_m, k: float) -> np.ndarray:
    """Horizontally (cylindrically) isotropic field: plane waves from all azimuths at el = 0."""
    d = _pair_vectors(positions_m)
    rho = np.hypot(d[..., 0], d[..., 1])
    return bessel_j0(k * rho).astype(complex)


def coherence_exponential(positions_m, correlation_length_m: float) -> np.ndarray:
    """exp(-r / L): short-correlation (flow-like) noise; positive definite in 3-D (Matern nu = 1/2)."""
    if not correlation_length_m > 0:
        raise NoiseModelError("correlation length must be positive")
    d = np.linalg.norm(_pair_vectors(positions_m), axis=-1)
    return np.exp(-d / correlation_length_m).astype(complex)


def coherence_far_field(positions_m, k: float, u) -> np.ndarray:
    a = np.exp(1j * k * (np.asarray(positions_m) @ np.asarray(u, dtype=float)))
    return np.outer(a, a.conj())


def density_uniform(u):
    return np.ones(u.shape[:-1])


def density_upward(exponent: float):
    """((1 + sin el) / 2)^m: smooth density weighted toward arrivals from above (assumed shape)."""
    def d(u):
        return ((1.0 + u[..., 2]) / 2.0) ** exponent
    return d


def density_horizontal_band(sigma_el_deg: float):
    """exp(-el^2 / (2 sigma^2)): energy concentrated near the horizontal (assumed shape)."""
    s = np.deg2rad(sigma_el_deg)

    def d(u):
        el = np.arcsin(np.clip(u[..., 2], -1.0, 1.0))
        return np.exp(-0.5 * (el / s) ** 2)
    return d


def _directional_on_grid(positions_m, k, density, n_el, n_az):
    g = SphereGrid(n_el if n_el % 2 else n_el + 1, n_az + (n_az % 2))
    u = g.flat_unit_vectors
    w = g.flat_weights_sr * density(u)
    if np.any(w < 0) or not np.sum(w) > 0:
        raise NoiseModelError("directional density must be non-negative and not identically zero")
    a = np.exp(1j * k * (u @ np.asarray(positions_m, dtype=float).T))  # (G, N)
    gam = (a.T * w) @ a.conj() / np.sum(w)
    return gam


def coherence_directional(positions_m, k: float, density, tol: float = 2e-4) -> np.ndarray:
    """Coherence of a directional noise density D(u) by sphere quadrature, with a convergence check.

    Computed on two grids (the second with twice the resolution); raises if they differ by more than
    ``tol`` in any entry.
    """
    r = np.asarray(positions_m, dtype=float)
    dmax = float(np.max(np.linalg.norm(_pair_vectors(r), axis=-1))) if len(r) > 1 else 0.0
    deg = int(np.ceil(k * dmax)) + 24
    n_el, n_az = max(33, deg // 2 + 9), max(64, 2 * deg + 16)
    g1 = _directional_on_grid(r, k, density, n_el, n_az)
    g2 = _directional_on_grid(r, k, density, 2 * n_el, 2 * n_az)
    err = float(np.max(np.abs(g1 - g2)))
    if err > tol:
        raise NoiseModelError(f"directional coherence not converged (max change {err:.2e} > {tol:g}); "
                              "density too sharp for the quadrature")
    return g2


def near_field_vector(positions_m, k: float, source_m, min_distance_m: float = 0.1) -> np.ndarray:
    """Spherical-wave vector h_n = (r0 / rho_n) exp(-j k (rho_n - r0)), r0 = distance to the centroid."""
    r = np.asarray(positions_m, dtype=float)
    xs = np.asarray(source_m, dtype=float)
    rho = np.linalg.norm(xs - r, axis=-1)
    if np.min(rho) < min_distance_m:
        raise NoiseModelError(f"point source within {min_distance_m} m of an element (inside the array?)")
    r0 = float(np.linalg.norm(xs - r.mean(axis=0)))
    return (r0 / rho) * np.exp(-1j * k * (rho - r0))


def check_covariance(r: np.ndarray, name: str = "covariance", rtol: float = 1e-10) -> np.ndarray:
    """Raise unless ``r`` is Hermitian and positive semidefinite (relative to its trace)."""
    r = np.asarray(r)
    if r.ndim != 2 or r.shape[0] != r.shape[1]:
        raise NoiseModelError(f"{name}: must be square")
    if not np.all(np.isfinite(r)):
        raise NoiseModelError(f"{name}: non-finite entries")
    scale = max(float(np.real(np.trace(r))), 1e-300)
    if np.max(np.abs(r - r.conj().T)) > rtol * scale:
        raise NoiseModelError(f"{name}: not Hermitian")
    ev = np.linalg.eigvalsh(0.5 * (r + r.conj().T))
    if ev.min() < -rtol * scale:
        raise NoiseModelError(f"{name}: not positive semidefinite (min eigenvalue {ev.min():.3e}, trace {scale:.3e})")
    return r


@dataclass(frozen=True)
class FieldComponent:
    """One component of an ambient field; ``fraction`` of the total ambient power at the reference point."""

    kind: str  # white | spherical | horizontal | directional | exponential | far_field
    fraction: float
    params: dict = field(default_factory=dict)

    def coherence(self, positions_m, k: float) -> np.ndarray:
        n = len(positions_m)
        if self.kind == "white":
            return coherence_white(n)
        if self.kind == "spherical":
            return coherence_spherical(positions_m, k)
        if self.kind == "horizontal":
            return coherence_horizontal(positions_m, k)
        if self.kind == "exponential":
            return coherence_exponential(positions_m, float(self.params["correlation_length_m"]))
        if self.kind == "far_field":
            u = unit_vector(float(self.params["az_deg"]), float(self.params["el_deg"]))
            return coherence_far_field(positions_m, k, u)
        if self.kind == "directional":
            shape = self.params["shape"]
            if shape == "upward":
                dens = density_upward(float(self.params["exponent"]))
            elif shape == "horizontal_band":
                dens = density_horizontal_band(float(self.params["sigma_el_deg"]))
            elif shape == "uniform":
                dens = density_uniform
            else:
                raise NoiseModelError(f"unknown directional shape {shape!r}")
            return coherence_directional(positions_m, k, dens)
        raise NoiseModelError(f"unknown noise component kind {self.kind!r}")


@dataclass(frozen=True)
class NoiseField:
    """Ambient field with unit total power at the reference point: sum of fractions = 1."""

    field_id: str
    components: tuple
    description: str = ""

    def __post_init__(self):
        fr = [c.fraction for c in self.components]
        if not self.components or any(f < 0 for f in fr) or abs(sum(fr) - 1.0) > 1e-9:
            raise NoiseModelError(f"{self.field_id}: component fractions must be non-negative and sum to 1")

    def coherence(self, geometry: ArrayGeometry, f_hz: float, c_mps: float) -> np.ndarray:
        k = 2 * np.pi * f_hz / c_mps
        pos = geometry.positions_m
        gam = sum(c.fraction * c.coherence(pos, k) for c in self.components)
        gam = check_covariance(np.asarray(gam), f"{self.field_id} @ {f_hz:g} Hz")
        if np.max(np.abs(np.real(np.diag(gam)) - 1.0)) > 1e-9:
            raise NoiseModelError(f"{self.field_id}: coherence diagonal is not 1 (normalization error)")
        return gam

    @staticmethod
    def from_config(spec: dict) -> "NoiseField":
        comps = []
        for c in spec["components"]:
            c = dict(c)
            kind = c.pop("type")
            frac = float(c.pop("fraction"))
            comps.append(FieldComponent(kind, frac, c))
        return NoiseField(spec["id"], tuple(comps), spec.get("description", ""))


def plane_wave(positions_m, f_hz: float, c_mps: float, u) -> np.ndarray:
    return steering_vectors(positions_m, u, f_hz, c_mps)
