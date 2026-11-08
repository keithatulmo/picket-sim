"""SIM-02A supplement: how sensitive are the guaranteed bands to the ambiguity criterion itself?

The SIM-02A run of record reports guaranteed conventional bands at -3, -6 and -10 dB (D03). A band
edge is set by the frequency at which an outside lobe first reaches the criterion. When a candidate's
intrinsic sidelobe plateau sits just below a criterion, a few hundredths of a dB in the criterion
moves the band edge by a large factor. This supplement measures that directly.

It re-runs the SIM-02A threshold code (``Sim02AStudy.thresholds`` / ``threshold_summary``) with the
resolved configuration stored in the run record, at each criterion and at the criterion +/- 0.1 dB,
and tabulates the worst-steering peak sidelobe level (observable space, error-free, narrowband DAS)
across each candidate's guaranteed -3 dB band. It never writes into the run directory.

Self-check: the guaranteed bands recomputed at the nominal criteria must reproduce the run-of-record
``thresholds_summary.csv`` to a relative 1e-9, otherwise the script raises.

    python tools/sim02a_criterion_margin.py results/sim02a/<run_id> --out reports/SIM-02A_criterion_margin

Writes ``<out>.md``, ``<out>_bands.csv`` and ``<out>_psl.csv``. Requires a clean tree unless
``--allow-dirty`` is given (the dirty flag is then printed in the output). Outside a git checkout (for
example an unpacked review-package source snapshot) the output says so instead of naming a commit.

Other modes:

* ``--levels L1 L2 ...`` computes guaranteed bands at the listed criteria (the nominal -3, -6 and -10 dB
  are always added so that the self-check runs) and writes ``<out>.md`` and ``<out>_bands.csv`` only,
  unless ``--psl`` is also given. Used for the D06 criterion-sensitivity table (SIM-02A review).
* ``--expect STEM`` compares the CSV files just written with ``STEM_bands.csv`` (and ``STEM_psl.csv``)
  byte for byte and exits with status 1 if they differ. Used to verify reproduction from a snapshot.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from picket_sim.acoustics import PlaneWaveManifold  # noqa: E402
from picket_sim.analysis import _lvl  # noqa: E402
from picket_sim.experiments.sim02a import Sim02AStudy  # noqa: E402
from picket_sim.metrics import observable_lobe_metrics  # noqa: E402
from picket_sim.records import git_state, software_versions  # noqa: E402

NOMINAL = (-3.0, -6.0, -10.0)
DELTA_DB = 0.1
REPRO_REL_TOL = 1e-9
KNIFE_REL = 0.10
PLATEAU_TOL_DB = 1e-3
PLATEAU_MIN_POINTS = 3


def plateau(f_hz: np.ndarray, psl_db: np.ndarray):
    """Longest run of consecutive grid points with PSL constant to PLATEAU_TOL_DB.

    Returns (mean PSL dB, first f, last f) or None if no run reaches PLATEAU_MIN_POINTS.
    """
    best, start = None, 0
    n = len(psl_db)
    for i in range(1, n + 1):
        if i == n or not (np.isfinite(psl_db[i]) and np.isfinite(psl_db[i - 1])
                          and abs(psl_db[i] - psl_db[i - 1]) <= PLATEAU_TOL_DB):
            length = i - start
            if length >= PLATEAU_MIN_POINTS and np.isfinite(psl_db[start]) and (best is None or length > best[3]):
                best = (float(np.mean(psl_db[start:i])), float(f_hz[start]), float(f_hz[i - 1]), length)
            start = i
    return best[:3] if best else None


def levels_for(nominal=NOMINAL, delta=DELTA_DB) -> list[float]:
    """Criteria evaluated in the default mode: each nominal level and the level +/- delta."""
    return sorted({round(L + d, 6) for L in nominal for d in (-delta, 0.0, delta)}, reverse=True)


def check_reproduction(summ: dict, ref: dict, nominal=NOMINAL) -> int:
    """Raise if recomputed bands at the nominal criteria differ from the run table; return values checked."""
    n_checked = 0
    if set(summ) != set(ref):
        raise RuntimeError(f"self-check failed: candidate sets differ {sorted(summ)} vs {sorted(ref)}")
    for aid, r in summ.items():
        for L in nominal:
            lv = _lvl(L)
            for key in (f"guaranteed_{lv}_lo_hz", f"guaranteed_{lv}_hi_hz", f"guaranteed_{lv}_ratio",
                        f"median_{lv}_ratio"):
                a, b = float(r[key]), _f(ref[aid][key])
                if not _same(a, b):
                    raise RuntimeError(f"self-check failed: {aid} {key} recomputed {a!r} vs run table {b!r}")
                n_checked += 1
    return n_checked


def knife_edges(band_rows: list[dict], nominal=NOMINAL, delta=DELTA_DB, rel=KNIFE_REL) -> list[str]:
    """Candidates whose guaranteed ratio changes by more than ``rel`` of nominal across +/- delta."""
    knife = []
    for row in band_rows:
        for L in nominal:
            lo_v, nom, hi_v = (float(row[f"guaranteed_{_lvl(round(x, 6))}_ratio"]) for x in (L + delta, L, L - delta))
            if all(np.isfinite([lo_v, nom, hi_v])) and abs(lo_v - hi_v) > rel * nom:
                knife.append(f"{row['array_id']} at {L:g} dB ({_ratio_txt(lo_v)} at {L + delta:g} dB, "
                             f"{_ratio_txt(hi_v)} at {L - delta:g} dB)")
    return knife


def compare_outputs(out: str, expect: str, suffixes=("_bands.csv", "_psl.csv")) -> list[str]:
    """Byte-for-byte comparison of written CSV files against expected files; returns mismatch messages."""
    problems = []
    for suf in suffixes:
        a, b = Path(f"{out}{suf}"), Path(f"{expect}{suf}")
        if not a.exists():
            continue
        if not b.exists():
            problems.append(f"expected file missing: {b}")
        elif a.read_bytes() != b.read_bytes():
            problems.append(f"differs from expected: {a} vs {b}")
    return problems


def provenance_text(gs: dict) -> str:
    """Code provenance phrase for the output header."""
    if gs.get("git_commit") is None:
        return "No git metadata (run from a source snapshot, not a git checkout)"
    return f"Code commit `{gs['git_commit'][:7]}`" + (" (DIRTY TREE)" if gs["git_dirty"] else " (clean tree)")


def _f(x) -> float:
    if x in ("", None):
        return float("nan")
    return float(x)


def _ratio_txt(v: float) -> str:
    if math.isnan(v):
        return "empty"
    if math.isinf(v):
        return "unbounded"
    return f"{v:.2f}"


def _same(a: float, b: float) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= REPRO_REL_TOL * max(1.0, abs(a), abs(b))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True, help="output path stem, e.g. reports/SIM-02A_criterion_margin")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--levels", nargs="+", type=float, default=None,
                    help="custom criteria in dB (nominal levels are added); writes bands only unless --psl")
    ap.add_argument("--psl", action="store_true", help="with --levels, also tabulate peak sidelobe levels")
    ap.add_argument("--expect", default=None, help="compare written CSV files with STEM_bands.csv / STEM_psl.csv")
    args = ap.parse_args(argv)

    run = Path(args.run_dir)
    record = json.load(open(run / "record.json"))
    cfg = record["config_resolved"]
    gs = git_state(REPO)
    if gs["git_dirty"] is True and not args.allow_dirty:
        raise SystemExit("working tree is dirty; commit first or pass --allow-dirty")

    custom = args.levels is not None
    levels = (sorted({round(x, 6) for x in list(args.levels) + list(NOMINAL)}, reverse=True) if custom
              else levels_for())
    do_psl = (not custom) or args.psl
    cfg_mod = dict(cfg)
    cfg_mod["ambiguity_levels_db"] = levels
    log = lambda m: print(m, file=sys.stderr, flush=True)  # noqa: E731
    study = Sim02AStudy(cfg_mod, log)
    t0 = time.time()
    _, alias = study.geometry_table()
    thr = study.thresholds()
    summ = {r["array_id"]: r for r in study.threshold_summary(thr, alias)}

    # ---- self-check against the run of record
    ref = {r["array_id"]: r for r in csv.DictReader(open(run / "tables" / "thresholds_summary.csv"))}
    n_checked = check_reproduction(summ, ref)

    band_rows = []
    for aid, r in summ.items():
        row = {"array_id": aid}
        for L in levels:
            lv = _lvl(L)
            row[f"guaranteed_{lv}_lo_hz"] = r[f"guaranteed_{lv}_lo_hz"]
            row[f"guaranteed_{lv}_hi_hz"] = r[f"guaranteed_{lv}_hi_hz"]
            row[f"guaranteed_{lv}_ratio"] = r[f"guaranteed_{lv}_ratio"]
        band_rows.append(row)

    # ---- worst-steering peak sidelobe across each candidate's guaranteed -3 dB band (error-free)
    psl_rows = []
    lv3 = _lvl(-3.0)
    for spec, g in (study.multichannel if do_psl else []):
        lo, hi = float(summ[g.array_id][f"guaranteed_{lv3}_lo_hz"]), float(summ[g.array_id][f"guaranteed_{lv3}_hi_hz"])
        if not (np.isfinite(lo) and np.isfinite(hi) and lo < hi):
            continue
        man = PlaneWaveManifold(g, study.c0)
        for f in study.f_grid[(study.f_grid >= lo) & (study.f_grid < hi)]:
            vals = []
            for st in study.ring:
                lm = observable_lobe_metrics(man, float(f), st.u, study.levels, study.settings.sphere,
                                             study.settings.reduced_1d_points)
                vals.append(lm.psl_db)
            v = np.array(vals, dtype=float)
            psl_rows.append({"array_id": g.array_id, "f_hz": float(f),
                             "psl_worst_steering_db": float(np.nanmax(v)) if np.isfinite(v).any() else float("nan"),
                             "psl_median_steering_db": float(np.nanmedian(v)) if np.isfinite(v).any() else float("nan"),
                             "n_steering_with_sidelobe": int(np.isfinite(v).sum()), "n_steering": len(v)})
        log(f"  PSL {g.array_id}: done")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}_bands.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(band_rows[0].keys()))
        w.writeheader()
        w.writerows(band_rows)
    if do_psl:
        with open(f"{out}_psl.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(psl_rows[0].keys()))
            w.writeheader()
            w.writerows(psl_rows)
    if custom:
        return _finish_custom(args, out, run, record, gs, levels, band_rows, n_checked, t0, log)

    # ---- plateau summary: maximum and median over the band of the worst-steering PSL
    by_id: dict[str, list[dict]] = {}
    for p in psl_rows:
        by_id.setdefault(p["array_id"], []).append(p)

    md = [
        "# SIM-02A supplement: sensitivity of guaranteed bands to the ambiguity criterion",
        "",
        f"Generated by `tools/sim02a_criterion_margin.py` from the resolved configuration in "
        f"`{run.as_posix()}/record.json` (config sha256 `{record['config_sha256'][:16]}...`). "
        f"{provenance_text(gs)}. "
        "The run directory is read, never written.",
        "",
        "Software: " + ", ".join(f"{k} {v}" for k, v in software_versions().items() if k in ("picket_sim", "python", "numpy"))
        + "; run of record: " + ", ".join(f"{k} {record['software'].get(k)}" for k in ("picket_sim", "python", "numpy")) + ".",
        "",
        f"Self-check: the guaranteed and median bands recomputed at -3, -6 and -10 dB reproduce the run-of-record "
        f"`thresholds_summary.csv` ({n_checked} values, relative tolerance {REPRO_REL_TOL:g}).",
        "",
        "Narrowband DAS, error-free, horizon steering set (24 azimuths at 15 deg), observable-space lobes. "
        "Guaranteed band: latest f_SL to earliest f_amb(L) over the steering set (SIM-01 Rev A definition). "
        "These are criteria sensitivities, not requirements (D03).",
        "",
        "## 1. Guaranteed band ratio at each criterion and at the criterion +/- 0.1 dB",
        "",
        "| ID | -2.9 | **-3.0** | -3.1 | -5.9 | **-6.0** | -6.1 | -9.9 | **-10.0** | -10.1 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    order = [-2.9, -3.0, -3.1, -5.9, -6.0, -6.1, -9.9, -10.0, -10.1]
    for row in band_rows:
        cells = []
        for L in order:
            v = float(row[f"guaranteed_{_lvl(L)}_ratio"])
            t = _ratio_txt(v)
            cells.append(f"**{t}**" if L in NOMINAL else t)
        md.append(f"| {row['array_id']} | " + " | ".join(cells) + " |")

    knife = knife_edges(band_rows)
    md += [
        "",
        "A large change across a 0.2 dB interval means the nominal band edge is set by a sidelobe plateau lying",
        "within 0.1 dB of the criterion, not by a lobe that rises steadily through it.",
        "",
        f"Knife-edge cases (guaranteed ratio changes by more than {KNIFE_REL:.0%} of its nominal value across the "
        f"+/- {DELTA_DB:g} dB interval): " + ("; ".join(knife) if knife else "none") + ".",
        "",
        "## 2. Worst-steering peak sidelobe level across the guaranteed -3 dB band",
        "",
        "Peak sidelobe level (PSL) relative to the mainlobe, maximum over the horizon steering set, at each grid",
        f"frequency ({cfg['frequency_grid']['points_per_decade']} points per decade) inside the guaranteed -3 dB band. "
        "Full values in the `_psl.csv` file.",
        "",
        f"Plateau: the worst-steering PSL where it is constant to {PLATEAU_TOL_DB:g} dB over at least "
        f"{PLATEAU_MIN_POINTS} consecutive grid frequencies (longest such run), with its frequency span.",
        "",
        "| ID | -3 dB band (Hz) | Grid points | Lowest worst-steering PSL (dB) | Plateau (dB) | Plateau span (Hz) | Highest (dB) |",
        "|---|---|---|---|---|---|---|",
    ]
    for aid, ps in by_id.items():
        v = np.array([p["psl_worst_steering_db"] for p in ps], dtype=float)
        fs = np.array([p["f_hz"] for p in ps], dtype=float)
        fin = v[np.isfinite(v)]
        lo = float(summ[aid][f"guaranteed_{lv3}_lo_hz"])
        hi = float(summ[aid][f"guaranteed_{lv3}_hi_hz"])
        pl = plateau(fs, v)
        pl_txt = (f"{pl[0]:.2f}", f"{pl[1]:,.0f} to {pl[2]:,.0f}") if pl else ("none", "n/a")
        if fin.size:
            md.append(f"| {aid} | {lo:,.0f} to {hi:,.0f} | {len(ps)} | {fin.min():.2f} | {pl_txt[0]} | {pl_txt[1]} | {fin.max():.2f} |")
        else:
            md.append(f"| {aid} | {lo:,.0f} to {hi:,.0f} | {len(ps)} | n/a | n/a | n/a | n/a |")
    md += ["", f"Computed in {time.time() - t0:.0f} s.", ""]
    Path(f"{out}.md").write_text("\n".join(md))
    log(f"wrote {out}.md, {out}_bands.csv, {out}_psl.csv")
    return _expect(args, out, log)


def _expect(args, out, log) -> int:
    if not args.expect:
        return 0
    problems = compare_outputs(str(out), args.expect)
    for p in problems:
        log(f"MISMATCH: {p}")
    if problems:
        return 1
    log(f"reproduction check: written CSV files are byte-identical to {args.expect}_*.csv")
    return 0


def _group(levels: list[float]) -> dict[float, list[float]]:
    """Assign each criterion to the nearest nominal level (for table layout)."""
    groups: dict[float, list[float]] = {L: [] for L in NOMINAL}
    for x in levels:
        groups[min(NOMINAL, key=lambda L: abs(L - x))].append(x)
    return {L: sorted(v, reverse=True) for L, v in groups.items()}


def _finish_custom(args, out, run, record, gs, levels, band_rows, n_checked, t0, log) -> int:
    md = [
        "# SIM-02A supplement: guaranteed bands under alternative ambiguity criteria (D06)",
        "",
        f"Generated by `tools/sim02a_criterion_margin.py --levels ...` from the resolved configuration in "
        f"`{run.as_posix()}/record.json` (config sha256 `{record['config_sha256'][:16]}...`). "
        f"{provenance_text(gs)}. The run directory is read, never written.",
        "",
        "Software: " + ", ".join(f"{k} {v}" for k, v in software_versions().items() if k in ("picket_sim", "python", "numpy"))
        + "; run of record: " + ", ".join(f"{k} {record['software'].get(k)}" for k in ("picket_sim", "python", "numpy")) + ".",
        "",
        f"Self-check: the guaranteed and median bands recomputed at -3, -6 and -10 dB reproduce the run-of-record "
        f"`thresholds_summary.csv` ({n_checked} values, relative tolerance {REPRO_REL_TOL:g}).",
        "",
        "Narrowband DAS, error-free, horizon steering set (24 azimuths at 15 deg), observable-space lobes. "
        "Guaranteed band ratio: earliest f_amb(L) over latest f_SL across the steering set. Criteria are applied "
        "in power; -6.0206 dB is half amplitude (20 log10 0.5 = -6.020600 dB to six decimals). The nominal -6 dB "
        "criterion is exactly -6.00 dB in power (D06). Sensitivities, not requirements.",
        "",
    ]
    for L, group in _group(levels).items():
        md += [f"## Criteria near {L:g} dB", "",
               "| ID | " + " | ".join((f"**{x:g}**" if x == L else f"{x:g}") for x in group) + " |",
               "|---|" + "---|" * len(group)]
        for row in band_rows:
            cells = []
            for x in group:
                t = _ratio_txt(float(row[f"guaranteed_{_lvl(x)}_ratio"]))
                cells.append(f"**{t}**" if x == L else t)
            md.append(f"| {row['array_id']} | " + " | ".join(cells) + " |")
        md.append("")
    md += [f"Computed in {time.time() - t0:.0f} s.", ""]
    Path(f"{out}.md").write_text("\n".join(md))
    log(f"wrote {out}.md, {out}_bands.csv")
    return _expect(args, out, log)


if __name__ == "__main__":
    raise SystemExit(main())
