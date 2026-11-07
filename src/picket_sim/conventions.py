"""Coordinate frame and angle conventions (ADR-0003).

Frame: right-handed Cartesian array frame, metres, +z up.
Azimuth: in the x-y plane from +x toward +y (counter-clockwise seen from above), degrees.
Elevation: positive above the x-y plane, degrees, in [-90, 90].
Direction vector u: unit vector from the array TOWARD the source (direction of arrival).

    u = [cos(el) cos(az), cos(el) sin(az), sin(el)]

This module is the only place where angles are converted to and from vectors. All public
arguments carry their unit in the name.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "unit_vector",
    "az_el_deg_from_unit",
    "wrap_deg",
    "angle_between_rad",
    "azimuth_tangent",
    "elevation_tangent",
    "great_circle_points",
    "horizontal_cut",
    "vertical_cut",
    "fibonacci_sphere",
]


def unit_vector(az_deg, el_deg) -> np.ndarray:
    """Direction-of-arrival unit vector(s) for azimuth/elevation in degrees.

    Inputs broadcast against each other; the result has shape ``broadcast_shape + (3,)``.
    """
    az = np.deg2rad(np.asarray(az_deg, dtype=float))
    el = np.deg2rad(np.asarray(el_deg, dtype=float))
    az, el = np.broadcast_arrays(az, el)
    ce = np.cos(el)
    return np.stack([ce * np.cos(az), ce * np.sin(az), np.sin(el)], axis=-1)


def az_el_deg_from_unit(u) -> tuple[np.ndarray, np.ndarray]:
    """Inverse of :func:`unit_vector`. Azimuth in [-180, 180), elevation in [-90, 90].

    The vector need not be normalized. At the poles the azimuth is returned as 0.
    """
    u = np.asarray(u, dtype=float)
    x, y, z = u[..., 0], u[..., 1], u[..., 2]
    rho = np.hypot(x, y)
    el = np.rad2deg(np.arctan2(z, rho))
    az = np.where(rho > 0.0, np.rad2deg(np.arctan2(y, x)), 0.0)
    return wrap_deg(az), el


def wrap_deg(angle_deg) -> np.ndarray:
    """Wrap angles to [-180, 180)."""
    a = np.asarray(angle_deg, dtype=float)
    return (a + 180.0) % 360.0 - 180.0


def angle_between_rad(u1, u2) -> np.ndarray:
    """Great-circle angle between direction vectors (robust for small and near-pi angles)."""
    u1 = np.asarray(u1, dtype=float)
    u2 = np.asarray(u2, dtype=float)
    cross = np.linalg.norm(np.cross(u1, u2), axis=-1)
    dot = np.sum(u1 * u2, axis=-1)
    return np.arctan2(cross, dot)


def azimuth_tangent(az_deg, el_deg) -> np.ndarray:
    """Unit tangent to the sphere at (az, el) pointing toward increasing azimuth.

    Equal to d u / d az normalized: [-sin(az), cos(az), 0]. Well defined at every elevation
    (at the poles it is the limit along the given azimuth).
    """
    az = np.deg2rad(np.asarray(az_deg, dtype=float))
    az = np.broadcast_to(az, np.broadcast_shapes(np.shape(az), np.shape(el_deg)))
    return np.stack([-np.sin(az), np.cos(az), np.zeros_like(az)], axis=-1)


def elevation_tangent(az_deg, el_deg) -> np.ndarray:
    """Unit tangent to the sphere at (az, el) pointing toward increasing elevation."""
    az = np.deg2rad(np.asarray(az_deg, dtype=float))
    el = np.deg2rad(np.asarray(el_deg, dtype=float))
    az, el = np.broadcast_arrays(az, el)
    se = np.sin(el)
    return np.stack([-se * np.cos(az), -se * np.sin(az), np.cos(el)], axis=-1)


def great_circle_points(u0, tangent, gamma_deg) -> np.ndarray:
    """Points on the great circle through ``u0`` leaving in direction ``tangent``.

    ``gamma_deg`` is the signed arc length from ``u0`` in degrees. ``tangent`` must be a unit
    vector orthogonal to ``u0``. Returns shape ``gamma.shape + (3,)``.
    """
    u0 = np.asarray(u0, dtype=float)
    t = np.asarray(tangent, dtype=float)
    if abs(float(np.dot(u0, t))) > 1e-9 or abs(np.linalg.norm(t) - 1.0) > 1e-9:
        raise ValueError("tangent must be a unit vector orthogonal to u0")
    g = np.deg2rad(np.asarray(gamma_deg, dtype=float))[..., None]
    return np.cos(g) * u0 + np.sin(g) * t


def horizontal_cut(az0_deg: float, el0_deg: float, gamma_deg) -> np.ndarray:
    """Great circle through (az0, el0) tangent to the azimuth direction.

    For el0 = 0 this is the horizon and gamma is the azimuth offset (az = az0 + gamma). For
    el0 != 0 it is the cross-elevation great circle (not the constant-elevation small circle).
    """
    u0 = unit_vector(az0_deg, el0_deg)
    return great_circle_points(u0, azimuth_tangent(az0_deg, el0_deg), gamma_deg)


def vertical_cut(az0_deg: float, el0_deg: float, gamma_deg) -> np.ndarray:
    """Great circle through (az0, el0) and the zenith.

    gamma is the elevation offset (el = el0 + gamma while |el0 + gamma| <= 90); beyond the pole the
    circle continues on the meridian az0 + 180.
    """
    u0 = unit_vector(az0_deg, el0_deg)
    return great_circle_points(u0, elevation_tangent(az0_deg, el0_deg), gamma_deg)


def fibonacci_sphere(n: int) -> np.ndarray:
    """Quasi-uniform unit vectors on the sphere (deterministic Fibonacci lattice)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    i = np.arange(n, dtype=float) + 0.5
    z = 1.0 - 2.0 * i / n
    golden = np.pi * (3.0 - np.sqrt(5.0))
    phi = golden * np.arange(n, dtype=float)
    rho = np.sqrt(np.clip(1.0 - z * z, 0.0, None))
    return np.stack([rho * np.cos(phi), rho * np.sin(phi), z], axis=-1)
