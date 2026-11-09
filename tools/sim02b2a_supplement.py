"""SIM-02B.2-A supplement: physical statements quoted in the report that are not themselves run-table rows.

1. Estimator laws in dB under stationary Gaussian noise (scale-invariant, so the same in every scenario whose
   reference and test windows share one noise law): mean and standard deviation of 10 log10(G_hat / G) for the
   cell-averaging estimator of M powers (closed form: (10 / ln 10)(psi(M) - ln M) and (10 / ln 10)^2 psi'(M)) and for
   the r-th of M order statistic (numerical integration of its exact density).
2. Contamination ceilings: with the target present in a reference window, a persistent tone masks itself, so Pd at
   high SNR is limited to the fraction of trials whose reference windows are clean. Computed from the run's own onset
   draws (the study's seeded generator) for each guard, and for the order statistic (clean when at most M - r
   reference windows are contaminated). Compared with the measured Pd at the top of the SNR grid.
3. Measured estimation error against the law (from the run table).

    python tools/sim02b2a_supplement.py results/sim02b2a/<run_id> [--out reports/SIM-02B2A_supplement]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from picket_sim.stats import case_rng  # noqa: E402
from picket_sim.tables import write_csv  # noqa: E402

C = 10 / math.log(10)
EULER = 0.5772156649015329


def ca_law_db(M):
    psi = -EULER + sum(1.0 / k for k in range(1, M))
    psi1 = math.pi ** 2 / 6 - sum(1.0 / k ** 2 for k in range(1, M))
    return C * (psi - math.log(M)), C * math.sqrt(psi1)


def os_law_db(M, r):
    """Exact density of the r-th smallest of M unit exponentials, integrated on a fine log grid."""
    t = np.linspace(-12.0, 4.0, 400001)  # t = ln x
    x = np.exp(t)
    lc = math.lgamma(M + 1) - math.lgamma(r) - math.lgamma(M - r + 1)
    logf = lc + (r - 1) * np.log(-np.expm1(-x)) - x * (M - r + 1) + t  # density in t (Jacobian x)
    w = np.exp(logf)
    dt = t[1] - t[0]
    z = np.sum(w) * dt
    m1 = np.sum(w * t) * dt / z
    m2 = np.sum(w * t * t) * dt / z
    return C * m1, C * math.sqrt(m2 - m1 * m1), z


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", default=str(REPO / "reports/SIM-02B2A_supplement"))
    a = ap.parse_args(argv)
    run = Path(a.run)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    rec = json.loads((run / "record.json").read_text())
    cfg = rec["config_resolved"]
    s2 = cfg["sim02b2a"]
    seed = int(cfg["seed"])
    norms = {n["id"]: n for n in s2["normalizers"] + s2.get("contamination_normalizers", [])}

    # 1. estimator laws
    laws = []
    for nid in ("TREF-CA16", "TREF-OS16", "FREF-CA8", "FREF-OS8"):
        n = norms[nid]
        M = int(n["M"]) if "M" in n else 2 * int(n["L"])
        if n["type"].endswith("_ca"):
            mu, sd = ca_law_db(M)
            norm_ok = 1.0
        else:
            mu, sd, norm_ok = os_law_db(M, int(n["r"]))
        if abs(norm_ok - 1) > 1e-6:
            raise SystemExit(f"order-statistic density does not integrate to 1: {norm_ok}")
        laws.append({"normalizer": nid, "powers_averaged_or_ranked": M, "rank": n.get("r", ""),
                     "law_bias_db": mu, "law_std_db": sd})
    err = list(csv.DictReader(open(run / "tables/estimation_error.csv")))
    for L in laws:
        rows = [r for r in err if r["normalizer"] == L["normalizer"] and r["scenario"] in
                ("STAT", "SHAPE-HI", "SHAPE-LO", "COH")]
        b = [float(r["bias_db"]) for r in rows]
        s = [float(r["std_db"]) for r in rows]
        L.update(measured_rows=len(rows), measured_bias_min=min(b), measured_bias_max=max(b),
                 measured_std_min=min(s), measured_std_max=max(s))

    # 2. contamination ceilings
    sc = next(x for x in s2["scenarios"] if "contamination" in x)
    rmax = int(sc["contamination"]["max_onset_windows"])
    npos = int(s2["evaluation"]["positive_trials"])
    with gzip.open(run / "tables/pd_curves.csv.gz", "rt") as fh:
        pd = [r for r in csv.DictReader(fh) if r["scenario"] == sc["id"]]
    ceil = []
    for cell in sc["cells"]:
        for cls in sc.get("classes", []):
            r_on = case_rng(seed, "onset", cell, cls).integers(0, rmax + 1, npos)  # as the study draws them
            for nid in ("TREF-CA16", "TREF-CA16-G8", "TREF-OS16"):
                n = norms[nid]
                g, M = int(n["guard"]), int(n["M"])
                ncont = np.clip(np.minimum(r_on, g + M) - g, 0, None)  # contaminated reference windows per trial
                allow = (M - int(n["r"])) if n["type"] == "tref_os" else 0
                clean = float(np.mean(ncont <= allow))
                top = [r for r in pd if r["cell"] == cell and r["class"] == cls and r["normalizer"] == nid
                       and float(r["pfa_target"]) == 1e-3]
                if not top:
                    continue
                hi = max(float(r["snr_db"]) for r in top)
                at = [float(r["pd"]) for r in top if float(r["snr_db"]) == hi]
                ceil.append({"cell": cell, "class": cls, "normalizer": nid, "guard": g, "M": M,
                             "tolerated_contaminated_windows": allow, "clean_fraction": clean,
                             "clean_fraction_design": (g + allow + 1) / (rmax + 1),
                             "measured_pd_top_snr_min": min(at), "measured_pd_top_snr_max": max(at),
                             "top_snr_db": hi, "rows": len(at)})
    # 3. interference: chance that more reference windows are disturbed than the order statistic tolerates
    itf = next((x for x in s2["scenarios"] if "interference" in x), None)
    intf = []
    if itf:
        q = float(itf["interference"]["probability"])
        for nid in ("TREF-OS16",):
            n = norms[nid]
            M, tol = int(n["M"]), int(n["M"]) - int(n["r"])
            p_more = 1.0 - sum(math.comb(M, k) * q ** k * (1 - q) ** (M - k) for k in range(tol + 1))
            intf.append({"normalizer": nid, "M": M, "tolerated": tol, "probability_per_window": q,
                         "p_more_than_tolerated": p_more, "p_any_disturbed": 1.0 - (1 - q) ** M})
    write_csv(Path(f"{a.out}_interference.csv"), intf)
    write_csv(Path(f"{a.out}_laws.csv"), laws)
    write_csv(Path(f"{a.out}_contamination.csv"), ceil)
    L = ["# SIM-02B.2-A supplement (computed with the study code)", "",
         f"Run `{run.name}`. Generated by `tools/sim02b2a_supplement.py`.", "",
         "## 1. Background estimator laws in dB (stationary Gaussian noise)", "",
         "| Normalizer | Powers | Rank | Law bias (dB) | Law std (dB) | Measured bias, min to max (dB) | "
         "Measured std, min to max (dB) | Rows |", "|---|---|---|---|---|---|---|---|"]
    for x in laws:
        L.append(f"| {x['normalizer']} | {x['powers_averaged_or_ranked']} | {x['rank']} | {x['law_bias_db']:+.3f} | "
                 f"{x['law_std_db']:.3f} | {x['measured_bias_min']:+.3f} to {x['measured_bias_max']:+.3f} | "
                 f"{x['measured_std_min']:.3f} to {x['measured_std_max']:.3f} | {x['measured_rows']} |")
    L += ["", "Measured rows: STAT, SHAPE-HI, SHAPE-LO and COH, every candidate, cell and mode in the run (reference "
          "and test windows share one noise law in these scenarios).", "",
          "## 2. Contamination ceiling for a persistent tone", "",
          f"Onset r uniform on 0 to {rmax} windows before the test window; reference window of age h contains the "
          "target when h <= r. Clean fraction = share of the run's own onset draws whose reference windows hold at "
          "most the tolerated number of contaminated windows (0 for cell averaging, M - r for the order statistic). The "
          "ceiling argument applies to the tone, whose power sits in one bin of every contaminated window; the "
          "broadband rows show that a broadband target is not capped by it (it raises the estimate but does not "
          "match the test-window statistic bin by bin).",
          "", "| Cell | Class | Normalizer | Guard | Tolerated | Clean fraction (draws) | Design (g + tol + 1)/(r_max + 1) "
          "| Measured Pd at top SNR, min to max | Top SNR (dB) |", "|---|---|---|---|---|---|---|---|---|"]
    for x in ceil:
        L.append(f"| {x['cell']} | {x['class']} | {x['normalizer']} | {x['guard']} | {x['tolerated_contaminated_windows']} | "
                 f"{x['clean_fraction']:.4f} | {x['clean_fraction_design']:.2f} | {x['measured_pd_top_snr_min']:.4f} to "
                 f"{x['measured_pd_top_snr_max']:.4f} | {x['top_snr_db']:.2f} |")
    L += ["", "## 3. Interference against the order statistic", "",
          "Each reference window independently holds the interferer with the stated probability; the order statistic "
          "is unaffected only while at most M - r windows are disturbed.", "",
          "| Normalizer | M | Tolerated | Probability per window | P(more than tolerated) | P(any disturbed) |",
          "|---|---|---|---|---|---|"]
    L += [f"| {x['normalizer']} | {x['M']} | {x['tolerated']} | {x['probability_per_window']:g} | "
          f"{x['p_more_than_tolerated']:.4f} | {x['p_any_disturbed']:.4f} |" for x in intf]
    Path(f"{a.out}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
