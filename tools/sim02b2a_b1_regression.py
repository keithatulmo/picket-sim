"""Regression of SIM-02B.2-A ORACLE results against the SIM-02B.1 run of record.

ORACLE normalization in SIM-02B.2-A is the SIM-02B.1 detector (true per-stream background). Under stationary nominal
noise (STAT) the SNR required for Pd 0.5 and 0.9 must therefore agree with the SIM-02B.1 PRIMARY rows of the same
band, window, candidate, mode, class and Pfa, within the combined sampling uncertainty of the two independent runs.

Cells map to SIM-02B.1 as C1 = B2 1 s, C2 = B1 1 s, C3 = B3 0.1 s (configuration). Uncertainty: SIM-02B.1 reports one
interval (snr_req_lo, snr_req_hi); SIM-02B.2-A reports the binomial interval and the threshold-induced interval
separately; the half-widths are combined in quadrature (independent runs). A row is "consistent" when the difference
is within 1.0 x and "marginal" when within 1.5 x the combined half-width. Rows censored in either run are listed
with their status and not compared.

    python tools/sim02b2a_b1_regression.py results/sim02b2a/<run> [--b1 results/sim02b1/<run>] [--out reports/...]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from picket_sim.tables import write_csv  # noqa: E402

B1_RUN = REPO / "results/sim02b1/20261108T125126Z_1c70e065_8dbe019"


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--b1", default=str(B1_RUN))
    ap.add_argument("--out", default=str(REPO / "reports/SIM-02B2A_b1_regression"))
    a = ap.parse_args(argv)
    run, b1 = Path(a.run), Path(a.b1)
    rec = json.loads((run / "record.json").read_text())
    cells = {c["id"]: c for c in rec["config_resolved"]["sim02b2a"]["cells"]}
    b1rows = list(csv.DictReader(open(b1 / "tables/snr_required.csv")))
    idx = {}
    for r in b1rows:
        if r["experiment"] == "PRIMARY" and r["scenario"] == "N-AMB":
            idx[(r["band"], _f(r["window_s"]), r["candidate"], r["mode"], r["class"], _f(r["pfa_target"]),
                 _f(r["pd_target"]))] = r
    out = []
    for r in csv.DictReader(open(run / "tables/snr_required.csv")):
        if r["scenario"] != "STAT" or r["normalizer"] != "ORACLE":
            continue
        c = cells[r["cell"]]
        key = (c["band"], float(c["window_s"]), r["candidate"], r["mode"], r["class"], _f(r["pfa_target"]),
               _f(r["pd_target"]))
        o = idx.get(key)
        if o is None:
            continue
        row = {"cell": r["cell"], "band": c["band"], "window_s": c["window_s"], "candidate": r["candidate"],
               "mode": r["mode"], "class": r["class"], "pfa_target": r["pfa_target"], "pd_target": r["pd_target"],
               "b2a_snr_req_db": _f(r["snr_req_db"]), "b1_snr_req_db": _f(o["snr_req_db"]),
               "b2a_method": r["threshold_method"], "b1_method": o["threshold_method"],
               "b2a_status": r["status"], "b1_status": o["status"]}
        if r["status"] != "ok" or o["status"] != "ok":
            row.update(diff_db=float("nan"), combined_half_width_db=float("nan"), verdict="censored")
        else:
            h1 = 0.5 * (_f(o["snr_req_hi"]) - _f(o["snr_req_lo"]))
            hb = 0.5 * (_f(r["binom_hi_db"]) - _f(r["binom_lo_db"]))
            ht = 0.5 * (_f(r["threshold_hi_db"]) - _f(r["threshold_lo_db"]))
            hs = [h for h in (h1, hb, ht) if math.isfinite(h)]
            hw = math.sqrt(sum(h * h for h in hs)) if hs else float("nan")
            d = row["b2a_snr_req_db"] - row["b1_snr_req_db"]
            verdict = ("consistent" if abs(d) <= hw else "marginal" if abs(d) <= 1.5 * hw else "inconsistent")
            row.update(diff_db=d, combined_half_width_db=hw, verdict=verdict)
        out.append(row)
    out.sort(key=lambda x: (x["cell"], x["candidate"], x["mode"], x["class"], float(x["pfa_target"]),
                            float(x["pd_target"])))
    write_csv(Path(f"{a.out}.csv"), out)
    comp = [x for x in out if x["verdict"] != "censored"]
    n = {v: sum(1 for x in comp if x["verdict"] == v) for v in ("consistent", "marginal", "inconsistent")}
    worst = max(comp, key=lambda x: abs(x["diff_db"]) / x["combined_half_width_db"]) if comp else None
    L = ["# SIM-02B.2-A ORACLE regression against SIM-02B.1", "",
         f"SIM-02B.2-A run `{run.name}`; SIM-02B.1 run `{b1.name}`. STAT, ORACLE normalizer, all cells, candidates, "
         "modes, classes, Pfa and Pd present in both runs.", "",
         f"Compared rows: {len(comp)}; consistent (within the combined 95 % half-width): {n['consistent']}; marginal "
         f"(within 1.5 x): {n['marginal']}; inconsistent: {n['inconsistent']}; censored in either run: "
         f"{len(out) - len(comp)}.", ""]
    if comp:
        ad = sorted(abs(x["diff_db"]) for x in comp)
        L += [f"Absolute difference: median {ad[len(ad) // 2]:.2f} dB, maximum {ad[-1]:.2f} dB.", "",
              f"Largest difference relative to its uncertainty: {worst['candidate']} {worst['mode']} {worst['class']} "
              f"{worst['cell']} Pfa {worst['pfa_target']} Pd {worst['pd_target']}: {worst['diff_db']:+.2f} dB against a "
              f"combined half-width of {worst['combined_half_width_db']:.2f} dB.", ""]
    L += ["With about 95 % intervals, roughly 5 % of rows are expected outside 1.0 x by chance (the intervals are "
          "approximate and the comparisons are not independent: rows share trials across Pd targets and Pfa).", "",
          "| Cell | Candidate | Mode | Class | Pfa | Pd | B.2-A (dB) | B.1 (dB) | Difference (dB) | Half-width (dB) | "
          "Verdict |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in out:
        L.append(f"| {x['cell']} | {x['candidate']} | {x['mode']} | {x['class']} | {x['pfa_target']} | {x['pd_target']} "
                 f"| {x['b2a_snr_req_db']:.2f} | {x['b1_snr_req_db']:.2f} | {x['diff_db']:+.2f} | "
                 f"{x['combined_half_width_db']:.2f} | {x['verdict']} |")
    Path(f"{a.out}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:8]))


if __name__ == "__main__":
    main()
