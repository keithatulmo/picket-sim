"""Sound-speed mismatch: peak-direction bias of a DAS scan computed with the wrong sound speed.

Data are generated with ``c_true``; the beamformer scans with steering vectors built from
``c_assumed``. The scan response is ``|W(k_t p_t - k_a p)|^2`` in the observable space, so for
rank 1 and rank 2 arrays the noise-free peak is exactly at

    p_est = (c_assumed / c_true) * p_true        (if inside the visible region |p| <= 1)

i.e. the observable direction-cosine vector is scaled. Consequences: a line array's cone angle is
biased (zero at broadside, largest toward endfire); a horizontal planar array's azimuth is
unbiased but its elevation magnitude is biased, strongly near the horizon; for a volumetric array
with isotropic second moment the direction is unbiased (to second order). The peak location is
frequency independent in this ideal model. These are deterministic biases, not noise effects.
"""

from __future__ import annotations

import numpy as np

from .acoustics import PlaneWaveManifold, steering_vectors
from .conventions import angle_between_rad, az_el_deg_from_unit, unit_vector
from .geometry import ArrayGeometry
from .grids import SphereGrid
from .metrics import _refine_1d, _refine_on_sphere

__all__ = ["mismatch_peak", "predicted_reduced_estimate"]


def _scan_fun(geometry: ArrayGeometry, f_hz: float, c_true: float, c_assumed: float, u_true):
    x = steering_vectors(geometry.positions_m, u_true, f_hz, c_true)
    scan = PlaneWaveManifold(geometry, c_assumed)
    n = geometry.n_elements

    def fun(u):
        a = scan.vectors(u, f_hz)
        return np.abs(a.conj() @ x) ** 2 / (n * n)

    return fun


def predicted_reduced_estimate(p_true: np.ndarray, alpha: float) -> np.ndarray:
    """Closed-form rank-1/2 estimate: scale by alpha and project radially onto |p| <= 1."""
    p = alpha * np.asarray(p_true, dtype=float)
    nrm = np.linalg.norm(p)
    return p / nrm if nrm > 1.0 else p


def mismatch_peak(
    geometry: ArrayGeometry,
    f_hz: float,
    c_true_mps: float,
    c_assumed_mps: float,
    az_true_deg: float,
    el_true_deg: float,
    sphere: SphereGrid,
    n_points_1d: int = 20001,
) -> dict:
    obs = geometry.observability
    u_true = unit_vector(az_true_deg, el_true_deg)
    fun = _scan_fun(geometry, f_hz, c_true_mps, c_assumed_mps, u_true)
    alpha = c_assumed_mps / c_true_mps
    out = {
        "array_id": geometry.array_id,
        "rank": obs.rank,
        "f_hz": f_hz,
        "c_true_mps": c_true_mps,
        "c_assumed_mps": c_assumed_mps,
        "az_true_deg": az_true_deg,
        "el_true_deg": el_true_deg,
    }
    nan = float("nan")
    keys = ("cone_angle_true_deg", "cone_angle_est_deg", "cone_angle_error_deg", "cone_angle_pred_error_deg",
            "az_est_deg", "az_error_deg", "abs_el_est_deg", "abs_el_error_deg", "abs_el_pred_error_deg",
            "direction_error_deg")
    out.update({k: nan for k in keys})
    if obs.rank == 0:
        out["note"] = "single sensor: no direction estimate"
        return out
    if obs.rank == 1:
        axis = obs.axis
        trial = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        b = trial - (trial @ axis) * axis
        b /= np.linalg.norm(b)

        def f1(pv):
            pv = np.clip(np.asarray(pv, dtype=float), -1, 1)
            return fun(pv[:, None] * axis + np.sqrt(1 - pv * pv)[:, None] * b)

        grid = np.linspace(-1, 1, n_points_1d)
        vals = f1(grid)
        k = int(np.argmax(vals))
        _, p_est = _refine_1d(f1, grid[k], grid[1] - grid[0], -1.0, 1.0)
        p_true = float(u_true @ axis)
        p_pred = float(predicted_reduced_estimate(np.array([p_true]), alpha)[0])
        ct, ce, cp = (float(np.rad2deg(np.arccos(np.clip(v, -1, 1)))) for v in (p_true, p_est, p_pred))
        out.update({"cone_angle_true_deg": ct, "cone_angle_est_deg": ce, "cone_angle_error_deg": ce - ct,
                    "cone_angle_pred_error_deg": cp - ct})
        out["note"] = "rank 1: only the cone angle is observable"
        return out
    # rank 2 and 3: global search on the sphere, then refine
    pv = fun(sphere.flat_unit_vectors)
    k = int(np.argmax(pv))
    a0, e0 = az_el_deg_from_unit(sphere.flat_unit_vectors[k])
    _, a_est, e_est = _refine_on_sphere(fun, float(a0), float(e0), sphere.max_spacing_deg, iters=6)
    u_est = unit_vector(a_est, e_est)
    if obs.rank == 2:
        # fold both onto the same side of the plane (mirror ambiguity), compare observable quantities
        n = obs.plane_normal
        if float(u_est @ n) * float(u_true @ n) < 0:
            u_est = obs.mirror(u_est)
        a_est, e_est = (float(v) for v in az_el_deg_from_unit(u_est))
        p_true = obs.reduce(u_true)
        p_pred = predicted_reduced_estimate(p_true, alpha)
        # elevation magnitude from |p| (valid for a horizontal plane: |p| = cos(el))
        el_pred = float(np.rad2deg(np.arccos(np.clip(np.linalg.norm(p_pred), 0, 1))))
        out["abs_el_pred_error_deg"] = el_pred - abs(el_true_deg)
        out["note"] = "rank 2: mirror image folded; elevation sign unobservable"
    else:
        out["note"] = "rank 3: full direction"
    out.update({
        "az_est_deg": a_est,
        "az_error_deg": float(((a_est - az_true_deg + 180) % 360) - 180),
        "abs_el_est_deg": abs(e_est),
        "abs_el_error_deg": abs(e_est) - abs(el_true_deg),
        "direction_error_deg": float(np.rad2deg(angle_between_rad(u_est, u_true))),
    })
    return out
