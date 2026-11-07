"""Derive SIM-01 conventional-band definitions from the immutable run-of-record tables.

Review item 3 (SIM-01 technical review): distinguish bands computed from median steering from
bands guaranteed across the modeled steering set. This script reads existing tables only; it does
not recompute or alter any experimental result.

    python tools/sim01_band_definitions.py results/sim01/<run_id> > reports/SIM-01_band_definitions.md

Definitions per steering set (horizon ring, depressed ring), for ambiguity level -3 dB:

* median band:     [median f_SL, median f_amb]      typical steering direction
* as reported:     [median f_SL, earliest f_amb]    SIM-01 Rev 0 report convention (mixed)
* guaranteed band: [latest f_SL, earliest f_amb]    holds for EVERY steering direction in the set;
                                                    empty if latest f_SL >= earliest f_amb
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def fmt(v: float) -> str:
    if v != v:  # nan
        return "n/a"
    if v == float("inf"):
        return "> 10,000"
    return f"{v:,.0f}"


def main(run_dir: str) -> int:
    run = Path(run_dir)
    rows = list(csv.DictReader(open(run / "tables" / "thresholds_summary.csv")))
    out = [
        "# SIM-01 conventional-band definitions (derived)",
        "",
        f"Derived by `tools/sim01_band_definitions.py` from `{run.as_posix()}/tables/thresholds_summary.csv`.",
        "No experimental result was recomputed or altered. Frequencies in Hz; ambiguity level -3 dB.",
        "",
        "* **Median band**: from the median f_SL to the median f_amb over the steering set (a typical direction).",
        "* **As reported (Rev 0)**: median f_SL to the earliest f_amb. This mixed convention was used in the",
        "  SIM-01 Rev 0 report and is neither typical nor guaranteed.",
        "* **Guaranteed band**: from the latest f_SL to the earliest f_amb, so that every steering direction in",
        "  the set has a closed mainlobe and no -3 dB ambiguity lobe. Empty when latest f_SL >= earliest f_amb.",
        "",
        "| ID | Steering set | Median band | Ratio | As reported (Rev 0) | Ratio | Guaranteed band | Ratio |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r["array_id"] == "A0":
            out.append(f"| A0 | {r['ring']} | none (no pattern) | n/a | none | n/a | none | n/a |")
            continue
        g = lambda k: float(r[k]) if r[k] not in ("", "inf") else (float("inf") if r[k] == "inf" else float("nan"))  # noqa: E731
        sl_med, sl_max = g("f_sl_median_hz"), g("f_sl_max_hz")
        am_med, am_min = g("f_amb_m3db_median_hz"), g("f_amb_m3db_min_hz")

        def band(lo, hi):
            if not (lo < hi):
                return "empty", "n/a"
            ratio = "n/a" if hi == float("inf") else f"{hi / lo:.2f}"
            return f"{fmt(lo)} to {fmt(hi)}", ratio

        b1, q1 = band(sl_med, am_med)
        b2, q2 = band(sl_med, am_min)
        b3, q3 = band(sl_max, am_min)
        out.append(f"| {r['array_id']} | {r['ring']} | {b1} | {q1} | {b2} | {q2} | {b3} | {q3} |")
    out += ["", "Steering sets: horizon ring (el = 0 deg) and depressed ring (el = -30 deg), 24 azimuths each at "
            "15 deg spacing. 'Guaranteed' applies only to these sampled directions and to the idealized model."]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
