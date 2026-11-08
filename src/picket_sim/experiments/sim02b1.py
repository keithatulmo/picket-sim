"""SIM-02B.1: signal and detection-model foundation (docs/SIM-02B_plan.md, ADR-0014 to ADR-0017).

Work unit ("case"): one candidate x band x window x noise scenario (truth), with the noise model assumed by
the detectors (equal to the truth in the primary experiment, different in mismatch cases). A case draws

* calibration null trials under the assumed model (thresholds),
* evaluation null trials under the true model (realized Pfa),
* positive trials per signal class under the true model (Pd on an SNR grid, common random numbers),

and returns table rows. Cases are independent and seeded from stable keys (``stats.case_rng``), so results
do not depend on scheduling or on which other cases run.
"""

from __future__ import annotations

import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from .. import detection as dt
from ..acoustics import validate_sound_speed
from ..config import ConfigError, build_array, config_sha256
from ..conventions import unit_vector
from ..detectors import Detectors, beam_sigma, beam_weights, harmonic_index, known_beams, normalize
from ..environment import self_noise_from_config, spectrum_from_config
from ..params import CONSTANTS, PROVENANCE, parse_param
from ..records import DirtyTreeError, RunDirectory, git_state, make_run_id, software_versions, utc_now
from ..signals import Grid, broadband_bins, chirp_bins, chirp_reference, delays_s, harmonic_bins, tone_bins
from ..stats import case_rng
from ..synthesis import CoherenceSpec, NoiseScenario, covariance_factor, draw_noise, to_waveform, welch_csd
from ..tables import write_csv

CLASS_DETECTOR = {"tone": "tonal", "harmonic": "harmonic", "broadband": "energy", "chirp": "mf"}
MEM_BUDGET_BYTES = 160e6


@dataclass(frozen=True)
class Case:
    cand: str
    band: str
    T: float
    truth: str
    assumed: str
    kind: str  # "primary" or "mismatch"
    experiment: str
    classes: tuple = ()


