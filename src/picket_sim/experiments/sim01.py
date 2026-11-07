"""SIM-01: array geometry and idealized acoustic performance.

Run with ``python -m picket_sim run configs/sim01/sim01_baseline.yaml``. Every number written by
this module is computed here from the configuration; nothing is typed in by hand.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

from ..acoustics import PlaneWaveManifold
from ..analysis import AnalysisSettings, Steering, _lvl, analyze_frequency, steering_thresholds
from ..beamforming import beampattern_power
from ..config import build_array, config_sha256, lattice_spacing_m, load_config
from ..conventions import horizontal_cut, unit_vector, vertical_cut
from ..geometry import uniform_linear, uniform_rectangular
from ..grids import SphereGrid, cut_offsets_deg, log_frequency_grid
from ..metrics import HALF_POWER, aliasing_onset_hz, exact_grating_onset_hz
from ..mismatch import mismatch_peak
from ..records import (
    DirtyTreeError,
    RunDirectory,
    git_state,
    make_run_id,
    software_versions,
    utc_now,
)
from ..tables import write_csv, write_markdown

__all__ = ["run", "Sim01Study"]

HP_DB = 10.0 * math.log10(HALF_POWER)


# ============================================================================ helpers
def _finite_or(x, alt):
    return x if (x is not None and np.isfinite(x)) else alt


def _stats(values, undefined_as=np.nan):
    v = np.array([undefined_as if (x is None or not np.isfinite(x)) else x for x in values], dtype=float)
    if v.size == 0:
        return np.nan, np.nan, np.nan
    return float(np.median(v)), float(np.min(v)), float(np.max(v))


def _defined(values):
    return [float(x) for x in values if x is not None and np.isfinite(x)]


def _group(rows, keys):
    out: dict[tuple, list] = {}
    for r in rows:
        out.setdefault(tuple(r[k] for k in keys), []).append(r)
    return out


def _band_mask(f, band):
    return (f >= band[0]) & (f < band[1])


NUMERICAL_TIE_REL = 1e-9  # values closer than this (relative) are numerically equal


def _attr_tol(a: dict, v: float, practical: bool) -> float:
    """Tie tolerance for one attribute value: numerical by default; declared engineering tolerance
    (``tol`` absolute and/or ``rel_tol`` relative, from the configuration) when ``practical``."""
    tol = NUMERICAL_TIE_REL * max(abs(v), 1.0)
    if practical:
        tol = max(tol, float(a.get("tol", 0.0)), float(a.get("rel_tol", 0.0)) * abs(v))
    return tol


def pareto_front(rows: list[dict], attributes: list[dict], practical: bool = False) -> list[dict]:
    """Mark Pareto-dominated rows. ``attributes``: dicts with ``key`` and ``sense`` (min|max).

    ``o`` dominates ``r`` if, on every attribute, ``o`` is not worse than ``r`` by more than the tie
    tolerance and, on at least one, ``o`` is better by more than it. Infinite values compare
    normally (``inf`` = beyond the analysed band). NaN attributes are treated as worst and listed.
    """
    def val(r, a):
        v = r.get(a["key"])
        v = np.nan if v is None else float(v)
        if np.isnan(v):
            return -np.inf
        return -v if a["sense"] == "min" else v

    def better(o, r, a):  # +1 o better, -1 o worse, 0 tie
        vo, vr = val(o, a), val(r, a)
        if vo == vr:
            return 0
        if not (np.isfinite(vo) and np.isfinite(vr)):
            return 1 if vo > vr else -1
        tol = max(_attr_tol(a, abs(vo), practical), _attr_tol(a, abs(vr), practical))
        if vo - vr > tol:
            return 1
        if vr - vo > tol:
            return -1
        return 0

    out = []
    for r in rows:
        dominated_by = []
        for o in rows:
            if o is r:
                continue
            cmp = [better(o, r, a) for a in attributes]
            if all(c >= 0 for c in cmp) and any(c > 0 for c in cmp):
                dominated_by.append(o["array_id"])
        undefined = [a["key"] for a in attributes if r.get(a["key"]) is None or np.isnan(float(r.get(a["key"])))]
        out.append({"array_id": r["array_id"], "pareto_dominated": bool(dominated_by),
                    "dominated_by": ";".join(dominated_by), "undefined_attributes": ";".join(undefined)})
    return out


# ============================================================================ study
class Sim01Study:
    def __init__(self, cfg: dict, log=print):
        self.cfg = cfg
        self.log = log
        self.c0 = float(cfg["physics"]["sound_speed_mps"])
        fg = cfg["frequency_grid"]
        self.f_grid = log_frequency_grid(fg["f_min_hz"], fg["f_max_hz"], int(fg["points_per_decade"]))
        self.f_max = float(fg["f_max_hz"])
        g = cfg["grids"]
        self.levels = tuple(float(x) for x in cfg["metrics"]["ambiguity_levels_db"])
        self.settings = AnalysisSettings(
            sphere=SphereGrid(int(g["sphere"]["n_el"]), int(g["sphere"]["n_az"])),
            cut_points=int(g.get("cut_points", 3600)),
            reduced_1d_points=int(g.get("reduced_1d_points", 4001)),
            ambiguity_levels_db=self.levels,
        )
        self.settings_fast = AnalysisSettings(
            sphere=self.settings.sphere, cut_points=self.settings.cut_points,
            reduced_1d_points=self.settings.reduced_1d_points, ambiguity_levels_db=self.levels,
            use_sphere_for_rank1=False,
        )
        self.specs = {a["id"]: a for a in cfg["arrays"]}
        self.geoms = [build_array(a) for a in cfg["arrays"]]
        self.steering = []
        for ring in cfg["steering"]["rings"]:
            step = float(ring["az_step_deg"])
            for az in np.arange(0.0, 360.0, step):
                self.steering.append(Steering(ring["name"], float(((az + 180) % 360) - 180), float(ring["el_deg"])))
        self.horizon_ring = cfg["steering"]["rings"][0]["name"]
        self.self_checks: dict = {}
        self.warnings: list[str] = []
        self.timings: dict = {}
        self.figures: list[str] = []

    # ------------------------------------------------------------------ geometry
    def geometry_table(self):
        rows, alias = [], {}
        for g in self.geoms:
            spec = self.specs[g.array_id]
            a = aliasing_onset_hz(g, self.c0, self.levels, self.f_max)
            alias[g.array_id] = a
            d = lattice_spacing_m(spec)
            s = g.summary()
            s.update({
                "label": spec.get("label", ""),
                "type": spec["type"],
                "lattice_spacing_m": d,
                "f_grating_lattice_analytic_hz": (self.c0 / (2 * d)) if d else None,
                "f_grating_exact_worst_hz": exact_grating_onset_hz(g, self.c0),
                "f_aperture_eq_lambda_hz": (self.c0 / g.aperture_m) if g.aperture_m > 0 else None,
                "wng_db": 10 * math.log10(g.n_elements),
                "max_di_spatially_uncorrelated_db": 10 * math.log10(g.n_elements),
            })
            for L in self.levels:
                s[f"f_alias_{_lvl(L)}_hz"] = a[L]
            s["positions_m"] = ";".join(f"({p[0]:.4f},{p[1]:.4f},{p[2]:.4f})" for p in g.positions_m)
            rows.append(s)
        # self-check: general reciprocal-lattice result must equal c/(2d) for declared lattices
        dev = [abs(r["f_grating_exact_worst_hz"] / r["f_grating_lattice_analytic_hz"] - 1)
               for r in rows if r["f_grating_lattice_analytic_hz"]]
        self.self_checks["exact_grating_vs_lattice_analytic_max_rel"] = max(dev) if dev else None
        if dev and max(dev) > 1e-9:
            raise RuntimeError("self-check failed: reciprocal-lattice grating onset disagrees with c/(2d)")
        return rows, alias

    # ------------------------------------------------------------------ main sweep
    def main_sweep(self, geoms=None, c=None, f_grid=None, steering=None, settings=None):
        geoms = geoms or self.geoms
        c = c or self.c0
        f_grid = self.f_grid if f_grid is None else f_grid
        steering = steering or self.steering
        settings = settings or self.settings
        rows = []
        for g in geoms:
            man = PlaneWaveManifold(g, c)
            t0 = time.time()
            for f in f_grid:
                rows += analyze_frequency(man, float(f), steering, settings)
            self.log(f"  sweep {g.array_id} (c={c:g}): {len(f_grid)} frequencies x {len(steering)} steering, "
                     f"{time.time() - t0:.1f} s")
        return rows

    def check_sweep(self, rows):
        tol = float(self.cfg["metrics"].get("di_quadrature_tolerance_db", 0.01))
        dev = [abs(r["di_db"] - r["di_quadrature_db"]) for r in rows if np.isfinite(r["di_quadrature_db"])]
        worst = max(dev) if dev else 0.0
        self.self_checks["di_closed_form_vs_quadrature_max_abs_db"] = worst
        self.self_checks["di_closed_form_vs_quadrature_tolerance_db"] = tol
        if worst > tol:
            raise RuntimeError(f"self-check failed: DI closed form vs quadrature differ by {worst:.4g} dB > {tol} dB")
        # rank-1 HPSF: exact 1-D value vs sphere-grid quadrature of the indicator (informational)
        d1 = [abs(r["hpsf"] - r["hpsf_sphere_grid"]) for r in rows
              if r["rank"] == 1 and np.isfinite(r["hpsf_sphere_grid"])]
        self.self_checks["hpsf_rank1_exact_vs_sphere_grid_max_abs"] = max(d1) if d1 else None
        # normalization: P(u0) == 1 exactly for every array at band edges and centre
        nerr = 0.0
        for g in self.geoms:
            man = PlaneWaveManifold(g, self.c0)
            for f in (self.f_grid[0], self.f_grid[len(self.f_grid) // 2], self.f_grid[-1]):
                for st in self.steering:
                    nerr = max(nerr, abs(float(beampattern_power(man, f, st.u, st.u[None, :])[0]) - 1.0))
        self.self_checks["normalization_max_abs_error"] = nerr
        if nerr > 1e-12:
            raise RuntimeError(f"self-check failed: normalized power at steering direction deviates by {nerr}")
        bad = sum(1 for r in rows if not r["resolution_ok"])
        self.self_checks["sweep_rows_resolution_limited"] = bad
        if bad:
            self.warnings.append(f"{bad} sweep rows have lobe widths below {4} grid samples (flagged resolution_ok=false)")

    # ------------------------------------------------------------------ thresholds
    def thresholds(self, geoms, c, steering, sweep_rows=None, settings=None, f_grid=None):
        settings = settings or self.settings
        f_grid = self.f_grid if f_grid is None else f_grid
        pre_by = {}
        if sweep_rows is not None:
            for key, rs in _group(sweep_rows, ("array_id", "ring", "az0_deg", "el0_deg")).items():
                rs = sorted(rs, key=lambda r: r["f_hz"])
                pre = {"hp": [r["min_power_db"] <= HP_DB for r in rs],
                       "sl": [np.isfinite(r["psl_obs_db"]) for r in rs]}
                for L in self.levels:
                    pre[f"amb_{_lvl(L)}"] = [bool(np.isfinite(r["psl_obs_db"]) and r["psl_obs_db"] >= L) for r in rs]
                pre_by[key] = pre
        out = []
        for g in geoms:
            man = PlaneWaveManifold(g, c)
            t0 = time.time()
            for st in steering:
                pre = pre_by.get((g.array_id, st.ring, st.az_deg, st.el_deg))
                out.append(steering_thresholds(man, st, f_grid, settings, pre))
            self.log(f"  thresholds {g.array_id} (c={c:g}): {len(steering)} steering, {time.time() - t0:.1f} s")
        return out

    def threshold_summary(self, thr_rows, alias, ring):
        rows = []
        for g in self.geoms:
            rs = [r for r in thr_rows if r["array_id"] == g.array_id and r["ring"] == ring]
            if not rs:
                continue
            row = {"array_id": g.array_id, "ring": ring, "n_steering": len(rs)}
            for key in ["f_hp_hz", "f_sl_hz"] + [f"f_amb_{_lvl(L)}_hz" for L in self.levels]:
                status = [r[key.replace("_hz", "_status")] for r in rs]
                vals = []
                for r, s in zip(rs, status):
                    if s == "not_reached":
                        vals.append(np.inf)  # above the analysed band
                    elif s.startswith("never") or s.startswith("undefined"):
                        vals.append(np.nan)
                    else:
                        vals.append(r[key])
                v = np.array(vals, dtype=float)
                if np.all(np.isnan(v)):
                    row[key.replace("_hz", "_min_hz")] = row[key.replace("_hz", "_median_hz")] = \
                        row[key.replace("_hz", "_max_hz")] = np.nan
                else:
                    row[key.replace("_hz", "_min_hz")] = float(np.nanmin(v))
                    row[key.replace("_hz", "_median_hz")] = float(np.nanmedian(v))
                    row[key.replace("_hz", "_max_hz")] = float(np.nanmax(v))
                row[key.replace("_hz", "_below_grid")] = int(sum(s == "below_grid" for s in status))
            a = alias.get(g.array_id, {})
            for L in self.levels:
                v = a.get(L)
                row[f"f_alias_worstcase_{_lvl(L)}_hz"] = (np.inf if v is None else v) if g.n_elements > 1 else np.nan
            rows.append(row)
        return rows

    # ------------------------------------------------------------------ summaries
    def summarize_by_frequency(self, rows):
        out = []
        for (aid, ring, f), rs in sorted(_group(rows, ("array_id", "ring", "f_hz")).items(),
                                          key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
            s = {"array_id": aid, "ring": ring, "f_hz": f, "n_steering": len(rs)}
            s["di_median_db"], s["di_min_db"], s["di_max_db"] = _stats([r["di_db"] for r in rs])
            s["hpsf_median"], s["hpsf_min"], s["hpsf_max"] = _stats([r["hpsf"] for r in rs])
            s["min_power_median_db"] = _stats([r["min_power_db"] for r in rs])[0]
            for cut in ("h", "v"):
                vals = [r[f"hpbw_{cut}_deg"] for r in rs]
                med, lo, hi = _stats(vals, undefined_as=np.inf)
                s[f"hpbw_{cut}_median_deg"], s[f"hpbw_{cut}_best_deg"], s[f"hpbw_{cut}_worst_deg"] = med, lo, hi
                s[f"hpbw_{cut}_undefined_frac"] = sum(not np.isfinite(v) for v in vals) / len(vals)
                d = _defined([r[f"max_outside_{cut}_db"] for r in rs])
                s[f"max_outside_{cut}_max_db"] = max(d) if d else np.nan
                s[f"max_outside_{cut}_defined_frac"] = len(d) / len(rs)
            d = _defined([r["psl_obs_db"] for r in rs])
            s["psl_obs_median_db"] = float(np.median(d)) if d else np.nan
            s["psl_obs_max_db"] = max(d) if d else np.nan
            s["psl_obs_defined_frac"] = len(d) / len(rs)
            for L in self.levels:
                k = f"n_amb_lobes_ge_{_lvl(L)}"
                s[f"{k}_max"] = max(r[k] for r in rs)
            s["resolution_ok_all"] = all(r["resolution_ok"] for r in rs)
            out.append(s)
        return out

    def band_metrics(self, summary_rows):
        bands = self.cfg["bands_hz"]
        out = {}
        for g in self.geoms:
            rs = [r for r in summary_rows if r["array_id"] == g.array_id and r["ring"] == self.horizon_ring]
            f = np.array([r["f_hz"] for r in rs])
            d = {}
            for name, band in bands.items():
                m = _band_mask(f, band)
                d[f"di_band_{name}_db"] = float(np.median(np.array([r["di_median_db"] for r in rs])[m]))
                d[f"hpsf_band_{name}"] = float(np.median(np.array([r["hpsf_median"] for r in rs])[m]))
            out[g.array_id] = d
        return out

    # ------------------------------------------------------------------ sensitivity
    def ula_sensitivity(self, f_grid):
        sens = self.cfg["sensitivity"]["ula"]
        rows, thr, geo = [], [], []
        for n in sens["n_elements"]:
            for d in sens["spacing_m"]:
                g = uniform_linear(int(n), float(d), (1, 0, 0), f"ULA-N{n}-d{d:g}")
                man = PlaneWaveManifold(g, self.c0)
                a = aliasing_onset_hz(g, self.c0, self.levels, self.f_max)
                geo.append({"array_id": g.array_id, "n_elements": n, "spacing_m": d, "aperture_m": g.aperture_m,
                            "f_grating_exact_worst_hz": self.c0 / (2 * d),
                            "f_first_null_broadside_hz": self.c0 / (n * d),
                            **{f"f_alias_{_lvl(L)}_hz": a[L] for L in self.levels}})
                for s in sens["steering"]:
                    st = Steering(s["name"], float(s["az_deg"]), float(s["el_deg"]))
                    for f in f_grid:
                        r = analyze_frequency(man, float(f), [st], self.settings_fast)[0]
                        r.update({"n_elements": n, "spacing_m": d})
                        rows.append(r)
                    t = steering_thresholds(man, st, f_grid, self.settings_fast)
                    t.update({"n_elements": n, "spacing_m": d, "aperture_m": g.aperture_m})
                    thr.append(t)
        return rows, thr, geo

    def scaled_family(self, base_spec_id, kind):
        """Square side sweep or A4 scale sweep: thresholds over a coarse horizon ring + q-space."""
        sens = self.cfg["sensitivity"]
        ring = [Steering("horizon", float(((az + 180) % 360) - 180), 0.0) for az in np.arange(0, 360, 30.0)]
        geos = []
        if kind == "square":
            for side in sens["square_side_m"]:
                geos.append((float(side), uniform_rectangular(2, 2, side, side, array_id=f"SQ-{side:g}m")))
        else:
            base = build_array(self.specs[base_spec_id])
            for sc in sens["a4_scale"]:
                geos.append((float(sc), base.scaled(float(sc), array_id=f"{base_spec_id}x{sc:g}")))
        out = []
        for param, g in geos:
            man = PlaneWaveManifold(g, self.c0)
            a = aliasing_onset_hz(g, self.c0, self.levels, self.f_max)
            ts = [steering_thresholds(man, st, self.f_grid, self.settings) for st in ring]
            row = {"array_id": g.array_id, "parameter": param, "aperture_m": g.aperture_m,
                   "min_spacing_m": g.min_spacing_m, "rank": g.observability.rank}
            for key in ["f_hp_hz", "f_sl_hz"] + [f"f_amb_{_lvl(L)}_hz" for L in self.levels]:
                v = np.array([np.inf if t[key.replace("_hz", "_status")] == "not_reached" else t[key] for t in ts])
                row[key.replace("_hz", "_median_hz")] = float(np.median(v))
                row[key.replace("_hz", "_min_hz")] = float(np.min(v))
                row[key.replace("_hz", "_below_grid")] = int(sum(t[key.replace("_hz", "_status")] == "below_grid" for t in ts))
            for L in self.levels:
                row[f"f_alias_worstcase_{_lvl(L)}_hz"] = np.inf if a[L] is None else a[L]
            fx = exact_grating_onset_hz(g, self.c0)
            row["f_grating_exact_worst_hz"] = np.inf if fx is None else fx
            out.append(row)
            self.log(f"  sensitivity {g.array_id}: done")
        return out

    def orientation_variants(self):
        sens = self.cfg["sensitivity"]
        ring = [s for s in self.steering if s.ring == self.horizon_ring]
        out = []
        variants = [self.specs["A1"], self.specs["A3"]] + list(sens["orientation_variants"])
        for spec in variants:
            g = build_array(spec)
            man = PlaneWaveManifold(g, self.c0)
            for f in sens["orientation_frequencies_hz"]:
                rs = analyze_frequency(man, float(f), ring, self.settings)
                s = self.summarize_by_frequency(rs)[0]
                s.update({"label": spec.get("label", ""), "rank": g.observability.rank,
                          "ambiguity_class": g.observability.ambiguity_class,
                          "ambiguity_description": g.observability.description})
                out.append(s)
        return out

    # ------------------------------------------------------------------ robustness
    def sound_speed_robustness(self, thr_c0_rows):
        rob = self.cfg["robustness"]
        step = 30.0
        ring = [Steering(self.horizon_ring, float(((az + 180) % 360) - 180), 0.0) for az in np.arange(0, 360, step)]
        geoms = [g for g in self.geoms if g.n_elements > 1]
        rows = []
        for c in rob["sound_speeds_mps"]:
            c = float(c)
            keyset = {(st.az_deg, st.el_deg) for st in ring}
            thr = [r for r in thr_c0_rows if r["ring"] == self.horizon_ring and (r["az0_deg"], r["el0_deg"]) in keyset]
            if c != self.c0 or len(thr) != len(keyset) * len(geoms):
                thr = self.thresholds(geoms, c, ring)  # reuse nominal results only if the steering set matches
            for g in geoms:
                ts = [t for t in thr if t["array_id"] == g.array_id]
                a = aliasing_onset_hz(g, c, self.levels, self.f_max)
                row = {"array_id": g.array_id, "c_mps": c}
                for key in ["f_hp_hz", "f_sl_hz"] + [f"f_amb_{_lvl(L)}_hz" for L in self.levels]:
                    v = np.array([np.inf if t[key.replace("_hz", "_status")] == "not_reached" else t[key] for t in ts])
                    row[key.replace("_hz", "_median_hz")] = float(np.median(v))
                    row[key.replace("_hz", "_min_hz")] = float(np.min(v))
                for L in self.levels:
                    row[f"f_alias_worstcase_{_lvl(L)}_hz"] = np.inf if a[L] is None else a[L]
                rows.append(row)
        # scaling check: every threshold must scale exactly with c (the model depends on f/c only)
        worst = 0.0
        base = {r["array_id"]: r for r in rows if r["c_mps"] == self.c0}
        for r in rows:
            b = base[r["array_id"]]
            for k, v in list(r.items()):
                if k.endswith("_hz") and np.isfinite(v) and np.isfinite(b[k]) and b[k] > 0:
                    rel = abs(v / b[k] - r["c_mps"] / self.c0)
                    r[k.replace("_hz", "_ratio_to_nominal")] = v / b[k]
                    worst = max(worst, rel)
        self.self_checks["threshold_scaling_with_c_max_abs_ratio_error"] = worst
        if worst > 0.02:
            self.warnings.append(f"threshold scaling with sound speed deviates by up to {worst:.3g} (expected ~0)")
        return rows

    def mismatch(self, alias):
        mm = self.cfg["robustness"]["mismatch"]
        rows = []
        for g in self.geoms:
            if g.n_elements < 2:
                continue
            a3 = alias[g.array_id].get(self.levels[-1])
            f = float(mm["max_frequency_hz"])
            if a3 is not None:
                f = min(f, 0.5 * a3)
            for ct in mm["true_mps"]:
                for az, el in mm["sources_deg"]:
                    rows.append(mismatch_peak(g, f, float(ct), float(mm["assumed_mps"]), float(az), float(el),
                                              self.settings.sphere))
        return rows

    # ------------------------------------------------------------------ figure data
    def figure_data(self, alias, thr_summary, summary_rows, ula_rows, ula_thr, ula_geo, a4_rows, sq_rows,
                    ss_rows, mm_rows):
        cfg = self.cfg
        figf = [float(f) for f in cfg["figure_frequencies_hz"]]
        sc = cfg["steering"]["showcase"]
        gam = cut_offsets_deg(3600)
        data = {"arrays": [], "figure_frequencies_hz": figf, "showcase": sc, "c_mps": self.c0}
        f_dense = log_frequency_grid(self.f_grid[0], self.f_grid[-1], 100)
        az_grid = -180.0 + 0.5 * np.arange(720)
        from ..plotting import equirect_grid

        map_az, map_el, u_map = equirect_grid(1.0)
        for g in self.geoms:
            man = PlaneWaveManifold(g, self.c0)
            spec = self.specs[g.array_id]
            d = {"id": g.array_id, "label": spec.get("label", g.array_id), "positions_m": g.positions_m,
                 "rank": g.observability.rank, "ambiguity_class": g.observability.ambiguity_class}
            # horizon cut, steering az=showcase az, el=0
            d["cut_h"] = {f: beampattern_power(man, f, unit_vector(sc["az_deg"], 0.0),
                                               horizontal_cut(sc["az_deg"], 0.0, gam)) for f in figf}
            d["cut_h_gamma_deg"] = gam
            d["cut_h_az0_deg"] = float(sc["az_deg"])
            # vertical cut through the showcase direction
            d["cut_v"] = {f: beampattern_power(man, f, unit_vector(sc["az_deg"], sc["el_deg"]),
                                               vertical_cut(sc["az_deg"], sc["el_deg"], gam)) for f in figf}
            d["cut_v_el0_deg"] = float(sc["el_deg"])
            # frequency-azimuth map on the horizon
            u0 = unit_vector(sc["az_deg"], 0.0)
            look = unit_vector(az_grid, 0.0)
            d["fa_map"] = np.stack([beampattern_power(man, f, u0, look) for f in f_dense])
            d["fa_f_hz"], d["fa_az_deg"] = f_dense, az_grid
            # full-sphere maps at the showcase direction
            us = unit_vector(sc["az_deg"], sc["el_deg"])
            d["sphere_maps"] = {f: beampattern_power(man, f, us, u_map) for f in figf}
            d["mirror_dir"] = None
            if g.observability.rank == 2:
                d["mirror_dir"] = g.observability.mirror(us)
            a = alias[g.array_id]
            d["alias_worst_db"] = {L: a.get(L) for L in self.levels}
            data["arrays"].append(d)
        data["sphere_map_az_deg"], data["sphere_map_el_deg"] = map_az, map_el
        data["summary"] = summary_rows
        data["thr_summary"] = thr_summary
        data["horizon_ring"] = self.horizon_ring
        data["levels"] = self.levels
        data["ula_rows"], data["ula_thr"], data["ula_geo"] = ula_rows, ula_thr, ula_geo
        data["a4_rows"], data["sq_rows"], data["ss_rows"], data["mm_rows"] = a4_rows, sq_rows, ss_rows, mm_rows
        data["bands_hz"] = cfg["bands_hz"]
        return data


# ============================================================================ entry point
def run(config_path, output_root=None, allow_dirty: bool = False, make_figures: bool = True,
        repo_dir=None, log=print, argv=None) -> Path:
    t_start = time.time()
    config_path = Path(config_path)
    cfg = load_config(config_path)
    cfg_sha = config_sha256(cfg)
    repo_dir = Path(repo_dir) if repo_dir else config_path.resolve().parent
    gs = git_state(repo_dir)
    if gs["git_dirty"] and not allow_dirty:
        raise DirtyTreeError("working tree has uncommitted changes to tracked files; commit them or pass --allow-dirty")
    created = utc_now()
    run_id = make_run_id(created, cfg_sha, gs["git_commit"])
    root = Path(output_root) if output_root else Path(cfg["output"]["root"])
    rd = RunDirectory(root, run_id)
    log(f"SIM-01 run {run_id} -> {root / run_id}")
    try:
        study = Sim01Study(cfg, log)
        T = study.timings
        tab = lambda name: rd.path("tables", name)  # noqa: E731

        t = time.time()
        geo_rows, alias = study.geometry_table()
        write_csv(tab("geometry_summary.csv"), geo_rows)
        T["geometry_s"] = time.time() - t

        t = time.time()
        log("main sweep")
        sweep = study.main_sweep()
        study.check_sweep(sweep)
        for r in sweep:
            r["min_power_db"] = max(r["min_power_db"], -300.0)  # exact nulls: clamp -inf for storage
        write_csv(tab("sweep_metrics.csv.gz"), sweep, gz=True)
        T["main_sweep_s"] = time.time() - t

        t = time.time()
        log("regime thresholds")
        thr = study.thresholds(study.geoms, study.c0, study.steering, sweep)
        write_csv(tab("thresholds_by_steering.csv"), thr)
        ring_names = [r["name"] for r in cfg["steering"]["rings"]]
        thr_sum = [row for ring in ring_names for row in study.threshold_summary(thr, alias, ring)]
        write_csv(tab("thresholds_summary.csv"), thr_sum)
        # consistency: worst-case (all steering) onset must not exceed any steering-specific onset
        worst_violation = 0.0
        for r in thr:
            a = alias[r["array_id"]]
            for L in study.levels:
                fs, fw = r.get(f"f_amb_{_lvl(L)}_hz"), a.get(L)
                if fw is not None and fs is not None and np.isfinite(fs) and r.get(f"f_amb_{_lvl(L)}_status") == "ok":
                    worst_violation = max(worst_violation, (fw - fs) / fs)
        study.self_checks["worstcase_alias_minus_steering_alias_max_rel"] = worst_violation
        if worst_violation > 0.01:
            raise RuntimeError(f"self-check failed: worst-case aliasing onset exceeds a steering-specific onset "
                               f"by {worst_violation:.3%}")
        T["thresholds_s"] = time.time() - t

        summ = study.summarize_by_frequency(sweep)
        write_csv(tab("summary_by_frequency.csv"), summ)

        t = time.time()
        log("representative frequencies")
        rep_rows = []
        for g in study.geoms:
            man = PlaneWaveManifold(g, study.c0)
            for f in cfg["representative_frequencies_hz"]:
                rep_rows += analyze_frequency(man, float(f), study.steering, study.settings)
        rep_sum = study.summarize_by_frequency(rep_rows)
        write_csv(tab("representative_frequencies.csv"), rep_sum)
        T["representative_s"] = time.time() - t

        bands = study.band_metrics(summ)
        hz = {r["array_id"]: r for r in thr_sum if r["ring"] == study.horizon_ring}
        comp = []
        rep_h = {(r["array_id"], r["f_hz"]): r for r in rep_sum if r["ring"] == study.horizon_ring}
        rep_d = {(r["array_id"], r["f_hz"]): r for r in rep_sum if r["ring"] != study.horizon_ring}
        for gr in geo_rows:
            aid = gr["array_id"]
            row = {k: gr[k] for k in ("array_id", "label", "n_elements", "aperture_m", "rank", "ambiguity_class",
                                      "wng_db")}
            row.update(bands[aid])
            h = hz.get(aid, {})
            fx = gr["f_grating_exact_worst_hz"]
            row["f_grating_exact_worst_hz"] = (np.inf if fx is None else fx) if gr["n_elements"] > 1 else np.nan
            row["f_hp_median_hz"] = h.get("f_hp_median_hz", np.nan)
            row["f_sl_median_hz"] = h.get("f_sl_median_hz", np.nan)
            for L in study.levels:
                row[f"f_amb_{_lvl(L)}_min_hz"] = h.get(f"f_amb_{_lvl(L)}_min_hz", np.nan)
                v = alias[aid].get(L)
                row[f"f_alias_{_lvl(L)}_hz"] = (np.inf if v is None else v) if gr["n_elements"] > 1 else np.nan
            for f in (1000.0, 2500.0, 5000.0):
                rh = rep_h.get((aid, f))
                row[f"hpbw_h_median_{int(f)}hz_deg"] = rh["hpbw_h_median_deg"] if rh else np.nan
                rdp = rep_d.get((aid, f))
                row[f"max_outside_v_depressed_{int(f)}hz_db"] = rdp["max_outside_v_max_db"] if rdp else np.nan
            comp.append(row)
        write_csv(tab("comparison.csv"), comp)
        pareto_rows, pareto_loo = [], []
        for ps in cfg["pareto"]["sets"]:
            rows_in = [r for r in comp if r["array_id"] in ps["arrays"]]
            for mode, practical in (("numerical ties", False), ("engineering tolerances", True)):
                for pr in pareto_front(rows_in, ps["attributes"], practical):
                    pr.update({"set": ps["name"], "tolerance": mode})
                    pareto_rows.append(pr)
                for drop in ps["attributes"]:
                    attrs = [a for a in ps["attributes"] if a is not drop]
                    dom = [pr for pr in pareto_front(rows_in, attrs, practical) if pr["pareto_dominated"]]
                    pareto_loo.append({"set": ps["name"], "tolerance": mode, "attribute_removed": drop["key"],
                                       "dominated": ";".join(f"{d['array_id']} (by {d['dominated_by']})"
                                                             for d in dom) or "none"})
        write_csv(tab("pareto.csv"), pareto_rows, ["set", "tolerance", "array_id", "pareto_dominated", "dominated_by",
                                                   "undefined_attributes"])
        write_csv(tab("pareto_leave_one_out.csv"), pareto_loo)

        t = time.time()
        log("sensitivity: line arrays")
        sens_grid = log_frequency_grid(study.f_grid[0], study.f_grid[-1], 30)
        ula_rows, ula_thr, ula_geo = study.ula_sensitivity(sens_grid)
        write_csv(tab("sensitivity_ula_sweep.csv.gz"), ula_rows, gz=True)
        write_csv(tab("sensitivity_ula_thresholds.csv"), ula_thr)
        write_csv(tab("sensitivity_ula_geometry.csv"), ula_geo)
        log("sensitivity: square side, A4 scale")
        sq_rows = study.scaled_family(None, "square")
        write_csv(tab("sensitivity_square_side.csv"), sq_rows)
        a4_rows = study.scaled_family("A4", "a4")
        write_csv(tab("sensitivity_a4_scale.csv"), a4_rows)
        log("sensitivity: orientation")
        ori_rows = study.orientation_variants()
        write_csv(tab("sensitivity_orientation.csv"), ori_rows)
        T["sensitivity_s"] = time.time() - t

        t = time.time()
        log("robustness: sound speed")
        ss_rows = study.sound_speed_robustness(thr)
        write_csv(tab("robustness_sound_speed.csv"), ss_rows)
        mm_rows = study.mismatch(alias)
        write_csv(tab("robustness_sound_speed_mismatch.csv"), mm_rows)
        T["robustness_s"] = time.time() - t

        _write_markdown_tables(rd, study, geo_rows, comp, pareto_rows, thr_sum, rep_sum, ss_rows, mm_rows,
                               a4_rows, sq_rows, ori_rows, ula_geo, ula_thr, pareto_loo)

        if make_figures:
            t = time.time()
            log("figures")
            from .. import plotting

            data = study.figure_data(alias, thr_sum, summ, ula_rows, ula_thr, ula_geo, a4_rows, sq_rows,
                                     ss_rows, mm_rows)
            study.figures = plotting.make_sim01_figures(data, rd.path("figures"))
            T["figures_s"] = time.time() - t

        T["total_s"] = time.time() - t_start
        sw = software_versions()
        sw.update(gs)
        record = {
            "run_id": run_id,
            "experiment_id": cfg["experiment"]["id"],
            "title": cfg["experiment"].get("title"),
            "status": "complete",
            "created_utc": created.isoformat(),
            "completed_utc": utc_now().isoformat(),
            "command": list(argv) if argv else sys.argv,
            "config_path": str(config_path),
            "config_sha256": cfg_sha,
            "config_resolved": cfg,
            "software": sw,
            "assumptions": cfg["experiment"].get("assumptions", []),
            "frequency_grid_hz": {"n": len(study.f_grid), "min": study.f_grid[0], "max": study.f_grid[-1]},
            "self_checks": study.self_checks,
            "warnings": study.warnings,
            "timings_s": T,
            "figures": study.figures,
        }
        _write_summary_md(rd, record, study)
        final = rd.finalize(record)
        log(f"done in {T['total_s']:.0f} s: {final}")
        return final
    except BaseException:
        rd.abort()
        raise


# ============================================================================ markdown outputs
def _fmt_hz(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    if np.isinf(v):
        return "> band"
    return f"{v:,.0f}"


def _write_markdown_tables(rd, study, geo_rows, comp, pareto_rows, thr_sum, rep_sum, ss_rows, mm_rows,
                           a4_rows, sq_rows, ori_rows, ula_geo, ula_thr, pareto_loo=()):
    L1, L3 = _lvl(study.levels[0]), _lvl(study.levels[-1])
    p = lambda n: rd.path("tables", n)  # noqa: E731
    write_markdown(p("pareto_leave_one_out.md"), list(pareto_loo), [
        ("set", "Attribute set", ""), ("tolerance", "Tie tolerance", ""), ("attribute_removed", "Attribute removed", ""),
        ("dominated", "Dominated candidates without it", ""),
    ], "Pareto sensitivity: dominance when one attribute is dropped", [
        "Shows which single attribute keeps each candidate on the Pareto front.",
    ])
    rep = []
    hz_ring = study.horizon_ring
    dep = {(r["array_id"], r["f_hz"]): r for r in rep_sum if r["ring"] != hz_ring}
    for r in rep_sum:
        if r["ring"] != hz_ring:
            continue
        rr = dict(r)
        d = dep.get((r["array_id"], r["f_hz"]), {})
        rr["dep_max_outside_v_max_db"] = d.get("max_outside_v_max_db", np.nan)
        rep.append(rr)
    write_markdown(p("representative_frequencies.md"), rep, [
        ("array_id", "ID", ""), ("f_hz", "f (Hz)", ".0f"), ("di_median_db", "DI median (dB)", ".2f"),
        ("di_min_db", "DI min", ".2f"), ("di_max_db", "DI max", ".2f"),
        ("hpbw_h_median_deg", "HPBW_h median (deg)", ".1f"), ("hpbw_h_worst_deg", "HPBW_h worst (deg)", ".1f"),
        ("hpbw_v_median_deg", "HPBW_v median (deg)", ".1f"),
        ("max_outside_h_max_db", "Largest h-cut lobe outside mainlobe (dB)", ".2f"),
        ("psl_obs_max_db", "PSL_obs worst (dB)", ".2f"), ("psl_obs_defined_frac", "PSL defined frac", ".2f"),
        (f"n_amb_lobes_ge_{L3}_max", "Lobes >= -3 dB (max)", ""), ("hpsf_median", "HPSF median", ".3f"),
        ("dep_max_outside_v_max_db", "Depressed 30: largest v-cut lobe (dB)", ".2f"),
    ], "Representative frequencies (horizon steering ring; last column from the el = -30 deg ring)", [
        "inf: the half-power region wraps the cut for at least half of the steering directions.",
        "n/a: undefined (no sidelobe region, no outside-mainlobe region, or single sensor).",
        "Largest h-cut lobe includes geometric ambiguity (left/right mirror of a horizontal line array); "
        "PSL_obs excludes it.",
        "Depressed 30 column: 0 dB for the horizontal square is its up/down mirror image.",
    ])
    write_markdown(p("geometry_summary.md"), geo_rows, [
        ("array_id", "ID", ""), ("label", "Configuration", ""), ("n_elements", "N", ""),
        ("aperture_m", "Max dimension (m)", ".3f"), ("min_spacing_m", "Min spacing (m)", ".3f"),
        ("rank", "Observable dims", ""), ("ambiguity_class", "Geometric ambiguity", ""),
        ("f_grating_exact_worst_hz", "Exact (0 dB) grating onset (Hz)", ",.0f"),
        (f"f_alias_{L1}_hz", f"Worst-case {study.levels[0]:g} dB lobe onset (Hz)", ",.0f"),
        (f"f_alias_{L3}_hz", f"Worst-case {study.levels[-1]:g} dB lobe onset (Hz)", ",.0f"),
        ("wng_db", "WNG (dB)", ".2f"),
    ], "Geometry summary", [
        "Worst-case onset: lowest frequency at which some steering/look pair produces a non-mainlobe "
        "lobe at or above the level in the observable space (array factor in wavevector space, |q| <= 2k).",
        "Exact grating onset: smallest reciprocal-lattice vector of the baselines (equals c/2d for the "
        "line and square lattices; exists for A4 because any 4 non-coplanar sensors form a lattice).",
        "n/a: undefined (single sensor) or no such lobe below the band edge.",
        f"Sound speed {study.c0:g} m/s.",
    ])
    rows = []
    for r in thr_sum:
        rr = dict(r)
        for k, v in r.items():
            if k.endswith("_hz"):
                rr[k] = _fmt_hz(v)
        rows.append(rr)
    write_markdown(p("thresholds_summary.md"), rows, [
        ("array_id", "ID", ""), ("ring", "Steering set", ""),
        ("f_hp_min_hz", "f_HP best (Hz)", ""), ("f_hp_median_hz", "f_HP median (Hz)", ""),
        ("f_hp_max_hz", "f_HP worst (Hz)", ""), ("f_sl_median_hz", "f_SL median (Hz)", ""),
        (f"f_amb_{L3}_min_hz", f"f_amb({study.levels[-1]:g} dB) earliest (Hz)", ""),
        (f"f_amb_{L3}_median_hz", f"f_amb({study.levels[-1]:g} dB) median (Hz)", ""),
        (f"f_amb_{L1}_min_hz", f"f_amb({study.levels[0]:g} dB) earliest (Hz)", ""),
        (f"f_alias_worstcase_{L3}_hz", f"Worst-case {study.levels[-1]:g} dB onset, any steering (Hz)", ""),
    ], "Regime thresholds over steering sets", [
        "f_HP: lowest frequency at which some direction is >= 3 dB below the steered response.",
        "f_SL: lowest frequency at which a sidelobe exists in the observable visible region.",
        "f_amb(L): lowest frequency at which an observable-space ambiguity lobe reaches L dB "
        "(geometric cone/mirror ambiguity excluded).",
        "'> band': not reached below the upper band edge; n/a: undefined (single sensor).",
    ])
    rows = []
    for r in comp:
        rr = dict(r)
        for k in ("f_hp_median_hz", "f_sl_median_hz", f"f_amb_{L3}_min_hz", f"f_alias_{L3}_hz",
                  "f_grating_exact_worst_hz"):
            rr[k] = _fmt_hz(r.get(k))
        rows.append(rr)
    write_markdown(p("comparison.md"), rows, [
        ("array_id", "ID", ""), ("n_elements", "N", ""), ("aperture_m", "Max dim (m)", ".2f"),
        ("ambiguity_class", "Geometric ambiguity", ""), ("wng_db", "WNG (dB)", ".1f"),
        ("di_band_low_db", "DI 0.1-1 kHz (dB)", ".2f"), ("di_band_mid_db", "DI 1-3 kHz (dB)", ".2f"),
        ("di_band_high_db", "DI 3-10 kHz (dB)", ".2f"),
        ("hpsf_band_low", "HPSF 0.1-1 kHz", ".2f"), ("hpsf_band_mid", "HPSF 1-3 kHz", ".2f"),
        ("hpsf_band_high", "HPSF 3-10 kHz", ".2f"),
        ("hpbw_h_median_1000hz_deg", "HPBW_h 1 kHz (deg)", ".0f"),
        ("hpbw_h_median_2500hz_deg", "HPBW_h 2.5 kHz (deg)", ".0f"),
        ("hpbw_h_median_5000hz_deg", "HPBW_h 5 kHz (deg)", ".0f"),
        ("f_hp_median_hz", "f_HP (Hz)", ""), ("f_sl_median_hz", "f_SL (Hz)", ""),
        (f"f_amb_{L3}_min_hz", "f_amb -3 dB horizon (Hz)", ""),
        (f"f_alias_{L3}_hz", "f_amb -3 dB any steering (Hz)", ""),
        ("f_grating_exact_worst_hz", "Exact grating onset (Hz)", ""),
    ], "Comparative results (horizon steering ring unless stated)", [
        "DI: directivity index vs spherically isotropic noise (ideal DAS), median over horizon steering, "
        "then median over frequencies in the band. Not detection performance.",
        "HPSF: fraction of all directions within 3 dB of the steered response (includes every ambiguity); "
        "1.0 = no half-power discrimination anywhere.",
        "HPBW_h: half-power width on the horizontal great circle, median over horizon steering; "
        "inf = half-power region wraps the circle for most steering directions (includes merged "
        "left/right mirror lobes for line arrays).",
        "WNG: white-noise gain of uniform DAS = 10 log10 N, independent of geometry and frequency.",
    ])
    write_markdown(p("pareto.md"), pareto_rows, [
        ("set", "Attribute set", ""), ("tolerance", "Tie tolerance", ""), ("array_id", "ID", ""),
        ("pareto_dominated", "Dominated", ""),
        ("dominated_by", "Dominated by", ""), ("undefined_attributes", "Undefined attributes", ""),
    ], "Pareto dominance (only attributes evaluated in SIM-01)", [
        "A candidate is dominated if another is at least as good on every listed attribute and strictly "
        "better on one. Attribute lists are in the configuration (pareto.sets).",
        "Numerical ties: differences below 1e-9 (relative) are ties. Engineering tolerances: differences "
        "below the per-attribute tol / rel_tol declared in the configuration are ties (smaller differences "
        "are not meaningful given model fidelity, sound-speed uncertainty and grid resolution).",
        "Cost is NOT evaluated; channel count and maximum dimension are proxies only.",
    ])
    rows = []
    for r in ss_rows:
        rr = dict(r)
        for k, v in r.items():
            if k.endswith("_hz"):
                rr[k] = _fmt_hz(v)
        rows.append(rr)
    write_markdown(p("robustness_sound_speed.md"), rows, [
        ("array_id", "ID", ""), ("c_mps", "c (m/s)", ".0f"), ("f_hp_median_hz", "f_HP median (Hz)", ""),
        ("f_sl_median_hz", "f_SL median (Hz)", ""), (f"f_amb_{L3}_min_hz", "f_amb -3 dB earliest (Hz)", ""),
        (f"f_alias_worstcase_{L3}_hz", "Worst-case -3 dB onset (Hz)", ""),
        ("f_hp_median_ratio_to_nominal", "f_HP ratio to nominal", ".4f"),
    ], "Sound-speed robustness (horizon ring, 30 degree steering step)")
    write_markdown(p("robustness_sound_speed_mismatch.md"), mm_rows, [
        ("array_id", "ID", ""), ("f_hz", "f (Hz)", ".0f"), ("c_true_mps", "c true", ".0f"),
        ("c_assumed_mps", "c assumed", ".0f"), ("az_true_deg", "az", ".0f"), ("el_true_deg", "el", ".0f"),
        ("cone_angle_error_deg", "Cone-angle error (deg)", "+.2f"),
        ("cone_angle_pred_error_deg", "Predicted (deg)", "+.2f"),
        ("az_error_deg", "Azimuth error (deg)", "+.2f"), ("abs_el_error_deg", "|el| error (deg)", "+.2f"),
        ("abs_el_pred_error_deg", "Predicted |el| error (deg)", "+.2f"),
        ("direction_error_deg", "Direction error (deg)", ".2f"),
    ], "Peak-direction bias from sound-speed mismatch (noise-free, ideal)")
    for name, rows_in, title in (("sensitivity_a4_scale.md", a4_rows, "A4 scale sensitivity"),
                                 ("sensitivity_square_side.md", sq_rows, "Square side-length sensitivity")):
        rows = []
        for r in rows_in:
            rr = dict(r)
            for k, v in r.items():
                if k.endswith("_hz"):
                    rr[k] = _fmt_hz(v)
                    base = k.replace("_median_hz", "").replace("_min_hz", "")
                    if r.get(f"{base}_below_grid"):
                        rr[k] = "<= " + rr[k] + " (below band)"
            rows.append(rr)
        write_markdown(p(name), rows, [
            ("array_id", "ID", ""), ("parameter", "Scale / side", ".3g"), ("aperture_m", "Max dim (m)", ".2f"),
            ("min_spacing_m", "Min spacing (m)", ".2f"), ("f_hp_median_hz", "f_HP median (Hz)", ""),
            ("f_sl_median_hz", "f_SL median (Hz)", ""), (f"f_amb_{L3}_min_hz", "f_amb -3 dB earliest (Hz)", ""),
            (f"f_alias_worstcase_{L3}_hz", "Worst-case -3 dB onset (Hz)", ""),
            ("f_grating_exact_worst_hz", "Exact grating onset (Hz)", ""),
        ], title + " (horizon ring, 30 degree steering step)")
    write_markdown(p("sensitivity_orientation.md"), ori_rows, [
        ("array_id", "ID", ""), ("label", "Configuration", ""), ("ambiguity_class", "Ambiguity", ""),
        ("f_hz", "f (Hz)", ".0f"), ("hpbw_h_median_deg", "HPBW_h median (deg)", ".0f"),
        ("hpbw_h_undefined_frac", "HPBW_h undefined frac", ".2f"),
        ("max_outside_h_max_db", "Max lobe outside mainlobe, h-cut (dB)", ".1f"),
        ("hpbw_v_median_deg", "HPBW_v median (deg)", ".0f"), ("hpsf_median", "HPSF median", ".2f"),
        ("di_median_db", "DI median (dB)", ".2f"),
    ], "Orientation sensitivity (horizon ring)")
    rows = []
    for r in ula_thr:
        rr = dict(r)
        for k, v in r.items():
            if k.endswith("_hz"):
                rr[k] = _fmt_hz(v)
        rows.append(rr)
    write_markdown(p("sensitivity_ula_thresholds.md"), rows, [
        ("array_id", "ID", ""), ("ring", "Steering", ""), ("n_elements", "N", ""), ("spacing_m", "d (m)", ".3f"),
        ("aperture_m", "Aperture (m)", ".3f"), ("f_hp_hz", "f_HP (Hz)", ""), ("f_sl_hz", "f_SL (Hz)", ""),
        (f"f_amb_{L3}_hz", "f_amb -3 dB (Hz)", ""), (f"f_amb_{L1}_hz", "f_amb -1 dB (Hz)", ""),
    ], "Line-array sensitivity: regime thresholds")


def _write_summary_md(rd, record, study):
    lines = [
        f"# {record['experiment_id']} run {record['run_id']}",
        "",
        f"* Title: {record['title']}",
        f"* Created (UTC): {record['created_utc']}",
        f"* Config: `{record['config_path']}` (sha256 `{record['config_sha256'][:16]}...`)",
        f"* Code: picket_sim {record['software']['picket_sim']}, git `{record['software'].get('git_commit')}`"
        f" (dirty: {record['software'].get('git_dirty')})",
        f"* Python {record['software']['python']}, NumPy {record['software']['numpy']}, "
        f"Matplotlib {record['software']['matplotlib']}",
        "",
        "## Self-checks",
        "",
    ]
    for k, v in record["self_checks"].items():
        lines.append(f"* `{k}`: {v}")
    lines += ["", "## Warnings", ""] + ([f"* {w}" for w in record["warnings"]] or ["* none"])
    lines += ["", "## Assumptions", ""] + [f"* {a}" for a in record["assumptions"]]
    lines += ["", "## Tables", ""]
    for name in ("geometry_summary.md", "comparison.md", "thresholds_summary.md", "pareto.md"):
        lines += [rd.path("tables", name).read_text(encoding="utf-8"), ""]
    lines += ["## Figures", ""] + [f"* `figures/{f}`" for f in record.get("figures", [])]
    rd.path("summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
