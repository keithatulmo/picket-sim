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
``--allow-dirty`` is given (the dirty flag is then printed in the output).
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
from picket_sim.records import git_state  # noqa: E402

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True, help="output path stem, e.g. reports/SIM-02A_criterion_margin")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args()

    run = Path(args.run_dir)
    record = json.load(open(run / "record.json"))
    cfg = record["config_resolved"]
    gs = git_state(REPO)
    if gs["git_dirty"] and not args.allow_dirty:
        raise SystemExit("working tree is dirty; commit first or pass --allow-dirty")

    levels = sorted({round(L + d, 6) for L in NOMINAL for d in (-DELTA_DB, 0.0, DELTA_DB)}, reverse=True)
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
    n_checked = 0
    for aid, r in summ.items():
        for L in NOMINAL:
            lv = _lvl(L)
            for key in (f"guaranteed_{lv}_lo_hz", f"guaranteed_{lv}_hi_hz", f"guaranteed_{lv}_ratio",
                        f"median_{lv}_ratio"):
                a, b = float(r[key]), _f(ref[aid][key])
                if not _same(a, b):
                    raise RuntimeError(f"self-check failed: {aid} {key} recomputed {a!r} vs run table {b!r}")
                n_checked += 1

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
    for spec, g in study.multichannel:
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
    with open(f"{out}_psl.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(psl_rows[0].keys()))
        w.writeheader()
        w.writerows(psl_rows)

    # ---- plateau summary: maximum and median over the band of the worst-steering PSL
    by_id: dict[str, list[dict]] = {}
    for p in psl_rows:
        by_id.setdefault(p["array_id"], []).append(p)

    md = [
        "# SIM-02A supplement: sensitivity of guaranteed bands to the ambiguity criterion",
        "",
        f"Generated by `tools/sim02a_criterion_margin.py` from the resolved configuration in "
        f"`{run.as_posix()}/record.json` (config sha256 `{record['config_sha256'][:16]}...`). "
        f"Code commit `{(gs['git_commit'] or 'unknown')[:7]}`"
        f"{' (DIRTY TREE)' if gs['git_dirty'] else ' (clean tree)'}. "
        "The run directory is read, never written.",
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

    knife = []
    for row in band_rows:
        for L in NOMINAL:
            lo_v, nom, hi_v = (float(row[f"guaranteed_{_lvl(x)}_ratio"]) for x in (L + DELTA_DB, L, L - DELTA_DB))
            if all(np.isfinite([lo_v, nom, hi_v])) and abs(lo_v - hi_v) > KNIFE_REL * nom:
                knife.append(f"{row['array_id']} at {L:g} dB ({_ratio_txt(lo_v)} at {L + DELTA_DB:g} dB, "
                             f"{_ratio_txt(hi_v)} at {L - DELTA_DB:g} dB)")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