@dataclass
class Sim02B1Study:
    cfg: dict
    log: object = print
    self_checks: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    timings: dict = field(default_factory=dict)

    def __post_init__(self):
        cfg = self.cfg
        self.c0 = validate_sound_speed(cfg["physics"]["sound_speed_mps"])
        self.seed = int(cfg["seed"])
        self.params = list(CONSTANTS)
        # candidates
        self.cand_specs = {s["id"]: s for s in cfg["candidates"]}
        if len(self.cand_specs) != len(cfg["candidates"]):
            raise ConfigError("candidate ids must be unique")
        self.geoms = {k: build_array(s) for k, s in self.cand_specs.items()}
        if "A0" not in self.geoms or self.geoms["A0"].n_elements != 1:
            raise ConfigError("the single-hydrophone reference A0 is required")
        # bands and windows
        self.bands = {b["id"]: b for b in cfg["bands"]}
        for b in self.bands.values():
            if not (0 < b["f_lo_hz"] < b["f_hi_hz"] < b["fs_hz"] / 2):
                raise ConfigError(f"band {b['id']}: need 0 < f_lo < f_hi < fs/2")
        self.trials = {float(k): v for k, v in cfg["trials"].items()}
        for w, v in self.trials.items():
            for key in ("cal", "eval", "pos"):
                if int(v[key]) < 1:
                    raise ConfigError(f"trials[{w}].{key} must be positive")
        # spectra, self-noise, scenarios
        self.spectra = {}
        for sid, spec in cfg["spectra"].items():
            self.spectra[sid] = spectrum_from_config(sid, spec, self.spectra, self.params)
        self.self_noise = {}
        self.chains = {}
        for sid, spec in cfg["self_noise"].items():
            fn, chain = self_noise_from_config(sid, spec, self.spectra, self.params)
            self.self_noise[sid] = fn
            if chain is not None:
                self.chains[sid] = chain
        self.scenarios = {}
        for sc in cfg["noise_scenarios"]:
            comps = []
            for c in sc["components"]:
                coh = c["coherence"]
                L = None
                if coh["kind"] == "exponential":
                    L = parse_param("correlation_length_m", coh["correlation_length_m"], f"{sc['id']}.coherence",
                                    require_d01=True)
                    self.params.append(L)
                    L = L.value
                if c["spectrum"] not in self.spectra:
                    raise ConfigError(f"{sc['id']}: unknown spectrum {c['spectrum']!r}")
                comps.append((self.spectra[c["spectrum"]], CoherenceSpec(coh["kind"], L)))
            sn = sc.get("self_noise", "none")
            if sn != "none" and sn not in self.self_noise:
                raise ConfigError(f"{sc['id']}: unknown self-noise {sn!r}")
            self.scenarios[sc["id"]] = NoiseScenario(sc["id"], comps, self.self_noise.get(sn) if sn != "none" else None)
        self.scenario_cfg = {sc["id"]: sc for sc in cfg["noise_scenarios"]}
        # signal classes and processing
        self.classes = cfg["signal_classes"]
        for name in self.classes:
            if name not in CLASS_DETECTOR:
                raise ConfigError(f"unknown signal class {name!r}")
        self.proc = cfg["processing"]
        step = float(self.proc["beam_search_az_step_deg"])
        self.search_az = np.arange(0.0, 360.0, step)
        self.search_u = np.stack([unit_vector(a, 0.0) for a in self.search_az])
        self.pfa = [float(p) for p in cfg["pfa"]]
        self.pd_targets = [float(p) for p in cfg["pd_targets"]]
        self.offsets = np.asarray(cfg["snr_grid_offsets_db"], dtype=float)
        self.chirp_margin = float(cfg["signal_classes"].get("chirp", {}).get("arrival_margin_s", 0.005))
        self._srcs = {}

    # ------------------------------------------------------------------------------------------ cases
    def trials_for(self, band: str, T: float) -> dict:
        """Trial counts for a window, with optional per-band overrides (``per_band: {B3: {cal: ...}}``)."""
        base = self.trials[float(T)]
        over = base.get("per_band", {}).get(band, {})
        return {k: int(over.get(k, base[k])) for k in ("cal", "eval", "pos")}

    def grid(self, band: str, T: float) -> Grid:
        b = self.bands[band]
        return Grid(float(T), float(b["fs_hz"]), float(b["f_lo_hz"]), float(b["f_hi_hz"]))

    def classes_for(self, band: str, T: float, allowed=None) -> tuple:
        out = []
        for name, spec in self.classes.items():
            if allowed is not None and name not in allowed:
                continue
            bands = spec.get("bands")
            wins = spec.get("windows_s")
            if bands is not None and band not in bands:
                continue
            if wins is not None and float(T) not in [float(w) for w in wins]:
                continue
            out.append(name)
        return tuple(out)

    def cases(self) -> list[Case]:
        out = []
        for ex in self.cfg["experiments"]:
            cands = list(self.cand_specs) if ex["candidates"] == "all" else ex["candidates"]
            for sc in ex["scenarios"]:
                for band in ex["bands"]:
                    for T in ex["windows_s"]:
                        cls = self.classes_for(band, T, ex.get("classes"))
                        for c in cands:
                            out.append(Case(c, band, float(T), sc, sc, "primary", ex["id"], cls))
        for mm in self.cfg.get("mismatch", []):
            for band in mm["bands"]:
                for T in mm["windows_s"]:
                    for c in mm["candidates"]:
                        out.append(Case(c, band, float(T), mm["truth"], mm["assumed"], "mismatch", mm["id"], ()))
        keys = [(c.cand, c.band, c.T, c.truth, c.assumed, c.experiment) for c in out]
        if len(set(keys)) != len(keys):
            raise ConfigError("duplicate cases in experiments")
        return out

    def modes(self, cand: str) -> list[str]:
        return ["single"] if self.geoms[cand].n_elements == 1 else ["beam_known", "beam_search", "incoherent"]

    # ------------------------------------------------------------------------------------------ thresholds
    def exact_threshold(self, mode, det, p, K):
        if mode not in ("single", "beam_known"):
            return None
        if det == "tonal":
            return dt.maxexp_isf(p, K)
        if det == "energy":
            return dt.erlang_isf(p, K)
        return None

    def bound_threshold(self, mode, det, p, grid, n_streams, n_fund, n_lags, inc=None):
        """Union-bound threshold (exact product over independent bins, Bonferroni elsewhere).

        Incoherent mode (``inc`` = dict with per-bin largest eigenvalue ``lam`` of the normalized coherence, its
        maximum ``lam_star``, the matched-filter channel-correlation eigenvalue ``lam_mf`` and ``n`` elements):
        q <= (lambda_max / n) Gamma(n, 1) per bin or lag, which is conservative.
        """
        if mode == "incoherent":
            if inc is None:
                return None
            n = inc["n"]
            if det == "tonal":
                return dt.incoherent_tonal_bound(p, inc["lam"], n)
            if det == "energy":
                return inc["lam_star"] / n * dt.erlang_isf(p, n * grid.K)
            if det == "harmonic":
                H = int(self.classes["harmonic"]["n_harmonics"])
                return inc["lam_star"] / n * dt.erlang_isf(p / n_fund, n * H)
            if det == "mf":
                return inc["lam_mf"] / n * dt.erlang_isf(p / n_lags, n)
            return None
        S = n_streams if mode == "beam_search" else 1
        K = grid.K
        if det == "tonal":
            q = -math.expm1(math.log1p(-p) / K)  # per-bin exceedance (bins independent)
            return -math.log(q / S)
        if det == "energy":
            return dt.erlang_isf(p / S, K)
        if det == "harmonic":
            return dt.erlang_isf(p / (S * n_fund), int(self.classes["harmonic"]["n_harmonics"]))
        if det == "mf":
            return math.log(S * n_lags / p)
        return None

    # ------------------------------------------------------------------------------------------ SNR placement
    def snr_center_db(self, cls: str, grid: Grid, g_true: np.ndarray) -> float:
        """Analytic A0 operating point at Pfa = 1e-3, used only to place the SNR grid (ADR-0015)."""
        p = 1e-3
        if cls == "tone":
            return 10 * math.log10(dt.maxexp_isf(p, grid.K) / grid.T) + 1.0
        if cls == "harmonic":
            H = int(self.classes["harmonic"]["n_harmonics"])
            F = harmonic_index(grid, H).shape[0]
            eta = dt.erlang_isf(p / F, H)
            return 10 * math.log10(max(eta - H, 1.0) / (H * grid.T)) + 1.0
        if cls == "broadband":
            eta = dt.erlang_isf(p, grid.K)
            mean_g = float(np.mean(g_true))
            d_per_snr = mean_g * float(np.sum(1.0 / g_true))
            return 10 * math.log10(max(eta - grid.K, 1.0) / d_per_snr)
        if cls == "chirp":
            L = int(self.proc["mf_oversample"]) * grid.K
            return 10 * math.log10(math.log(L / p))
        raise ValueError(cls)

    # ------------------------------------------------------------------------------------------ sources
    def source_params(self, cls: str, band: str, T: float, n: int, grid: Grid) -> dict:
        key = (cls, band, float(T), n)
        if key in self._srcs:
            return self._srcs[key]
        rng = case_rng(self.seed, "src", cls, band, float(T))
        az = rng.uniform(0.0, 360.0, n)
        out = {"az": az, "u": np.stack([unit_vector(a, 0.0) for a in az])}
        df = grid.df
        if cls == "tone":
            out["f0"] = rng.uniform(grid.f_lo + 2 * df, grid.f_hi - 2 * df, n)
            out["phase"] = rng.uniform(0, 2 * np.pi, n)
        elif cls == "harmonic":
            H = int(self.classes["harmonic"]["n_harmonics"])
            lo, hi = grid.f_lo + df, grid.f_hi / H - df
            if not lo < hi:
                raise ConfigError(f"harmonic fundamental range empty for {band}, T = {T}")
            out["f0"] = rng.uniform(lo, hi, n)
            out["phase"] = rng.uniform(0, 2 * np.pi, (n, H))
        elif cls == "chirp":
            cp = self.classes["chirp"]["per_band"][band]
            dur = float(cp["duration_s"])
            lo, hi = self.chirp_margin, T - dur - self.chirp_margin
            if not lo < hi:
                raise ConfigError(f"chirp does not fit the {T} s window in {band}")
            out["t0"] = rng.uniform(lo, hi, n)
        elif cls == "broadband":
            out["seed_key"] = ("bbsig", band, float(T))
        self._srcs[key] = out
        return out

    def chirp_ref(self, band, grid):
        cp = self.classes["chirp"]["per_band"][band]
        return chirp_reference(grid, float(cp["f1_hz"]), float(cp["f2_hz"]), float(cp["duration_s"]),
                               float(cp.get("taper", 0.2)))

    def signal_unit(self, cls, band, grid, src, idx, pos, g_true, ref=None) -> np.ndarray:
        """Signal bins at 0 dB input SNR (ADR-0015) for trials ``idx``: (t, K, N)."""
        out = np.empty((len(idx), grid.K, pos.shape[0]), dtype=complex)
        for j, i in enumerate(idx):
            tau = delays_s(pos, src["u"][i], self.c0)
            if cls == "tone":
                f0 = src["f0"][i]
                A = math.sqrt(2.0 * float(np.interp(f0, grid.f, g_true)))
                s = tone_bins(grid, f0, A, src["phase"][i], tau)
            elif cls == "harmonic":
                H = int(self.classes["harmonic"]["n_harmonics"])
                fh = src["f0"][i] * np.arange(1, H + 1)
                amps = np.sqrt(2.0 * np.interp(fh, grid.f, g_true))
                s = harmonic_bins(grid, src["f0"][i], amps, src["phase"][i], tau)
            elif cls == "broadband":
                gs = float(np.sum(g_true) * grid.df / (grid.f_hi - grid.f_lo))  # band SNR = 1
                rng = case_rng(self.seed, *src["seed_key"], int(i))
                s = broadband_bins(grid, gs, tau, rng)
            elif cls == "chirp":
                A = 1.0 / math.sqrt(float(np.sum(np.abs(ref) ** 2 / g_true)))  # E/N0_eff = 1
                s = chirp_bins(grid, ref, A, src["t0"][i], tau)
            else:
                raise ValueError(cls)
            out[j] = s.T
        return out

    # ------------------------------------------------------------------------------------------ one case
    def run_case(self, case: Case) -> dict:
        t_start = time.time()
        geom = self.geoms[case.cand]
        pos = geom.positions_m
        N = pos.shape[0]
        grid = self.grid(case.band, case.T)
        truth, assumed = self.scenarios[case.truth], self.scenarios[case.assumed]
        c_true = truth.covariance(pos, grid.f, self.c0)
        f_true = covariance_factor(c_true, f"{case.truth}/{case.cand}/{case.band}")
        if case.assumed == case.truth:
            c_ass, f_ass = c_true, f_true
        else:
            c_ass = assumed.covariance(pos, grid.f, self.c0)
            f_ass = covariance_factor(c_ass, f"{case.assumed}/{case.cand}/{case.band}")
        g_true = truth.element_psd(grid.f)
        modes = self.modes(case.cand)
        S = len(self.search_az)
        if N > 1:
            sw = beam_weights(pos, self.search_u, grid.f, self.c0)
            ss = beam_sigma(sw, c_ass)
        else:
            sw = ss = None
        classes = case.classes if case.kind == "primary" else self.classes_for(case.band, case.T)
        dets = sorted({CLASS_DETECTOR[c] for c in classes})
        H = int(self.classes.get("harmonic", {}).get("n_harmonics", 4))
        hidx = harmonic_index(grid, H) if "harmonic" in dets else None
        ref = self.chirp_ref(case.band, grid) if "mf" in dets else None
        oversample = int(self.proc["mf_oversample"])
        detector = Detectors(hidx, None, oversample)
        n_lags = oversample * grid.K
        n_fund = 0 if hidx is None else hidx.shape[0]
        sig_n = np.sqrt(np.einsum("knn->kn", c_ass))  # (K, N)
        replicas = {}
        if ref is not None:
            replicas["single"] = (ref / sig_n[:, 0])[None, :]
            replicas["incoherent"] = (ref[:, None] / sig_n).T
            if sw is not None:
                replicas["beam_search"] = (ref[:, None] / ss).T
        n_streams = {"single": 1, "beam_known": 1, "beam_search": S, "incoherent": N}
        inc = None
        if N > 1:
            dn = 1.0 / sig_n
            rnorm = c_ass * dn[:, :, None] * dn[:, None, :]  # normalized coherence per bin (unit diagonal)
            lam = np.linalg.eigvalsh(rnorm)[:, -1]
            inc = {"n": N, "lam": lam, "lam_star": float(lam.max()), "lam_mf": float("nan")}
            if ref is not None:
                w2 = np.abs(replicas["incoherent"]) ** 2  # (N, K)
                wn = w2 / w2.sum(axis=1, keepdims=True)
                mcov = np.einsum("nk,mk,knm->nm", np.sqrt(wn), np.sqrt(wn), rnorm)
                inc["lam_mf"] = float(np.linalg.eigvalsh(0.5 * (mcov + mcov.T))[-1])
        width = N + (S if N > 1 else 0) + (oversample * S if "mf" in dets else 0)
        chunk = int(max(1, min(512, MEM_BUDGET_BYTES // (16 * grid.K * max(width, 1)))))

        def stats_for(x, look_u):
            out = {}
            for mode in modes:
                kw = {}
                if mode == "beam_search":
                    kw = {"search_w": sw, "search_sigma": ss}
                elif mode == "beam_known":
                    kwn, ksg = known_beams(look_u, pos, grid.f, self.c0, c_ass)
                    kw = {"known_w": kwn, "known_sigma": ksg}
                z = normalize(x, mode, c_ass, **kw)
                comb = "mean" if mode == "incoherent" else "max"
                st = detector.power_stats(np.abs(z) ** 2, comb, [d for d in dets if d != "mf"])
                if "mf" in dets:
                    rep = (ref[None, :] / ksg)[:, None, :] if mode == "beam_known" else replicas[mode]
                    st["mf"] = detector.mf_stat(detector.mf_lags(z, rep), comb)
                for d, v in st.items():
                    out[(mode, d)] = v
            return out

        # ---- null sets
        tr = self.trials_for(case.band, case.T)
        null = {}
        for set_name, model_id, fac in (("cal", case.assumed, f_ass), ("eval", case.truth, f_true)):
            n = int(tr[set_name])
            acc = {}
            for ci, s0 in enumerate(range(0, n, chunk)):
                t = min(chunk, n - s0)
                rng = case_rng(self.seed, "null", set_name, model_id, case.cand, case.band, float(case.T), ci, chunk)
                x = draw_noise(fac, rng, t, dtype=np.complex64)
                look = np.stack([unit_vector(a, 0.0) for a in rng.uniform(0, 360, t)])
                for k, v in stats_for(x, look).items():
                    acc.setdefault(k, []).append(v)
            null[set_name] = {k: np.concatenate(v) for k, v in acc.items()}

        rows_thr = []
        thresholds = {}
        for mode in modes:
            for d in dets:
                cal = null["cal"][(mode, d)]
                ev = null["eval"][(mode, d)]
                for p in self.pfa:
                    ex = self.exact_threshold(mode, d, p, grid.K)
                    bd = self.bound_threshold(mode, d, p, grid, n_streams[mode], n_fund, n_lags, inc)
                    thr = dt.choose_threshold(p, cal, exact=ex, bound=bd)
                    thresholds[(mode, d, p)] = thr
                    rp = dt.realized_pfa(ev, thr["eta"])
                    rb = dt.realized_pfa(ev, bd) if bd is not None else None
                    rows_thr.append({
                        "experiment": case.experiment, "kind": case.kind, "candidate": case.cand, "band": case.band,
                        "window_s": case.T, "truth": case.truth, "assumed": case.assumed, "mode": mode,
                        "detector": d, "pfa_target": p, "method": thr["method"], "eta": thr["eta"],
                        "eta_lo": thr["eta_lo"], "eta_hi": thr["eta_hi"], "n_cal": len(cal), "n_eval": len(ev),
                        "realized_pfa": rp["p"], "realized_lo": rp["lo"], "realized_hi": rp["hi"],
                        "realized_k": rp["k"], "bound_eta": bd if bd is not None else float("nan"),
                        "bound_realized_pfa": rb["p"] if rb else float("nan"),
                        "bound_realized_hi": rb["hi"] if rb else float("nan"),
                        "exact_eta": ex if ex is not None else float("nan"), "K_bins": grid.K,
                        "streams": n_streams[mode], "fundamentals": n_fund, "lags": n_lags,
                    })
        result = {"case": case, "thresholds": rows_thr, "pd": [], "snr_req": [], "roc": []}
        if case.kind != "primary":
            result["seconds"] = time.time() - t_start
            return result

        # ---- positive sets
        roc_keys = {(r["candidate"], r["band"], float(r["window_s"]), r["scenario"], r["class"])
                    for r in self.cfg.get("roc_cases", [])}
        for cls in classes:
            d = CLASS_DETECTOR[cls]
            n = int(tr["pos"])
            src = self.source_params(cls, case.band, case.T, n, grid)
            center = self.snr_center_db(cls, grid, g_true)
            snr = center + self.offsets
            alpha = 10.0 ** (snr / 20.0)
            pos_stats = {m: np.empty((snr.size, n)) for m in modes}
            for ci, s0 in enumerate(range(0, n, chunk)):
                t = min(chunk, n - s0)
                idx = np.arange(s0, s0 + t)
                rng = case_rng(self.seed, "pos", cls, case.truth, case.cand, case.band, float(case.T), ci, chunk)
                xn = draw_noise(f_true, rng, t, dtype=np.complex64)
                xs = self.signal_unit(cls, case.band, grid, src, idx, pos, g_true, ref).astype(np.complex64)
                for mode in modes:
                    kw = {}
                    if mode == "beam_search":
                        kw = {"search_w": sw, "search_sigma": ss}
                    elif mode == "beam_known":
                        kwn, ksg = known_beams(src["u"][idx], pos, grid.f, self.c0, c_ass)
                        kw = {"known_w": kwn, "known_sigma": ksg}
                    zn = normalize(xn, mode, c_ass, **kw)
                    zs = normalize(xs, mode, c_ass, **kw)
                    comb = "mean" if mode == "incoherent" else "max"
                    if d == "mf":
                        rep = (ref[None, :] / ksg)[:, None, :] if mode == "beam_known" else replicas[mode]
                        mn = detector.mf_lags(zn, rep)
                        ms = detector.mf_lags(zs, rep)
                        for j, a in enumerate(alpha):
                            pos_stats[mode][j, idx] = detector.mf_stat(mn + np.float32(a) * ms, comb)
                    else:
                        for j, a in enumerate(alpha):
                            pos_stats[mode][j, idx] = detector.power_stats(np.abs(zn + np.float32(a) * zs) ** 2, comb, [d])[d]
            for mode in modes:
                for p in self.pfa:
                    thr = thresholds[(mode, d, p)]
                    curve = [dt.pd_with_interval(pos_stats[mode][j], thr) for j in range(snr.size)]
                    for j, cv in enumerate(curve):
                        result["pd"].append({
                            "candidate": case.cand, "band": case.band, "window_s": case.T, "scenario": case.truth,
                            "class": cls, "detector": d, "mode": mode, "pfa_target": p, "threshold_method": thr["method"],
                            "snr_db": float(snr[j]), "pd": cv["pd"], "pd_lo": cv["lo"], "pd_hi": cv["hi"], "n_pos": n})
                    pdv = np.array([c["pd"] for c in curve])
                    plo = np.array([c["lo"] for c in curve])
                    phi = np.array([c["hi"] for c in curve])
                    for tgt in self.pd_targets:
                        v, st = dt.snr_at_pd(snr, pdv, tgt)
                        lo, _ = dt.snr_at_pd(snr, phi, tgt)
                        hi, _ = dt.snr_at_pd(snr, plo, tgt)
                        result["snr_req"].append({
                            "experiment": case.experiment, "candidate": case.cand, "band": case.band,
                            "window_s": case.T, "scenario": case.truth, "class": cls, "detector": d, "mode": mode,
                            "pfa_target": p, "pd_target": tgt, "threshold_method": thr["method"], "snr_req_db": v,
                            "snr_req_lo": lo, "snr_req_hi": hi, "status": st, "snr_grid_lo": float(snr[0]),
                            "snr_grid_hi": float(snr[-1])})
                if (case.cand, case.band, float(case.T), case.truth, cls) in roc_keys:
                    cal = np.sort(null["cal"][(mode, d)])
                    j0 = int(np.argmin(np.abs(self.offsets)))
                    for pf in np.logspace(-3, -0.3, 28):
                        eta = cal[min(int(math.ceil(cal.size * (1 - pf))), cal.size) - 1]
                        result["roc"].append({"candidate": case.cand, "band": case.band, "window_s": case.T,
                                              "scenario": case.truth, "class": cls, "mode": mode,
                                              "snr_db": float(snr[j0]), "pfa": float(np.mean(cal > eta)),
                                              "pd": float(np.mean(pos_stats[mode][j0] > eta))})
        result["seconds"] = time.time() - t_start
        return result

    # ------------------------------------------------------------------------------------------ verification
    def covariance_validation(self) -> list[dict]:
        cv = self.cfg["covariance_validation"]
        rows = []
        for sc in cv["scenarios"]:
            for cand in cv["candidates"]:
                pos = self.geoms[cand].positions_m
                b = cv["band"]
                grid = self.grid(b, float(cv["window_s"]))
                cmat = self.scenarios[sc].covariance(pos, grid.f, self.c0)
                rng = case_rng(self.seed, "covval", sc, cand, b)
                x = draw_noise(covariance_factor(cmat), rng, 1)[0].T
                w = to_waveform(x, grid)
                f, g, nseg = welch_csd(w, grid.fs, int(cv["nperseg"]))
                lo, hi = grid.f_lo * 1.2, grid.f_hi * 0.9
                sel = (f >= lo) & (f <= hi)
                model = self.scenarios[sc].covariance(pos, f[sel], self.c0)
                diag = np.real(np.einsum("fnn->fn", model)).mean(axis=1)
                rel = np.abs(g[sel] - model) / diag[:, None, None]
                band_pow = float(np.sum(self.scenarios[sc].element_psd(grid.f)) * grid.df)
                rows.append({"scenario": sc, "candidate": cand, "band": b, "window_s": grid.T, "segments": nseg,
                             "frequencies": int(sel.sum()), "median_rel_error": float(np.median(rel)),
                             "max_rel_error": float(np.max(rel)), "expected_rel_se": 1.0 / math.sqrt(nseg),
                             "waveform_var_over_band_power": float(np.var(w, axis=1).mean() / band_pow)})
        return rows

    def waveform_examples(self, out_dir: Path) -> list[dict]:
        """Rebuild selected positive trials from their seed keys and write time-domain waveforms (npz)."""
        rows = []
        for ex in self.cfg.get("waveform_examples", []):
            cand, band, T, sc, cls = ex["candidate"], ex["band"], float(ex["window_s"]), ex["scenario"], ex["class"]
            pos = self.geoms[cand].positions_m
            grid = self.grid(band, T)
            truth = self.scenarios[sc]
            cmat = truth.covariance(pos, grid.f, self.c0)
            g_true = truth.element_psd(grid.f)
            n = self.trials_for(band, T)["pos"]
            src = self.source_params(cls, band, T, n, grid)
            ref = self.chirp_ref(band, grid) if cls == "chirp" else None
            i = int(ex["trial"])
            chunk_rng = case_rng(self.seed, "waveform", cls, sc, cand, band, T, i)
            xn = draw_noise(covariance_factor(cmat), chunk_rng, 1)[0]
            xs = self.signal_unit(cls, band, grid, src, [i], pos, g_true, ref)[0]
            a = 10 ** (float(ex["snr_db"]) / 20)
            wn = to_waveform(xn.T, grid)
            wsig = to_waveform((a * xs).T, grid)
            name = f"wave_{cls}_{cand}_{band}_{T:g}s.npz"
            np.savez_compressed(out_dir / name, fs=grid.fs, noise=wn, signal=wsig, positions_m=pos,
                                azimuth_deg=src["az"][i], snr_db=float(ex["snr_db"]))
            rows.append({"file": name, "class": cls, "candidate": cand, "band": band, "window_s": T, "trial": i,
                         "snr_db": float(ex["snr_db"]), "azimuth_deg": float(src["az"][i]),
                         "noise_rms_upa": float(np.sqrt(np.mean(wn ** 2))),
                         "signal_rms_upa": float(np.sqrt(np.mean(wsig ** 2)))})
        return rows

    def clipping_check(self, max_snr_db: float) -> dict:
        """Largest simulated rms (noise + strongest signal) against every chain's clip level (12 dB crest)."""
        worst = []
        for sc_id, sc in self.scenarios.items():
            sn_id = self.scenario_cfg[sc_id].get("self_noise", "none")
            if sn_id not in self.chains:
                continue
            clip_db = 20 * math.log10(self.chains[sn_id].clip_pressure_upa_peak)
            for b in self.bands.values():
                f = np.linspace(b["f_lo_hz"], b["f_hi_hz"], 2001)
                noise = float(np.trapezoid(sc.element_psd(f), f))
                rms_db = 10 * math.log10(noise * (1 + 10 ** (max_snr_db / 10)))
                worst.append(clip_db - (rms_db + 12.0))
        return {"min_headroom_db": float(min(worst)) if worst else float("nan")}

    def provenance_rows(self) -> list[dict]:
        rows = [p.row_full() for p in self.params]
        counts = {k: sum(r["provenance"] == k for r in rows) for k in PROVENANCE}
        self.self_checks["parameters_by_provenance"] = counts
        return rows


# ---------------------------------------------------------------------------------------------- workers
_STUDY: Sim02B1Study | None = None


def _init_worker(cfg):
    global _STUDY
    _STUDY = Sim02B1Study(cfg, log=lambda m: None)


def _work(case: Case) -> dict:
    return _STUDY.run_case(case)


def load_sim02b1_config(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    Sim02B1Study(cfg, log=lambda m: None).cases()  # validates
    return cfg


def detection_gain_rows(snr_rows: list[dict]) -> list[dict]:
    """SNR_req(A0) - SNR_req(candidate) at matching band, window, scenario, class, Pfa and Pd (ADR-0015)."""
    a0 = {(r["band"], r["window_s"], r["scenario"], r["class"], r["pfa_target"], r["pd_target"]): r
          for r in snr_rows if r["candidate"] == "A0"}
    out = []
    for r in snr_rows:
        if r["candidate"] == "A0":
            continue
        k = (r["band"], r["window_s"], r["scenario"], r["class"], r["pfa_target"], r["pd_target"])
        b = a0.get(k)
        if b is None:
            continue
        ok = r["status"] == "ok" and b["status"] == "ok"
        g = b["snr_req_db"] - r["snr_req_db"] if ok else float("nan")
        lo = b["snr_req_lo"] - r["snr_req_hi"] if ok else float("nan")
        hi = b["snr_req_hi"] - r["snr_req_lo"] if ok else float("nan")
        status = "ok" if ok else f"A0 {b['status']}; candidate {r['status']}"
        out.append({"experiment": r["experiment"], "candidate": r["candidate"], "mode": r["mode"],
                    "band": r["band"], "window_s": r["window_s"], "scenario": r["scenario"], "class": r["class"],
                    "pfa_target": r["pfa_target"], "pd_target": r["pd_target"], "gain_db": g, "gain_lo_db": lo,
                    "gain_hi_db": hi, "status": status, "threshold_method": r["threshold_method"],
                    "a0_threshold_method": b["threshold_method"]})
    return out


def run(config_path, output_root=None, allow_dirty: bool = False, make_figures: bool = True, repo_dir=None,
        log=print, argv=None, workers: int | None = None) -> Path:
    t_start = time.time()
    config_path = Path(config_path)
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    study = Sim02B1Study(cfg, log)
    cases = study.cases()
    cfg_sha = config_sha256(cfg)
    repo_dir = Path(repo_dir) if repo_dir else config_path.resolve().parent
    gs = git_state(repo_dir)
    if gs["git_dirty"] and not allow_dirty:
        raise DirtyTreeError("working tree has uncommitted changes to tracked files; commit them or pass --allow-dirty")
    created = utc_now()
    run_id = make_run_id(created, cfg_sha, gs["git_commit"])
    root = Path(output_root) if output_root else Path(cfg["output"]["root"])
    rd = RunDirectory(root, run_id)
    log(f"SIM-02B.1 run {run_id} -> {root / run_id} ({len(cases)} cases)")
    T = study.timings
    try:
        tab = lambda n: rd.path("tables", n)  # noqa: E731
        prov = study.provenance_rows()
        write_csv(tab("parameters_by_provenance.csv"), prov)
        write_csv(tab("cases.csv"), [{"experiment": c.experiment, "kind": c.kind, "candidate": c.cand, "band": c.band,
                                      "window_s": c.T, "truth": c.truth, "assumed": c.assumed,
                                      "classes": ";".join(c.classes)} for c in cases])
        # verification before the experiment
        t = time.time()
        cov = study.covariance_validation()
        write_csv(tab("covariance_validation.csv"), cov)
        worst = max(r["median_rel_error"] / r["expected_rel_se"] for r in cov)
        study.self_checks["covariance_validation_worst_median_error_in_se"] = worst
        study.self_checks["covariance_validation_worst_variance_ratio"] = max(
            abs(r["waveform_var_over_band_power"] - 1) for r in cov)
        if worst > 3.0:
            raise RuntimeError(f"self-check failed: time-series CSD deviates from the model ({worst:.2f} SE median)")
        T["covariance_validation_s"] = time.time() - t
        # cases (largest first for load balance)
        order = sorted(cases, key=lambda c: -study.grid(c.band, c.T).K * study.geoms[c.cand].n_elements)
        n_workers = workers or int(os.environ.get("PICKET_WORKERS", os.cpu_count() or 1))
        t = time.time()
        results = []
        if n_workers > 1:
            with ProcessPoolExecutor(max_workers=n_workers, initializer=_init_worker, initargs=(cfg,)) as ex:
                for i, r in enumerate(ex.map(_work, order, chunksize=1)):
                    results.append(r)
                    c = r["case"]
                    log(f"  [{i + 1}/{len(order)}] {c.experiment} {c.cand} {c.band} {c.T:g}s {c.truth}"
                        f"{'' if c.assumed == c.truth else ' (assumed ' + c.assumed + ')'}: {r['seconds']:.1f} s")
        else:
            for i, c in enumerate(order):
                r = study.run_case(c)
                results.append(r)
                log(f"  [{i + 1}/{len(order)}] {c.experiment} {c.cand} {c.band} {c.T:g}s {c.truth}: {r['seconds']:.1f} s")
        T["cases_s"] = time.time() - t
        key = lambda r: (r["case"].experiment, r["case"].truth, r["case"].assumed, r["case"].band, r["case"].T,  # noqa: E731
                         r["case"].cand)
        results.sort(key=key)
        thr_rows = [x for r in results for x in r["thresholds"]]
        pd_rows = [x for r in results for x in r["pd"]]
        snr_rows = [x for r in results for x in r["snr_req"]]
        roc_rows = [x for r in results for x in r["roc"]]
        write_csv(tab("thresholds_and_pfa.csv"), thr_rows)
        write_csv(tab("pd_curves.csv.gz"), pd_rows, gz=True)
        write_csv(tab("snr_required.csv"), snr_rows)
        gain_rows = detection_gain_rows(snr_rows)
        write_csv(tab("detection_gain_vs_a0.csv"), gain_rows)
        write_csv(tab("roc_curves.csv"), roc_rows)
        write_csv(tab("case_timings.csv"), [{"experiment": r["case"].experiment, "candidate": r["case"].cand,
                                             "band": r["case"].band, "window_s": r["case"].T,
                                             "truth": r["case"].truth, "assumed": r["case"].assumed,
                                             "seconds": r["seconds"]} for r in results])
        # self-checks on false-alarm calibration (matched noise only): exact predictive laws (ADR-0015).
        # Empirical thresholds: beta-binomial; exact thresholds: binomial; bounds: upper tail at the target.
        matched = [r for r in thr_rows if r["kind"] == "primary"]
        for meth in ("exact", "empirical", "bound"):
            ps = []
            for r in matched:
                if meth == "bound":
                    if not (math.isfinite(r["bound_eta"]) and math.isfinite(r["bound_realized_pfa"])):
                        continue
                    k = int(round(r["bound_realized_pfa"] * r["n_eval"]))
                    ps.append(dt.calibration_pvalue("bound", k, r["n_eval"], r["pfa_target"])[1])
                elif r["method"] == meth:
                    ps.append(dt.calibration_pvalue(meth, r["realized_k"], r["n_eval"], r["pfa_target"], r["n_cal"])[0])
            if not ps:
                continue
            ps = np.array(ps)
            study.self_checks[f"pfa_{meth}_rows"] = int(ps.size)
            study.self_checks[f"pfa_{meth}_fraction_p_below_0p05"] = float(np.mean(ps < 0.05))
            study.self_checks[f"pfa_{meth}_min_p_times_rows"] = float(min(1.0, ps.min() * ps.size))
            if ps.min() * ps.size < 1e-3:
                raise RuntimeError(f"self-check failed: {meth} thresholds miscalibrated (Bonferroni p < 1e-3)")
        clip = study.clipping_check(float(np.max(study.offsets)) + 40.0)
        study.self_checks["clipping_min_headroom_db"] = clip["min_headroom_db"]
        if clip["min_headroom_db"] < 0:
            raise RuntimeError("self-check failed: a simulated signal would clip the acquisition chain")
        wave_dir = rd.path("waveforms")
        wave_dir.mkdir(parents=True, exist_ok=True)
        wrows = study.waveform_examples(wave_dir)
        write_csv(tab("waveform_examples.csv"), wrows)
        if make_figures:
            t = time.time()
            from .. import plotting_sim02b1

            study.figures = plotting_sim02b1.make_figures(study, rd.path("figures"), pd_rows, gain_rows, thr_rows,
                                                          roc_rows, cov, wave_dir, wrows)
            T["figures_s"] = time.time() - t
        else:
            study.figures = []
        T["total_s"] = time.time() - t_start
        sw = software_versions()
        sw.update(gs)
        record = {"run_id": run_id, "experiment_id": "SIM-02B.1", "title": cfg["experiment"]["title"],
                  "status": "complete", "created_utc": created.isoformat(), "completed_utc": utc_now().isoformat(),
                  "command": list(argv) if argv else sys.argv, "config_path": str(config_path),
                  "config_sha256": cfg_sha, "config_resolved": cfg, "software": sw,
                  "assumptions": cfg["experiment"].get("assumptions", []), "self_checks": study.self_checks,
                  "warnings": study.warnings, "timings_s": T, "figures": study.figures, "workers": n_workers}
        lines = [f"# SIM-02B.1 run {run_id}", "", f"* Config sha256 `{cfg_sha[:16]}...`; code `{gs.get('git_commit')}` "
                 f"(dirty: {gs.get('git_dirty')})", f"* Cases: {len(cases)}; workers: {n_workers}", "",
                 "## Self-checks", ""]
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
