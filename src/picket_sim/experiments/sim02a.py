"""SIM-02A: sensor, noise and error modeling (ADR-0009 to ADR-0013).

Run with ``python -m picket_sim run configs/sim02a/sim02a_baseline.yaml``. Every number written by
this module is computed from the configuration (and, for regression checks, from the SIM-01 run of
record). Assumed scenario values are labeled by provenance in ``parameters_by_provenance.csv``.
"""

from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import numpy as np
import yaml

from ..acoustics import PlaneWaveManifold, steering_vectors, validate_sound_speed
from ..analysis import AnalysisSettings, Steering, _lvl, steering_thresholds
from ..config import ConfigError, build_array, config_sha256
from ..conventions import unit_vector
from ..errors import ErrorModel, error_model_from_config
from ..grids import SphereGrid, cut_offsets_deg, log_frequency_grid
from ..metrics import aliasing_onset_hz, circular_profile_metrics, exact_grating_onset_hz
from ..noisefields import NoiseField, near_field_vector
from ..params import CONSTANTS, PROVENANCE, Param, ParamError, parse_param
from ..rag import horizontal_scan_with_errors, rag_db, rag_with_errors_db
from ..records import DirtyTreeError, RunDirectory, git_state, make_run_id, software_versions, utc_now
from ..sensor import PowerLawSpectrum, chain_from_config, db10
from ..stats import case_rng, mean_ci, quantile_ci, wilson_ci
from ..tables import write_csv, write_markdown
from .sim01 import pareto_front

__all__ = ["run", "Sim02AStudy", "load_sim02a_config"]


def _block_provenance(block: dict, context: str) -> Param:
    prov = block.get("provenance")
    src = str(block.get("source", "")).strip()
    if prov not in PROVENANCE or len(src) < 8:
        raise ParamError(f"{context}: block requires provenance in {PROVENANCE} and a source")
    return Param(context, float("nan"), "-", prov, src, context)


