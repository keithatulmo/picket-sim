"""Beampattern metrics (definitions in ADR-0005 and docs/metrics.md).

All functions here operate on *normalized* DAS power patterns ``P`` (``P(u0) = 1``). Undefined
metrics are returned as ``nan`` together with a reason string; they are never forced to a number.

Definitions
-----------
Cut (great circle through the steering direction, offset ``gamma`` in degrees, ``gamma = 0`` at
the steering direction):

* ``hpbw_deg``: angular width of the connected region around ``gamma = 0`` with ``P >= 0.5``
  (edges linearly interpolated). Undefined when that region wraps the whole circle.
* mainlobe: region around ``gamma = 0`` bounded by the first local minimum on each side.
* ``max_outside_db``: largest ``P`` strictly outside the mainlobe on the cut (sidelobes *and*
  geometric ambiguity, e.g. the left/right mirror of a horizontal line array). Undefined when the
  mainlobe covers the whole circle.

Observable space (removes geometric ambiguity; see :mod:`picket_sim.geometry`):

* rank 1: the pattern is a function of ``p = u . axis`` on ``[-1, 1]``; analysed in 1-D.
* rank 2 and 3: analysed on the sphere; for rank 2 the mirror image of the steering direction is
  excluded together with the mainlobe.
* ``psl_db``: largest local maximum of ``P`` other than the mainlobe (and its mirror image).
  Undefined when no such local maximum exists in the visible region.
* ``n_lobes_ge``: number of distinct non-mainlobe lobes with peak ``>=`` each level.

Sphere (includes all ambiguity): half-power sphere fraction ``hpsf`` and minimum of ``P``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .acoustics import PlaneWaveManifold
from .beamforming import beampattern_power
from .conventions import angle_between_rad, az_el_deg_from_unit, unit_vector
from .geometry import ArrayGeometry
from .grids import SphereGrid

__all__ = [
    "CutMetrics",
    "circular_profile_metrics",
    "LobeMetrics",
    "observable_lobe_metrics",
    "half_power_sphere_fraction",
    "aliasing_onset_hz",
    "exact_grating_onset_hz",
    "first_crossing_frequency",
    "db",
    "HALF_POWER",
]

HALF_POWER = 0.5  # -3.0103 dB; the conventional "-3 dB" level, used exactly
_MONO_TOL = 1e-12  # tolerance on power when testing for a strict increase (first minimum)


def db(p) -> float:
    p = float(p)
    return 10.0 * np.log10(p) if p > 0 else -np.inf


# ============================================================================ circular cuts
@dataclass(frozen=True)
class CutMetrics:
    hpbw_deg: float
    hpbw_left_deg: float
    hpbw_right_deg: float
    hpbw_reason: str
    mainlobe_left_deg: float
    mainlobe_right_deg: float
    max_outside: float
    max_outside_gamma_deg: float
    outside_reason: str

    @property
    def max_outside_db(self) -> float:
        return db(self.max_outside) if np.isfinite(self.max_outside) else float("nan")


def _walk(p_center: float, seq: np.ndarray):
    """One direction of a walk from the centre of a profile.

    ``seq[j]`` lies ``j + 1`` samples from the centre. Returns ``(j_half, j_min)``: index of the
    first sample below ``HALF_POWER`` and index of the first local minimum (the sample before the
    first strict rise), each ``None`` if not found.
    """
    below = np.flatnonzero(seq < HALF_POWER)
    j_half = int(below[0]) if below.size else None
    prev = np.concatenate(([p_center], seq[:-1]))
    rises = np.flatnonzero(seq > prev + _MONO_TOL)
    if rises.size and rises[0] == 0:
        # the profile rises immediately away from the centre: the centre is not a peak
        raise ValueError("profile centre is not a local maximum; steering/normalization error")
    j_min = int(rises[0]) - 1 if rises.size else None
    return j_half, j_min


def circular_profile_metrics(gamma_deg: np.ndarray, p: np.ndarray) -> CutMetrics:
    """Metrics of a power profile sampled uniformly around a full great circle.

    ``gamma_deg`` must be uniform on [-180, 180) and contain 0 exactly (see
    :func:`picket_sim.grids.cut_offsets_deg`).
    """
    gamma_deg = np.asarray(gamma_deg, dtype=float)
    p = np.asarray(p, dtype=float)
    n = gamma_deg.size
    step = 360.0 / n
    i0 = int(np.flatnonzero(np.isclose(gamma_deg, 0.0, atol=1e-12))[0])
    right = p[(i0 + np.arange(1, n)) % n]
    left = p[(i0 - np.arange(1, n)) % n]
    pc = p[i0]

    jr_half, jr_min = _walk(pc, right)
    jl_half, jl_min = _walk(pc, left)

    # ---- half-power width
    def crossing(j, seq):
        prev = pc if j == 0 else seq[j - 1]
        frac = (prev - HALF_POWER) / (prev - seq[j])
        return step * (j + frac)

    if jr_half is None or jl_half is None:
        hpbw = hl = hr = float("nan")
        hreason = "P >= -3 dB around the entire cut: no half-power discrimination along this cut"
    else:
        hr, hl = crossing(jr_half, right), crossing(jl_half, left)
        hpbw = hr + hl
        hreason = ""

    # ---- mainlobe (first minimum each side) and the region outside it
    sr = jr_min + 1 if jr_min is not None else None  # steps right of centre to the right minimum
    sl = jl_min + 1 if jl_min is not None else None
    ml_r = step * sr if sr is not None else float("nan")
    ml_l = step * sl if sl is not None else float("nan")
    mo, mo_g = float("nan"), float("nan")
    if sr is None or sl is None:
        oreason = "mainlobe is monotone around the whole cut: no region outside the mainlobe"
    else:
        steps = np.arange(sr + 1, n - sl)  # strictly between the two minima, the long way round
        if steps.size == 0:
            oreason = "mainlobe minima meet: no region outside the mainlobe"
        else:
            vals = p[(i0 + steps) % n]
            k = int(np.argmax(vals))
            mo = float(vals[k])
            mo_g = float(((step * steps[k] + 180.0) % 360.0) - 180.0)
            oreason = ""
    return CutMetrics(hpbw, hl, hr, hreason, ml_l, ml_r, mo, mo_g, oreason)


# ============================================================================ sphere metrics
def half_power_sphere_fraction(p_sphere: np.ndarray, weights_sr: np.ndarray) -> float:
    """Fraction of all directions (solid-angle weighted) with ``P >= 0.5``."""
    return float(np.sum(weights_sr * (p_sphere >= HALF_POWER)) / (4.0 * np.pi))


def _sphere_neighbour_extrema(p: np.ndarray):
    """Max and min over the 8 neighbours of each node of an (n_el, n_az) product grid.

    Azimuth wraps; rows beyond the poles are the pole rows rotated by 180 degrees in azimuth.
    """
    n_el, n_az = p.shape
    half = n_az // 2
    top = np.roll(p[-1:], half, axis=1)
    bot = np.roll(p[:1], half, axis=1)
    padded = np.vstack([bot, p, top])
    padded = np.hstack([padded[:, -1:], padded, padded[:, :1]])
    nmax = np.full(p.shape, -np.inf)
    nmin = np.full(p.shape, np.inf)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            sl = padded[1 + di : 1 + di + n_el, 1 + dj : 1 + dj + n_az]
            nmax = np.maximum(nmax, sl)
            nmin = np.minimum(nmin, sl)
    return nmax, nmin


def _refine_on_sphere(fun, az_deg: float, el_deg: float, h_deg: float, iters: int = 4, m: int = 4):
    """Iterative local zoom maximization of ``fun(u)`` around (az, el). Returns (value, az, el)."""
    best_az, best_el = az_deg, el_deg
    best = float(fun(unit_vector(best_az, best_el)[None, :])[0])
    offs = np.arange(-m, m + 1, dtype=float)
    for _ in range(iters):
        az = best_az + offs * h_deg
        el = np.clip(best_el + offs * h_deg, -90.0, 90.0)
        aa, ee = np.meshgrid(az, el, indexing="xy")
        vals = fun(unit_vector(aa, ee).reshape(-1, 3))
        k = int(np.argmax(vals))
        if vals[k] > best:
            best = float(vals[k])
            best_az, best_el = float(aa.reshape(-1)[k]), float(ee.reshape(-1)[k])
        h_deg /= m
    return best, best_az, best_el


def _refine_1d(fun, x: float, h: float, lo: float, hi: float, iters: int = 5, m: int = 8):
    best_x = x
    best = float(fun(np.array([x]))[0])
    offs = np.arange(-m, m + 1, dtype=float)
    for _ in range(iters):
        xs = np.clip(best_x + offs * h, lo, hi)
        vals = fun(xs)
        k = int(np.argmax(vals))
        if vals[k] > best:
            best, best_x = float(vals[k]), float(xs[k])
        h /= m
    return best, best_x


@dataclass
class LobeMetrics:
    """Observable-space lobe structure for one (array, frequency, steering) case."""

    rank: int
    psl: float  # power (linear); nan if undefined
    psl_reason: str
    psl_direction: np.ndarray | None  # a representative direction (3,) of the peak sidelobe
    n_lobes_ge: dict = field(default_factory=dict)  # level_db -> count of non-mainlobe lobes
    min_power: float = float("nan")
    hpsf: float = float("nan")
    resolution_ok: bool = True

    @property
    def psl_db(self) -> float:
        return db(self.psl) if np.isfinite(self.psl) else float("nan")

    @property
    def sidelobe_region_exists(self) -> bool:
        return np.isfinite(self.psl)


#: Minimum number of grid samples across a characteristic lobe width (lambda / aperture) for
#: lobe metrics to be considered adequately resolved.
MIN_SAMPLES_PER_LOBE = 4


def lobe_width_scale(manifold: PlaneWaveManifold, f_hz: float) -> float:
    """Characteristic lobe width lambda/aperture (radians, or direction-cosine units)."""
    ap = manifold.geometry.aperture_m
    return float("inf") if ap == 0 else (manifold.c_mps / f_hz) / ap


def _resolution_ok_1d(manifold, f_hz, n_points) -> bool:
    return lobe_width_scale(manifold, f_hz) >= MIN_SAMPLES_PER_LOBE * (2.0 / (n_points - 1))


def _resolution_ok_sphere(manifold, f_hz, sphere) -> bool:
    return np.rad2deg(lobe_width_scale(manifold, f_hz)) >= MIN_SAMPLES_PER_LOBE * sphere.max_spacing_deg


def _rank1_lobes(manifold, f_hz, u0, levels_db, n_points):
    geom = manifold.geometry
    obs = geom.observability
    axis = obs.axis
    # any unit vector orthogonal to the axis; the rank-1 pattern does not depend on it
    trial = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    b = trial - (trial @ axis) * axis
    b /= np.linalg.norm(b)

    def u_of(pv):
        pv = np.clip(np.asarray(pv, dtype=float), -1.0, 1.0)
        return pv[:, None] * axis + np.sqrt(1.0 - pv * pv)[:, None] * b

    def fun(pv):
        return beampattern_power(manifold, f_hz, u0, u_of(pv))

    p0 = float(np.clip(u0 @ axis, -1.0, 1.0))
    base = np.linspace(-1.0, 1.0, n_points)
    grid = np.unique(np.concatenate([base, [p0]]))
    i0 = int(np.searchsorted(grid, p0))
    vals = fun(grid)

    # HPSF: u . axis is uniformly distributed on [-1, 1] for uniformly distributed directions
    mid = -1.0 + (np.arange(n_points) + 0.5) * (2.0 / n_points)
    hpsf = float(np.mean(fun(mid) >= HALF_POWER))
    pmin = float(vals.min())

    # first minimum on each side of p0 (boundaries are the endfire directions)
    right = vals[i0 + 1 :]
    left = vals[:i0][::-1]
    jr = _walk(vals[i0], right)[1] if right.size else None
    jl = _walk(vals[i0], left)[1] if left.size else None
    regions = []
    if jr is not None:
        regions.append(np.arange(i0 + 1 + jr + 1, grid.size))
    if jl is not None:
        regions.append(np.arange(0, i0 - 1 - jl))
    regions = [r for r in regions if r.size]
    dp = 2.0 / (n_points - 1)
    res_ok = _resolution_ok_1d(manifold, f_hz, n_points)
    if not regions:
        return LobeMetrics(1, float("nan"), "no sidelobe in the visible region (mainlobe fills it)", None,
                           {L: 0 for L in levels_db}, pmin, hpsf, res_ok)
    lobes = []  # (value, p)
    for reg in regions:
        v = vals[reg]
        # local maxima within the region, including region end points that are boundary maxima
        for idx_local in range(v.size):
            gi = reg[idx_local]
            lv = vals[gi - 1] if gi - 1 >= 0 else -np.inf
            rv = vals[gi + 1] if gi + 1 < grid.size else -np.inf
            if vals[gi] >= lv and vals[gi] >= rv and (vals[gi] > min(lv, rv) + _MONO_TOL):
                lobes.append((vals[gi], grid[gi]))
    if not lobes:
        return LobeMetrics(1, float("nan"), "sidelobe region has no local maximum", None,
                           {L: 0 for L in levels_db}, pmin, hpsf, res_ok)
    refined = []
    for v, pv in sorted(lobes, reverse=True)[:12]:
        rv, rp = _refine_1d(fun, pv, dp, -1.0, 1.0)
        refined.append((rv, rp))
    refined += [(v, pv) for v, pv in sorted(lobes, reverse=True)[12:]]
    psl, ppk = max(refined)
    counts = {L: int(sum(1 for v, _ in refined if v >= 10 ** (L / 10.0))) for L in levels_db}
    return LobeMetrics(1, float(psl), "", u_of(np.array([ppk]))[0], counts, pmin, hpsf,
                       _resolution_ok_1d(manifold, f_hz, n_points))


def _sphere_lobes(manifold, f_hz, u0, levels_db, sphere: SphereGrid, p_sphere=None):
    geom = manifold.geometry
    obs = geom.observability
    if p_sphere is None:
        p_sphere = beampattern_power(manifold, f_hz, u0, sphere.unit_vectors)
    hpsf = half_power_sphere_fraction(p_sphere, sphere.weights_sr)
    pmin = float(p_sphere.min())
    nmax, nmin = _sphere_neighbour_extrema(p_sphere)
    is_max = (p_sphere >= nmax) & (p_sphere > nmin + _MONO_TOL)
    cand = np.argwhere(is_max)
    uu = sphere.unit_vectors[cand[:, 0], cand[:, 1]]
    excl_rad = np.deg2rad(2.5 * sphere.max_spacing_deg)
    keep = angle_between_rad(uu, u0[None, :]) > excl_rad
    mirror_u0 = None
    if obs.rank == 2:
        mirror_u0 = obs.mirror(u0)
        keep &= angle_between_rad(uu, mirror_u0[None, :]) > excl_rad
    cand, uu = cand[keep], uu[keep]
    vals = p_sphere[cand[:, 0], cand[:, 1]] if cand.size else np.array([])
    res_ok = _resolution_ok_sphere(manifold, f_hz, sphere)
    if vals.size == 0:
        return LobeMetrics(obs.rank, float("nan"), "no sidelobe in the visible region (mainlobe fills it)",
                           None, {L: 0 for L in levels_db}, pmin, hpsf, res_ok)

    def fun(u):
        return beampattern_power(manifold, f_hz, u0, u)

    order = np.argsort(-vals)
    refined = []
    for rank_i, j in enumerate(order):
        az, el = az_el_deg_from_unit(uu[j])
        if rank_i < 12:
            v, a, e = _refine_on_sphere(fun, float(az), float(el), sphere.max_spacing_deg)
        else:
            v, a, e = float(vals[j]), float(az), float(el)
        refined.append((v, unit_vector(a, e)))
    # de-duplicate: for rank 2 fold every lobe onto one side of the array plane; merge lobes whose
    # peaks are within 2 grid spacings (a lobe sampled by several nodes, or a mirror pair).
    merged: list[tuple[float, np.ndarray]] = []
    tol = np.deg2rad(2.0 * sphere.max_spacing_deg)
    for v, u in sorted(refined, key=lambda t: -t[0]):
        key = u
        if obs.rank == 2 and float(u @ obs.plane_normal) < 0:
            key = obs.mirror(u)
        if any(angle_between_rad(key, mk) < tol for _, mk in merged):
            continue
        merged.append((v, key))
    psl, pdir = merged[0]
    counts = {L: int(sum(1 for v, _ in merged if v >= 10 ** (L / 10.0))) for L in levels_db}
    return LobeMetrics(obs.rank, float(psl), "", pdir, counts, pmin, hpsf, res_ok)


def observable_lobe_metrics(
    manifold: PlaneWaveManifold,
    f_hz: float,
    u0: np.ndarray,
    levels_db=(-1.0, -3.0),
    sphere: SphereGrid | None = None,
    n_points_1d: int = 4001,
    p_sphere: np.ndarray | None = None,
) -> LobeMetrics:
    """Observable-space lobe metrics plus sphere HPSF/minimum (see module docstring)."""
    if manifold.element_response is not None:
        raise NotImplementedError("observable-space reduction assumes ideal omnidirectional elements")
    u0 = np.asarray(u0, dtype=float)
    rank = manifold.geometry.observability.rank
    if rank == 0:
        return LobeMetrics(0, float("nan"), "single omnidirectional sensor: no pattern", None,
                           {L: 0 for L in levels_db}, 1.0, 1.0)
    if rank == 1:
        return _rank1_lobes(manifold, f_hz, u0, levels_db, n_points_1d)
    if sphere is None:
        raise ValueError("a SphereGrid is required for rank-2 and rank-3 geometries")
    return _sphere_lobes(manifold, f_hz, u0, levels_db, sphere, p_sphere)


# ============================================================================ worst-case aliasing
def aliasing_onset_hz(
    geometry: ArrayGeometry,
    c_mps: float,
    levels_db=(-1.0, -3.0),
    f_max_hz: float = 10_000.0,
    n_dirs_2d: int = 1440,
    n_dirs_3d: int = 10_000,
    samples_per_lobe: int = 40,
) -> dict:
    """Worst case (over all steering and look directions) ambiguity-lobe onset frequency.

    The DAS pattern is ``|W(k (u - u0))|^2`` with ``W(q) = mean_n exp(j q . s_n)`` in the
    observable space; every ``q`` with ``|q| <= 2k`` is realised by some (steering, look) pair.
    Along rays from ``q = 0`` the mainlobe ends at the first local minimum; the smallest ``|q|``
    beyond it with ``|W|^2 >= L`` gives ``f_L = c |q| / (4 pi)``. Returns ``{level_db: f or None}``
    (``None`` = no such lobe up to ``f_max_hz``) plus diagnostic keys.
    """
    obs = geometry.observability
    r = obs.rank
    out = {"rank": r, "f_max_hz": f_max_hz}
    if r == 0:
        out.update({L: None for L in levels_db})
        out["reason"] = "single sensor: no pattern, aliasing undefined"
        return out
    s = geometry.reduced_positions_m  # (N, r)
    q_max = 4.0 * np.pi * f_max_hz / c_mps
    dq = (2.0 * np.pi / geometry.aperture_m) / samples_per_lobe
    t = np.arange(0.0, q_max + dq, dq)
    if r == 1:
        dirs = np.array([[1.0]])  # |W(-q)| = |W(q)|: one direction suffices
    elif r == 2:
        ang = np.pi * np.arange(n_dirs_2d) / n_dirs_2d  # half circle by symmetry
        dirs = np.stack([np.cos(ang), np.sin(ang)], axis=-1)
    else:
        from .conventions import fibonacci_sphere

        d = fibonacci_sphere(2 * n_dirs_3d)
        dirs = d[d[:, 2] >= 0][:n_dirs_3d]
    levels_lin = {L: 10 ** (L / 10.0) for L in levels_db}
    best = {L: np.inf for L in levels_db}
    chunk = max(1, int(2_000_000 // (t.size * s.shape[0])))
    for i in range(0, dirs.shape[0], chunk):
        dd = dirs[i : i + chunk]
        proj = dd @ s.T  # (D, N)
        w = np.mean(np.exp(1j * t[None, :, None] * proj[:, None, :]), axis=-1)
        pw = np.abs(w) ** 2  # (D, T)
        rises = pw[:, 1:] > pw[:, :-1] + _MONO_TOL
        has = rises.any(axis=1)
        first_rise = np.where(has, np.argmax(rises, axis=1) + 1, t.size)  # index of first rising sample
        idx = np.arange(t.size)[None, :]
        beyond = idx >= first_rise[:, None]
        for L, lv in levels_lin.items():
            hit = beyond & (pw >= lv)
            any_hit = hit.any(axis=1)
            if not any_hit.any():
                continue
            j = np.argmax(hit, axis=1)
            for row in np.flatnonzero(any_hit):
                jj = int(j[row])
                p_prev, p_cur = pw[row, jj - 1], pw[row, jj]
                frac = 0.0 if p_cur == p_prev else (lv - p_prev) / (p_cur - p_prev)
                q = t[jj - 1] + np.clip(frac, 0.0, 1.0) * dq
                best[L] = min(best[L], q)
    for L in levels_db:
        f = c_mps * best[L] / (4.0 * np.pi)
        out[L] = float(f) if np.isfinite(f) and f <= f_max_hz else None
    out["q_step_rad_per_m"] = dq
    out["n_directions"] = int(dirs.shape[0])
    return out


def exact_grating_onset_hz(geometry: ArrayGeometry, c_mps: float, f_max_hz: float = 1e6, search: int = 8):
    """Worst-case onset of EXACT grating lobes (``|W(q)| = 1``, q != 0), or None if none exist.

    Exact grating lobes exist when the sensor baselines generate a lattice in the observable
    space. Candidates are the reciprocal lattice of ``rank`` linearly independent baselines (the
    shortest ones), ``q = 2 pi D^-1 m`` for integer ``m``; a candidate is a grating lobe if every
    baseline satisfies ``q . d in 2 pi Z`` (checked as ``|W(q)|^2 > 1 - 1e-9``). For a minimal
    array (``N - 1 == rank``, e.g. any non-coplanar 4-element array) the check always passes:
    irregular placement cannot prevent exact grating lobes. Generic arrays with more elements than
    ``rank + 1`` and incommensurate baselines have none. Returns ``f = c |q_min| / (4 pi)``, the
    lowest frequency at which some (steering, look) pair sees a 0 dB grating lobe.
    """
    obs = geometry.observability
    r = obs.rank
    if r == 0:
        return None
    s = geometry.reduced_positions_m
    base = s[1:] - s[0]
    # choose r independent baselines, shortest first
    order = np.argsort(np.linalg.norm(base, axis=1), kind="stable")
    chosen: list[np.ndarray] = []
    for i in order:
        cand = chosen + [base[i]]
        if np.linalg.matrix_rank(np.array(cand), tol=1e-9) == len(cand):
            chosen = cand
        if len(chosen) == r:
            break
    recip = 2.0 * np.pi * np.linalg.inv(np.array(chosen))  # columns g_j with d_i . g_j = 2 pi delta_ij
    grids = np.meshgrid(*([np.arange(-search, search + 1)] * r), indexing="ij")
    m = np.stack([g.ravel() for g in grids], axis=1).astype(float)
    m = m[np.any(m != 0, axis=1)]
    q = m @ recip.T
    qn = np.linalg.norm(q, axis=1)
    idx = np.argsort(qn, kind="stable")
    q_max = 4.0 * np.pi * f_max_hz / c_mps
    for j in idx:
        if qn[j] > q_max:
            break
        w = np.mean(np.exp(1j * (s @ q[j])))
        if abs(w) ** 2 > 1.0 - 1e-9:
            return float(c_mps * qn[j] / (4.0 * np.pi))
    return None


# ============================================================================ thresholds
def first_crossing_frequency(predicate, f_grid_hz, values=None, iters: int = 40, rel_tol: float = 1e-4):
    """Lowest frequency at which ``predicate(f)`` becomes True.

    Scans ``f_grid_hz`` (ascending) up to the first True (lazily, or from precomputed boolean
    ``values``), then bisects in log-frequency between the last False and the first True grid
    point. Returns ``(f, status)``: ``"ok"``; ``"below_grid"`` (True already at the first grid
    point, f is that point and only an upper bound); or ``"not_reached"`` (never True on the grid,
    f is nan). Assumes a single False-to-True transition inside the bracketing grid interval.
    """
    f_grid_hz = np.asarray(f_grid_hz, dtype=float)
    j = None
    if values is not None:
        values = np.asarray(values, dtype=bool)
        if values.any():
            j = int(np.argmax(values))
    else:
        for i, f in enumerate(f_grid_hz):
            if predicate(float(f)):
                j = i
                break
    if j is None:
        return float("nan"), "not_reached"
    if j == 0:
        return float(f_grid_hz[0]), "below_grid"
    lo, hi = np.log(f_grid_hz[j - 1]), np.log(f_grid_hz[j])
    for _ in range(iters):
        if hi - lo < rel_tol:
            break
        mid = 0.5 * (lo + hi)
        if predicate(float(np.exp(mid))):
            hi = mid
        else:
            lo = mid
    return float(np.exp(hi)), "ok"
