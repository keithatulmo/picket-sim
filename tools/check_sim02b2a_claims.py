"""Check every quantitative claim in the SIM-02B.2-A report, transmittal and reviewer message.

Same contract as tools/check_sim02b1_claims.py (CLAUDE.md, cycle close-out step 2): each check recomputes a quoted
figure from the run-of-record tables (or with the study code, for statements that are not table rows) at the
precision written, and the documents must contain the quoted text. Exit status 1 if any check fails.

    python tools/check_sim02b2a_claims.py results/sim02b2a/<run_id>
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import math
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from picket_sim import noise_estimation as ne  # noqa: E402
from picket_sim.detection import calibration_pvalue  # noqa: E402
from picket_sim.stats import wilson_ci  # noqa: E402

RESULTS: list[tuple[bool, str, str, str]] = []
B1_RUN = REPO / "results/sim02b1/20261108T125126Z_1c70e065_8dbe019"
ADAPT = ("TREF-CA16", "TREF-OS16", "FREF-CA8", "FREF-OS8")
TREF = ("TREF-CA16", "TREF-OS16")
FREF = ("FREF-CA8", "FREF-OS8")
DET = {"tone": "tonal", "harmonic": "harmonic", "broadband": "energy", "chirp": "mf"}


def check(label, quoted, computed, ok=None):
    if ok is None:
        ok = quoted == computed
    RESULTS.append((bool(ok), label, str(quoted), str(computed)))


def f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def rd(x, n=2):
    return round(float(x) + 0.0, n)


def rg(vals, n=2):
    v = [float(x) for x in vals if math.isfinite(float(x))]
    return (rd(min(v), n), rd(max(v), n))


def _tool(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class T:
    def __init__(self, run: Path):
        self.run = run
        t = run / "tables"
        L = lambda n: list(csv.DictReader(open(t / n)))  # noqa: E731
        self.thr, self.pfa, self.err = L("thresholds.csv"), L("realized_pfa.csv"), L("estimation_error.csv")
        self.snr, self.loss, self.gain = L("snr_required.csv"), L("detection_loss_vs_oracle.csv"), L("gain_vs_a0.csv")
        self.cfar, self.cost, self.prov = L("cfar_loss_exact.csv"), L("normalizer_cost.csv"), L("parameters_by_provenance.csv")
        self.fah = L("false_alerts_per_hour.csv")
        with gzip.open(t / "pd_curves.csv.gz", "rt") as fh:
            self.pd = list(csv.DictReader(fh))
        self.rec = json.loads((run / "record.json").read_text())
        self.tix = {(r["candidate"], r["cell"], r["normalizer"], r["mode"], r["detector"], r["pfa_target"]): r
                    for r in self.thr}

    def tails(self, r):
        t = self.tix[(r["candidate"], r["cell"], r["normalizer"], r["mode"], r["detector"], r["pfa_target"])]
        meth = "empirical" if t["method"] in ("empirical", "fast null simulation") else "exact"
        k, n, p = int(r["realized_k"]), int(r["n_eval"]), f(r["pfa_target"])
        nc = int(t["n"]) if meth == "empirical" else 0
        up = calibration_pvalue(meth, k, n, p, nc)[1]
        lo = 1.0 - calibration_pvalue(meth, k + 1, n, p, nc)[1] if k < n else 1.0
        return up, lo

    def flagged(self, r):
        up, lo = self.tails(r)
        return up < 1e-3 or lo < 1e-3

    def losses(self, cell="C1", sc="STAT", cls="tone", norms=("TREF-CA16",), modes=None, cands=None, pf=1e-3, pd=0.5):
        return [r for r in self.loss if r["cell"] == cell and r["scenario"] == sc and r["class"] == cls
                and r["normalizer"] in norms and f(r["pfa_target"]) == pf and f(r["pd_target"]) == pd
                and (modes is None or r["mode"] in modes) and (cands is None or r["candidate"] in cands)]

    def g(self, cell, cls, cand, mode, norm, sc="STAT"):
        r = [x for x in self.gain if x["cell"] == cell and x["scenario"] == sc and x["class"] == cls
             and x["candidate"] == cand and x["mode"] == mode and x["normalizer"] == norm
             and f(x["pfa_target"]) == 1e-3 and f(x["pd_target"]) == 0.5]
        return f(r[0]["gain_db"]) if r else float("nan")

    def sr(self, sc, cls, n, c, m, cell="C1"):
        r = [x for x in self.snr if x["scenario"] == sc and x["cell"] == cell and x["class"] == cls
             and x["normalizer"] == n and x["candidate"] == c and x["mode"] == m and f(x["pfa_target"]) == 1e-3
             and f(x["pd_target"]) == 0.5]
        return f(r[0]["snr_req_db"]) if r else float("nan")


CM = [("A0", "single")] + [(c, m) for c in ("A1", "P8-C", "A4") for m in ("beam_search", "incoherent")]
Q: dict = {}  # quoted strings built from computed values, then required in the documents


def claims(t: T):
    rec = t.rec
    tm = rec["timings_s"]
    check("run status, workers, clean commit", ("complete", 4, "73fbe35", False),
          (rec["status"], rec["workers"], rec["software"]["git_commit"][:7], rec["software"]["git_dirty"]))
    check("run total time (s)", 8172, round(tm["total_s"]))
    check("config sha256 prefix", "27abcd691b9aeefc", rec["config_sha256"][:16])
    ncal = len({(r["candidate"], r["cell"]) for r in t.thr})
    neval = len({(r["candidate"], r["cell"], r["scenario"]) for r in t.snr})
    check("calibration and evaluation cases", (12, 48), (ncal, neval))
    pv = {k: sum(1 for r in t.prov if r["provenance"] == k) for k in ("published", "measured", "assumed")}
    check("provenance published, measured, assumed", (4, 0, 27), (pv["published"], pv["measured"], pv["assumed"]))

    # ---- configuration values quoted in the methods
    s2 = rec["config_resolved"]["sim02b2a"]
    cal, ev = s2["calibration"], s2["evaluation"]
    sc = {x["id"]: x for x in s2["scenarios"]}
    nm = {n["id"]: n for n in s2["normalizers"] + s2["contamination_normalizers"]}
    check("calibration settings", (100000, 2000, 20000, 0.25),
          (cal["a0_fast_samples"], cal["batch"], max(cal["max_trials"].values()), cal["tolerance_db"]))
    check("evaluation counts", (10000, 4000, 400),
          (ev["null_trials"]["STAT"], ev["null_trials"]["default"], ev["positive_trials"]))
    check("interference and contamination settings", (0.25, 10.0, 24),
          (sc["INTERF"]["interference"]["probability"], sc["INTERF"]["interference"]["level_db"],
           sc["CONTAM"]["contamination"]["max_onset_windows"]))
    check("normalizer settings", (16, 2, 12, 8, 2, 8),
          (nm["TREF-CA16"]["M"], nm["TREF-CA16"]["guard"], nm["TREF-OS16"]["r"], nm["FREF-CA8"]["L"],
           nm["FREF-CA8"]["G"], nm["TREF-CA16-G8"]["guard"]))
    check("A0 extra reference counts", [4, 8, 16, 32, 64], s2["a0_reference_counts"])
    step = float(rec["config_resolved"]["processing"]["beam_search_az_step_deg"])
    check("C1 bins and search beams", (1801, 24),
          (int([r for r in t.cfar if r["cell"] == "C1"][0]["K_bins"]), round(360 / step)))
    check("run time (h)", 2.3, rd(tm["total_s"] / 3600, 1))
    ct = list(csv.DictReader(open(t.run / "tables" / "case_timings.csv")))
    hrs = [f(r["seconds"]) / 20000 * 100000 / 3600 for r in ct if r["phase"] == "calibration"
           and r["cell"] == "C1" and r["candidate"] != "A0"]
    check("core-hours per array in C1 for 100,000 calibration trials", (2.5, 3.0), rg(hrs, 1))

    # ---- finding 1: STAT calibration (independent recomputation with the exact predictive laws)
    st = [r for r in t.pfa if r["scenario"] == "STAT" and int(r["n_eval"]) * f(r["pfa_target"]) >= 1]
    tl = [t.tails(r) for r in st]
    p2 = [min(1.0, 2 * min(u, lo)) for u, lo in tl]
    check("STAT rows", 1170, len(st))
    check("STAT share of two-sided p < 0.05 (%)", 4.3, rd(100 * sum(x < 0.05 for x in p2) / len(p2), 1))
    check("STAT rows with a tail below 0.001", 0, sum(1 for u, lo in tl if u < 1e-3 or lo < 1e-3))
    check("STAT Bonferroni smallest p (capped)", 1.0, rd(min(1.0, min(p2) * len(p2)), 2))
    check("record self-check agrees", 1.0, rec["self_checks"]["stat_calibration_min_p_times_rows"])
    os_rows = [(p, u) for r, p, (u, _) in zip(st, p2, tl) if r["normalizer"] == "TREF-OS16"]
    check("TREF-OS16 share p < 0.05 (%) of rows", (8.3, 180),
          (rd(100 * sum(p < 0.05 for p, _ in os_rows) / len(os_rows), 1), len(os_rows)))
    check("TREF-OS16 smallest upper-tail p", 0.0018, rd(min(u for _, u in os_rows), 4))
    ag = [r for r in t.thr if r["normalizer"] == "ORACLE" and r.get("empirical_eta") not in ("", None)]
    ins = [f(r["empirical_eta_lo"]) <= f(r["eta"]) <= f(r["empirical_eta_hi"]) for r in ag]
    check("ORACLE tail methods inside empirical interval", (33, 36), (sum(ins), len(ins)))
    check("largest tail-method difference (dB)", 0.206,
          rd(max(abs(10 * math.log10(f(r["eta"]) / f(r["empirical_eta"]))) for r in ag), 3))
    for meth, q in (("conditional Monte Carlo", (17, 18)), ("exact quadratic form", (16, 18))):
        rr = [r for r in ag if r["method"] == meth]
        check(f"{meth} inside", q, (sum(f(r["empirical_eta_lo"]) <= f(r["eta"]) <= f(r["empirical_eta_hi"])
                                        for r in rr), len(rr)))
    cnt = {m: sum(1 for r in t.thr if r["method"] == m) for m in {r["method"] for r in t.thr}}
    check("threshold method counts", {"exact": 90, "fast null simulation": 252, "exact quadratic form": 54,
                                      "conditional Monte Carlo": 54, "empirical": 720, "not estimated": 360}, cnt)
    ne_rows = [r for r in t.thr if r["method"] == "not estimated"]
    check("not-estimated rows: arrays at 1e-4; adaptive, ORACLE/NOMINAL non-tonal", (True, 252, 108),
          (all(r["candidate"] != "A0" and f(r["pfa_target"]) == 1e-4 for r in ne_rows),
           sum(r["normalizer"] in ADAPT for r in ne_rows),
           sum(r["normalizer"] in ("ORACLE", "NOMINAL") and r["detector"] != "tonal" for r in ne_rows)))
    meds, mx = [], []
    for c in ("A1", "P8-C", "A4"):
        for cell in ("C1", "C2", "C3"):
            w = sorted(f(r["eta_interval_db"]) for r in t.thr if r["candidate"] == c and r["cell"] == cell
                       and r["normalizer"] in ADAPT and f(r["pfa_target"]) == 1e-3)
            meds.append(w[len(w) // 2])
            mx.append(w[-1])
    check("adaptive array interval medians (dB)", (0.26, 0.40), rg(meds))
    check("adaptive array interval max (dB)", 0.74, rd(max(mx)))
    check("every array case ran to the cap", True,
          all(r["stop"] == "cap" for r in t.thr if r["candidate"] != "A0" and r["stop"]))
    cmc = [f(r["eta_interval_db"]) for r in t.thr if r["method"] == "conditional Monte Carlo"]
    check("CMC 95 % precision (dB)", (0.0007, 0.007), (rd(min(cmc), 4), rd(max(cmc), 3)))

    # ---- finding 2: cost of estimation
    v = lambda **k: [f(r["loss_db"]) for r in t.losses(**k)]  # noqa: E731
    check("A0 tone TREF-CA16", 2.10, rd(v(modes=("single",))[0]))
    check("beam tone TREF-CA16", (2.51, 2.63), rg(v(modes=("beam_search",))))
    check("incoherent tone TREF-CA16", (1.16, 1.74), rg(v(modes=("incoherent",))))
    check("broadband TREF-CA16 all", (0.11, 0.47), rg(v(cls="broadband")))
    check("A0 tone FREF-CA8", 2.27, rd(v(norms=("FREF-CA8",), modes=("single",))[0]))
    check("beam tone FREF-CA8", (2.63, 2.80), rg(v(norms=("FREF-CA8",), modes=("beam_search",))))
    check("TREF-OS16 A0 and beam", (3.02, 3.47), rg(v(norms=("TREF-OS16",), modes=("single", "beam_search"))))
    check("FREF-OS8 A0 and beam", (3.35, 3.94), rg(v(norms=("FREF-OS8",), modes=("single", "beam_search"))))
    check("Pd 0.9 tone TREF-CA16", (1.08, 2.91), rg(v(pd=0.9)))
    check("Pd 0.9 tone FREF-CA8", (1.59, 3.16), rg(v(norms=("FREF-CA8",), pd=0.9)))
    check("A0 tone TREF-CA16 at Pfa 1e-2, 1e-3, 1e-4", (1.78, 2.10, 2.39),
          tuple(rd(v(modes=("single",), pf=p)[0]) for p in (1e-2, 1e-3, 1e-4)))
    diffs, c1 = [], []
    for r in t.cfar:
        M = int(r["M"])
        if f(r["pfa_target"]) != 1e-3:
            continue
        ex = f(r["tonal_cfar_loss_db"])
        # independent recomputation of the exact law
        check(f"exact CFAR loss {r['cell']} M={M}", rd(ex, 6), rd(ne.cfar_loss_db(1e-3, int(r["K_bins"]), M), 6))
        if r["cell"] == "C1":
            c1.append((M, rd(ex)))
        if M >= 8:
            nid = "TREF-CA16" if M == 16 else f"TREF-CA{M}-A0"
            m = t.losses(cell=r["cell"], norms=(nid,), modes=("single",))
            diffs.append(abs(f(m[0]["loss_db"]) - ex))
    check("measured vs exact CFAR loss, M 8 to 64, max diff (dB)", 0.13, rd(max(diffs)))
    check("C1 exact losses M=8,16,32,64", (4.48, 2.10, 1.01, 0.50), tuple(x for M, x in sorted(c1) if M >= 8))
    check("C1 exact loss M=4", 9.95, dict(c1)[4])
    a0m4 = t.losses(norms=("TREF-CA4-A0",), modes=("single",))
    check("M=4 measured is censored", True, a0m4[0]["status"] != "ok")

    # ---- finding 3: gains
    def gd(cells, modes, classes):
        out = []
        for cell in cells:
            for m in modes:
                for cl in classes:
                    for c in ("A1", "P8-C", "A4"):
                        o = t.g(cell, cl, c, m, "ORACLE")
                        for n in ADAPT:
                            a = t.g(cell, cl, c, m, n)
                            if math.isfinite(a) and math.isfinite(o):
                                out.append(a - o)
        return out
    check("beam tonal/harmonic gain change C1,C3", (-0.94, -0.19), rg(gd(("C1", "C3"), ("beam_search",), ("tone", "harmonic"))))
    check("beam broadband/chirp gain change C1,C3", (-0.33, 0.18), rg(gd(("C1", "C3"), ("beam_search",), ("broadband", "chirp"))))
    check("incoherent tone gain change C1,C3", (0.13, 1.80), rg(gd(("C1", "C3"), ("incoherent",), ("tone",))))
    check("P8-C beam tone C1 ORACLE gain", 3.42, rd(t.g("C1", "tone", "P8-C", "beam_search", "ORACLE")))
    check("P8-C beam tone C1 adaptive", (2.83, 3.05), rg([t.g("C1", "tone", "P8-C", "beam_search", n) for n in ADAPT]))
    check("P8-C beam broadband C1 ORACLE gain", 4.30, rd(t.g("C1", "broadband", "P8-C", "beam_search", "ORACLE")))
    check("P8-C beam broadband C1 adaptive", (4.06, 4.12),
          rg([t.g("C1", "broadband", "P8-C", "beam_search", n) for n in TREF]))
    c2 = [f(r["gain_db"]) for r in t.gain if r["cell"] == "C2" and r["scenario"] == "STAT" and r["normalizer"] in ADAPT
          and f(r["pfa_target"]) == 1e-3 and f(r["pd_target"]) == 0.5]
    check("C2 adaptive gains", (-0.26, 0.72), rg(c2))

    def ranking_same(mode):
        same = True
        for cell in ("C1", "C3"):
            for cl in ("tone", "harmonic", "broadband", "chirp"):
                o = sorted(("A1", "P8-C", "A4"), key=lambda c: t.g(cell, cl, c, mode, "ORACLE"))
                for n in ADAPT:
                    gs = {c: t.g(cell, cl, c, mode, n) for c in ("A1", "P8-C", "A4")}
                    if all(math.isfinite(x) for x in gs.values()):
                        same &= sorted(gs, key=gs.get) == o
        return same
    check("beam-search ranking unchanged C1, C3", True, ranking_same("beam_search"))
    check("incoherent ranking not always unchanged", False, ranking_same("incoherent"))

    # ---- finding 4: robustness
    def ratio(sc, norms, det, pf, cells=("C1",)):
        return [f(r["realized_pfa"]) / pf for r in t.pfa if r["scenario"] == sc and r["cell"] in cells
                and r["normalizer"] in norms and r["detector"] == det and f(r["pfa_target"]) == pf]
    check("STEP+1 TREF tonal ratio at 1e-3", (3.50, 11.25), rg(ratio("STEP+1", TREF, "tonal", 1e-3)))
    check("STEP+1 energy realized Pfa (TREF, NOMINAL)", (1.0, 1.0),
          rg([x * 1e-3 for x in ratio("STEP+1", TREF + ("NOMINAL",), "energy", 1e-3)]))
    check("STEP+3 TREF tonal ratio at 1e-3", (106, 355), rg(ratio("STEP+3", TREF, "tonal", 1e-3), 0))
    fsteps = [r for r in t.pfa if r["scenario"] in ("STEP+1", "STEP+3") and r["normalizer"] in FREF]
    check("FREF flagged rows in step scenarios (all cells, Pfa)", (0, True), (sum(t.flagged(r) for r in fsteps), len(fsteps) > 100))
    eb = lambda sc, n: [f(r["bias_db"]) for r in t.err if r["scenario"] == sc and r["normalizer"] == n]  # noqa: E731
    check("INTERF bias TREF-CA16", (4.55, 5.02), rg(eb("INTERF", "TREF-CA16")))
    check("INTERF bias TREF-OS16", (3.15, 3.84), rg(eb("INTERF", "TREF-OS16")))
    it = [r for r in t.pfa if r["scenario"] == "INTERF" and r["normalizer"] in TREF and f(r["pfa_target"]) == 1e-2]
    check("INTERF TREF ratio at 1e-2", (0.0, 0.17), rg([f(r["realized_pfa"]) / 1e-2 for r in it]))
    check("INTERF TREF rows at 1e-2 all flagged conservative", True,
          all(t.tails(r)[1] < 1e-3 for r in it) and len(it) == 56)

    def extra(sc, norms, cls="tone"):
        st = {(r["candidate"], r["mode"], r["normalizer"]): f(r["loss_db"]) for r in t.losses(norms=norms, cls=cls)}
        return [f(r["loss_db"]) - st[(r["candidate"], r["mode"], r["normalizer"])]
                for r in t.losses(sc=sc, norms=norms, cls=cls) if r["status"] == "ok"]
    check("INTERF extra tonal loss TREF-CA16", (4.52, 5.42), rg(extra("INTERF", ("TREF-CA16",))))
    check("INTERF extra tonal loss TREF-OS16", (1.95, 2.83), rg(extra("INTERF", ("TREF-OS16",))))
    bb = t.losses(sc="INTERF", cls="broadband", norms=TREF)
    check("INTERF broadband TREF censored", (12, 14), (sum(1 for r in bb if r["status"] != "ok"), len(bb)))
    check("INTERF FREF tonal relative to STAT", (-0.18, 0.26), rg(extra("INTERF", FREF)))
    sup = _tool("sim02b2a_supplement")
    q, M, tol = 0.25, 16, 4
    pm = 1.0 - sum(math.comb(M, k) * q ** k * (1 - q) ** (M - k) for k in range(tol + 1))
    check("P(more than 4 of 16 disturbed) (%)", 37, round(100 * pm))
    # contamination
    tops = {}
    for n in ("TREF-CA16", "TREF-CA16-G8", "TREF-OS16"):
        rows = [r for r in t.pd if r["scenario"] == "CONTAM" and r["class"] == "tone" and r["normalizer"] == n
                and f(r["pfa_target"]) == 1e-3]
        hi = max(f(r["snr_db"]) for r in rows)
        tops[n] = [f(r["pd"]) for r in rows if f(r["snr_db"]) == hi]
    check("CONTAM tone top Pd guard 2", (0.11, 0.13), rg(tops["TREF-CA16"]))
    check("CONTAM tone top Pd guard 8", (0.38, 0.39), rg(tops["TREF-CA16-G8"]))
    check("CONTAM tone top Pd order statistic", (0.225, 0.2825), rg(tops["TREF-OS16"], 4))
    from picket_sim.stats import case_rng
    import numpy as np
    cfg = t.rec["config_resolved"]
    r_on = case_rng(int(cfg["seed"]), "onset", "C1", "tone").integers(0, 25, int(cfg["sim02b2a"]["evaluation"]["positive_trials"]))
    check("clean fractions g2, g8, OS", (0.11, 0.38, 0.285),
          (rd(np.mean(r_on <= 2)), rd(np.mean(r_on <= 8)), rd(np.mean(np.clip(np.minimum(r_on, 18) - 2, 0, None) <= 4), 3)))
    ct = [r for r in t.snr if r["scenario"] == "CONTAM" and r["class"] == "tone" and r["normalizer"] in TREF + ("TREF-CA16-G8",)
          and f(r["pd_target"]) == 0.5]
    check("TREF never reaches Pd 0.5 on contaminated tones", True, all(r["status"] != "ok" for r in ct) and len(ct) > 0)
    fr = [t.sr("CONTAM", "tone", n, c, m) - t.sr("STAT", "tone", n, c, m) for n in FREF for c, m in CM]
    check("CONTAM FREF tone relative to STAT", (-0.26, 0.46), rg(fr))
    bt = [t.sr("CONTAM", "broadband", n, c, m) - t.sr("STAT", "broadband", n, c, m) for n in TREF for c, m in CM]
    check("CONTAM broadband TREF relative to STAT", (4.59, 5.65), rg(bt))
    b8 = [t.sr("CONTAM", "broadband", "TREF-CA16-G8", c, m) - t.sr("STAT", "broadband", "TREF-CA16", c, m) for c, m in CM]
    check("CONTAM broadband guard 8 relative to STAT", (1.59, 1.95), rg(b8))
    # shape
    sh = [r for r in t.pfa if r["scenario"] in ("SHAPE-HI", "SHAPE-LO") and r["normalizer"] in ADAPT]
    check("SHAPE adaptive flagged rows", 0, sum(t.flagged(r) for r in sh))
    check("SHAPE-HI NOMINAL realized Pfa", (1.0, 1.0),
          rg([f(r["realized_pfa"]) for r in t.pfa if r["scenario"] == "SHAPE-HI" and r["normalizer"] == "NOMINAL"]))
    check("SHAPE-LO NOMINAL tone loss", (5.05, 5.29), rg(v(sc="SHAPE-LO", norms=("NOMINAL",))))

    # ---- finding 5: coherence
    coh = [r for r in t.pfa if r["scenario"] == "COH" and r["mode"] == "incoherent" and f(r["pfa_target"]) == 1e-2]
    check("COH incoherent zero-count rows at 1e-2", (121, 132, {"4000"}),
          (sum(int(r["realized_k"]) == 0 for r in coh), len(coh), {r["n_eval"] for r in coh}))
    check("ORACLE among the zero-count rows", True, any(r["normalizer"] == "ORACLE" and int(r["realized_k"]) == 0 for r in coh))
    bs = [r for r in t.pfa if r["scenario"] == "COH" and r["mode"] == "beam_search" and f(r["pfa_target"]) == 1e-2
          and r["normalizer"] != "NOMINAL"]
    top = max(bs, key=lambda r: f(r["realized_pfa"]))
    check("COH beam-search max ratio at 1e-2 (candidate, cell)", (2.93, "A4", "C2"),
          (rd(f(top["realized_pfa"]) / 1e-2), top["candidate"], top["cell"]))

    # ---- finding 6: per hour (table and arithmetic)
    fa = {(f(r["window_s"]), f(r["pfa"])): f(r["false_alerts_per_hour_per_detector"]) for r in t.fah}
    check("false alerts per hour", (3.6, 36.0, 0.36), (rd(fa[(1.0, 1e-3)], 6), rd(fa[(0.1, 1e-3)], 6), rd(fa[(1.0, 1e-4)], 6)))

    # ---- finding 7: regression (recomputed by the tool into a temporary file)
    reg = _tool("sim02b2a_b1_regression")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            reg.main([str(t.run), "--b1", str(B1_RUN), "--out", str(Path(d) / "r")])
        rows = list(csv.DictReader(open(Path(d) / "r.csv")))
    vv = lambda s: sum(1 for r in rows if r["verdict"] == s)  # noqa: E731
    est = [r for r in rows if r["verdict"] in ("consistent", "marginal", "inconsistent")]
    check("regression consistent, marginal, inconsistent of estimate rows", (343, 5, 0, 348),
          (vv("consistent"), vv("marginal"), vv("inconsistent"), len(est)))
    bd = [r for r in rows if r["verdict"].startswith("bound")]
    ex = sorted(-f(r["diff_db"]) for r in bd)
    check("bounds held, max and median excess (dB)", (48, 48, 3.53, 0.65),
          (vv("bound holds"), len(bd), rd(ex[-1]), rd(ex[len(ex) // 2])))

    two = sum(1 for r in bd if abs(f(r["diff_db"])) > 1.5 * f(r["combined_half_width_db"]))
    check("bound rows that a two-sided test would call inconsistent", 21, two)
    check("record self-check as written (ERRATA)", "66 of 72",
          rec["self_checks"]["oracle_exact_or_cmc_within_empirical_interval"])

    # ---- uncertainty widths
    bw, tw = [], []
    for r in t.snr:
        if r["scenario"] == "STAT" and r["cell"] == "C1" and f(r["pfa_target"]) == 1e-3 and f(r["pd_target"]) == 0.5 \
                and r["status"] == "ok":
            b = f(r["binom_hi_db"]) - f(r["binom_lo_db"])
            w = f(r["threshold_hi_db"]) - f(r["threshold_lo_db"])
            if math.isfinite(b):
                bw.append(b)
            if math.isfinite(w) and r["threshold_method"] == "empirical":
                tw.append(w)
    check("binomial SNR interval width median, max (dB)", (0.43, 1.07), (rd(statistics.median(bw)), rd(max(bw))))
    check("threshold SNR interval width median, max (dB)", (0.34, 0.93), (rd(statistics.median(tw)), rd(max(tw))))

    # ---- estimator laws (study code: supplement functions) and measured agreement
    ca = sup.ca_law_db(16)
    os_ = sup.os_law_db(16, 12)
    check("cell-averaging law bias, std (dB)", (-0.137, 1.103), (rd(ca[0], 3), rd(ca[1], 3)))
    check("order-statistic law bias, std (dB)", (0.923, 1.359), (rd(os_[0], 3), rd(os_[1], 3)))
    meas = [f(r["bias_db"]) for r in t.err if r["normalizer"] == "TREF-CA16" and r["scenario"] in
            ("STAT", "SHAPE-HI", "SHAPE-LO", "COH")]
    check("measured TREF-CA16 bias within 0.02 dB of law", True, max(abs(x - ca[0]) for x in meas) < 0.02)

    # ---- cost
    cs = {r["normalizer"]: r for r in t.cost}
    check("ns per stream-bin", (7.33, 24.70, 109.92, 254.71),
          tuple(rd(f(cs[n]["ns_per_stream_bin"])) for n in ("TREF-CA16", "FREF-CA8", "TREF-OS16", "FREF-OS8")))
    check("operations 16, history 18 (time) and 0 (frequency)", (16, 18, 0),
          ({int(r["operations_per_stream_bin"]) for r in t.cost}.pop(), int(cs["TREF-CA16"]["memory_windows"]),
           int(cs["FREF-CA8"]["memory_windows"])))
    check("order statistic at least 10 times the average", True,
          f(cs["TREF-OS16"]["ns_per_stream_bin"]) / f(cs["TREF-CA16"]["ns_per_stream_bin"]) >= 10
          and f(cs["FREF-OS8"]["ns_per_stream_bin"]) / f(cs["FREF-CA8"]["ns_per_stream_bin"]) >= 10)

    # ---- errata statement: Wilson flag at n Pfa = 1
    lo3 = wilson_ci(3, 10000)["lo"]
    lo2 = wilson_ci(2, 10000)["lo"]
    p3 = 1.0 - sum(math.comb(10000, k) * 1e-4 ** k * (1 - 1e-4) ** (10000 - k) for k in range(3))
    check("Wilson flags 3 (not 2) of 10,000 at Pfa 1e-4; probability", (True, 0.08), (lo3 > 1e-4 >= lo2, rd(p3)))

    # ---- tests of this increment
    import subprocess
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
                         + [str(REPO / "tests" / n) for n in ("test_sim02b2a_models.py", "test_sim02b2a_pipeline.py",
                                                              "test_sim02b2a_tools.py")],
                         capture_output=True, text=True, cwd=REPO).stdout
    m = re.search(r"(\d+) tests? collected", out)
    check("increment tests (collected)", 35, int(m.group(1)) if m else None)


def text_checks(docs: dict, required: dict, forbidden: list):
    text = {k: " ".join(p.read_text(encoding="utf-8").split()) for k, p in docs.items() if p.exists()}
    for k, phrases in required.items():
        if k not in text:
            check(f"{k}: document present", True, False)
            continue
        missing = [ph for ph in phrases if ph not in text[k]]
        check(f"{k}: quotes every checked value", [], missing)
        unquoted = re.sub(r'"[^"]*"', "", text[k])
        bad = [ph for ph in forbidden if ph in unquoted]
        check(f"{k}: contains no forbidden phrase or em dash", [], bad)


REQUIRED: dict = {
    "report": [
        "12 calibration and 48 evaluation cases, 8,172 s on 4 worker processes", "git `73fbe35` (clean tree)",
        "sha256 `27abcd691b9aeefc...`", "4 published records, 0 measured, 27 assumed",
        "Across 1,170 evaluation rows", "gives 4.3 % of two-sided p-values below 0.05 and no tail probability below 0.001",
        "(Bonferroni-adjusted smallest p-value 1.0)", "in 33 of 36 statistics, the largest difference 0.206 dB",
        "costs tonal detection 2.10 dB on A0 and 2.51 to 2.63 dB with beam search",
        "broadband energy detection only 0.11 to 0.47 dB", "(2.27 dB on A0, 2.63 to 2.80 dB with beam search)",
        "3.02 to 3.47 dB from reference windows and 3.35 to 3.94 dB from reference bins",
        "agree within 0.13 dB in all three cells", "(C1: 4.48, 2.10, 1.01 and 0.50 dB for 8, 16, 32 and 64 windows)",
        "(A0 tone: 1.78, 2.10 and 2.39 dB at Pfa 1e-2, 1e-3 and 1e-4)", "fall by 0.19 to 0.94 dB",
        "change by -0.33 to 0.18 dB (C1 and C3)", "keeps 2.83 to 3.05 dB of its 3.42 dB tonal gain",
        "4.06 to 4.12 dB of its 4.30 dB broadband gain", "(tones: 0.13 to 1.80 dB more)",
        "every adaptive gain lies between -0.26 and 0.72 dB", "by 3.50 to 11.25 at Pfa 1e-3",
        "drives the energy detector to Pfa 1.0", "multiplies the tonal rate by 106 to 355",
        "by 4.55 to 5.02 dB on average (cell averaging) and 3.15 to 3.84 dB (order statistic)",
        "fall to 0 to 0.17 of the target at Pfa 1e-2 (every row flagged conservative)",
        "loses a further 4.52 to 5.42 dB (cell averaging) or 1.95 to 2.83 dB", "fails to reach Pd 0.5 in 12 of 14 rows",
        "(-0.18 to 0.26 dB relative to stationary noise)", "0.11 to 0.13 with a 2-window guard and 0.38 to 0.39 with an",
        "(0.11 and 0.38 for the run's onset draws)", "unaffected for tones (-0.26 to 0.46 dB)",
        "need 4.59 to 5.65 dB more SNR", "reduces this to 1.59 to 1.95 dB", "costs 5.05 to 5.29 dB for tones",
        "121 of 132 rows at Pfa 1e-2 produce no false alarm in 4,000 trials", "up to 2.93 times (A4, 20 to 200 Hz)",
        "252 adaptive rows and 108 ORACLE and NOMINAL rows",
        "at Pfa 1e-3 raises 3.6 false alerts per hour (36 with 0.1 s windows; 0.36 at Pfa 1e-4)",
        "In 343 of 348 comparable rows", "(5 marginal, none inconsistent)",
        "the bounds held in 48 of 48 rows and overstated the SNR required by up to 3.53 dB (median 0.65 dB)",
        "(95 % precision 0.0007 to 0.007 dB)", "medians of 0.26 to 0.40 dB per candidate and cell (maximum 0.74 dB)",
        "median width of 0.43 dB (maximum 1.07 dB)", "median width of 0.34 dB (maximum 0.93 dB)",
        "exact 90 rows, fast null simulation 252, exact quadratic form 54, conditional Monte Carlo 54, sequential empirical 720, not estimated 360 (arrays at Pfa 1e-4:",
        "TREF-OS16 with 8.3 % of 180 correlated rows (smallest upper-tail p-value 0.0018)", "(1.16 to 1.74 dB for tones)",
        "1.08 to 2.91 dB (TREF-CA16) and 1.59 to 3.16 dB (FREF-CA8)",
        "-0.137 dB and 1.103 dB; 12th of 16 +0.923 dB and 1.359 dB", "(exact 9.95 dB)",
        "occur in 37 % of trials", "its ceiling is the clean fraction 0.285; the measured Pd at the top of the grid is 0.225 to 0.2825",
        "7.33 ns (TREF-CA16), 24.70 ns (FREF-CA8), 109.92 ns (TREF-OS16) and 254.71 ns (FREF-OS8), all with 16 operations",
        "hold 18 windows of history", "35 tests cover this increment", "(100,000 samples;", "batches of 2,000",
        "within 0.25 dB or at 20,000 trials", "Noise-only trials: 10,000 (STAT) or 4,000; positive trials: 400 per SNR point",
        "with probability 0.25, a plane-wave Gaussian interferer 10 dB above ambient", "onset 0 to 24 windows",
        "(up to 24 beams times 1,801 bins)", "about 2.3 hours on 4 cores",
    ],
}
REQUIRED["transmittal"] = [
    "| Date | 2026-11-09 |", "35 tests in `tests/test_sim02b2a_*.py`", "(within 0.13 dB)", "(33 of 36)",
    "(343 of 348 consistent)", "which happens with probability 0.08 under correct calibration",
    "(66 of 72; 33 of 36 distinct statistics)", "(108 of the 360 are ORACLE and NOMINAL rows",
    "as 2.40 times target (it is 2.93)", "reported 21 inconsistencies", "(all 48 hold)",
    "(4 published records, 0 measured, 27 assumed)", "1,170 rows, 4.3 % of p-values below 0.05, none below 0.001",
    "costs tonal detection 2.10 dB on A0 and 2.51 to 2.63 dB with beam search, broadband 0.11 to 0.47 dB",
    "matches the exact CFAR law within 0.13 dB", "keeps 2.83 to 3.05 dB of its 3.42 dB tonal gain",
    "(-0.26 to 0.72 dB)", "(tonal false alarms 3.50 to 11.25 times target)", "(4.52 to 5.42 dB extra loss)",
    "121 of 132 incoherent rows give no false alarm at Pfa 1e-2", "up to 2.93 times target",
    "3.6 false alerts per hour per detector", "2.5 to 3.0 core-hours per array",
]
REQUIRED["message"] = [
    "(4 published records, 27 assumed, none measured)", "Across 1,170 evaluation rows, 4.3 %",
    "none falls below 0.001", "2.10 dB on A0 and 2.51 to 2.63 dB with beam search, and broadband detection 0.11 to 0.47 dB",
    "within 0.13 dB", "keeps 2.83 to 3.05 dB of its 3.42 dB tonal gain", "(-0.26 to 0.72 dB)", "by 3.50 to 11.25",
    "121 of 132 incoherent rows", "up to 2.93 times its target", "3.6 false alerts per hour", "quoted as 2.40 times target instead of 2.93",
    "2.5 to 3.0 core-hours per array", "about 2.3 hours on four cores", "[date]", "keithatulmo/picket-sim",
    "branch claude/beautiful-darwin-vbeoue", "SIM-02B2A_transmittal.pdf (4 pages)", "SIM-02B2A_engineering_report.pdf (8 pages)",
    "PCK-SIM-001_SIM-02B.2-A_Review_Package_20261109T003718Z_27abcd69_73fbe35.zip (18.8 MB)",
    "All 249 verification tests pass at the packaging baseline and 241 at the run's code commit",
]
FORBIDDEN = [chr(0x2014), "detection range of", "km detection", "earn their keep", "@"]


def main(argv=None, quiet: bool = False) -> int:
    RESULTS.clear()
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--report", default=str(REPO / "reports/SIM-02B2A_engineering_report.md"))
    ap.add_argument("--transmittal", default=str(REPO / "reports/SIM-02B2A_transmittal.md"))
    ap.add_argument("--message", default=str(REPO / "reports/SIM-02B2A_reviewer_message.md"))
    a = ap.parse_args(argv)
    claims(T(Path(a.run_dir)))
    text_checks({"report": Path(a.report), "transmittal": Path(a.transmittal), "message": Path(a.message)},
                REQUIRED, FORBIDDEN)
    nf = sum(not x[0] for x in RESULTS)
    if not quiet:
        w = max(len(x[1]) for x in RESULTS)
        for ok, label, q, cpt in RESULTS:
            print(f"{'PASS' if ok else 'FAIL'}  {label:<{w}}  quoted {q}  computed {cpt}")
        print(f"\n{len(RESULTS) - nf} of {len(RESULTS)} claims pass")
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