def load_sim02a_config(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if cfg.get("experiment", {}).get("id") != "SIM-02A":
        raise ConfigError("not a SIM-02A configuration")
    Sim02AStudy(cfg, log=lambda *a, **k: None, dry=True)  # full validation, raises on any problem
    return cfg


def _eta_label(e):
    return "none" if e is None else f"{e:g}"


def _parabolic_peak(y_db, i):
    """Sub-sample offset of a peak at index i of a circular array (parabola through 3 points)."""
    n = len(y_db)
    a, b, c = y_db[(i - 1) % n], y_db[i], y_db[(i + 1) % n]
    den = a - 2 * b + c
    return 0.0 if den == 0 else float(np.clip(0.5 * (a - c) / den, -0.5, 0.5))


class Sim02AStudy:
    def __init__(self, cfg: dict, log=print, dry: bool = False):
        self.cfg, self.log = cfg, log
        self.c0 = validate_sound_speed(cfg["physics"]["sound_speed_mps"])
        fg = cfg["frequency_grid"]
        self.f_grid = log_frequency_grid(float(fg["f_min_hz"]), float(fg["f_max_hz"]), int(fg["points_per_decade"]))
        self.f_max = float(fg["f_max_hz"])
        self.bands = {k: (float(v[0]), float(v[1])) for k, v in cfg["bands_hz"].items()}
        for b, (lo, hi) in self.bands.items():
            if not (self.f_grid[0] * (1 - 1e-9) <= lo < hi <= self.f_grid[-1] * (1 + 1e-9)):
                raise ConfigError(f"band {b} outside the frequency grid")
        self.levels = tuple(float(x) for x in cfg["ambiguity_levels_db"])
        g = cfg["grids"]
        self.settings = AnalysisSettings(SphereGrid(int(g["sphere"]["n_el"]), int(g["sphere"]["n_az"])),
                                         int(g["cut_points"]), int(g["reduced_1d_points"]), self.levels,
                                         use_sphere_for_rank1=False)
        step = float(cfg["steering"]["horizon_az_step_deg"])
        self.ring = [Steering("horizon", float(((a + 180) % 360) - 180), 0.0) for a in np.arange(0, 360, step)]
        self.ring_u = np.stack([s.u for s in self.ring])
        self.cands = [(spec, build_array(spec)) for spec in cfg["candidates"]]
        ids = [s["id"] for s, _ in self.cands]
        if len(set(ids)) != len(ids):
            raise ConfigError("candidate ids must be unique")
        self.params: list[Param] = list(CONSTANTS)
        self.sensors = []
        for spec in cfg["sensor_scenarios"]:
            chain, ps = chain_from_config(spec)
            self.sensors.append(chain)
            self.params += ps
        self.ambients = []
        for spec in cfg["ambient_scenarios"]:
            ps = {k: parse_param(k, spec[k], spec["id"]) for k in
                  ("level_db_re_1upa2_per_hz", "reference_frequency_hz", "slope_db_per_decade")}
            self.params += list(ps.values())
            self.ambients.append(PowerLawSpectrum(spec["id"], *(ps[k].value for k in (
                "level_db_re_1upa2_per_hz", "reference_frequency_hz", "slope_db_per_decade"))))
        self.signal_classes = []
        for spec in cfg["signal_classes"]:
            kind = spec["kind"]
            if kind == "tonal":
                cf = 20 * math.log10(math.sqrt(2.0))
            elif kind == "harmonic":
                k = int(spec["n_partials"])
                if k < 1:
                    raise ConfigError("n_partials must be >= 1")
                cf = 20 * math.log10(math.sqrt(2.0 * k))
            elif kind == "specified":
                p = parse_param("crest_factor_db", spec["crest_factor_db"], spec["id"])
                self.params.append(p)
                cf = p.value
            else:
                raise ConfigError(f"unknown signal class kind {kind!r}")
            self.signal_classes.append((spec["id"], kind, cf))
        self.fields = [NoiseField.from_config(f) for f in cfg["noise_fields"]]
        self.params.append(_block_provenance(cfg["noise_field_parameters"], "noise_field_parameters"))
        self.eta = [None if e is None else float(e) for e in cfg["eta_db"]]
        host = cfg["host_scenarios"]
        self.params.append(_block_provenance(host, "host_scenarios"))
        self.host = host
        self.errors = []
        for spec in cfg["error_scenarios"]:
            em, ps = error_model_from_config(spec)
            self.errors.append(em)
            self.params += ps
        sw = cfg["error_sweeps"]
        self.params.append(_block_provenance(sw, "error_sweeps"))
        self.sweeps = sw
        self.mc = cfg["monte_carlo"]
        if int(self.mc["trials"]) < 200 or int(self.mc["trials_sweep"]) < 200:
            raise ConfigError("Monte Carlo trials must be >= 200 for the interval estimates")
        for f in list(self.mc["frequencies_hz"]) + list(host["frequencies_hz"]):
            if not self.f_grid[0] * (1 - 1e-9) <= float(f) <= self.f_grid[-1] * (1 + 1e-9):
                raise ConfigError(f"frequency {f} outside the analysis grid")
        self.self_checks: dict = {}
        self.warnings: list[str] = []
        self.timings: dict = {}
        self.figures: list[str] = []
        self._gamma_cache: dict = {}

    @property
    def multichannel(self):
        return [(s, g) for s, g in self.cands if g.n_elements > 1]

    # ================================================================ provenance and geometry
    def provenance_rows(self):
        rows = [p.row() for p in self.params]
        counts = {k: sum(r["provenance"] == k for r in rows) for k in PROVENANCE}
        self.self_checks["parameters_by_provenance"] = counts
        return rows

    def geometry_table(self):
        rows, alias = [], {}
        for spec, g in self.cands:
            a = aliasing_onset_hz(g, self.c0, self.levels, self.f_max)
            fx = exact_grating_onset_hz(g, self.c0, self.f_max)
            alias[g.array_id] = a
            r = {"array_id": g.array_id, "family": spec.get("family"), "footprint": spec.get("footprint"),
                 "label": spec.get("label"), **{k: v for k, v in g.summary().items() if k != "array_id"},
                 "f_grating_exact_worst_hz": fx if g.n_elements > 1 else None}
            for L in self.levels:
                r[f"f_alias_{_lvl(L)}_hz"] = a.get(L)
            r["positions_m"] = ";".join(f"({p[0]:.4f},{p[1]:.4f},{p[2]:.4f})" for p in g.positions_m)
            rows.append(r)
        # regression: A4 envelope must reproduce the SIM-01 A4 coordinates
        reg = self.cfg.get("regression", {})
        if reg.get("sim01_run"):
            import json

            s1 = json.load(open(Path(reg["sim01_run"]) / "record.json"))["config_resolved"]
            a4_old = build_array(next(a for a in s1["arrays"] if a["id"] == "A4"))
            a4_new = next(g for s, g in self.cands if s["id"] == "A4")
            dev = float(np.max(np.abs(a4_old.positions_m - a4_new.positions_m)))
            self.self_checks["a4_regression_max_abs_position_m"] = dev
            if dev > 1e-12:
                raise RuntimeError(f"self-check failed: A4 envelope differs from SIM-01 A4 by {dev} m")
        return rows, alias

    # ================================================================ acquisition chain
    def acquisition(self):
        spec_rows, eta_rows, dr_rows, adc_rows = [], [], [], []
        for ch in self.sensors:
            ok = (self.f_grid >= ch.bandwidth_low_hz) & (self.f_grid <= ch.bandwidth_high_hz)
            th, pre, adc = ch.thermal_upa2_per_hz(self.f_grid), ch.preamp_upa2_per_hz(self.f_grid), ch.adc_upa2_per_hz(
                self.f_grid)
            for i, f in enumerate(self.f_grid):
                r = {"sensor": ch.scenario_id, "f_hz": f, "within_declared_bandwidth": bool(ok[i]),
                     "thermal_db": db10(th[i]), "preamp_db": db10(pre[i]), "adc_db": db10(adc[i]),
                     "self_noise_db": db10(th[i] + pre[i] + adc[i])}
                for amb in self.ambients:
                    r[f"{amb.scenario_id}_db"] = float(db10(amb(f)))
                spec_rows.append(r)
            for b, (lo, hi) in self.bands.items():
                covered = ch.covers(lo, hi)
                fb = self.f_grid[(self.f_grid >= lo) & (self.f_grid <= hi)]
                adc_margin = float(np.median(db10(ch.preamp_upa2_per_hz(fb) + ch.thermal_upa2_per_hz(fb))
                                             - db10(ch.adc_upa2_per_hz(fb))))
                adc_rows.append({"sensor": ch.scenario_id, "band": b, "acquirable": covered,
                                 "analog_minus_adc_noise_db_median": adc_margin,
                                 "clip_level_db_re_1upa_peak": 20 * math.log10(ch.clip_pressure_upa_peak),
                                 "clipping_stage": ch.clipping_stage})
                for amb in self.ambients:
                    eta_b = float(np.median(db10(ch.self_noise_upa2_per_hz(fb)) - db10(amb(fb))))
                    eta_rows.append({"sensor": ch.scenario_id, "ambient": amb.scenario_id, "band": b,
                                     "acquirable": covered, "eta_median_db": eta_b,
                                     "eta_min_db": float(np.min(db10(ch.self_noise_upa2_per_hz(fb)) - db10(amb(fb)))),
                                     "eta_max_db": float(np.max(db10(ch.self_noise_upa2_per_hz(fb)) - db10(amb(fb))))})
                    for sid, kind, cf in self.signal_classes:
                        row = {"sensor": ch.scenario_id, "ambient": amb.scenario_id, "band": b, "signal_class": sid,
                               "crest_factor_db": cf, "acquirable": covered}
                        if covered:
                            row.update(ch.dynamic_range_db(lo, hi, cf, amb))
                            row["status"] = "ok"
                        else:
                            row["status"] = "not acquirable: band outside declared bandwidth or at/above Nyquist"
                        dr_rows.append(row)
        return spec_rows, eta_rows, dr_rows, adc_rows

    # ================================================================ realized array gain
    def gamma(self, g, fld, f):
        key = (g.array_id, fld.field_id, float(f))
        if key not in self._gamma_cache:
            self._gamma_cache[key] = fld.coherence(g, f, self.c0)
        return self._gamma_cache[key]

    def rag_sweep(self):
        rows = []
        white_dev, iso_dev = 0.0, 0.0
        from ..noise import directivity_index_db

        for spec, g in self.cands:
            t0 = time.time()
            n = g.n_elements
            for fld in self.fields:
                for f in self.f_grid:
                    gam = self.gamma(g, fld, f)
                    for e in self.eta:
                        eta = 0.0 if e is None else 10 ** (e / 10)
                        r = rag_db(g.positions_m, f, self.c0, self.ring_u, gam, eta)
                        rows.append({"array_id": g.array_id, "field": fld.field_id, "eta_db": _eta_label(e),
                                     "f_hz": float(f), "rag_median_db": float(np.median(r)),
                                     "rag_min_db": float(np.min(r)), "rag_max_db": float(np.max(r))})
                        if fld.field_id == "WHITE":
                            white_dev = max(white_dev, float(np.max(np.abs(r - 10 * np.log10(n)))))
                        if fld.field_id == "ISO" and e is None:
                            di = np.atleast_1d(directivity_index_db(PlaneWaveManifold(g, self.c0), f, self.ring_u))
                            iso_dev = max(iso_dev, float(np.max(np.abs(r - di))))
            self.log(f"  RAG {g.array_id}: {time.time() - t0:.1f} s")
        self.self_checks["rag_white_vs_10logN_max_abs_db"] = white_dev
        self.self_checks["rag_iso_no_sensor_noise_vs_sim01_DI_max_abs_db"] = iso_dev
        if white_dev > 1e-9 or iso_dev > 1e-9:
            raise RuntimeError("self-check failed: RAG limits (white -> 10 log10 N, isotropic -> DI)")
        return rows

    def rag_band_summary(self, rows):
        out = []
        from collections import defaultdict

        grp = defaultdict(list)
        for r in rows:
            grp[(r["array_id"], r["field"], r["eta_db"])].append(r)
        for (aid, fld, eta), rs in grp.items():
            f = np.array([r["f_hz"] for r in rs])
            v = np.array([r["rag_median_db"] for r in rs])
            row = {"array_id": aid, "field": fld, "eta_db": eta}
            for b, (lo, hi) in self.bands.items():
                m = (f >= lo) & (f <= hi)
                row[f"{b}_median_db"] = float(np.median(v[m]))
                row[f"{b}_min_db"] = float(np.min(v[m]))
            out.append(row)
        return out

    # ================================================================ host noise
    def host_noise(self):
        h = self.host
        fld = next(x for x in self.fields if x.field_id == h["field"])
        eta = 10 ** (float(h["eta_db"]) / 10)
        rows = []
        for spec, g in self.cands:
            ctr = g.centroid_m
            for src in h["sources"]:
                u_h = unit_vector(float(src["az_deg"]), float(src["el_deg"]))
                for f in h["frequencies_hz"]:
                    f = float(f)
                    k = 2 * np.pi * f / self.c0
                    if src["type"] == "near_field":
                        xs = ctr + float(src["range_m"]) * u_h
                        hv = near_field_vector(g.positions_m, k, xs)
                    elif src["type"] == "far_field":
                        hv = steering_vectors(g.positions_m - ctr, u_h, f, self.c0)
                    else:
                        raise ConfigError(f"unknown host source type {src['type']!r}")
                    gam = fld.coherence(g, f, self.c0)
                    base = rag_db(g.positions_m, f, self.c0, self.ring_u, gam, eta)
                    for hnr_db in h["hnr_db"]:
                        hnr = 10 ** (float(hnr_db) / 10)
                        r = rag_db(g.positions_m, f, self.c0, self.ring_u, gam, eta, hnr, hv)
                        i_host = int(np.argmin(np.abs(((np.array([s.az_deg for s in self.ring]) - float(src["az_deg"])
                                                        + 180) % 360) - 180)))
                        rows.append({"array_id": g.array_id, "host": src["id"], "f_hz": f, "hnr_db": float(hnr_db),
                                     "rag_median_db": float(np.median(r)), "rag_min_db": float(np.min(r)),
                                     "rag_at_host_azimuth_db": float(r[i_host]),
                                     "rag_no_host_median_db": float(np.median(base)),
                                     "rag_change_due_to_host_median_db": float(np.median(r - base))})
        return rows

    # ================================================================ channel-error Monte Carlo
    def _mc_case(self, g, f, az, em, trials, key, need_scan=True):
        n = g.n_elements
        draw = em.sample(case_rng(int(self.mc["base_seed"]), *key), trials, n)
        step = float(self.mc["scan_step_deg"])
        gam = cut_offsets_deg(int(round(360 / step)))
        p = horizontal_scan_with_errors(g.positions_m, f, self.c0, az, az + gam, draw)  # (T, A)
        i0 = int(np.flatnonzero(gam == 0.0)[0])
        ideal = horizontal_scan_with_errors(g.positions_m, f, self.c0, az, az + gam,
                                            ErrorModel("ideal", 0, 0, 0, 0).sample(case_rng(0, "ideal"), 1, n))[0]
        cm = circular_profile_metrics(gam, ideal)
        main = mean_ci(p[:, i0])
        expect = em.expected_mainlobe_power(n, f, self.c0)
        out = {"array_id": g.array_id, "f_hz": f, "target_az_deg": az, "scenario": em.scenario_id, "trials": trials,
               "sigma_total_phase_deg": float(np.rad2deg(np.sqrt(em.phase_variance_rad2(f, self.c0)))),
               "mainlobe_power_mean": main["mean"], "mainlobe_power_lo": main["lo"], "mainlobe_power_hi": main["hi"],
               "mainlobe_power_expected": expect, "mainlobe_z": (main["mean"] - expect) / main["se"] if main["se"] > 0
               else 0.0,
               "signal_loss_db": -10 * math.log10(main["mean"])}
        closed = bool(np.isfinite(cm.mainlobe_left_deg) and np.isfinite(cm.mainlobe_right_deg))
        inside = (gam >= -cm.mainlobe_left_deg) & (gam <= cm.mainlobe_right_deg) if closed else np.ones_like(gam, bool)
        # Cut statistics are defined only where the error-free cut discriminates at half power and has a
        # region outside its mainlobe; otherwise "outside lobes" are just the broad pattern (ADR-0005).
        out["closed_mainlobe"] = bool(closed and np.any(~inside) and np.isfinite(cm.hpbw_deg))
        if not need_scan:
            return out
        if not out["closed_mainlobe"]:
            out["status"] = ("no half-power discrimination or no closed mainlobe on the horizontal cut: "
                             "ambiguity and bearing statistics undefined")
            return out
        pin, pout = p[:, inside].max(axis=1), p[:, ~inside].max(axis=1)
        amb_db = 10 * np.log10(pout / pin)
        out["ideal_outside_lobe_db"] = float(10 * math.log10(ideal[~inside].max()))
        q50, q90 = quantile_ci(amb_db, 0.5), quantile_ci(amb_db, 0.9)
        out.update({"amb_level_median_db": q50["est"], "amb_level_median_lo": q50["lo"],
                    "amb_level_median_hi": q50["hi"], "amb_level_p90_db": q90["est"], "amb_level_p90_lo": q90["lo"],
                    "amb_level_p90_hi": q90["hi"]})
        for L in self.levels:
            w = wilson_ci(int(np.sum(amb_db >= L)), trials)
            out[f"p_amb_ge_{_lvl(L)}"] = w["p"]
            out[f"p_amb_ge_{_lvl(L)}_lo"], out[f"p_amb_ge_{_lvl(L)}_hi"] = w["lo"], w["hi"]
        # Exact ties (e.g. the left/right mirror of a line array, for which the scanned response is
        # symmetric in azimuth whatever the channel errors) cannot be resolved by the peak: count them
        # separately instead of letting argmax pick the first index.
        tie = pout >= pin * (1.0 - 1e-9)
        idx_all = np.argmax(p, axis=1)
        gross_mask = (~tie) & (~inside[idx_all])
        p_in = np.where(inside[None, :], p, -np.inf)
        idx_in = np.argmax(p_in, axis=1)  # correct-side (in-mainlobe) peak
        pdb = 10 * np.log10(p)
        err = np.array([gam[i] + step * _parabolic_peak(pdb[t], i) for t, i in enumerate(idx_in)])
        fine = ~gross_mask
        tw, gw = wilson_ci(int(np.sum(tie)), trials), wilson_ci(int(np.sum(gross_mask)), trials)
        out.update({"unresolved_tie_rate": tw["p"], "unresolved_tie_lo": tw["lo"], "unresolved_tie_hi": tw["hi"],
                    "gross_error_rate": gw["p"], "gross_error_lo": gw["lo"], "gross_error_hi": gw["hi"],
                    "fine_trials": int(np.sum(fine))})
        if np.sum(fine) >= 200:
            m2 = mean_ci(err[fine] ** 2)
            out.update({"fine_rms_error_deg": math.sqrt(m2["mean"]), "fine_rms_lo": math.sqrt(max(m2["lo"], 0.0)),
                        "fine_rms_hi": math.sqrt(m2["hi"])})
        else:
            out["fine_rms_error_deg"] = float(np.sqrt(np.mean(err[fine] ** 2))) if np.any(fine) else float("nan")
            out["status"] = "fewer than 200 non-gross trials: no interval on the fine RMS error"
        return out

    def mc_scenarios(self):
        rows = []
        trials = int(self.mc["trials"])
        frac = float(self.mc["rag_thermal_fraction"])
        eta = 10 ** (float(self.mc["rag_eta_db"]) / 10)
        for spec, g in self.multichannel:
            t0 = time.time()
            for f in self.mc["frequencies_hz"]:
                f = float(f)
                for az in self.mc["target_az_deg"]:
                    az = float(az)
                    ideal_rag = float(rag_with_errors_db(g.positions_m, f, self.c0, unit_vector(az, 0.0),
                                                         ErrorModel("ideal", 0, 0, 0, 0).sample(case_rng(0, "i"), 1,
                                                                                                  g.n_elements),
                                                         eta * frac, eta * (1 - frac))[0])
                    for em in self.errors:
                        key = (g.array_id, f, az, em.scenario_id)
                        row = self._mc_case(g, f, az, em, trials, key)
                        draw = em.sample(case_rng(int(self.mc["base_seed"]), *key, "rag"), trials, g.n_elements)
                        rag = rag_with_errors_db(g.positions_m, f, self.c0, unit_vector(az, 0.0), draw,
                                                 eta * frac, eta * (1 - frac))
                        s = mean_ci(rag)
                        row.update({"rag_ideal_db": ideal_rag, "rag_mean_db": s["mean"], "rag_lo_db": s["lo"],
                                    "rag_hi_db": s["hi"], "rag_degradation_db": ideal_rag - s["mean"]})
                        rows.append(row)
            self.log(f"  MC scenarios {g.array_id}: {time.time() - t0:.1f} s")
        return rows

    def mc_sweeps(self):
        rows = []
        trials = int(self.mc["trials_sweep"])
        az = float(self.mc["sweep_target_az_deg"])
        kinds = {"sigma_phase_deg": lambda v: ErrorModel(f"phase {v:g} deg", 0, v, 0, 0),
                 "sigma_gain_db": lambda v: ErrorModel(f"gain {v:g} dB", v, 0, 0, 0),
                 "sigma_position_m": lambda v: ErrorModel(f"position {v:g} m", 0, 0, v, 0),
                 "sigma_timing_s": lambda v: ErrorModel(f"timing {v:g} s", 0, 0, 0, v)}
        for spec, g in self.multichannel:
            for kname, make in kinds.items():
                for v in self.sweeps[kname]:
                    em = make(float(v))
                    for f in self.mc["frequencies_hz"]:
                        f = float(f)
                        row = self._mc_case(g, f, az, em, trials, (g.array_id, f, az, "sweep", kname, float(v)))
                        row.update({"error_type": kname, "error_level": float(v)})
                        rows.append(row)
        return rows

    # ================================================================ thresholds at -3/-6/-10
    def thresholds(self):
        rows = []
        for spec, g in self.multichannel:
            t0 = time.time()
            man = PlaneWaveManifold(g, self.c0)
            for st in self.ring:
                t = steering_thresholds(man, st, self.f_grid, self.settings)
                rows.append(t)
            self.log(f"  thresholds {g.array_id}: {time.time() - t0:.1f} s")
        return rows

    def threshold_summary(self, thr_rows, alias):
        out = []
        keys = ["f_hp_hz", "f_sl_hz"] + [f"f_amb_{_lvl(L)}_hz" for L in self.levels]
        for spec, g in self.multichannel:
            rs = [r for r in thr_rows if r["array_id"] == g.array_id]
            row = {"array_id": g.array_id}
            for key in keys:
                st = [r[key.replace("_hz", "_status")] for r in rs]
                v = np.array([np.inf if s == "not_reached" else r[key] for r, s in zip(rs, st)], dtype=float)
                base = key[:-3]
                row[f"{base}_min_hz"], row[f"{base}_median_hz"], row[f"{base}_max_hz"] = (
                    float(np.min(v)), float(np.median(v)), float(np.max(v)))
                row[f"{base}_below_grid"] = int(sum(s == "below_grid" for s in st))
            for L in self.levels:
                lv = _lvl(L)
                g_lo, g_hi = row["f_sl_max_hz"], row[f"f_amb_{lv}_min_hz"]
                m_lo, m_hi = row["f_sl_median_hz"], row[f"f_amb_{lv}_median_hz"]
                row[f"guaranteed_{lv}_lo_hz"], row[f"guaranteed_{lv}_hi_hz"] = (g_lo, g_hi) if g_lo < g_hi else (
                    float("nan"), float("nan"))
                row[f"guaranteed_{lv}_ratio"] = (g_hi / g_lo) if (g_lo < g_hi and np.isfinite(g_hi)) else (
                    float("inf") if g_lo < g_hi else float("nan"))
                row[f"median_{lv}_ratio"] = (m_hi / m_lo) if (m_lo < m_hi and np.isfinite(m_hi)) else (
                    float("inf") if m_lo < m_hi else float("nan"))
                a = alias[g.array_id].get(L)
                row[f"f_alias_worstcase_{lv}_hz"] = float("inf") if a is None else a
            out.append(row)
        return out

    def regression_vs_sim01(self, thr_sum):
        reg = self.cfg.get("regression", {})
        if not reg.get("sim01_run"):
            return []
        path = Path(reg["sim01_run"]) / "tables" / "thresholds_summary.csv"
        old = {r["array_id"]: r for r in csv.DictReader(open(path)) if r["ring"] == "horizon"}
        tol = float(reg["threshold_rel_tol"])
        rows, worst = [], 0.0
        for r in thr_sum:
            if r["array_id"] not in old:
                continue
            o = old[r["array_id"]]
            for k in ("f_hp_min_hz", "f_hp_median_hz", "f_hp_max_hz", "f_sl_min_hz", "f_sl_median_hz", "f_sl_max_hz",
                      "f_amb_m3db_min_hz", "f_amb_m3db_median_hz"):
                a, b = float(r[k]), float(o[k]) if o[k] not in ("", "inf") else float("inf")
                if b > self.f_grid[-1] or a > self.f_grid[-1] or not np.isfinite(b) or b < 100.0:
                    continue  # outside the overlap of the two analysis grids
                rel = abs(a / b - 1)
                worst = max(worst, rel)
                rows.append({"array_id": r["array_id"], "quantity": k, "sim01_hz": b, "sim02a_hz": a, "rel_diff": rel})
        self.self_checks["sim01_threshold_regression_max_rel_diff"] = worst
        self.self_checks["sim01_threshold_regression_n"] = len(rows)
        if worst > tol:
            raise RuntimeError(f"self-check failed: -3 dB thresholds differ from SIM-01 by {worst:.3%} > {tol:.1%}")
        return rows

    # ================================================================ Pareto tolerance sensitivity (D06)
    def pareto_sensitivity(self, rag_summary, thr_sum, geo_rows, mc_rows):
        pc = self.cfg["pareto"]
        scales = [float(s) for s in pc["tolerance_scales"]]

        def scaled(attrs, s):
            out = []
            for a in attrs:
                b = dict(a)
                for key in ("tol", "rel_tol"):
                    if key in b:
                        b[key] = float(b[key]) * s
                out.append(b)
            return out

        def run_sets(name, rows, attrs):
            res = []
            for s in scales:
                dom = [d for d in pareto_front(rows, scaled(attrs, s), practical=s > 0) if d["pareto_dominated"]]
                res.append({"set": name, "tolerance_scale": s,
                            "dominated": ";".join(f"{d['array_id']} (by {d['dominated_by']})" for d in dom) or "none"})
            return res

        out = []
        s1cfg = yaml.safe_load(open(pc["sim01_config"]))
        s1rows = []
        for r in csv.DictReader(open(pc["sim01_comparison"])):
            rr = {"array_id": r["array_id"]}
            for k, v in r.items():
                if k == "array_id":
                    continue
                try:
                    rr[k] = float(v) if v not in ("",) else float("nan")
                except ValueError:
                    rr[k] = v
            s1rows.append(rr)
        for ps in s1cfg["pareto"]["sets"]:
            out += run_sets(f"SIM-01 {ps['name']}", [r for r in s1rows if r["array_id"] in ps["arrays"]], ps["attributes"])
        # SIM-02A attribute rows
        geo = {r["array_id"]: r for r in geo_rows}
        thr = {r["array_id"]: r for r in thr_sum}
        rag = {(r["array_id"], r["field"], r["eta_db"]): r for r in rag_summary}
        rows = []
        for spec, g in self.multichannel:
            aid = g.array_id
            r = {"array_id": aid, "n_elements": g.n_elements, "aperture_m": g.aperture_m,
                 "rank": g.observability.rank, "f_hp_median_hz": thr[aid]["f_hp_median_hz"]}
            for b in ("B1", "B2", "B3"):
                r[f"rag_iso_eta0_{b}_db"] = rag[(aid, "ISO", "0")][f"{b}_median_db"]
            a3 = geo[aid].get("f_alias_m3db_hz")
            r["f_alias_m3db_hz"] = float("inf") if a3 is None else float(a3)
            ms = [m for m in mc_rows if m["array_id"] == aid and m["scenario"].startswith("E2") and m["f_hz"] == 5000.0]
            p6 = [m.get("p_amb_ge_m6db", float("nan")) for m in ms]
            r["e2_p_amb6_5k"] = float(np.max(p6)) if p6 and np.all(np.isfinite(p6)) else float("nan")
            rows.append(r)
        out += run_sets("SIM-02A multichannel", rows, pc["sim02a_attributes"])
        return out, rows

    # ================================================================ markdown
    def markdown(self, rd, geo_rows, eta_rows, dr_rows, adc_rows, rag_sum, host_rows, mc_rows, thr_sum, reg_rows,
                 par_rows, par_attr_rows, prov_rows):
        p = lambda n: rd.path("tables", n)  # noqa: E731

        def fhz(v):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return "n/a"
            return "> 20,000" if math.isinf(v) else f"{v:,.0f}"

        write_markdown(p("parameters_by_provenance.md"), prov_rows, [
            ("provenance", "Provenance", ""), ("context", "Context", ""), ("parameter", "Parameter", ""),
            ("value", "Value", ".4g"), ("unit", "Unit", ""), ("source", "Source / rationale", "")],
            "Parameters by provenance (ADR-0010)", ["No measured values exist in SIM-02A.",
                                                    "Block entries (value n/a) carry provenance for a whole block."])
        rows = []
        for r in geo_rows:
            rr = dict(r)
            for k in ("f_grating_exact_worst_hz",) + tuple(f"f_alias_{_lvl(L)}_hz" for L in self.levels):
                v = r.get(k)
                rr[k] = "n/a" if r["n_elements"] == 1 else ("> 20,000" if v is None else f"{v:,.0f}")
            rows.append(rr)
        write_markdown(p("candidates.md"), rows, [
            ("array_id", "ID", ""), ("family", "Family", ""), ("footprint", "Footprint", ""), ("label", "Configuration", ""),
            ("n_elements", "N", ""), ("aperture_m", "Max dim (m)", ".3f"), ("min_spacing_m", "Min spacing (m)", ".3f"),
            ("extent_z_m", "Vertical extent (m)", ".2f"), ("ambiguity_class", "Geometric ambiguity", ""),
            ("f_grating_exact_worst_hz", "Exact grating onset (Hz)", ""),
            *[(f"f_alias_{_lvl(L)}_hz", f"Worst-case {L:g} dB onset (Hz)", "") for L in self.levels]],
            "SIM-02A candidates", ["Footprint C = 0.45 m, E = 0.90 m, I = A4 envelope, D = 4 m class (assumed).",
                                   "'> 20,000': not reached below 20 kHz."])
        write_markdown(p("acquisition_eta_by_band.md"), eta_rows, [
            ("sensor", "Sensor scenario", ""), ("ambient", "Ambient scenario", ""), ("band", "Band", ""),
            ("acquirable", "Acquirable", ""), ("eta_median_db", "eta median (dB)", "+.1f"),
            ("eta_min_db", "eta min", "+.1f"), ("eta_max_db", "eta max", "+.1f")],
            "Self-noise to ambient ratio eta by band (assumed scenarios)",
            ["eta > 0 dB: sensor-limited (realized gain tends to 10 log10 N); eta < 0 dB: ambient-limited "
             "(realized gain tends to the field's directivity).", "All levels are assumed scenarios (ADR-0010)."])
        write_markdown(p("acquisition_dynamic_range.md"), [r for r in dr_rows if r["ambient"].endswith("moderate")], [
            ("sensor", "Sensor", ""), ("band", "Band", ""), ("signal_class", "Signal class", ""),
            ("crest_factor_db", "Crest factor (dB)", ".1f"), ("max_rms_signal_db_re_1upa", "Max rms signal (dB re 1 uPa)", ".1f"),
            ("self_noise_band_db", "Self-noise in band (dB)", ".1f"), ("ambient_band_db", "Ambient in band (dB)", ".1f"),
            ("dr_over_total_noise_db", "Dynamic range over total noise (dB)", ".1f"), ("status", "Status", "")],
            "Dynamic range by band and signal class (ambient: AMB-ASSUMED-moderate)",
            ["Max rms signal = clip level minus crest factor. Noise integrated over the band.",
             "Other ambient scenarios: acquisition_dynamic_range.csv."])
        write_markdown(p("acquisition_adc.md"), adc_rows, [
            ("sensor", "Sensor", ""), ("band", "Band", ""), ("acquirable", "Acquirable", ""),
            ("analog_minus_adc_noise_db_median", "Analog minus ADC noise (dB)", "+.1f"),
            ("clip_level_db_re_1upa_peak", "Clip level (dB re 1 uPa peak)", ".1f"), ("clipping_stage", "Clips first", "")],
            "Converter noise versus analog noise", ["Positive: analog (sensor + preamplifier) noise dominates the ADC."])
        band_cols = []
        for b in self.bands:
            band_cols.append((f"{b}_median_db", f"{b} median (dB)", "+.2f"))
        for fid in [f.field_id for f in self.fields]:
            write_markdown(p(f"rag_{fid}.md"), [r for r in rag_sum if r["field"] == fid], [
                ("array_id", "ID", ""), ("eta_db", "eta (dB)", ""), *band_cols],
                f"Realized array gain relative to A0, field {fid} (median over horizon steering, then over band)",
                ["eta 'none': no sensor noise. B4 is exploratory."])
        write_markdown(p("host_noise.md"), [r for r in host_rows if r["hnr_db"] == 10.0], [
            ("array_id", "ID", ""), ("host", "Host source", ""), ("f_hz", "f (Hz)", ".0f"),
            ("rag_no_host_median_db", "RAG without host (dB)", "+.1f"), ("rag_median_db", "RAG with host, median (dB)", "+.1f"),
            ("rag_min_db", "RAG with host, worst (dB)", "+.1f"), ("rag_at_host_azimuth_db", "RAG toward host azimuth (dB)", "+.1f")],
            "Host-noise scenarios at host-to-ambient ratio +10 dB (ISO ambient, eta -10 dB)",
            ["All host placements and levels are assumed and generic (no vessel geometry).",
             "RAG relative to A0, which receives the full host noise."])
        sel = [r for r in mc_rows if r["target_az_deg"] == 30.0]
        write_markdown(p("mc_scenarios.md"), sel, [
            ("array_id", "ID", ""), ("f_hz", "f (Hz)", ".0f"), ("scenario", "Scenario", ""),
            ("sigma_total_phase_deg", "Total phase sigma (deg)", ".1f"), ("signal_loss_db", "Signal loss (dB)", ".2f"),
            ("rag_degradation_db", "RAG loss, ISO eta 0 dB (dB)", ".2f"), ("ideal_outside_lobe_db", "Ideal outside lobe (dB)", ".1f"),
            ("amb_level_p90_db", "Outside lobe, 90th pct (dB)", ".1f"), ("p_amb_ge_m6db", "P(>= -6 dB)", ".2f"),
            ("p_amb_ge_m10db", "P(>= -10 dB)", ".2f"), ("unresolved_tie_rate", "Unresolved tie rate", ".2f"),
            ("gross_error_rate", "Gross bearing error rate", ".2f"),
            ("fine_rms_error_deg", "Fine RMS error (deg)", ".2f"), ("status", "Note", "")],
            "Channel-error Monte Carlo, target azimuth 30 deg (all target azimuths in mc_scenarios.csv)",
            ["Noise-free calibration effects only; additive-noise estimation errors are SIM-02B.",
             "Unresolved tie: the largest lobe outside the mainlobe equals the mainlobe peak exactly (line arrays: "
             "the left/right mirror, for every error draw). Fine error is measured at the correct-side peak.",
             "Undefined (n/a) where the error-free cut has no half-power discrimination. Intervals in the CSV."])
        rows = []
        for r in thr_sum:
            rr = {"array_id": r["array_id"]}
            for L in self.levels:
                lv = _lvl(L)
                lo, hi = r[f"guaranteed_{lv}_lo_hz"], r[f"guaranteed_{lv}_hi_hz"]
                rr[f"g_{lv}"] = "empty" if not np.isfinite(lo) else f"{fhz(lo)} to {fhz(hi)}"
                rr[f"gr_{lv}"] = r[f"guaranteed_{lv}_ratio"]
                rr[f"mr_{lv}"] = r[f"median_{lv}_ratio"]
            rr["f_hp"] = fhz(r["f_hp_median_hz"])
            rr["f_sl"] = fhz(r["f_sl_median_hz"])
            rows.append(rr)
        cols = [("array_id", "ID", ""), ("f_hp", "f_HP median (Hz)", ""), ("f_sl", "f_SL median (Hz)", "")]
        for L in self.levels:
            lv = _lvl(L)
            cols += [(f"g_{lv}", f"Guaranteed band {L:g} dB (Hz)", ""), (f"gr_{lv}", "ratio", ".2f"),
                     (f"mr_{lv}", "median-band ratio", ".2f")]
        write_markdown(p("thresholds_bands.md"), rows, cols,
                       "Conventional bands under -3, -6 and -10 dB ambiguity criteria (horizon steering)",
                       [f"Guaranteed: latest f_SL to earliest f_amb over the {len(self.ring)} horizon steering directions.",
                        "Median: median f_SL to median f_amb. inf: no ambiguity lobe at that level below 20 kHz.",
                        "Narrowband DAS criteria only (ADR-0008)."])
        write_markdown(p("regression_sim01.md"), reg_rows, [
            ("array_id", "ID", ""), ("quantity", "Quantity", ""), ("sim01_hz", "SIM-01 (Hz)", ",.1f"),
            ("sim02a_hz", "SIM-02A (Hz)", ",.1f"), ("rel_diff", "Relative difference", ".2e")],
            "Regression of -3 dB thresholds against the SIM-01 run of record")
        write_markdown(p("pareto_tolerance_sensitivity.md"), par_rows, [
            ("set", "Attribute set", ""), ("tolerance_scale", "Tolerance scale", ".1f"), ("dominated", "Dominated", "")],
            "Pareto tolerance sensitivity (D06): dominance at scaled engineering tolerances",
            ["Scale 0 = numerical ties only; 1 = configured provisional tolerances.",
             "Conditional on evaluated attributes only; no candidate is eliminated (D06)."])

    # ================================================================ figure data handled in plotting_sim02a


def run(config_path, output_root=None, allow_dirty: bool = False, make_figures: bool = True, repo_dir=None,
        log=print, argv=None) -> Path:
    t_start = time.time()
    config_path = Path(config_path)
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    study = Sim02AStudy(cfg, log)
    cfg_sha = config_sha256(cfg)
    repo_dir = Path(repo_dir) if repo_dir else config_path.resolve().parent
    gs = git_state(repo_dir)
    if gs["git_dirty"] and not allow_dirty:
        raise DirtyTreeError("working tree has uncommitted changes to tracked files; commit them or pass --allow-dirty")
    created = utc_now()
    run_id = make_run_id(created, cfg_sha, gs["git_commit"])
    root = Path(output_root) if output_root else Path(cfg["output"]["root"])
    rd = RunDirectory(root, run_id)
    log(f"SIM-02A run {run_id} -> {root / run_id}")
    T = study.timings
    try:
        tab = lambda n: rd.path("tables", n)  # noqa: E731
        prov = study.provenance_rows()
        write_csv(tab("parameters_by_provenance.csv"), prov)
        t = time.time()
        geo_rows, alias = study.geometry_table()
        write_csv(tab("candidates.csv"), geo_rows)
        T["geometry_s"] = time.time() - t

        t = time.time()
        log("acquisition chain")
        spec_rows, eta_rows, dr_rows, adc_rows = study.acquisition()
        write_csv(tab("acquisition_self_noise.csv"), spec_rows)
        write_csv(tab("acquisition_eta_by_band.csv"), eta_rows)
        write_csv(tab("acquisition_dynamic_range.csv"), dr_rows)
        write_csv(tab("acquisition_adc.csv"), adc_rows)
        T["acquisition_s"] = time.time() - t

        t = time.time()
        log("realized array gain")
        rag_rows = study.rag_sweep()
        write_csv(tab("rag_by_frequency.csv.gz"), rag_rows, gz=True)
        rag_sum = study.rag_band_summary(rag_rows)
        write_csv(tab("rag_band_summary.csv"), rag_sum)
        T["rag_s"] = time.time() - t

        t = time.time()
        log("host noise")
        host_rows = study.host_noise()
        write_csv(tab("host_noise.csv"), host_rows)
        T["host_s"] = time.time() - t

        t = time.time()
        log("Monte Carlo: scenarios")
        mc_rows = study.mc_scenarios()
        write_csv(tab("mc_scenarios.csv"), mc_rows)
        log("Monte Carlo: one-at-a-time sweeps")
        sw_rows = study.mc_sweeps()
        write_csv(tab("mc_sweeps.csv"), sw_rows)
        z = np.array([r["mainlobe_z"] for r in mc_rows + sw_rows])
        study.self_checks["mc_mainlobe_vs_closed_form_cases"] = int(z.size)
        study.self_checks["mc_mainlobe_vs_closed_form_max_abs_z"] = float(np.max(np.abs(z)))
        study.self_checks["mc_mainlobe_vs_closed_form_frac_abs_z_gt_3"] = float(np.mean(np.abs(z) > 3))
        if np.max(np.abs(z)) > 5.0:
            raise RuntimeError("self-check failed: Monte Carlo mainlobe power deviates from the closed form by > 5 SE")
        target = float(study.mc["ci_relative_target"])
        wide = sum(1 for r in mc_rows if (r["mainlobe_power_hi"] - r["mainlobe_power_lo"]) / 2
                   > target * r["mainlobe_power_mean"])
        study.self_checks["mc_rows_ci_wider_than_target"] = wide
        if wide:
            study.warnings.append(f"{wide} Monte Carlo rows have a mainlobe-power CI half-width above "
                                  f"{target:.0%} of the mean")
        T["monte_carlo_s"] = time.time() - t

        t = time.time()
        log("thresholds at -3/-6/-10 dB")
        thr = study.thresholds()
        write_csv(tab("thresholds_by_steering.csv"), thr)
        thr_sum = study.threshold_summary(thr, alias)
        write_csv(tab("thresholds_summary.csv"), thr_sum)
        reg_rows = study.regression_vs_sim01(thr_sum)
        write_csv(tab("regression_sim01.csv"), reg_rows)
        T["thresholds_s"] = time.time() - t

        par_rows, par_attr = study.pareto_sensitivity(rag_sum, thr_sum, geo_rows, mc_rows)
        write_csv(tab("pareto_tolerance_sensitivity.csv"), par_rows)
        write_csv(tab("pareto_sim02a_attributes.csv"), par_attr)

        study.markdown(rd, geo_rows, eta_rows, dr_rows, adc_rows, rag_sum, host_rows, mc_rows, thr_sum, reg_rows,
                       par_rows, par_attr, prov)
        if make_figures:
            t = time.time()
            log("figures")
            from .. import plotting_sim02a

            study.figures = plotting_sim02a.make_figures(study, rd.path("figures"), geo_rows, spec_rows, dr_rows,
                                                         rag_rows, host_rows, mc_rows, sw_rows, thr_sum, par_rows)
            T["figures_s"] = time.time() - t
        T["total_s"] = time.time() - t_start
        sw = software_versions()
        sw.update(gs)
        record = {"run_id": run_id, "experiment_id": "SIM-02A", "title": cfg["experiment"]["title"],
                  "status": "complete", "created_utc": created.isoformat(), "completed_utc": utc_now().isoformat(),
                  "command": list(argv) if argv else sys.argv, "config_path": str(config_path),
                  "config_sha256": cfg_sha, "config_resolved": cfg, "software": sw,
                  "assumptions": cfg["experiment"].get("assumptions", []), "self_checks": study.self_checks,
                  "warnings": study.warnings, "timings_s": T, "figures": study.figures}
        lines = [f"# SIM-02A run {run_id}", "", f"* Config sha256 `{cfg_sha[:16]}...`; code `{gs.get('git_commit')}` "
                 f"(dirty: {gs.get('git_dirty')})", "", "## Self-checks", ""]
        lines += [f"* `{k}`: {v}" for k, v in study.self_checks.items()]
        lines += ["", "## Warnings", ""] + ([f"* {w}" for w in study.warnings] or ["* none"])
        lines += ["", "## Tables", ""] + [f"* `tables/{q.name}`" for q in sorted(rd.path("tables").iterdir())]
        lines += ["", "## Figures", ""] + [f"* `figures/{f}`" for f in study.figures]
        rd.path("summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        final = rd.finalize(record)
        log(f"done in {T['total_s']:.0f} s: {final}")
        return final
    except BaseException:
        rd.abort()
        raise
