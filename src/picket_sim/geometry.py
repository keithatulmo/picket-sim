"""Array geometry: arbitrary 3-D sensor coordinates and observability (ambiguity) analysis.

Positions are in metres in the array frame defined in :mod:`picket_sim.conventions`.

Observability
-------------
For a plane wave, the per-element phase is ``k u . r_n``. A phase common to all channels is not
observable (it is indistinguishable from the source phase), so the array response depends on the
direction ``u`` only through ``Q^T u``, where the columns of ``Q`` are an orthonormal basis of the
span of the difference vectors ``r_n - r_m`` (equivalently, of the centred positions). The rank of
that span fixes the *geometric* ambiguity exactly, independently of frequency:

* rank 0: single sensor (or coincident sensors); no directional information.
* rank 1: collinear; only the angle to the axis is observable (cone of ambiguity).
* rank 2: coplanar; reflection through the plane is unobservable (mirror ambiguity).
* rank 3: volumetric; no geometric ambiguity (aliasing can still occur).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

import numpy as np

__all__ = [
    "ArrayGeometry",
    "Observability",
    "single_hydrophone",
    "uniform_linear",
    "uniform_rectangular",
    "from_coordinates",
    "rotation_matrix_from_axes",
    "RANK_TOL_M",
]

#: Absolute tolerance (metres) on singular values of the centred position matrix used to decide
#: the rank of the sensor-difference span. 1 nm is far below any physical placement tolerance.
RANK_TOL_M = 1e-9

AMBIGUITY_CLASS = {
    0: "omnidirectional",
    1: "conical",
    2: "mirror",
    3: "none",
}


@dataclass(frozen=True)
class Observability:
    """Result of the observability analysis of a geometry."""

    rank: int
    basis: np.ndarray  # (3, rank) orthonormal basis of the difference span
    singular_values_m: np.ndarray  # (3,) singular values of the centred positions (RMS-scaled)
    ambiguity_class: str
    description: str
    axis: np.ndarray | None = None  # rank 1: unit array axis
    plane_normal: np.ndarray | None = None  # rank 2: unit normal of the array plane

    def reduce(self, u) -> np.ndarray:
        """Observable coordinates ``Q^T u`` of direction vector(s) ``u`` (shape ``(..., rank)``)."""
        return np.asarray(u, dtype=float) @ self.basis

    def mirror(self, u) -> np.ndarray:
        """Geometric mirror image of ``u`` (rank 2 only): reflection through the array plane."""
        if self.rank != 2:
            raise ValueError("mirror image is defined only for planar (rank-2) geometries")
        u = np.asarray(u, dtype=float)
        n = self.plane_normal
        return u - 2.0 * (u @ n)[..., None] * n


def _canonical_sign(v: np.ndarray) -> np.ndarray:
    """Flip a vector so that its first non-negligible component is positive (deterministic)."""
    for comp in v:
        if abs(comp) > 1e-12:
            return v if comp > 0 else -v
    return v


@dataclass(frozen=True)
class ArrayGeometry:
    """Sensor coordinates and metadata.

    Parameters
    ----------
    array_id:
        Identifier (e.g. ``"A1"``).
    positions_m:
        ``(N, 3)`` sensor coordinates in metres.
    description:
        Free text describing the configuration and its assumptions.
    """

    array_id: str
    positions_m: np.ndarray
    description: str = ""
    element_ids: tuple[str, ...] = field(default=())

    def __post_init__(self):
        pos = np.array(self.positions_m, dtype=float, copy=True)
        if pos.ndim != 2 or pos.shape[1] != 3 or pos.shape[0] < 1:
            raise ValueError(f"{self.array_id}: positions_m must have shape (N, 3), got {pos.shape}")
        if not np.all(np.isfinite(pos)):
            raise ValueError(f"{self.array_id}: positions must be finite")
        pos.setflags(write=False)
        object.__setattr__(self, "positions_m", pos)
        ids = tuple(self.element_ids) or tuple(f"E{i + 1}" for i in range(pos.shape[0]))
        if len(ids) != pos.shape[0]:
            raise ValueError(f"{self.array_id}: element_ids length must equal number of elements")
        object.__setattr__(self, "element_ids", ids)

    # ------------------------------------------------------------------ basic properties
    @property
    def n_elements(self) -> int:
        return int(self.positions_m.shape[0])

    @property
    def centroid_m(self) -> np.ndarray:
        return self.positions_m.mean(axis=0)

    @property
    def centered_positions_m(self) -> np.ndarray:
        return self.positions_m - self.centroid_m

    @property
    def pairwise_distances_m(self) -> np.ndarray:
        d = self.positions_m[:, None, :] - self.positions_m[None, :, :]
        return np.linalg.norm(d, axis=-1)

    @property
    def aperture_m(self) -> float:
        """Largest inter-element distance (0 for a single sensor)."""
        return float(self.pairwise_distances_m.max())

    @property
    def min_spacing_m(self) -> float:
        """Smallest inter-element distance (NaN for a single sensor)."""
        n = self.n_elements
        if n < 2:
            return float("nan")
        d = self.pairwise_distances_m[np.triu_indices(n, k=1)]
        return float(d.min())

    @property
    def extent_m(self) -> np.ndarray:
        """Axis-aligned bounding-box size (x, y, z) in metres."""
        return self.positions_m.max(axis=0) - self.positions_m.min(axis=0)

    # ------------------------------------------------------------------ observability
    @cached_property
    def observability(self) -> Observability:
        c = self.centered_positions_m
        if self.n_elements == 1:
            sv = np.zeros(3)
            vt = np.eye(3)
        else:
            _, s, vt = np.linalg.svd(c, full_matrices=True)
            sv = np.zeros(3)
            sv[: s.size] = s
        rank = int(np.sum(sv > RANK_TOL_M))
        basis = np.array(vt[:rank].T, dtype=float)
        for j in range(rank):
            basis[:, j] = _canonical_sign(basis[:, j])
        axis = normal = None
        if rank == 0:
            desc = "single or coincident sensors: no directional information at any frequency"
        elif rank == 1:
            axis = basis[:, 0].copy()
            desc = (
                "collinear: only the angle from the array axis "
                f"[{axis[0]:+.3f}, {axis[1]:+.3f}, {axis[2]:+.3f}] is observable; every direction on "
                "the cone of constant axis angle gives an identical response"
            )
        elif rank == 2:
            normal = _canonical_sign(np.cross(basis[:, 0], basis[:, 1]))
            normal = normal / np.linalg.norm(normal)
            desc = (
                "coplanar: reflection through the array plane (normal "
                f"[{normal[0]:+.3f}, {normal[1]:+.3f}, {normal[2]:+.3f}]) is unobservable; "
                "each direction has an identical-response mirror image"
            )
        else:
            desc = "volumetric: no geometric ambiguity; frequency-dependent aliasing may still occur"
        rms = sv / np.sqrt(max(self.n_elements, 1))
        return Observability(
            rank=rank,
            basis=basis,
            singular_values_m=rms,
            ambiguity_class=AMBIGUITY_CLASS[rank],
            description=desc,
            axis=axis,
            plane_normal=normal,
        )

    @property
    def reduced_positions_m(self) -> np.ndarray:
        """Centred positions expressed in the observable basis, shape ``(N, rank)``."""
        return self.centered_positions_m @ self.observability.basis

    # ------------------------------------------------------------------ transforms
    def translated(self, offset_m, array_id: str | None = None) -> "ArrayGeometry":
        return ArrayGeometry(
            array_id or self.array_id,
            self.positions_m + np.asarray(offset_m, dtype=float),
            self.description,
            self.element_ids,
        )

    def rotated(self, rotation: np.ndarray, array_id: str | None = None, about_centroid=True):
        """Rigidly rotate positions by a 3x3 proper rotation matrix."""
        r = np.asarray(rotation, dtype=float)
        if r.shape != (3, 3) or not np.allclose(r @ r.T, np.eye(3), atol=1e-12):
            raise ValueError("rotation must be an orthogonal 3x3 matrix")
        if not np.isclose(np.linalg.det(r), 1.0):
            raise ValueError("rotation must be proper (det = +1)")
        origin = self.centroid_m if about_centroid else np.zeros(3)
        pos = (self.positions_m - origin) @ r.T + origin
        return ArrayGeometry(array_id or self.array_id, pos, self.description, self.element_ids)

    def scaled(self, factor: float, array_id: str | None = None, about_centroid=True):
        """Scale all inter-element distances by ``factor`` (> 0)."""
        if factor <= 0:
            raise ValueError("scale factor must be positive")
        origin = self.centroid_m if about_centroid else np.zeros(3)
        pos = (self.positions_m - origin) * factor + origin
        return ArrayGeometry(array_id or self.array_id, pos, self.description, self.element_ids)

    def summary(self) -> dict:
        obs = self.observability
        return {
            "array_id": self.array_id,
            "n_elements": self.n_elements,
            "aperture_m": self.aperture_m,
            "min_spacing_m": self.min_spacing_m,
            "extent_x_m": float(self.extent_m[0]),
            "extent_y_m": float(self.extent_m[1]),
            "extent_z_m": float(self.extent_m[2]),
            "rank": obs.rank,
            "ambiguity_class": obs.ambiguity_class,
            "ambiguity_description": obs.description,
        }


# ---------------------------------------------------------------------- factories
def _unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("zero-length direction")
    return v / n


def single_hydrophone(array_id: str = "A0", position_m=(0.0, 0.0, 0.0), description: str = ""):
    return ArrayGeometry(array_id, np.asarray(position_m, dtype=float)[None, :], description)


def uniform_linear(
    n_elements: int,
    spacing_m: float,
    axis=(1.0, 0.0, 0.0),
    array_id: str = "ULA",
    description: str = "",
    centered: bool = True,
) -> ArrayGeometry:
    """Uniform line array of ``n_elements`` along ``axis`` with ``spacing_m``."""
    if n_elements < 1:
        raise ValueError("n_elements must be >= 1")
    if n_elements > 1 and spacing_m <= 0:
        raise ValueError("spacing_m must be positive")
    a = _unit(axis)
    idx = np.arange(n_elements, dtype=float)
    if centered:
        idx = idx - idx.mean()
    pos = idx[:, None] * spacing_m * a[None, :]
    return ArrayGeometry(array_id, pos, description)


def uniform_rectangular(
    nx: int,
    ny: int,
    dx_m: float,
    dy_m: float,
    axis_u=(1.0, 0.0, 0.0),
    axis_v=(0.0, 1.0, 0.0),
    array_id: str = "URA",
    description: str = "",
    centered: bool = True,
) -> ArrayGeometry:
    """Rectangular grid of ``nx`` x ``ny`` sensors in the plane spanned by ``axis_u``, ``axis_v``."""
    au, av = _unit(axis_u), _unit(axis_v)
    if abs(np.dot(au, av)) > 1e-12:
        raise ValueError("axis_u and axis_v must be orthogonal")
    iu = np.arange(nx, dtype=float)
    iv = np.arange(ny, dtype=float)
    if centered:
        iu, iv = iu - iu.mean(), iv - iv.mean()
    gu, gv = np.meshgrid(iu * dx_m, iv * dy_m, indexing="xy")
    pos = gu.reshape(-1, 1) * au + gv.reshape(-1, 1) * av
    return ArrayGeometry(array_id, pos, description)


def from_coordinates(positions_m, array_id: str = "ARB", description: str = "", element_ids=()):
    return ArrayGeometry(array_id, np.asarray(positions_m, dtype=float), description, tuple(element_ids))


def rotation_matrix_from_axes(axis, angle_deg: float) -> np.ndarray:
    """Right-handed rotation about ``axis`` by ``angle_deg`` (Rodrigues)."""
    k = _unit(axis)
    t = np.deg2rad(angle_deg)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(t) * kx + (1 - np.cos(t)) * (kx @ kx)
