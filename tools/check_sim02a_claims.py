"""Check every quantitative claim in the SIM-02A findings, transmittal and reviewer message.

CLAUDE.md requires that numbers be reported only from run tables and that quoted ranges be checked
programmatically. Each check below recomputes a quoted figure from the run-of-record tables (or the
criterion-margin supplement, itself self-checked against those tables) and compares it with the
value as written, at the precision written. Exit status 1 if any check fails.

    python tools/check_sim02a_claims.py results/sim02a/<run_id> [--sim01 results/sim01/<run_id>]
        [--supplement reports/SIM-02A_criterion_margin]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import sys
from collections import Counter
from pathlib import Path

RESULTS: list[tuple[bool, str, str, str]] = []


def check(label: str, quoted, computed, ok: bool | None = None):
    if ok is None:
        ok = quoted == computed
    RESULTS.append((bool(ok), label, str(quoted), str(computed)))


def rd(x: float, n: int) -> float:
    return round(float(x) + 0.0, n)


def rng(vals, n):
    v = [float(x) for x in vals]
    return (rd(min(v), n), rd(max(v), n))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--sim01", default="results/sim01/20261107T203522Z_d64d297c_8043684")
    ap.add_argument("--supplement", default="reports/SIM-02A_criterion_margin")
    a = ap.parse_args()
    T = Path(a.run_dir) / "tables"
    P = lambda f: list(csv.DictReader(open(T / f)))  # noqa: E731

    cand = {r["array_id"]: r for r in P("candidates.csv")}
    small = [k for k, r in cand.items() if float(r["aperture_m"]) <= 1.0701 and k != "A0"]
    wng = {k: 10 * math.log10(int(r["n_elements"])) for k, r in cand.items()}
    check("largest aperture in the 'up to 1.07 m' set (m)", 1.07, rd(max(float(cand[k]["aperture_m"]) for k in small), 2))

    # ---- provenance
    c = Counter(r["provenance"] for r in P("parameters_by_provenance.csv"))
    check("parameters assumed / published / measured", (72, 1, 0), (c["assumed"], c["published"], c["measured"]))

    # ---- item 1: realized gain
    rs = P("rag_band_summary.csv")
    sel = lambda fld, eta: [r for r in rs if r["field"] == fld and r["eta_db"] == eta]  # noqa: E731
    iso = {r["array_id"]: r for r in sel("ISO", "none")}
    check("ISO B1 band median, max over arrays <= 1.07 m (dB)", 0.07, rd(max(float(iso[k]["B1_median_db"]) for k in small), 2))
    check("ISO B1 band median, V-D (dB)", 1.08, rd(iso["V-D"]["B1_median_db"], 2))
    check("ISO B2 band median range, arrays <= 1.07 m (dB)", (0.6, 5.2), rng([iso[k]["B2_median_db"] for k in small], 1))
    f200 = [r for r in csv.DictReader(gzip.open(T / "rag_by_frequency.csv.gz", "rt"))
            if r["field"] == "ISO" and r["eta_db"] == "none" and abs(float(r["f_hz"]) - 200.0) < 1e-6 and r["array_id"] in small]
    top = max(f200, key=lambda r: float(r["rag_median_db"]))
    check("ISO gain at 200 Hz, max steering median, arrays <= 1.07 m (dB, array)", (0.73, "A4"), (rd(top["rag_median_db"], 2), top["array_id"]))
    s20 = {r["array_id"]: r for r in sel("ISO", "20")}
    g = max(wng[k] - float(s20[k][f"{b}_median_db"]) for k in small for b in ("B1", "B2", "B3", "B4"))
    check("eta=+20 dB: max gap to 10log10N, any band, arrays <= 1.07 m (dB)", 0.29, rd(g, 2))
    fl = {r["array_id"]: r for r in sel("FLOW", "none")}
    low = {k: [wng[k] - float(fl[k][f"{b}_median_db"]) for b in ("B1", "B2")] for k in small}
    over = sorted(k for k, v in low.items() if max(v) > 0.5)
    check("FLOW: arrays > 0.5 dB short of 10log10N below 2 kHz", ["A1", "P6-C", "P8-C"], over)
    check("FLOW: their shortfall below 2 kHz (dB)", (0.9, 1.7), rng([x for k in over for x in low[k]], 1))
    check("FLOW: B1 shortfall of those arrays (dB) [Section 4.2]", (1.0, 1.7), rng([low[k][0] for k in over], 1))
    hi_gap = max(wng[k] - float(fl[k][f"{b}_median_db"]) for k in small for b in ("B3", "B4"))
    check("FLOW: max shortfall above 2 kHz (dB)", 0.16, rd(hi_gap, 2))
    check("FLOW: A1 B1 median (dB)", 4.59, rd(fl["A1"]["B1_median_db"], 2))
    check("nearest-element spacing of A1, P6-C, P8-C (m)", (0.15, 0.23), rng([cand[k]["min_spacing_m"] for k in over], 2))
    check("neighbor correlation exp(-d/0.1 m) of those arrays", (0.11, 0.22),
          rng([math.exp(-float(cand[k]["min_spacing_m"]) / 0.1) for k in over], 2))

    # ---- item 2: acquisition
    eta = P("acquisition_eta_by_band.csv")
    s1 = [float(r["eta_median_db"]) for r in eta if r["sensor"].startswith("S1") and r["acquirable"] == "true"]
    check("S1 self-noise/ambient band medians (dB)", (-20.0, -74.4), (rd(max(s1), 1), rd(min(s1), 1)))
    pick = lambda s, amb, b: next(r for r in eta if r["sensor"].startswith(s) and r["ambient"].endswith(amb) and r["band"] == b)  # noqa: E731
    check("S2 quiet B4 eta (dB)", 4.0, rd(pick("S2", "quiet", "B4")["eta_median_db"], 1))
    check("S3 quiet B2, B3 eta (dB)", (1.8, 12.1), (rd(pick("S3", "quiet", "B2")["eta_median_db"], 1), rd(pick("S3", "quiet", "B3")["eta_median_db"], 1)))
    check("S3 cannot acquire B4", True, all(r["acquirable"] != "true" for r in eta if r["sensor"].startswith("S3") and r["band"] == "B4"))
    adc = {r["band"]: r for r in P("acquisition_adc.csv") if r["sensor"].startswith("S2")}
    check("S2 analog minus ADC noise, B3 and B4 (dB)", (-2.7, -3.2), (rd(adc["B3"]["analog_minus_adc_noise_db_median"], 1), rd(adc["B4"]["analog_minus_adc_noise_db_median"], 1)))

    # ---- item 3: bands and ring sidelobes
    ts = {r["array_id"]: r for r in P("thresholds_summary.csv")}
    for k, q in (("SQ4-C", (1.28, 1.14, 1.03)), ("P6-C", (2.53, 2.37, 1.28)), ("P8-C", (3.78, 2.80, 1.32))):
        check(f"{k} guaranteed ratio -3/-6/-10 dB", q, tuple(rd(ts[k][f"guaranteed_m{L}db_ratio"], 2) for L in (3, 6, 10)))
    check("ISO B3 band median P8-C, SQ4-C (dB)", (8.58, 5.88), (rd(iso["P8-C"]["B3_median_db"], 2), rd(iso["SQ4-C"]["B3_median_db"], 2)))
    sup = Path(a.supplement)
    psl = list(csv.DictReader(open(f"{sup}_psl.csv")))
    bands = {r["array_id"]: r for r in csv.DictReader(open(f"{sup}_bands.csv"))}

    def plateau(k):
        v = sorted(float(r["psl_worst_steering_db"]) for r in psl if r["array_id"] == k and r["psl_worst_steering_db"] not in ("", "nan"))
        return v[len(v) // 2] if len(v) % 2 else 0.5 * (v[len(v) // 2 - 1] + v[len(v) // 2])

    check("P6-C, P8-C median worst-steering PSL over -3 dB band (dB)", (-6.02, -7.77), (rd(plateau("P6-C"), 2), rd(plateau("P8-C"), 2)))
    check("P6-C guaranteed ratio at -5.9 / -6.0 / -6.1 dB", (2.37, 2.37, 1.69),
          tuple(rd(bands["P6-C"][f"guaranteed_{t}_ratio"], 2) for t in ("m5p9db", "m6db", "m6p1db")))
    check("P8-C guaranteed ratio at -5.9 / -6.0 / -6.1 dB", (2.80, 2.80, 2.80),
          tuple(rd(bands["P8-C"][f"guaranteed_{t}_ratio"], 2) for t in ("m5p9db", "m6db", "m6p1db")))

    # ---- item 4: volumetric
    vol = [ts[k] for k in ("V-C", "V-D", "V-DS")]
    check("volumetric guaranteed -3 dB ratio range", (1.06, 1.14), rng([r["guaranteed_m3db_ratio"] for r in vol], 2))
    check("volumetric guaranteed -6 and -10 dB bands empty", True,
          all(r[f"guaranteed_m{L}db_ratio"] in ("", "nan") for r in vol for L in (6, 10)))
    check("V-D, V-DS guaranteed -3 dB band (Hz)", (146, 182),
          (round(min(float(ts[k]["guaranteed_m3db_lo_hz"]) for k in ("V-D", "V-DS"))),
           round(max(float(ts[k]["guaranteed_m3db_hi_hz"]) for k in ("V-D", "V-DS")))))

    # ---- item 5: channel errors
    mc = P("mc_scenarios.csv")
    check("E2 max mean signal loss up to 15 kHz (dB)", 0.17, rd(max(float(r["signal_loss_db"]) for r in mc if r["scenario"].startswith("E2")), 2))
    check("E3 signal loss at 15 kHz, range (dB)", (3.2, 4.5),
          rng([r["signal_loss_db"] for r in mc if r["scenario"].startswith("E3") and float(r["f_hz"]) == 15000], 1))
    p8 = [r for r in mc if r["array_id"] == "P8-C" and r["scenario"].startswith("E3") and float(r["f_hz"]) == 15000]
    check("P8-C E3 15 kHz signal loss over target azimuths (dB)", (4.3, 4.4), rng([r["signal_loss_db"] for r in p8], 1))
    check("P8-C E3 15 kHz gross-error rate over target azimuths (%)", (65, 81), tuple(round(100 * x) for x in rng([r["gross_error_rate"] for r in p8], 3)))
    p30 = next(r for r in p8 if float(r["target_az_deg"]) == 30)
    check("P8-C E3 15 kHz az 30: rate and 95 % interval (%)", (65, 62, 68),
          tuple(round(100 * float(p30[k])) for k in ("gross_error_rate", "gross_error_lo", "gross_error_hi")))
    st = float(p30["sigma_total_phase_deg"])
    tim = math.degrees(2 * math.pi * 15000 * 1e-5)
    check("E3 15 kHz: timing / total phase sigma (deg)", (54, 66), (round(tim), round(st)))
    check("E3 15 kHz: timing share of phase variance", "about two thirds", "about two thirds" if 0.6 < (tim / st) ** 2 < 0.72 else f"{(tim / st) ** 2:.2f}")

    # ---- item 6: lines structurally ambiguous
    lines = [r for r in mc if r["array_id"] in ("A1", "A2") and r["structural_ambiguity"] in ("true", "false")]
    not_amb = sorted({float(r["target_az_deg"]) for r in lines if r["structural_ambiguity"] == "false"})
    check("A1/A2: cases without structural ambiguity occur only at endfire (target az)", [0.0], not_amb)
    check("A1/A2: structurally ambiguous cases exist at every non-endfire target with a closed mainlobe", True,
          all(r["structural_ambiguity"] == "true" for r in lines if float(r["target_az_deg"]) not in (0.0, 180.0)))

    # ---- item 7: host noise
    hn = [r for r in P("host_noise.csv") if float(r["hnr_db"]) == 10]
    h100 = [r for r in hn if float(r["f_hz"]) == 100]
    check("host +10 dB, 100 Hz, median gain, arrays <= 1.07 m (dB)", (0.0, 0.2), rng([r["rag_median_db"] for r in h100 if r["array_id"] in small], 1))
    check("host +10 dB, 100 Hz, median gain, V-D and V-DS (dB)", (2.1, 3.2), rng([r["rag_median_db"] for r in h100 if r["array_id"] in ("V-D", "V-DS")], 1))
    h2k = [r for r in hn if float(r["f_hz"]) == 2000 and r["array_id"] in small]
    check("host +10 dB, 2 kHz, median gain range (dB)", (4.7, 12.0), rng([r["rag_median_db"] for r in h2k], 1))
    check("host +10 dB, 2 kHz, worst steering range (dB)", (0.3, 1.7), rng([r["rag_min_db"] for r in h2k], 1))

    # ---- item 8: Pareto
    par = P("pareto_tolerance_sensitivity.csv")
    d = {(r["set"], float(r["tolerance_scale"])): r["dominated"] for r in par}
    s01 = [k for k in d if k[0].startswith("SIM-01 all")]
    check("SIM-01 set: A2 dominated only from 2x tolerance", True,
          all(("A2" in d[k]) == (k[1] >= 2) for k in s01))
    s02 = [k for k in d if k[0].startswith("SIM-02A")]
    vd = sorted(k[1] for k in s02 if "V-D (by V-DS)" in d[k])
    check("SIM-02A set: V-D dominated by V-DS at scales", [1.0, 2.0], vd)

    # ---- SIM-01 closure ratios (cover message), horizon ring
    s1t = {r["array_id"]: r for r in csv.DictReader(open(Path(a.sim01) / "tables" / "thresholds_summary.csv")) if r["ring"] == "horizon"}

    def ratios(k):
        r = s1t[k]
        gl, gh = float(r["f_sl_max_hz"]), float(r["f_amb_m3db_min_hz"])
        ml, mh = float(r["f_sl_median_hz"]), float(r["f_amb_m3db_median_hz"])
        return rd(gh / gl, 2), rd(mh / ml, 2)

    check("SIM-01 horizon guaranteed ratios A1, A3, A4", (1.77, 1.28, 1.06), tuple(ratios(k)[0] for k in ("A1", "A3", "A4")))
    check("SIM-01 horizon median ratios A1, A3, A4", (3.54, 1.54, 1.36), tuple(ratios(k)[1] for k in ("A1", "A3", "A4")))

    w = max(len(x[1]) for x in RESULTS)
    for ok, label, q, cpt in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {label:<{w}}  quoted {q}  computed {cpt}")
    nf = sum(not x[0] for x in RESULTS)
    print(f"\n{len(RESULTS) - nf} of {len(RESULTS)} claims pass")
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
