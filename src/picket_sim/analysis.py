"""Per-case analysis: compose physics and metrics for (array, frequency, steering set).

This layer is study-independent; SIM-01 orchestration lives in :mod:`picket_sim.experiments`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .acoustics import PlaneWaveManifold
from .beamforming import beampattern_power
from .conventions import az_el_deg_from_unit, horizontal_cut, unit_vector, vertical_cut
from .grids import SphereGrid, cut_offsets_deg
from .metrics import (
    HALF_POWER,
    circular_profile_metrics,
    db,
    first_crossing_frequency,
    half_power_sphere_fraction,
    observable_lobe_metrics,
)
from .noise import directivity_index_db, directivity_index_from_pattern_db

__all__ = ["Steering", "AnalysisSettings", "analyze_frequency", "steering_thresholds", "THRESHOLD_KEYS"]


@dataclass(frozen=True)
class Steering:
    ring: str
    az_deg: float
    el_deg: float

    @property
    def u(self) -> np.ndarray:
        return unit_vector(self.az_deg, self.el_deg)


@dataclass(frozen=True)
class AnalysisSettings:
    sphere: SphereGrid
    cut_points: int = 3600
    reduced_1d_points: int = 4001
    ambiguity_levels_db: tuple = (-1.0, -3.0)
    use_sphere_for_rank1: bool = True  # sphere pattern for rank 1 too (DI quadrature check, HPSF cross-check)


def _nan_if(x, cond):
    return float("nan") if cond else float(x)


def analyze_frequency(
    manifold: PlaneWaveManifold,
    f_hz: float,
    steering: list[Steering],
    settings: AnalysisSettings,
) -> list[dict]:
    """Metrics for every steering direction at one frequency. Returns one dict per steering."""
    geom = manifold.geometry
    rank = geom.observability.rank
    s_u = np.stack([s.u for s in steering])
    lam = manifold.c_mps / f_hz
    di = np.atleast_1d(directivity_index_db(manifold, f_hz, s_u))

    use_sphere = rank >= 2 or settings.use_sphere_for_rank1
    if use_sphere:
        sph = settings.sphere
        p_sph = beampattern_power(manifold, f_hz, s_u, sph.flat_unit_vectors)  # (S, G)
        di_num = directivity_index_from_pattern_db(p_sph, sph.flat_weights_sr)
    else:
        p_sph = None
        di_num = np.full(len(steering), np.nan)

    gam = cut_offsets_deg(settings.cut_points)
    rows = []
    for i, st in enumerate(steering):
        ph = beampattern_power(manifold, f_hz, st.u, horizontal_cut(st.az_deg, st.el_deg, gam))
        pv = beampattern_power(manifold, f_hz, st.u, vertical_cut(st.az_deg, st.el_deg, gam))
        ch = circular_profile_metrics(gam, ph)
        cv = circular_profile_metrics(gam, pv)
        p_grid = None
        if p_sph is not None:
            p_grid = p_sph[i].reshape(settings.sphere.n_el, settings.sphere.n_az)
        lm = observable_lobe_metrics(
            manifold,
            f_hz,
            st.u,
            settings.ambiguity_levels_db,
            sphere=settings.sphere,
            n_points_1d=settings.reduced_1d_points,
            p_sphere=p_grid if rank >= 2 else None,
        )
        psl_az = psl_el = psl_cone = float("nan")
        if lm.psl_direction is not None:
            if rank == 1:
                psl_cone = float(np.rad2deg(np.arccos(np.clip(lm.psl_direction @ geom.observability.axis, -1, 1))))
            else:
                a, e = az_el_deg_from_unit(lm.psl_direction)
                psl_az, psl_el = float(a), float(e)
        hpsf_sphere = float("nan")
        if p_sph is not None:
            hpsf_sphere = half_power_sphere_fraction(p_sph[i], settings.sphere.flat_weights_sr)
        row = {
            "array_id": geom.array_id,
            "rank": rank,
            "ring": st.ring,
            "az0_deg": st.az_deg,
            "el0_deg": st.el_deg,
            "f_hz": float(f_hz),
            "c_mps": manifold.c_mps,
            "wavelength_m": lam,
            "aperture_over_lambda": geom.aperture_m / lam,
            "di_db": float(di[i]),
            "di_quadrature_db": float(di_num[i]),
            "hpsf": lm.hpsf if rank >= 1 else 1.0,
            "hpsf_sphere_grid": hpsf_sphere if rank >= 1 else 1.0,
            "min_power_db": db(lm.min_power) if rank >= 1 else 0.0,
            "hpbw_h_deg": ch.hpbw_deg,
            "hpbw_h_reason": ch.hpbw_reason,
            "max_outside_h_db": ch.max_outside_db,
            "max_outside_h_gamma_deg": ch.max_outside_gamma_deg,
            "hpbw_v_deg": cv.hpbw_deg,
            "hpbw_v_reason": cv.hpbw_reason,
            "max_outside_v_db": cv.max_outside_db,
            "max_outside_v_gamma_deg": cv.max_outside_gamma_deg,
            "psl_obs_db": lm.psl_db,
            "psl_obs_reason": lm.psl_reason,
            "psl_obs_az_deg": psl_az,
            "psl_obs_el_deg": psl_el,
            "psl_obs_cone_angle_deg": psl_cone,
        }
        for L in settings.ambiguity_levels_db:
            row[f"n_amb_lobes_ge_{_lvl(L)}"] = lm.n_lobes_ge.get(L, 0)
        row["resolution_ok"] = bool(lm.resolution_ok)
        rows.append(row)
    return rows


def _lvl(level_db: float) -> str:
    """Column-name fragment for a level, e.g. -3.0 -> 'm3db'."""
    v = float(level_db)
    s = f"{abs(v):g}".replace(".", "p")
    return ("m" if v < 0 else "p") + s + "db"


THRESHOLD_KEYS = ("f_hp_hz", "f_sl_hz")


def steering_thresholds(
    manifold: PlaneWaveManifold,
    st: Steering,
    f_grid_hz: np.ndarray,
    settings: AnalysisSettings,
    precomputed: dict | None = None,
    rel_tol: float = 1e-3,
) -> dict:
    """Regime thresholds for one steering direction.

    * ``f_hp_hz``: lowest frequency at which some direction is suppressed by >= 3 dB
      (min of P <= 0.5). Below it DAS gives no half-power discrimination anywhere.
    * ``f_sl_hz``: lowest frequency at which a sidelobe exists in the observable visible region
      (mainlobe no longer fills it).
    * ``f_amb_<L>_hz``: lowest frequency at which an ambiguity lobe (observable-space,
      non-mainlobe local maximum) reaches level L dB.

    ``precomputed`` may hold boolean arrays on ``f_grid_hz`` (keys ``hp``, ``sl``, ``amb_<L>``) from
    a sweep to avoid recomputing the scan; bisection always re-evaluates the physics.
    """
    rank = manifold.geometry.observability.rank
    out = {"array_id": manifold.geometry.array_id, "ring": st.ring, "az0_deg": st.az_deg,
           "el0_deg": st.el_deg, "c_mps": manifold.c_mps}
    if rank == 0:
        out.update({"f_hp_hz": float("nan"), "f_hp_status": "never (single sensor)",
                    "f_sl_hz": float("nan"), "f_sl_status": "never (single sensor)"})
        for L in settings.ambiguity_levels_db:
            out[f"f_amb_{_lvl(L)}_hz"] = float("nan")
            out[f"f_amb_{_lvl(L)}_status"] = "undefined (single sensor)"
        return out

    cache: dict[float, object] = {}

    def lobes(f):
        if f not in cache:
            p_grid = None
            if rank >= 2:
                p_grid = beampattern_power(manifold, f, st.u, settings.sphere.unit_vectors)
            cache[f] = observable_lobe_metrics(
                manifold, f, st.u, settings.ambiguity_levels_db, settings.sphere,
                settings.reduced_1d_points, p_grid,
            )
        return cache[f]

    pre = precomputed or {}
    f_hp, s_hp = first_crossing_frequency(lambda f: lobes(f).min_power <= HALF_POWER, f_grid_hz,
                                          pre.get("hp"), rel_tol=rel_tol)
    f_sl, s_sl = first_crossing_frequency(lambda f: lobes(f).sidelobe_region_exists, f_grid_hz,
                                          pre.get("sl"), rel_tol=rel_tol)
    out.update({"f_hp_hz": f_hp, "f_hp_status": s_hp, "f_sl_hz": f_sl, "f_sl_status": s_sl})
    for L in settings.ambiguity_levels_db:
        lv = 10 ** (L / 10.0)
        f_a, s_a = first_crossing_frequency(
            lambda f, lv=lv: bool(np.isfinite(lobes(f).psl) and lobes(f).psl >= lv),
            f_grid_hz, pre.get(f"amb_{_lvl(L)}"), rel_tol=rel_tol,
        )
        out[f"f_amb_{_lvl(L)}_hz"] = f_a
        out[f"f_amb_{_lvl(L)}_status"] = s_a
    return out
