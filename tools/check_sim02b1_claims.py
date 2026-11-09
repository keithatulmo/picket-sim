"""Check every quantitative claim in the SIM-02B.1 findings, transmittal and reviewer message.

Same contract as tools/check_sim02a_claims.py (CLAUDE.md, cycle close-out step 2): each check recomputes a quoted
figure from the run-of-record tables at the precision written; the documents must quote the checked values.
Exit status 1 if any check fails.

    python tools/check_sim02b1_claims.py results/sim02b1/<run_id>
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS: list[tuple[bool, str, str, str]] = []


def check(label: str, quoted, computed, ok: bool | None = None):
    if ok is None:
        ok = quoted == computed
    RESULTS.append((bool(ok), label, str(quoted), str(computed)))


def rd(x, n):
    return round(float(x) + 0.0, n)


def rng(vals, n):
    v = [float(x) for x in vals]
    return (rd(min(v), n), rd(max(v), n))


def f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


class Tables:
    def __init__(self, run: Path):
        self.run = run
        t = run / "tables"
        self.gain = list(csv.DictReader(open(t / "detection_gain_vs_a0.csv")))
        self.snr = list(csv.DictReader(open(t / "snr_required.csv")))
        self.thr = list(csv.DictReader(open(t / "thresholds_and_pfa.csv")))
        self.prov = list(csv.DictReader(open(t / "parameters_by_provenance.csv")))
        self.cov = list(csv.DictReader(open(t / "covariance_validation.csv")))
        self.record = json.loads((run / "record.json").read_text())
        with gzip.open(t / "pd_curves.csv.gz", "rt") as fh:
            self.pd = list(csv.DictReader(fh))

    def g(self, scenario, cand, mode, band, window, cls, pfa=1e-3, pd=0.5) -> dict:
        rows = [r for r in self.gain if r["scenario"] == scenario and r["candidate"] == cand and r["mode"] == mode
                and r["band"] == band and f(r["window_s"]) == window and r["class"] == cls
                and f(r["pfa_target"]) == pfa and f(r["pd_target"]) == pd]
        if len(rows) != 1:
            raise KeyError((scenario, cand, mode, band, window, cls, pfa, pd, len(rows)))
        return rows[0]

    def gains(self, **sel) -> list[dict]:
        out = []
        for r in self.gain:
            ok = True
            for k, v in sel.items():
                rv = r[k]
                if isinstance(v, (list, tuple, set)):
                    ok &= (f(rv) in v) if isinstance(next(iter(v)), float) else (rv in v)
                elif isinstance(v, float):
                    ok &= f(rv) == v
                else:
                    ok &= rv == v
            if ok:
                out.append(r)
        return out


PRIM = ["A1", "A2", "P6-C", "P8-C", "A4"]
VALID = ("exact", "empirical")


def valid(r) -> bool:
    return r["status"] == "ok" and r["threshold_method"] in VALID and r["a0_threshold_method"] in VALID


def sel(T, pfa=1e-3, pd=0.5, **k) -> list[dict]:
    out = []
    for r in T.gain:
        if f(r["pfa_target"]) != pfa or f(r["pd_target"]) != pd:
            continue
        good = True
        for key, v in k.items():
            col = "class" if key == "cls" else key
            rv = f(r[col]) if col == "window_s" else r[col]
            good &= (rv in v) if isinstance(v, (list, tuple)) else rv == v
        if good and valid(r):
            out.append(r)
    return out


def grng(rows, n=1):
    if not rows:
        return None
    return rng([r["gain_db"] for r in rows], n)


def claims(T: Tables):
    """Quantitative claims of the SIM-02B.1 report, transmittal and reviewer message (run of record)."""
    rec = T.record
    check("run status, cases, workers", ("complete", 139, 4),
          (rec["status"], len(list(csv.DictReader(open(T.run / "tables" / "cases.csv")))), rec["workers"]))
    check("run time (s), rounded", 5907, round(rec["timings_s"]["total_s"]))
    check("code commit, clean", ("8dbe019", False), (rec["software"]["git_commit"][:7], rec["software"]["git_dirty"]))
    check("Python, NumPy", ("3.13.18", "2.5.4"), (rec["software"]["python"], rec["software"]["numpy"]))
    c = {k: sum(r["provenance"] == k for r in T.prov) for k in ("published", "measured", "assumed")}
    check("provenance published / measured / assumed", (2, 0, 23), (c["published"], c["measured"], c["assumed"]))

    # Finding 1
    b1 = sel(T, scenario="N-AMB", band="B1", candidate=PRIM, window_s=[0.1, 1.0])
    check("F1 B1 ambient-limited gain range (dB), valid cells", (-0.2, 0.8, 120), grng(b1) + (len(b1),))
    check("F1 B1 intervals containing zero", 119, sum(f(r["gain_lo_db"]) <= 0 <= f(r["gain_hi_db"]) for r in b1))
    pen = {}
    for r in sel(T, scenario="N-AMB", candidate=PRIM, mode="beam_search"):
        k = sel(T, scenario="N-AMB", candidate=r["candidate"], mode="beam_known", band=r["band"],
                window_s=f(r["window_s"]), cls=r["class"])
        if k:
            pen.setdefault(r["band"], []).append((f(k[0]["gain_db"]) - f(r["gain_db"]), r["candidate"]))
    check("F1/F3 search penalty B1 (dB)", (-0.3, 0.1), rng([x for x, _ in pen["B1"]], 1))
    check("F3 search penalty B2 (dB)", (-0.4, 1.2), rng([x for x, _ in pen["B2"]], 1))
    check("F3 search penalty B3 (dB)", (0.5, 2.9), rng([x for x, _ in pen["B3"]], 1))
    check("F3 largest B3 penalty belongs to A4", "A4", max(pen["B3"])[1])
    check("F1 V-D B1 beam search 1 s (dB)", (2.1, 4.0), grng(sel(T, scenario="N-AMB", band="B1", candidate="V-D",
                                                                     window_s=1.0, mode="beam_search")))
    check("F1 V-DS B1 beam search 1 s (dB)", (1.6, 3.2), grng(sel(T, scenario="N-AMB", band="B1", candidate="V-DS",
                                                                      window_s=1.0, mode="beam_search")))

    # Finding 2 and Section 3.2 table
    q = {"B2": [0.1, 1.0], "B3": [0.1]}
    exp_tab = {
        ("B2", "beam_search"): {"all": (1.5, 5.0), "A1": (1.5, 2.5), "A2": (3.0, 4.3), "P6-C": (2.5, 3.7), "P8-C": (2.1, 4.0), "A4": (4.2, 5.0)},
        ("B2", "beam_known"): {"A1": (1.4, 2.5), "A2": (3.3, 4.7), "P6-C": (3.0, 4.8), "P8-C": (2.8, 4.8), "A4": (5.0, 6.0)},
        ("B2", "incoherent"): {"all": (0.5, 4.5), "A1": (0.5, 0.9), "A2": (1.0, 1.8), "P6-C": (0.7, 1.3), "P8-C": (0.7, 1.4), "A4": (1.5, 4.5)},
        ("B3", "beam_search"): {"all": (3.5, 7.4), "A1": (4.6, 5.1), "A2": (4.4, 5.0), "P6-C": (5.8, 6.5), "P8-C": (6.9, 7.4), "A4": (3.5, 4.5)},
        ("B3", "beam_known"): {"A1": (5.4, 6.1), "A2": (5.5, 6.4), "P6-C": (7.1, 7.7), "P8-C": (8.0, 9.0), "A4": (5.8, 6.4)},
        ("B3", "incoherent"): {"all": (2.3, 5.3), "A1": (3.0, 4.0), "A2": (2.7, 4.4), "P6-C": (3.9, 5.0), "P8-C": (4.4, 5.3), "A4": (2.3, 4.7)},
    }
    for (b, m), d in exp_tab.items():
        for cand, quoted in d.items():
            cands = PRIM if cand == "all" else cand
            check(f"S3.2 {b} {m} {cand} gain range (dB)", quoted,
                  grng(sel(T, scenario="N-AMB", band=b, candidate=cands, window_s=q[b], mode=m)))
    check("S3.2 A1 B2 beam-known tone gains at 0.1 / 1 / 10 s (dB)", (1.6, 1.7, 1.8),
          tuple(rd(sel(T, scenario="N-AMB", band="B2", candidate="A1", window_s=w, mode="beam_known", cls="tone")[0]["gain_db"], 1)
                for w in (0.1, 1.0, 10.0)))
    check("S3.2 P8-E B2 beam search 1 s (dB)", (5.3, 6.4),
          grng(sel(T, scenario="N-AMB", band="B2", candidate="P8-E", window_s=1.0, mode="beam_search")))
    check("S3.2 60 s tonal B1 beam known (dB)", (-0.1, 0.1),
          grng(sel(T, scenario="N-AMB", band="B1", candidate=PRIM, window_s=60.0, mode="beam_known", cls="tone")))

    # Finding 4/5 and Section 3.3 table (T = 1 s)
    scen = {("N-AMB", "B1"): ((-0.2, 0.7), (-0.2, 0.4)), ("N-AMB", "B2"): ((1.7, 4.9), (0.6, 4.1)),
            ("N-FLOW", "B1"): ((4.3, 7.8), (3.1, 6.5)), ("N-FLOW", "B2"): ((4.5, 7.3), (3.2, 6.7)),
            ("N-SENS", "B1"): ((5.7, 9.0), (3.3, 6.8)), ("N-SENS", "B2"): ((4.9, 8.5), (3.1, 7.1))}
    for (sc, b), (bs, inc) in scen.items():
        check(f"S3.3 {sc} {b} beam search 1 s (dB)", bs, grng(sel(T, scenario=sc, band=b, candidate=PRIM, window_s=1.0, mode="beam_search")))
        check(f"S3.3 {sc} {b} incoherent 1 s (dB)", inc, grng(sel(T, scenario=sc, band=b, candidate=PRIM, window_s=1.0, mode="incoherent")))
    for sc, quoted in (("N-AMB", (3.1, 7.4)), ("N-FLOW", (3.3, 8.1)), ("N-SENS", (3.1, 7.9))):
        check(f"S3.3 {sc} B3 beam search 1 s at Pfa 1e-2 (dB)", quoted,
              grng(sel(T, pfa=0.01, scenario=sc, band="B3", candidate=PRIM, window_s=1.0, mode="beam_search")))
    check("S3.3 B3 1 s beam search has no valid cells at Pfa 1e-3", 0,
          len(sel(T, scenario="N-AMB", band="B3", window_s=1.0, mode="beam_search")))
    check("S3.3 P8-C sensor-limited beam known B1, B2 1 s (dB)", (8.7, 9.1),
          grng(sel(T, scenario="N-SENS", band=["B1", "B2"], candidate="P8-C", window_s=1.0, mode="beam_known")))
    inc = sel(T, scenario=["N-FLOW", "N-SENS"], band="B1", candidate=PRIM, window_s=1.0, mode="incoherent")
    check("F5 incoherent flow-like or sensor-limited B1 1 s (dB)", (3.1, 6.8), grng(inc))

    # Section 3.1 and Finding 9
    def a0(b, w, cls):
        r = [x for x in T.snr if x["candidate"] == "A0" and x["scenario"] == "N-AMB" and x["band"] == b
             and f(x["window_s"]) == w and x["class"] == cls and f(x["pfa_target"]) == 1e-3 and f(x["pd_target"]) == 0.5]
        return f(r[0]["snr_req_db"]) if r and r[0]["status"] == "ok" else float("nan")
    tab31 = {"tone": [20.7, 11.7, 2.2, 21.7, 12.5, 3.2, 22.1, 13.0, 3.9],
             "harmonic": [16.1, 7.0, -2.4, 17.1, 8.0, -1.4, 17.2, 8.1, -1.4],
             "broadband": [-3.3, -8.5, -13.7, -6.9, -12.0, -16.8, -11.6, -16.8, -22.0]}
    for cls, vals in tab31.items():
        check(f"S3.1 A0 SNR required, {cls} (dB)", vals,
              [rd(a0(b, w, cls), 1) for b in ("B1", "B2", "B3") for w in (0.1, 1.0, 10.0)])
    check("S3.1 A0 SNR required, chirp (dB)", [9.5, 10.6, 10.8, 11.5, 11.3, 12.0],
          [rd(a0(b, w, "chirp"), 1) for b in ("B1", "B2", "B3") for w in (0.1, 1.0)])
    tone_dec = (a0("B2", 0.1, "tone") - a0("B2", 10.0, "tone")) / 2
    bb_dec = (a0("B2", 0.1, "broadband") - a0("B2", 10.0, "broadband")) / 2
    check("F9 A0 per-decade improvement B2, tone / broadband (dB)", (9.25, 4.94), (rd(tone_dec, 2), rd(bb_dec, 2)))
    gt = f(sel(T, scenario="N-AMB", band="B2", candidate="P8-C", window_s=1.0, mode="beam_search", cls="tone")[0]["gain_db"])
    gb = f(sel(T, scenario="N-AMB", band="B2", candidate="P8-C", window_s=1.0, mode="beam_search", cls="broadband")[0]["gain_db"])
    check("F9 P8-C beam search 1 s B2 gain, tone / broadband (dB)", (2.9, 3.6), (rd(gt, 1), rd(gb, 1)))
    check("F9 equivalent A0 integration factors", (2.06, 5.36),
          (rd(10 ** (2.9 / tone_dec), 2), rd(10 ** (3.6 / bb_dec), 2)))

    # Findings 6 and 7, Section 4 (mismatch, target 0.01)
    mm = [r for r in T.thr if r["kind"] == "mismatch" and f(r["pfa_target"]) == 0.01]

    def mr(exp, dets, cands=None, modes=None, band=None):
        v = [r["realized_pfa"] for r in mm if r["experiment"] == exp and r["detector"] in dets
             and (cands is None or r["candidate"] in cands) and (modes is None or r["mode"] in modes)
             and (band is None or r["band"] == band)]
        return rng(v, 3)
    nb = ("tonal", "harmonic", "mf")
    alld = ("tonal", "harmonic", "mf", "energy")
    check("F6 +1 dB: tonal/harmonic/mf, all candidates", (0.075, 0.332), mr("MM-LEVEL+1", nb))
    check("F6 +1 dB: energy", (1.0, 1.0), mr("MM-LEVEL+1", ("energy",)))
    check("S4 +1 dB: A0 tonal/harmonic/mf", (0.112, 0.203), mr("MM-LEVEL+1", nb, cands=["A0"]))
    check("F6 +3 dB: all", (0.844, 1.0), mr("MM-LEVEL+3", alld))
    check("F6 shape: tonal/harmonic/energy", (0.999, 1.0), mr("MM-SHAPE", ("tonal", "harmonic", "energy")))
    check("S4 shape: mf", (0.0, 0.001), mr("MM-SHAPE", ("mf",)))
    check("F7 white assumed: A0", (0.009, 0.01), mr("MM-COH-WHITE", alld, cands=["A0"]))
    check("F7 white assumed: arrays, beams, B1", (1.0, 1.0),
          mr("MM-COH-WHITE", alld, cands=["A1", "P8-C", "A4"], modes=["beam_known", "beam_search"], band="B1"))
    check("S4 white assumed: A1, P8-C beams B2", (1.0, 1.0),
          mr("MM-COH-WHITE", alld, cands=["A1", "P8-C"], modes=["beam_known", "beam_search"], band="B2"))
    check("S4 white assumed: A4 beams B2", (0.033, 1.0),
          mr("MM-COH-WHITE", alld, cands=["A4"], modes=["beam_known", "beam_search"], band="B2"))
    check("S4 flow truth: A0", (0.007, 0.012), mr("MM-COH-FLOW", alld, cands=["A0"]))
    check("F7 flow truth: arrays B1", (0.0, 0.0), mr("MM-COH-FLOW", alld, cands=["A1", "P8-C", "A4"], band="B1"))
    check("S4 flow truth: A1, P8-C B2", (0.0, 0.0), mr("MM-COH-FLOW", alld, cands=["A1", "P8-C"], band="B2"))
    check("R1 Pfa multiplication for +1 dB (narrowband detectors)", (7.5, 33),
          (rd(mr("MM-LEVEL+1", nb)[0] * 100, 1), round(mr("MM-LEVEL+1", nb)[1] * 100)))

    # Finding 8 and Section 4 (exact calibration test, bound conservatism)
    sys.path.insert(0, str(REPO / "src"))
    from picket_sim.detection import calibration_pvalue
    prim = [r for r in T.thr if r["kind"] == "primary"]
    out = {}
    for meth in ("exact", "empirical", "bound"):
        ps = []
        for r in prim:
            if meth == "bound":
                if r["bound_eta"] in ("", "nan") or r["bound_realized_pfa"] in ("", "nan"):
                    continue
                k = int(round(f(r["bound_realized_pfa"]) * int(r["n_eval"])))
                ps.append(calibration_pvalue("bound", k, int(r["n_eval"]), f(r["pfa_target"]))[1])
            elif r["method"] == meth:
                ps.append(calibration_pvalue(meth, int(r["realized_k"]), int(r["n_eval"]), f(r["pfa_target"]),
                                             int(r["n_cal"]))[0])
        out[meth] = (len(ps), rd(100 * sum(p < 0.05 for p in ps) / len(ps), 1), rd(min(1.0, min(ps) * len(ps)), 3))
    check("F8 exact: rows, % p < 0.05, Bonferroni min p", (648, 2.8, 0.645), out["exact"])
    check("F8 empirical: rows, % p < 0.05, Bonferroni min p", (1460, 3.8, 1.0), out["empirical"])
    check("F8 bound: rows, % p < 0.05, Bonferroni min p", (3324, 1.0, 0.203), out["bound"])
    import statistics

    def bmed(modes):
        v = [f(r["bound_realized_pfa"]) / f(r["pfa_target"]) for r in prim if r["mode"] in modes
             and r["bound_eta"] not in ("", "nan") and f(r["n_eval"]) * f(r["pfa_target"]) >= 10]
        return rd(statistics.median(v), 2)
    check("F8 bound median realized/target: beam search, incoherent", (0.20, 0.00),
          (bmed(["beam_search"]), bmed(["incoherent"])))
    check("S4 single-stream bounds median realized/target", (0.90, 0.93), (bmed(["beam_known"]), bmed(["single"])))

    # Section 5 self-checks
    sc = rec["self_checks"]
    check("S5 covariance worst median error (SE)", 0.84, rd(sc["covariance_validation_worst_median_error_in_se"], 2))
    check("S5 waveform variance within 0.8 % of band power", True, sc["covariance_validation_worst_variance_ratio"] < 0.008)
    check("S5 clipping headroom (dB)", 10.5, rd(sc["clipping_min_headroom_db"], 1))

    # transmittal and message specifics
    flow_sens_b1 = sel(T, scenario=["N-FLOW", "N-SENS"], band="B1", candidate=PRIM, window_s=1.0, mode="beam_search")
    check("message: flow-like or sensor-limited B1 beam search 1 s (dB)", (4.3, 9.0), grng(flow_sens_b1))
    check("transmittal: run minutes vs estimate", (98, 75), (int(rec["timings_s"]["total_s"] // 60), 75))
    errata = (T.run.parent / "ERRATA.md").read_text()
    check("transmittal: errata figures present", True, all(x in errata for x in ("5.72", "14.1 %", "3.09")))
    sc0 = rec["self_checks"]
    check("transmittal: recorded self-check values", (5.72, 14.1, 3.09),
          (rd(sc0["pfa_empirical_max_abs_z"], 2), rd(100 * sc0["pfa_empirical_fraction_ci_excluding_target"], 1),
           rd(sc0["bound_max_upper_realized_over_target"], 2)))
    # The quoted counts describe the SIM-02B.1 packaging baseline (a394c5e). They are checked against that
    # baseline's recorded test inventory (copied from the delivered package, 05_verification/
    # test_inventory_baseline.txt), and every test it lists must still exist in the tree being checked; later
    # baselines may add tests. (Until SIM-02B.2-A this check counted the current tree and so passed only at a394c5e.)
    import subprocess
    inv = (REPO / "tests/fixtures/sim02b1_test_inventory_a394c5e.txt").read_text().splitlines()
    ids = [x for x in inv if "::" in x]
    now = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
                         cwd=REPO, capture_output=True, text=True).stdout.splitlines()
    missing = sorted(set(ids) - {x for x in now if "::" in x})
    check("tests collected at the SIM-02B.1 baseline (all / supplementary)", (214, 15),
          (len(ids), sum(1 for x in ids if x.startswith("tests/test_supplementary_tools.py::"))))
    check("every SIM-02B.1 baseline test still collected", [], missing[:5])

    # Appendix A (SIM-02A D06 supplement)
    d06 = {r["array_id"]: r for r in csv.DictReader(open(REPO / "reports" / "SIM-02A_criteria_D06_bands.csv"))}
    six = [tuple(rd(d06[a][f"guaranteed_{k}_ratio"], 2) for k in ("m6db", "m6p0206db", "m6p5db", "m5db", "m7db"))
           for a in ("P6-C", "P6-E")]
    check("A D06 six-element circles: -6, -6.0206, -6.5, -5, -7 dB", [(2.37, 1.73, 1.55, 2.42, 1.48)] * 2, six)
    check("A D06 eight-element circles -5 / -7 dB", [(2.93, 2.72)] * 2,
          [(rd(d06[a]["guaranteed_m5db_ratio"], 2), rd(d06[a]["guaranteed_m7db_ratio"], 2)) for a in ("P8-C", "P8-E")])
    others = [abs(f(r["guaranteed_m5db_ratio"]) - f(r["guaranteed_m7db_ratio"])) for a, r in d06.items()
              if a not in ("P6-C", "P6-E", "P8-C", "P8-E") and r["guaranteed_m5db_ratio"] not in ("", "nan")]
    check("A D06 other candidates' largest change -5 to -7 dB", 0.07, rd(max(others), 2))
    empty = sorted(a for a, r in d06.items() if all(r[f"guaranteed_{k}_ratio"] in ("", "nan")
                                                     for k in ("m5db", "m5p5db", "m6db", "m6p0206db", "m6p5db", "m7db")))
    check("A D06 candidates without a band between -5 and -7 dB", ["A4", "V-C", "V-D", "V-DS"], empty)


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
    "report": ["gains range from -0.2 to 0.8 dB, and 119 of 120 intervals contain zero",
               "V-D 2.1 to 4.0 dB", "V-DS 1.6 to 3.2 dB", "B2 gains are 1.5 to 5.0 dB",
               "In B3 (0.1 s) they are 3.5 to 7.4 dB", "P8-C reaches 8.0 to 9.0 dB",
               "Searching for the direction costs 0.5 to 2.9 dB in B3", "In B2 the cost is -0.4 to 1.2 dB",
               "B1 gains are 4.3 to 7.8 dB in flow-like noise and 5.7 to 9.0 dB in sensor-limited noise",
               "0.5 to 4.5 dB in ambient-limited B2 and 2.3 to 5.3 dB in B3 (0.1 s), and 3.1 to 6.8 dB",
               "0.075 to 0.332", "0.844 to 1.0", "0.999 to 1.0", "(A0: 0.009 to 0.01)",
               "2.8 % and empirical thresholds 3.8 %", "0.645 and 1.0", "median of 0.20",
               "9.25 dB less input SNR per decade", "4.94 dB per decade", "(2.9 dB for tones, 3.6 dB for broadband)",
               "2.06 and 5.36 times longer", "2 published records, 0 measured, 23 assumed",
               "worst median error 0.84 standard errors", "at least 10.5 dB", "multiplies Pfa by 7.5 to 33",
               "it is 1.73, and at -6.5 dB 1.55", "falls from 2.42 to 1.48", "from 2.93 to 2.72",
               "changes by at most 0.07", "A1 gains 1.6, 1.7 and 1.8 dB", "(B2 5.3 to 6.4 dB)",
               "-0.1 to 0.1 dB for every primary candidate", "8.7 to 9.1 dB in B1 and B2",
               "648 exact-threshold rows, 2.8 %", "1,460 empirical rows, 3.8 %", "3,324 bound rows (one-sided), 1.0 %",
               "0.645, 1.0 and 0.203", "median of 0.90 to 0.93", "5,907 s on 4 worker processes",
               "214 pass at the packaging baseline and 212 at the run's code commit"],
    "transmittal": ["gains -0.2 to 0.8 dB, and 119", "of 120 intervals contain zero", "(V-D 2.1 to 4.0 dB)",
                    "1.5 to 5.0 dB in B2 (0.1 and 1 s) and 3.5 to 7.4 dB in B3 (0.1 s)", "8.0 to",
                    "4.3 to 7.8 dB flow-like, 5.7 to", "into 0.075 to 0.332 (energy detector 1.0)",
                    "0.645 for exact and 1.0 for empirical", "2.06 times longer on A0 for tones and 5.36 times",
                    "fall from 2.37 to 1.73 at -6.0206 dB", "(15 tests)", "largest z 5.72",
                    "14.1 % of intervals excluding the target", "up to 3.09 times the target", "0.59 % of its energy",
                    "The run took 98 minutes against a 75-minute estimate"],
    "message": ["Gains run from -0.2 to 0.8 dB and 119 of 120 intervals contain zero",
                "1.5 to 5.0 dB from 200 Hz to 2 kHz, and 3.5 to 7.4 dB from 2 to 10 kHz in 0.1 s windows",
                "4.3 to 9.0 dB below 200 Hz", "turns a 0.01 target into 0.075 to 0.332, and into 1.0",
                "2.06 times longer on A0 for tones and 5.36 times", "2 records are published, 23 assumed and none measured",
                "2.37 at exactly -6.00 dB and 1.73 at -6.0206 dB", "Fifteen new tests", "All 214 verification tests",
                "98 minutes against a 75-minute estimate", "(4 pages)", "(9 pages)", "(21.6 MB)",
                "the 59 claims checks pass", "reproduces every run table byte for byte"],
}
FORBIDDEN = [chr(0x2014), "detection range of", "km detection", "earn their keep"]


def main(argv=None, quiet: bool = False) -> int:
    RESULTS.clear()
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--report", default=str(REPO / "reports/SIM-02B1_engineering_report.md"))
    ap.add_argument("--transmittal", default=str(REPO / "reports/SIM-02B1_transmittal.md"))
    ap.add_argument("--message", default=str(REPO / "reports/SIM-02B1_reviewer_message.md"))
    a = ap.parse_args(argv)
    T = Tables(Path(a.run_dir))
    claims(T)
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
