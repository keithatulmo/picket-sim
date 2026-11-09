"""SIM-02B.2-A: adaptive noise estimation and false-alarm control (docs/SIM-02B2A_plan.md, ADR-0018 to ADR-0020).

Two phases of independent work units:

1. Calibration (candidate x cell) under the nominal design model: thresholds for every normalizer, mode, detector
   and Pfa. A0 uses exact laws and exact-in-distribution scalar simulation (single-channel reference powers are
   Gamma or order statistics of exponentials); arrays use sequential full synthesis with a stopping rule, plus the
   exact quadratic-form law (ORACLE incoherent tonal) and conditional Monte Carlo (ORACLE beam-search tonal).
2. Evaluation (candidate x cell x scenario) with the fixed design thresholds: realized Pfa on noise-only trials,
   Pd curves on positive trials, estimation error, detection loss against ORACLE and gain against A0.

Adaptive normalizers see only stream data (ADR-0019); the oracle path is separate.
"""

from __future__ import annotations

import math
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from .. import detection as dt
from .. import noise_estimation as ne
from .. import qforms
from ..config import ConfigError, config_sha256
from ..conventions import unit_vector
from ..detectors import Detectors, beam_sigma, beam_weights, harmonic_index
from ..records import DirtyTreeError, RunDirectory, git_state, make_run_id, software_versions, utc_now
from ..signals import broadband_bins, delays_s, tone_bins
from ..stats import Z95, case_rng, wilson_ci
from ..synthesis import covariance_factor, draw_noise, steering_bins
from ..tables import write_csv
from .sim02b1 import CLASS_DETECTOR, Sim02B1Study

MEM_BUDGET = 120e6
ADAPTIVE = ("tref_ca", "tref_os", "fref_ca", "fref_os")


@dataclass(frozen=True)
class CalCase:
    cand: str
    cell: str


@dataclass(frozen=True)
class EvalCase:
    cand: str
    cell: str
    scenario: str


# ---------------------------------------------------------------------------------------------- normalizers
def apply_normalizer(spec: dict, y_test_pow: np.ndarray, hist_pow: np.ndarray | None, fidx: np.ndarray | None,
                     model_g: np.ndarray | None = None) -> np.ndarray:
    """Background estimate G_hat (t, S, K) for one normalizer.

    Adaptive types receive only data: ``y_test_pow`` (t, S, K) test-window powers and ``hist_pow`` (t, H, S, K)
    reference-window powers ordered by age (index 0 = one window before the test). ``model_g`` (S, K) is used only by
    the oracle and nominal types.
    """
    kind = spec["type"]
    if kind in ("oracle", "nominal"):
        return np.broadcast_to(model_g[None], y_test_pow.shape)
    if kind in ("tref_ca", "tref_os"):
        g, m = int(spec["guard"]), int(spec["M"])
        ref = hist_pow[:, g:g + m]
        if ref.shape[1] != m:
            raise ValueError("not enough reference windows for this normalizer")
        ref = np.moveaxis(ref, 1, -2)  # (t, S, M, K): estimators reduce the window axis (second to last)
        return ne.tref_ca(ref) if kind == "tref_ca" else ne.tref_os(ref, int(spec["r"]))
    if kind == "fref_ca":
        return ne.fref_ca(y_test_pow, fidx)
    if kind == "fref_os":
        return ne.fref_os(y_test_pow, fidx, int(spec["r"]))
    raise ValueError(f"unknown normalizer type {kind!r}")


EXACT_FLAG_P = 1e-3  # realized counts are flagged when their exact predictive tail probability is below this


def exact_tails(thr: dict, k: int, n: int, pfa: float) -> tuple[float, float]:
    """(P(K >= k), P(K <= k)) for a realized count under correct calibration of the design threshold: binomial for
    exact, quadratic-form and conditional Monte Carlo thresholds; beta-binomial for empirical and fast-simulation
    thresholds, which carries the threshold's own sampling error (detection.calibration_pvalue)."""
    meth = "empirical" if thr["method"] in ("empirical", "fast null simulation") else "exact"
    n_cal = int(thr.get("n", 0)) if meth == "empirical" else 0
    up = dt.calibration_pvalue(meth, k, n, pfa, n_cal)[1]
    low = 1.0 - dt.calibration_pvalue(meth, k + 1, n, pfa, n_cal)[1] if k < n else 1.0
    return up, low


def history_needed(norms: list[dict]) -> int:
    return max([int(n["guard"]) + int(n["M"]) for n in norms if n["type"] in ("tref_ca", "tref_os")] + [0])


