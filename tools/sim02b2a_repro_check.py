"""Partial reproduction of the SIM-02B.2-A run of record: recompute selected cases, require identical table rows.

A full rerun takes about three hours on four cores. Every work unit of the study is seeded by its own identity
(candidate, cell, scenario, chunk), independent of worker scheduling, so any single unit can be recomputed alone.
This tool rebuilds the study from the resolved configuration stored in the run record, recalibrates the named
calibration cases, evaluates the named evaluation cases with the run's own thresholds, formats every value with the
same table writer, and compares the rows with the run tables string for string. Exit status 1 on any difference.

    python tools/sim02b2a_repro_check.py results/sim02b2a/<run_id> [--cal A0:C2 A1:C2] [--eval A0:C2:STEP+3 ...]

Defaults (about 10 minutes on one core): calibration A0:C2 and A1:C2; evaluation A0:C2:STEP+3, A1:C2:STEP+3 and
A1:C2:COH.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from picket_sim.experiments.sim02b2a import CalCase, EvalCase, Sim02B2AStudy  # noqa: E402
from picket_sim.tables import fmt_value  # noqa: E402

KEYS = {"thresholds.csv": ("candidate", "cell", "normalizer", "mode", "detector", "pfa_target"),
        "realized_pfa.csv": ("candidate", "cell", "scenario", "normalizer", "mode", "detector", "pfa_target"),
        "estimation_error.csv": ("candidate", "cell", "scenario", "normalizer", "mode"),
        "snr_required.csv": ("candidate", "cell", "scenario", "class", "normalizer", "mode", "pfa_target",
                             "pd_target")}


def _num(x):
    return float(x) if x not in ("", None) else float("nan")  # the table writer stores nan as an empty field


def as_strings(rows):
    return [{k: fmt_value(v) for k, v in r.items()} for r in rows]


def compare(name, run_rows, new_rows, where):
    key = KEYS[name]
    sel = [r for r in run_rows if all(r[k] == v for k, v in where.items())]
    a = {tuple(r[k] for k in key): r for r in sel}
    b = {tuple(r[k] for k in key): r for r in new_rows}
    problems = []
    if set(a) != set(b):
        problems.append(f"row keys differ: {len(set(a) - set(b))} only in run, {len(set(b) - set(a))} only in rerun")
    for k in sorted(set(a) & set(b)):
        diff = [c for c in a[k] if a[k][c] != b[k].get(c, "")]
        if diff:
            problems.append(f"{k}: columns {diff} differ, e.g. {diff[0]}: run {a[k][diff[0]]} rerun {b[k].get(diff[0], "")}")
    return len(a), problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--cal", nargs="*", default=["A0:C2", "A1:C2"])
    ap.add_argument("--eval", nargs="*", default=["A0:C2:STEP+3", "A1:C2:STEP+3", "A1:C2:COH"])
    a = ap.parse_args(argv)
    run = Path(a.run)
    rec = json.loads((run / "record.json").read_text())
    st = Sim02B2AStudy(rec["config_resolved"], log=lambda m: None)
    tab = {n: list(csv.DictReader(open(run / "tables" / n))) for n in KEYS}
    thr_run = tab["thresholds.csv"]
    fails, lines = 0, []
    for spec in a.cal:
        cand, cell = spec.split(":")
        t0 = time.time()
        res = st.calibrate(CalCase(cand, cell))
        n, prob = compare("thresholds.csv", thr_run, as_strings(res["thresholds"]), {"candidate": cand, "cell": cell})
        lines.append(f"{'PASS' if not prob else 'FAIL'}  calibration {spec}: {n} threshold rows "
                     f"({time.time() - t0:.0f} s)")
        lines += [f"      {p}" for p in prob[:5]]
        fails += bool(prob)
    # evaluation with the run's thresholds (parsed back to numbers, as the run passed them)
    thresholds = {}
    for r in thr_run:
        k = (r["candidate"], r["cell"], r["normalizer"], r["mode"], r["detector"], float(r["pfa_target"]))
        thresholds[k] = {"eta": _num(r["eta"]), "eta_lo": _num(r["eta_lo"]), "eta_hi": _num(r["eta_hi"]),
                         "method": r["method"]}
    for spec in a.eval:
        cand, cell, sc = spec.split(":")
        t0 = time.time()
        res = st.evaluate(EvalCase(cand, cell, sc), thresholds)
        for name, rows in (("realized_pfa.csv", res["pfa"]), ("estimation_error.csv", res["err"]),
                           ("snr_required.csv", res["snr"])):
            n, prob = compare(name, tab[name], as_strings(rows), {"candidate": cand, "cell": cell, "scenario": sc})
            lines.append(f"{'PASS' if not prob else 'FAIL'}  evaluation {spec} {name}: {n} rows "
                         f"({time.time() - t0:.0f} s)")
            lines += [f"      {p}" for p in prob[:5]]
            fails += bool(prob)
    print("\n".join(lines))
    print(f"\n{'all identical' if not fails else f'{fails} comparisons differ'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
