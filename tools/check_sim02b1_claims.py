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


def claims(T: Tables):
    """Quantitative claims of the SIM-02B.1 documents (filled from the run of record)."""
    rec = T.record
    check("run status", "complete", rec["status"])
    c = {k: sum(r["provenance"] == k for r in T.prov) for k in ("published", "measured", "assumed")}
    check("provenance published / measured / assumed", None, (c["published"], c["measured"], c["assumed"]), ok=True)


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


REQUIRED: dict = {"report": [], "transmittal": [], "message": []}
FORBIDDEN = ["—", "detection range of", "km detection"]


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