@dataclass
class Sim02B2AStudy:
    cfg: dict
    log: object = print
    self_checks: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    timings: dict = field(default_factory=dict)

    def __post_init__(self):
        self.b1 = Sim02B1Study(self.cfg, lambda m: None)
        s = self.cfg["sim02b2a"]
        self.s2 = s
        self.c0 = self.b1.c0
        self.seed = int(self.cfg["seed"])
        self.nominal = s["nominal_scenario"]
        if self.nominal not in self.b1.scenarios:
            raise ConfigError("unknown nominal scenario")
        self.cells = {c["id"]: c for c in s["cells"]}
        self.norms = list(s["normalizers"])
        self.cnorms = list(s.get("contamination_normalizers", []))
        ids = [n["id"] for n in self.norms + self.cnorms]
        if len(set(ids)) != len(ids):
            raise ConfigError("normalizer ids must be unique")
        for n in self.norms + self.cnorms:
            if n["type"] not in ("oracle", "nominal") + ADAPTIVE:
                raise ConfigError(f"unknown normalizer type {n['type']!r}")
        self.alias = {}
        for cn in self.cnorms:  # guard changes which noise windows are used, not the null law
            same = [n for n in self.norms if n["type"] == cn["type"] and n.get("M") == cn.get("M")
                    and n.get("r") == cn.get("r")]
            if not same:
                raise ConfigError(f"{cn['id']}: no calibrated normalizer with the same type and M")
            self.alias[cn["id"]] = same[0]["id"]
        self.a0_extra = [{"id": f"TREF-CA{m}-A0", "type": "tref_ca", "M": int(m), "guard": 2}
                         for m in s.get("a0_reference_counts", []) if int(m) != 16]
        self.scen = {x["id"]: x for x in s["scenarios"]}
        for x in self.scen.values():
            for key in ("reference", "test"):
                if x[key] not in self.b1.scenarios:
                    raise ConfigError(f"{x['id']}: unknown noise scenario {x[key]!r}")
            for c in x["cells"]:
                if c not in self.cells:
                    raise ConfigError(f"{x['id']}: unknown cell {c!r}")
        self.pfa = [float(p) for p in s["pfa"]]
        self.excl = s.get("excluded", [])
        self.cal = s["calibration"]
        self.ev = s["evaluation"]
        self.search_u = self.b1.search_u
        self.S = len(self.search_u)

    # ------------------------------------------------------------------------------------------ helpers
    def grid(self, cell: str):
        c = self.cells[cell]
        return self.b1.grid(c["band"], float(c["window_s"]))

    def modes(self, cand: str) -> list[str]:
        return ["single"] if self.b1.geoms[cand].n_elements == 1 else ["beam_search", "incoherent"]

    def classes(self, cell: str, scenario: str | None = None) -> tuple:
        c = self.cells[cell]
        cls = self.b1.classes_for(c["band"], float(c["window_s"]))
        if scenario is not None and "classes" in self.scen[scenario]:
            cls = tuple(x for x in cls if x in self.scen[scenario]["classes"])
        return cls

    def excluded(self, norm: dict, det: str) -> bool:
        return any(norm["type"] in e["normalizer_types"] and det == e["detector"] for e in self.excl)

    def cal_cases(self) -> list[CalCase]:
        return [CalCase(c, cell) for c in self.b1.cand_specs for cell in self.cells]

    def eval_cases(self) -> list[EvalCase]:
        return [EvalCase(c, cell, sc) for sc, x in self.scen.items() for cell in x["cells"] for c in self.b1.cand_specs]

    def _cov(self, scen_id: str, pos, f):
        return self.b1.scenarios[scen_id].covariance(pos, f, self.c0)

    def stream_model(self, mode, cmat, sw):
        """Model background per stream (S, K) for oracle/nominal normalization."""
        if mode == "single":
            return np.real(cmat[:, 0, 0])[None, :]
        if mode == "incoherent":
            return np.real(np.einsum("knn->kn", cmat)).T
        return beam_sigma(sw, cmat).T ** 2

    @staticmethod
    def to_streams(x, mode, sw):
        """Stream bins (..., S, K) from element bins (..., K, N)."""
        if mode == "single":
            return x[..., 0][..., None, :]
        if mode == "incoherent":
            return np.swapaxes(x, -1, -2)
        swc = sw.conj().astype(x.dtype)  # (K, N, S); batched matrix products are several times faster than einsum
        return np.swapaxes((x[..., None, :] @ swc)[..., 0, :], -1, -2)

    # ------------------------------------------------------------------------------------------ statistics
    def stats_for(self, y, ghat, dets, comb, detector, ref):
        """Detector statistics (t,) for test streams y (t, S, K) normalized by ghat (t, S, K)."""
        u = (np.abs(y) ** 2) / ghat
        out = detector.power_stats(u, comb, [d for d in dets if d != "mf"])
        if "mf" in dets:
            sq = np.sqrt(ghat)
            out["mf"] = detector.mf_stat(detector.mf_lags((y / sq).astype(np.complex64),
                                                          (ref[None, None, :] / sq).astype(np.complex64)), comb)
        return out

    def all_stats(self, y_test, hist_pow, model_g, norms, dets, comb, detector, ref, fidx, pre=None):
        """{normalizer id: {detector: (t,)}} for one mode; model_g: {"oracle": (S,K), "nominal": (S,K)}.

        ``pre``: optional {normalizer id: G_hat} computed earlier from the same reference windows (time-reference
        estimates do not depend on the test window, so they are reused across signal amplitudes)."""
        ptest = np.abs(y_test) ** 2
        res = {}
        for n in norms:
            mg = model_g.get(n["type"]) if n["type"] in ("oracle", "nominal") else None
            g = pre[n["id"]] if pre and n["id"] in pre else apply_normalizer(n, ptest, hist_pow, fidx, mg)
            d_ok = [d for d in dets if not self.excluded(n, d)]
            res[n["id"]] = self.stats_for(y_test, g, d_ok, comb, detector, ref)
        return res

    # ------------------------------------------------------------------------------------------ trial synthesis
    def synth(self, cand, cell, scen_id, n, rng, H, signal=None):
        """Element bins of n trials: test window (n, K, N) and H history windows (n, H, K, N), complex64.

        ``signal``: optional callable (idx_window_age) -> (n, K, N) added to the test window (age 0) and, for
        contamination, to history windows (age >= 1) where the callable returns non-zero bins.
        """
        st = self._ctx(cand, cell, scen_id)
        xt = draw_noise(st["f_test"], rng, n, dtype=np.complex64)
        xh = draw_noise(st["f_ref"], rng, n * H, dtype=np.complex64).reshape(n, H, *xt.shape[1:]) if H else None
        x = self.scen.get(scen_id, {})  # the nominal design model is stationary and clean
        if H and "interference" in x:
            itf = x["interference"]
            grid = st["grid"]
            hit = rng.uniform(size=(n, H)) < float(itf["probability"])
            az = rng.uniform(0, 360, size=(n, H))
            gi = self.b1.spectra[itf["spectrum"]](grid.f) * 10 ** (float(itf["level_db"]) / 10)
            for i, h in zip(*np.nonzero(hit)):
                u = unit_vector(az[i, h], 0.0)
                s = broadband_bins(grid, gi, delays_s(st["pos"], u, self.c0), rng)  # (N, K)
                xh[i, h] += s.T.astype(np.complex64)
        return xt, xh

    def _ctx(self, cand, cell, scen_id):
        key = (cand, cell, scen_id)
        if not hasattr(self, "_ctx_cache"):
            self._ctx_cache = {}
        if key in self._ctx_cache:
            return self._ctx_cache[key]
        grid = self.grid(cell)
        pos = self.b1.geoms[cand].positions_m
        x = self.scen[scen_id] if scen_id in self.scen else {"reference": scen_id, "test": scen_id}
        c_ref = self._cov(x["reference"], pos, grid.f)
        c_test = self._cov(x["test"], pos, grid.f) * 10 ** (float(x.get("test_offset_db", 0.0)) / 10)
        c_nom = self._cov(self.nominal, pos, grid.f)
        ctx = {"grid": grid, "pos": pos, "c_ref": c_ref, "c_test": c_test, "c_nom": c_nom,
               "f_ref": covariance_factor(c_ref, f"{scen_id}/{cand}/ref"),
               "f_test": covariance_factor(c_test, f"{scen_id}/{cand}/test"),
               "g_true": np.real(c_test[:, 0, 0]), "g_nom": np.real(c_nom[:, 0, 0])}
        n_el = pos.shape[0]
        ctx["sw"] = beam_weights(pos, self.search_u, grid.f, self.c0) if n_el > 1 else None
        self._ctx_cache[key] = ctx
        return ctx

    def _detector(self, cell):
        grid = self.grid(cell)
        cls = self.classes(cell)
        dets = sorted({CLASS_DETECTOR[c] for c in cls})
        H = int(self.b1.classes.get("harmonic", {}).get("n_harmonics", 4))
        hidx = harmonic_index(grid, H) if "harmonic" in dets else None
        c = self.cells[cell]
        ref = self.b1.chirp_ref(c["band"], grid) if "mf" in dets else None
        det = Detectors(hidx, None, int(self.b1.proc["mf_oversample"]))
        fidx = None
        L = [n["L"] for n in self.norms if n["type"] in ("fref_ca", "fref_os")]
        G = [n["G"] for n in self.norms if n["type"] in ("fref_ca", "fref_os")]
        if L:
            if len(set(L)) != 1 or len(set(G)) != 1:
                raise ConfigError("all frequency-reference normalizers must share L and G")
            fidx = ne.fref_index(grid.K, int(L[0]), int(G[0]))
        return dets, det, ref, fidx, (hidx.shape[0] if hidx is not None else 0)

    def _chunk(self, cand, cell, H):
        grid = self.grid(cell)
        n_el = self.b1.geoms[cand].n_elements
        width = (H + 1) * (n_el + (self.S if n_el > 1 else 1)) + 4 * self.S
        return int(max(1, min(256, MEM_BUDGET // (8 * grid.K * width))))

    # ------------------------------------------------------------------------------------------ null trials
    def null_stats(self, cand, cell, scen_id, n, key, norms):
        """Noise-only statistics {(norm, mode, det): (n,)} and estimation-error samples."""
        ctx = self._ctx(cand, cell, scen_id)
        dets, detector, ref, fidx, _ = self._detector(cell)
        H = history_needed(norms)
        chunk = self._chunk(cand, cell, H)
        modes = self.modes(cand)
        model = {m: {"oracle": self.stream_model(m, ctx["c_test"], ctx["sw"]),
                     "nominal": self.stream_model(m, ctx["c_nom"], ctx["sw"])} for m in modes}
        acc, err = {}, {}
        for ci, s0 in enumerate(range(0, n, chunk)):
            t = min(chunk, n - s0)
            rng = case_rng(self.seed, "null2a", key, scen_id, cand, cell, ci, chunk)
            xt, xh = self.synth(cand, cell, scen_id, t, rng, H)
            for m in modes:
                y = self.to_streams(xt, m, ctx["sw"])
                hp = np.abs(self.to_streams(xh, m, ctx["sw"])) ** 2 if H else None
                comb = "mean" if m == "incoherent" else "max"
                res = self.all_stats(y, hp, model[m], norms, dets, comb, detector, ref, fidx)
                for nid, dd in res.items():
                    for d, v in dd.items():
                        acc.setdefault((nid, m, d), []).append(v)
                if key == "eval":  # estimation error against the true test-window background
                    p = np.abs(y) ** 2
                    for nrm in norms:
                        if nrm["type"] in ADAPTIVE:
                            g = apply_normalizer(nrm, p, hp, fidx)
                            e = 10 * np.log10(g / model[m]["oracle"][None])
                            err.setdefault((nrm["id"], m), []).append(e[:, :, ::7].ravel())
        stats = {k: np.concatenate(v) for k, v in acc.items()}
        errs = {k: np.concatenate(v) for k, v in err.items()}
        return stats, errs

    # ------------------------------------------------------------------------------------------ calibration
    def calibrate(self, case: CalCase) -> dict:
        t0 = time.time()
        if self.b1.geoms[case.cand].n_elements == 1:
            rows, extra = self._calibrate_a0(case)
        else:
            rows, extra = self._calibrate_array(case)
        return {"case": case, "thresholds": rows, "extra": extra, "seconds": time.time() - t0}

    def _thr_row(self, case, nid, mode, det, p, thr, extra=None):
        r = {"candidate": case.cand, "cell": case.cell, "normalizer": nid, "mode": mode, "detector": det,
             "pfa_target": p, "method": thr["method"], "eta": thr["eta"], "eta_lo": thr["eta_lo"],
             "eta_hi": thr["eta_hi"], "n": thr.get("n_cal", 0), "stop": thr.get("stop", ""),
             "eta_interval_db": (10 * math.log10(thr["eta_hi"] / thr["eta_lo"])
                                 if thr["eta_lo"] > 0 and math.isfinite(thr["eta_hi"]) else float("nan"))}
        r.update(extra or {})
        return r

    def a0_fast_null(self, case, n):
        """Single-channel noise-only statistics {(normalizer, detector): (n,)} under the nominal design, drawn
        exactly in distribution without synthesizing reference windows: the test-window bins are CN(0, g); the mean
        of M independent reference powers is g Gamma(M, 1/M); the r-th smallest of M is g (-ln(1 - B)) with
        B ~ Beta(r, M - r + 1) (probability integral transform of the exponential order statistic)."""
        grid = self.grid(case.cell)
        ctx = self._ctx(case.cand, case.cell, self.nominal)
        g = ctx["g_nom"]
        dets, detector, ref, fidx, _ = self._detector(case.cell)
        norms = self.norms + self.a0_extra
        rng = case_rng(self.seed, "cal-a0-fast", case.cand, case.cell)
        chunk = int(max(1, min(4000, 4e7 // (grid.K * 8))))
        acc = {}
        for s0 in range(0, n, chunk):
            t = min(chunk, n - s0)
            y = (np.sqrt(g / 2) * (rng.standard_normal((t, 1, grid.K)) + 1j * rng.standard_normal((t, 1, grid.K))))
            y = y.astype(np.complex64)
            p = np.abs(y) ** 2
            for nrm in norms:
                k = nrm["type"]
                if k in ("oracle", "nominal"):
                    gh = np.broadcast_to(g[None, None], p.shape)
                elif k == "tref_ca":
                    gh = (g * rng.gamma(int(nrm["M"]), 1.0 / int(nrm["M"]), size=p.shape)).astype(np.float32)
                elif k == "tref_os":
                    mm, r = int(nrm["M"]), int(nrm["r"])
                    gh = (g * -np.log1p(-rng.beta(r, mm - r + 1, size=p.shape))).astype(np.float32)
                else:
                    gh = apply_normalizer(nrm, p, None, fidx)
                d_ok = [d for d in dets if not self.excluded(nrm, d)]
                for d, v in self.stats_for(y, gh, d_ok, "max", detector, ref).items():
                    acc.setdefault((nrm["id"], d), []).append(v)
        return {k: np.concatenate(v) for k, v in acc.items()}

    def _calibrate_a0(self, case):
        """A0: exact laws and exact-in-distribution scalar simulation of the single-channel null."""
        grid = self.grid(case.cell)
        norms = self.norms + self.a0_extra
        acc = self.a0_fast_null(case, int(self.cal["a0_fast_samples"]))
        rows = []
        for (nid, d), v in acc.items():
            nrm = next(x for x in norms if x["id"] == nid)
            for pf in self.pfa:
                exact = None
                if d == "tonal":
                    pb = ne.per_bin_pfa(pf, grid.K)
                    if nrm["type"] in ("oracle", "nominal"):
                        exact = -math.log(pb)
                    elif nrm["type"] == "tref_ca":
                        exact = ne.ca_cfar_isf(pb, int(nrm["M"]))
                    elif nrm["type"] == "tref_os":
                        exact = ne.os_cfar_isf(pb, int(nrm["M"]), int(nrm["r"]))
                elif d == "energy" and nrm["type"] in ("oracle", "nominal"):
                    exact = dt.erlang_isf(pf, grid.K)
                thr = dt.choose_threshold(pf, v, exact=exact)
                if thr["method"] == "empirical":
                    thr["method"] = "fast null simulation"
                emp = dt.realized_pfa(v, thr["eta"]) if exact is not None else None
                rows.append(self._thr_row(case, nid, "single", d, pf, thr, {
                    "check_fast_pfa": emp["p"] if emp else float("nan"), "n_fast": int(v.size)}))
        return rows, {}

    def _calibrate_array(self, case):
        """Arrays: sequential full synthesis under the nominal design; exact and conditional-MC ORACLE checks."""
        batch = int(self.cal["batch"])
        cap = int(self.cal["max_trials"][case.cell])
        tol = float(self.cal["tolerance_db"])
        ok_p = [p for p in self.pfa if p * cap >= dt.MIN_EXCEEDANCES]
        p_stop = min(ok_p) if ok_p else None  # None: no empirical level reachable; run to the cap
        acc, n, stop = {}, 0, "cap"
        while n < cap:
            st, _ = self.null_stats(case.cand, case.cell, self.nominal, batch, f"cal{n}", self.norms)
            for k, v in st.items():
                acc.setdefault(k, []).append(v)
            n += batch
            if p_stop is None or n * p_stop < dt.MIN_EXCEEDANCES:
                continue
            widths = []
            for k, v in acc.items():
                thr = dt.empirical_threshold(np.concatenate(v), p_stop)
                if thr["eta_lo"] > 0:
                    widths.append(10 * math.log10(thr["eta_hi"] / thr["eta_lo"]))
            if widths and max(widths) <= tol:
                stop = f"interval <= {tol} dB at Pfa {p_stop:g}"
                break
        ctx = self._ctx(case.cand, case.cell, self.nominal)
        grid = ctx["grid"]
        oracle_exact = self._oracle_exact(case, ctx)
        rows = []
        for (nid, m, d), v in acc.items():
            v = np.concatenate(v)
            for pf in self.pfa:
                exact = oracle_exact.get((m, d, pf)) if nid in ("ORACLE", "NOMINAL") else None
                thr = dt.choose_threshold(pf, v, exact=exact[0] if exact else None)
                thr["stop"] = stop
                if exact:
                    thr["method"] = exact[1]
                    thr["eta_lo"], thr["eta_hi"] = exact[2], exact[3]
                extra = {"n_sequential": n}
                if exact:
                    emp = dt.choose_threshold(pf, v)
                    extra["empirical_eta"] = emp["eta"]
                    extra["empirical_eta_lo"], extra["empirical_eta_hi"] = emp["eta_lo"], emp["eta_hi"]
                rows.append(self._thr_row(case, nid, m, d, pf, thr, extra))
        return rows, {"n_sequential": n, "stop": stop, "K": grid.K}

    def _oracle_exact(self, case, ctx) -> dict:
        """ORACLE thresholds by the exact quadratic-form law (incoherent tonal) and conditional Monte Carlo
        (beam-search tonal). {(mode, det, pfa): (eta, method, lo, hi)}."""
        out = {}
        grid = ctx["grid"]
        cm = ctx["c_nom"]
        d = np.sqrt(np.real(np.einsum("knn->kn", cm)))
        rn = cm / (d[:, :, None] * d[:, None, :])
        n_el = cm.shape[1]
        lam = np.linalg.eigvalsh(0.5 * (rn + np.conj(np.swapaxes(rn, 1, 2)))) / n_el  # (K, N)

        def p_inc(x):
            q = qforms.hypoexp_sf(x, lam)
            return -np.expm1(np.sum(np.log1p(-np.minimum(q, 1 - 1e-16))))
        for pf in self.pfa:
            lo, hi = 0.0, 1.0
            while p_inc(hi) > pf:
                hi *= 2
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if p_inc(mid) > pf else (lo, mid)
            out[("incoherent", "tonal", pf)] = (hi, "exact quadratic form", hi, hi)
        # conditional Monte Carlo for the beam-search tonal maximum; bins are independent, every bin is estimated
        sw = ctx["sw"]
        cb = np.einsum("knb,knm,kmc->kbc", sw.conj(), cm, sw)  # (K, S, S) beam covariance
        sd = np.sqrt(np.real(np.einsum("kbb->kb", cb)))
        rb = cb / (sd[:, :, None] * sd[:, None, :])
        ncmc = int(self.cal["cmc_samples_per_bin"])
        est = [qforms.ConditionalMax(rb[k], ncmc, case_rng(self.seed, "cmc", case.cand, case.cell, k))
               for k in range(grid.K)]

        def p_beam(x, with_se=False):
            r = [e.sf(x) for e in est]
            q = np.array([a for a, _ in r])
            pw = -np.expm1(np.sum(np.log1p(-np.minimum(q, 1 - 1e-16))))
            if not with_se:
                return pw
            return pw, math.sqrt(float(np.sum(np.array([b for _, b in r]) ** 2)))
        for pf in self.pfa:
            lo, hi = 0.0, 1.0
            while p_beam(hi) > pf:
                hi *= 2
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if p_beam(mid) > pf else (lo, mid)
            pw, se = p_beam(hi, True)
            rel = min(0.99, Z95 * se / pf)
            # P ~ C exp(-eta): a probability error of +/- rel moves the threshold by log(1 +/- rel)
            out[("beam_search", "tonal", pf)] = (hi, "conditional Monte Carlo", hi + math.log1p(-rel),
                                                  hi + math.log1p(rel))
        return out

    # ------------------------------------------------------------------------------------------ evaluation
    def evaluate(self, case: EvalCase, thresholds: dict) -> dict:
        t0 = time.time()
        sc = self.scen[case.scenario]
        norms = self.norms + (self.cnorms if "contamination" in sc else [])
        null_norms = list(self.norms)
        if self.b1.geoms[case.cand].n_elements == 1 and case.scenario == "STAT":
            norms = norms + self.a0_extra
            null_norms = null_norms + self.a0_extra
        nkey = case.scenario if case.scenario in self.ev["null_trials"] else "default"
        n_null = int(self.ev["null_trials"][nkey])
        rows_pfa, rows_err = [], []
        if "contamination" not in sc:  # contamination changes positive trials only
            stats, errs = self.null_stats(case.cand, case.cell, case.scenario, n_null, "eval", null_norms)
            for (nid, m, d), v in stats.items():
                for pf in self.pfa:
                    thr = thresholds.get((case.cand, case.cell, nid, m, d, pf))
                    if thr is None or not math.isfinite(thr["eta"]):
                        continue
                    rp = dt.realized_pfa(v, thr["eta"])
                    # descriptive Wilson status (evaluation sampling only; biased toward 'liberal' when n Pfa ~ 1)
                    status = ("liberal" if rp["lo"] > pf else "conservative" if rp["hi"] < pf else "consistent")
                    up, low = exact_tails(thr, rp["k"], rp["n"], pf)
                    ex = "liberal" if up < EXACT_FLAG_P else "conservative" if low < EXACT_FLAG_P else "consistent"
                    rows_pfa.append({"candidate": case.cand, "cell": case.cell, "scenario": case.scenario,
                                     "normalizer": nid, "mode": m, "detector": d, "pfa_target": pf,
                                     "threshold_method": thr["method"], "n_eval": rp["n"], "realized_k": rp["k"],
                                     "realized_pfa": rp["p"], "realized_lo": rp["lo"], "realized_hi": rp["hi"],
                                     "pfa_status": status, "p_upper_exact": up, "p_lower_exact": low,
                                     "pfa_status_exact": ex, "false_alerts_per_hour": rp["p"] * 3600 / float(self.cells[case.cell]["window_s"])})
            for (nid, m), e in errs.items():
                rows_err.append({"candidate": case.cand, "cell": case.cell, "scenario": case.scenario, "normalizer": nid,
                                 "mode": m, "bias_db": float(np.mean(e)), "std_db": float(np.std(e)),
                                 "p05_db": float(np.percentile(e, 5)), "p95_db": float(np.percentile(e, 95)),
                                 "samples": int(e.size)})
        pd_rows, snr_rows = self._positives(case, norms, thresholds)
        return {"case": case, "pfa": rows_pfa, "err": rows_err, "pd": pd_rows, "snr": snr_rows,
                "seconds": time.time() - t0}

    def _signal_fn(self, cls, case, ctx, src, idx, r_onset):
        """Signal bins for window age h (0 = test window): (t, K, N) at 0 dB input SNR (true element PSD)."""
        grid, pos = ctx["grid"], ctx["pos"]
        g_true = ctx["g_true"]
        cref = self.b1.chirp_ref(self.cells[case.cell]["band"], grid) if cls == "chirp" else None
        base = self.b1.signal_unit(cls, self.cells[case.cell]["band"], grid, src, idx, pos, g_true, cref)

        def at_age(h):
            if h == 0:
                return base
            out = np.zeros_like(base)
            for j, i in enumerate(idx):
                if h > r_onset[j]:
                    continue
                tau = delays_s(pos, src["u"][i], self.c0)
                if cls == "tone":
                    f0 = src["f0"][i]
                    A = math.sqrt(2.0 * float(np.interp(f0, grid.f, g_true)))
                    out[j] = tone_bins(grid, f0, A, src["phase"][i] - 2 * np.pi * f0 * h * grid.T, tau).T
                elif cls == "broadband":
                    gs = float(np.sum(g_true) * grid.df / (grid.f_hi - grid.f_lo))
                    rng = case_rng(self.seed, "contam-bb", case.cell, int(i), int(h))
                    out[j] = broadband_bins(grid, gs, tau, rng).T
                else:
                    raise ConfigError("contamination is defined for tone and broadband classes only")
            return out
        return at_age

    def _positives(self, case, norms, thresholds):
        sc = self.scen[case.scenario]
        ctx = self._ctx(case.cand, case.cell, case.scenario)
        grid = ctx["grid"]
        dets, detector, ref, fidx, _ = self._detector(case.cell)
        H = history_needed(norms)
        chunk = max(1, self._chunk(case.cand, case.cell, H) // 2)
        modes = self.modes(case.cand)
        model = {m: {"oracle": self.stream_model(m, ctx["c_test"], ctx["sw"]),
                     "nominal": self.stream_model(m, ctx["c_nom"], ctx["sw"])} for m in modes}
        n = int(self.ev["positive_trials"])
        pd_rows, snr_rows = [], []
        cell = self.cells[case.cell]
        for cls in self.classes(case.cell, case.scenario):
            d = CLASS_DETECTOR[cls]
            src = self.b1.source_params(cls, cell["band"], float(cell["window_s"]), n, grid)
            center = self.b1.snr_center_db(cls, grid, ctx["g_nom"])
            snr = center + self.b1.offsets
            alpha = (10.0 ** (snr / 20.0)).astype(np.float32)
            stats = {}
            r_all = (case_rng(self.seed, "onset", case.cell, cls).integers(
                0, int(sc["contamination"]["max_onset_windows"]) + 1, n) if "contamination" in sc else np.zeros(n, int))
            for ci, s0 in enumerate(range(0, n, chunk)):
                t = min(chunk, n - s0)
                idx = np.arange(s0, s0 + t)
                rng = case_rng(self.seed, "pos2a", cls, case.scenario, case.cand, case.cell, ci, chunk)
                xt, xh = self.synth(case.cand, case.cell, case.scenario, t, rng, H)
                sig = self._signal_fn(cls, case, ctx, src, idx, r_all[idx])
                st0 = sig(0).astype(np.complex64)
                sh = (np.stack([sig(h + 1) for h in range(H)], axis=1).astype(np.complex64)
                      if "contamination" in sc and H else None)
                for m in modes:
                    comb = "mean" if m == "incoherent" else "max"
                    yn = self.to_streams(xt, m, ctx["sw"])
                    ys = self.to_streams(st0, m, ctx["sw"])
                    hn = self.to_streams(xh, m, ctx["sw"]) if H else None
                    hs = self.to_streams(sh, m, ctx["sw"]) if sh is not None else None
                    hp0 = np.abs(hn) ** 2 if hn is not None else None
                    # without contamination the reference windows hold noise only: estimate once, reuse for every SNR
                    pre = ({nr["id"]: apply_normalizer(nr, None, hp0, fidx) for nr in norms
                            if nr["type"] in ("tref_ca", "tref_os")} if hs is None else None)
                    for j, a in enumerate(alpha):
                        y = yn + a * ys
                        hp = np.abs(hn + a * hs) ** 2 if hs is not None else hp0
                        res = self.all_stats(y, hp, model[m], norms, [d], comb, detector, ref, fidx, pre)
                        for nid, dd in res.items():
                            if d in dd:
                                stats.setdefault((nid, m), np.empty((snr.size, n)))[j, idx] = dd[d]
            for (nid, m), v in stats.items():
                for pf in self.pfa:
                    thr = thresholds.get((case.cand, case.cell, self.alias.get(nid, nid), m, d, pf))
                    if thr is None or not math.isfinite(thr["eta"]):
                        continue
                    pdv, plo, phi, pel, peh = [], [], [], [], []
                    for j in range(snr.size):
                        x = v[j]
                        k = int(np.sum(x > thr["eta"]))
                        w = wilson_ci(k, x.size)
                        pdv.append(k / x.size)
                        plo.append(w["lo"])
                        phi.append(w["hi"])
                        pel.append(float(np.mean(x > thr["eta_hi"])))
                        peh.append(float(np.mean(x > thr["eta_lo"])))
                        pd_rows.append({"candidate": case.cand, "cell": case.cell, "scenario": case.scenario,
                                        "class": cls, "detector": d, "normalizer": nid, "mode": m, "pfa_target": pf,
                                        "threshold_method": thr["method"], "snr_db": float(snr[j]), "pd": k / x.size,
                                        "pd_binom_lo": w["lo"], "pd_binom_hi": w["hi"],
                                        "pd_at_eta_hi": pel[-1], "pd_at_eta_lo": peh[-1], "n_pos": int(x.size)})
                    for tgt in (0.5, 0.9):
                        val, status = dt.snr_at_pd(snr, np.array(pdv), tgt)
                        lo_b, _ = dt.snr_at_pd(snr, np.array(phi), tgt)
                        hi_b, _ = dt.snr_at_pd(snr, np.array(plo), tgt)
                        lo_t, _ = dt.snr_at_pd(snr, np.array(peh), tgt)
                        hi_t, _ = dt.snr_at_pd(snr, np.array(pel), tgt)
                        snr_rows.append({"candidate": case.cand, "cell": case.cell, "scenario": case.scenario,
                                         "class": cls, "detector": d, "normalizer": nid, "mode": m, "pfa_target": pf,
                                         "pd_target": tgt, "threshold_method": thr["method"], "snr_req_db": val,
                                         "status": status, "binom_lo_db": lo_b, "binom_hi_db": hi_b,
                                         "threshold_lo_db": lo_t, "threshold_hi_db": hi_t,
                                         "snr_grid_lo": float(snr[0]), "snr_grid_hi": float(snr[-1])})
        return pd_rows, snr_rows


# ---------------------------------------------------------------------------------------------- workers
_STUDY: Sim02B2AStudy | None = None
_THR: dict | None = None


def _init(cfg, thr):
    global _STUDY, _THR
    _STUDY = Sim02B2AStudy(cfg, log=lambda m: None)
    _THR = thr


def _cal_work(case):
    return _STUDY.calibrate(case)


def _eval_work(case):
    return _STUDY.evaluate(case, _THR)


def load_sim02b2a_config(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    st = Sim02B2AStudy(cfg, log=lambda m: None)
    st.cal_cases()
    st.eval_cases()
    return cfg


def derived_rows(study, snr_rows, pfa_rows=None):
    """Detection loss against ORACLE (same candidate, mode, class, scenario, Pfa, Pd) and gain against A0 (same
    normalizer). With ``pfa_rows``, every row carries the realized false-alarm status of the normalizer in the same
    scenario (a loss or gain obtained at a liberal realized Pfa is not a detection result). CONTAM has no null set of
    its own: its noise is the stationary nominal noise, so the STAT null of the same cell is used and named."""
    idx = {(r["candidate"], r["cell"], r["scenario"], r["class"], r["normalizer"], r["mode"], r["pfa_target"],
            r["pd_target"]): r for r in snr_rows}
    pidx = {(r["candidate"], r["cell"], r["scenario"], r["normalizer"], r["mode"], r["detector"], r["pfa_target"]): r
            for r in (pfa_rows or [])}

    def fa(cand, cell, sc, nid, m, cls, pf):
        src = "STAT" if "contamination" in study.scen.get(sc, {}) else sc
        r = pidx.get((cand, cell, src, study.alias.get(nid, nid), m, CLASS_DETECTOR[cls], pf))
        if not r:
            return float("nan"), "no null set", src
        return r["realized_pfa"], r.get("pfa_status_exact", r["pfa_status"]), src
    loss, gain = [], []
    for k, r in idx.items():
        cand, cell, sc, cls, nid, m, pf, pd = k
        o = idx.get((cand, cell, sc, cls, "ORACLE", m, pf, pd))
        rp, rs, src = fa(cand, cell, sc, nid, m, cls, pf)
        if o is not None and nid != "ORACLE":
            ok = r["status"] == "ok" and o["status"] == "ok"
            op, os_, _ = fa(cand, cell, sc, "ORACLE", m, cls, pf)
            loss.append({"candidate": cand, "cell": cell, "scenario": sc, "class": cls, "normalizer": nid, "mode": m,
                         "pfa_target": pf, "pd_target": pd,
                         "loss_db": r["snr_req_db"] - o["snr_req_db"] if ok else float("nan"),
                         "status": "ok" if ok else f"normalizer {r['status']}; oracle {o['status']}",
                         "threshold_method": r["threshold_method"], "realized_pfa": rp, "pfa_status": rs,
                         "oracle_realized_pfa": op, "oracle_pfa_status": os_, "pfa_source": src})
        if cand != "A0":
            a = idx.get(("A0", cell, sc, cls, nid, "single", pf, pd))
            if a is not None:
                ok = r["status"] == "ok" and a["status"] == "ok"
                ap, as_, _ = fa("A0", cell, sc, nid, "single", cls, pf)
                gain.append({"candidate": cand, "cell": cell, "scenario": sc, "class": cls, "normalizer": nid,
                             "mode": m, "pfa_target": pf, "pd_target": pd,
                             "gain_db": a["snr_req_db"] - r["snr_req_db"] if ok else float("nan"),
                             "status": "ok" if ok else f"A0 {a['status']}; candidate {r['status']}",
                             "threshold_method": r["threshold_method"], "a0_threshold_method": a["threshold_method"],
                             "realized_pfa": rp, "pfa_status": rs, "a0_realized_pfa": ap, "a0_pfa_status": as_,
                             "pfa_source": src})
    return loss, gain


def cost_benchmark(study) -> list[dict]:
    """Measured processing time per stream-bin for each normalizer (this machine; indicative only)."""
    rows = []
    rng = np.random.default_rng(1)
    t, H, S, K = 16, 18, 24, 1801
    p = rng.exponential(size=(t, S, K)).astype(np.float32)
    hp = rng.exponential(size=(t, H, S, K)).astype(np.float32)
    fidx = ne.fref_index(K, 8, 2)
    for nrm in study.norms:
        if nrm["type"] not in ADAPTIVE:
            continue
        reps, t0 = 5, time.perf_counter()
        for _ in range(reps):
            apply_normalizer(nrm, p, hp, fidx)
        dt_s = (time.perf_counter() - t0) / reps
        rows.append({"normalizer": nrm["id"], "type": nrm["type"], "ns_per_stream_bin": 1e9 * dt_s / (t * S * K),
                     "operations_per_stream_bin": ({"tref_ca": int(nrm.get("M", 0)), "tref_os": int(nrm.get("M", 0)),
                                                    "fref_ca": 2 * int(nrm.get("L", 0)),
                                                    "fref_os": 2 * int(nrm.get("L", 0))})[nrm["type"]],
                     "memory_windows": int(nrm.get("M", 0)) + int(nrm.get("guard", 0))})
    return rows


def run(config_path, output_root=None, allow_dirty: bool = False, make_figures: bool = True, repo_dir=None,
        log=print, argv=None, workers: int | None = None) -> Path:
    t_start = time.time()
    config_path = Path(config_path)
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    study = Sim02B2AStudy(cfg, log)
    cfg_sha = config_sha256(cfg)
    repo_dir = Path(repo_dir) if repo_dir else config_path.resolve().parent
    gs = git_state(repo_dir)
    if gs["git_dirty"] and not allow_dirty:
        raise DirtyTreeError("working tree has uncommitted changes to tracked files; commit them or pass --allow-dirty")
    created = utc_now()
    run_id = make_run_id(created, cfg_sha, gs["git_commit"])
    root = Path(output_root) if output_root else Path(cfg["output"]["root"])
    rd = RunDirectory(root, run_id)
    cal_cases, ev_cases = study.cal_cases(), study.eval_cases()
    log(f"SIM-02B.2-A run {run_id} -> {root / run_id} ({len(cal_cases)} calibration, {len(ev_cases)} evaluation cases)")
    T = study.timings
    n_workers = workers or int(os.environ.get("PICKET_WORKERS", os.cpu_count() or 1))
    try:
        tab = lambda n: rd.path("tables", n)  # noqa: E731
        prov = study.b1.provenance_rows()
        study.self_checks["parameters_by_provenance"] = study.b1.self_checks["parameters_by_provenance"]
        write_csv(tab("parameters_by_provenance.csv"), prov)
        # phase 1: calibration
        t = time.time()
        order = sorted(cal_cases, key=lambda c: -study.grid(c.cell).K * study.b1.geoms[c.cand].n_elements)
        cal = []
        with ProcessPoolExecutor(max_workers=n_workers, initializer=_init, initargs=(cfg, {})) as ex:
            for i, r in enumerate(ex.map(_cal_work, order, chunksize=1)):
                cal.append(r)
                log(f"  calibration [{i + 1}/{len(order)}] {r['case'].cand} {r['case'].cell}: {r['seconds']:.1f} s "
                    f"{r['extra'].get('stop', '')}")
        T["calibration_s"] = time.time() - t
        thr_rows = [x for r in cal for x in r["thresholds"]]
        thr_rows.sort(key=lambda r: (r["cell"], r["candidate"], r["normalizer"], r["mode"], r["detector"], r["pfa_target"]))
        write_csv(tab("thresholds.csv"), thr_rows)
        thresholds = {(r["candidate"], r["cell"], r["normalizer"], r["mode"], r["detector"], r["pfa_target"]): r
                      for r in thr_rows}
        # phase 2: evaluation
        t = time.time()
        order = sorted(ev_cases, key=lambda c: -study.grid(c.cell).K * study.b1.geoms[c.cand].n_elements)
        res = []
        with ProcessPoolExecutor(max_workers=n_workers, initializer=_init, initargs=(cfg, thresholds)) as ex:
            for i, r in enumerate(ex.map(_eval_work, order, chunksize=1)):
                res.append(r)
                c = r["case"]
                log(f"  evaluation [{i + 1}/{len(order)}] {c.scenario} {c.cand} {c.cell}: {r['seconds']:.1f} s")
        T["evaluation_s"] = time.time() - t
        res.sort(key=lambda r: (r["case"].scenario, r["case"].cell, r["case"].cand))
        pfa_rows = [x for r in res for x in r["pfa"]]
        err_rows = [x for r in res for x in r["err"]]
        pd_rows = [x for r in res for x in r["pd"]]
        snr_rows = [x for r in res for x in r["snr"]]
        loss_rows, gain_rows = derived_rows(study, snr_rows, pfa_rows)
        write_csv(tab("realized_pfa.csv"), pfa_rows)
        write_csv(tab("estimation_error.csv"), err_rows)
        write_csv(tab("pd_curves.csv.gz"), pd_rows, gz=True)
        write_csv(tab("snr_required.csv"), snr_rows)
        write_csv(tab("detection_loss_vs_oracle.csv"), loss_rows)
        write_csv(tab("gain_vs_a0.csv"), gain_rows)
        write_csv(tab("case_timings.csv"), [{"phase": "calibration", "candidate": r["case"].cand, "cell": r["case"].cell,
                                             "scenario": "", "seconds": r["seconds"]} for r in cal]
                  + [{"phase": "evaluation", "candidate": r["case"].cand, "cell": r["case"].cell,
                      "scenario": r["case"].scenario, "seconds": r["seconds"]} for r in res])
        # A0 CFAR loss against reference count (exact) and per-hour false-alert conversion
        cfar = []
        for cid in study.cells:
            K = study.grid(cid).K
            for M in sorted(set(study.s2.get("a0_reference_counts", [16]))):
                for pf in study.pfa:
                    cfar.append({"cell": cid, "K_bins": K, "M": M, "pfa_target": pf,
                                 "tonal_cfar_loss_db": ne.cfar_loss_db(pf, K, M)})
        write_csv(tab("cfar_loss_exact.csv"), cfar)
        write_csv(tab("false_alerts_per_hour.csv"),
                  [{"window_s": w, "pfa": pf, "false_alerts_per_hour_per_detector": pf * 3600 / w}
                   for w in (0.1, 1.0, 10.0, 60.0) for pf in (0.01, 0.001, 0.0001)])
        write_csv(tab("normalizer_cost.csv"), cost_benchmark(study))
        try:
            _self_checks(study, thr_rows, pfa_rows)
        except RuntimeError:  # keep the evidence (not a run of record), then fail visibly
            diag = Path(root).parent / "_scratch" / "failed_self_check" / run_id
            shutil.copytree(rd.path("tables"), diag / "tables")
            log(f"self-check failed; tables kept for diagnosis in {diag}")
            raise
        if make_figures:
            from .. import plotting_sim02b2a

            study.figures = plotting_sim02b2a.make_figures(study, rd.path("figures"), thr_rows, pfa_rows, pd_rows,
                                                           loss_rows, gain_rows, err_rows)
        else:
            study.figures = []
        T["total_s"] = time.time() - t_start
        sw = software_versions()
        sw.update(gs)
        record = {"run_id": run_id, "experiment_id": "SIM-02B.2-A", "title": cfg["experiment"]["title"],
                  "status": "complete", "created_utc": created.isoformat(), "completed_utc": utc_now().isoformat(),
                  "command": list(argv) if argv else sys.argv, "config_path": str(config_path),
                  "config_sha256": cfg_sha, "config_resolved": cfg, "software": sw,
                  "assumptions": cfg["experiment"].get("assumptions", []), "self_checks": study.self_checks,
                  "warnings": study.warnings, "timings_s": T, "figures": study.figures, "workers": n_workers}
        lines = [f"# SIM-02B.2-A run {run_id}", "", f"* Config sha256 `{cfg_sha[:16]}...`; code `{gs.get('git_commit')}`"
                 f" (dirty: {gs.get('git_dirty')})", f"* Calibration cases {len(cal_cases)}, evaluation cases "
                 f"{len(ev_cases)}; workers {n_workers}", "", "## Self-checks", ""]
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


def _self_checks(study, thr_rows, pfa_rows):
    """Calibration consistency under the nominal design (STAT) with exact predictive laws; method agreement."""
    stat = [r for r in pfa_rows if r["scenario"] == "STAT"]
    ps = []
    for r in stat:
        thr = next((t for t in thr_rows if (t["candidate"], t["cell"], t["normalizer"], t["mode"], t["detector"],
                                             t["pfa_target"]) == (r["candidate"], r["cell"], r["normalizer"], r["mode"],
                                                                  r["detector"], r["pfa_target"])), None)
        if thr is None or r["n_eval"] * r["pfa_target"] < 1:
            continue
        meth = "empirical" if thr["method"] in ("empirical", "fast null simulation") else "exact"
        n_cal = int(thr["n"]) if meth == "empirical" else 0
        ps.append(dt.calibration_pvalue(meth, int(r["realized_k"]), int(r["n_eval"]), float(r["pfa_target"]), n_cal)[0])
    if ps:
        ps = np.array(ps)
        study.self_checks["stat_calibration_rows"] = int(ps.size)
        study.self_checks["stat_calibration_fraction_p_below_0p05"] = float(np.mean(ps < 0.05))
        study.self_checks["stat_calibration_min_p_times_rows"] = float(min(1.0, ps.min() * ps.size))
        if ps.min() * ps.size < 1e-3:
            raise RuntimeError("self-check failed: STAT false-alarm calibration inconsistent (Bonferroni p < 1e-3)")
    agree = []
    for r in thr_rows:  # ORACLE only: NOMINAL is the same statistic under the nominal design
        if r["normalizer"] != "ORACLE":
            continue
        if "empirical_eta" in r and isinstance(r.get("empirical_eta"), float) and math.isfinite(r["empirical_eta"]):
            if r["empirical_eta_lo"] <= r["eta"] <= r["empirical_eta_hi"]:
                agree.append(1)
            else:
                agree.append(0)
    if agree:
        study.self_checks["oracle_exact_or_cmc_within_empirical_interval"] = (f"{sum(agree)} of {len(agree)} distinct "
                                                                              "statistics")
