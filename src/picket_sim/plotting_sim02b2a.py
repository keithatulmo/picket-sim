"""SIM-02B.2-A figures (all values read from the run's own rows)."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

NCOL = {"ORACLE": "#0b0b0b", "NOMINAL": "#9ca3af", "TREF-CA16": "#2f6fb0", "TREF-OS16": "#7aa6d6",
        "FREF-CA8": "#c2410c", "FREF-OS8": "#f59e0b", "TREF-CA16-G8": "#15803d"}


def _save(fig, out: Path, name: str, names: list):
    fig.savefig(out / name, dpi=130, bbox_inches="tight")
    plt.close(fig)
    names.append(name)


def make_figures(study, out: Path, thr_rows, pfa_rows, pd_rows, loss_rows, gain_rows, err_rows):
    out.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    p0 = 0.001
    norms = [n["id"] for n in study.norms]
    scen = [s for s in study.scen if s != "CONTAM"]

    # 1. false-alarm stability across scenarios, C1
    combos = [("A0", "single", "tonal"), ("P8-C", "beam_search", "tonal"), ("A0", "single", "energy"),
              ("P8-C", "beam_search", "energy")]
    fig, axes = plt.subplots(1, len(combos), figsize=(16, 4.2), sharey=True)
    for ax, (c, m, d) in zip(axes, combos):
        for k, nid in enumerate(norms):
            xs, ys, lo, hi = [], [], [], []
            for i, sc in enumerate(scen):
                r = [x for x in pfa_rows if x["candidate"] == c and x["mode"] == m and x["detector"] == d
                     and x["normalizer"] == nid and x["scenario"] == sc and x["cell"] == "C1"
                     and x["pfa_target"] == p0]
                if r:
                    xs.append(i + 0.1 * (k - len(norms) / 2))
                    ys.append(max(r[0]["realized_pfa"], 2e-5))
                    lo.append(max(r[0]["realized_lo"], 2e-5))
                    hi.append(max(r[0]["realized_hi"], 2e-5))
            if xs:
                ax.errorbar(xs, ys, yerr=[np.array(ys) - np.array(lo), np.array(hi) - np.array(ys)], fmt="o", ms=3,
                            color=NCOL.get(nid, "k"), label=nid, lw=0.8)
        ax.axhline(p0, color="k", lw=0.8, ls="--")
        ax.set_yscale("log")
        ax.set_xticks(range(len(scen)), scen, rotation=45, fontsize=7)
        ax.set_title(f"{c} {m} {d}, C1 (B2, 1 s)", fontsize=9)
    axes[0].set_ylabel("realized Pfa at target 1e-3 (95 %); zero counts at 2e-5")
    axes[0].legend(fontsize=6)
    fig.tight_layout()
    _save(fig, out, "s2b2a_fig01_pfa_stability.png", names)

    # 2. detection loss against ORACLE, STAT, C1, Pd 0.5
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for ax, (c, m) in zip(axes, [("A0", "single"), ("P8-C", "beam_search"), ("P8-C", "incoherent")]):
        cls = ["tone", "harmonic", "broadband", "chirp"]
        for k, nid in enumerate([n for n in norms if n != "ORACLE"]):
            vals = []
            for cl in cls:
                r = [x for x in loss_rows if x["candidate"] == c and x["mode"] == m and x["normalizer"] == nid
                     and x["scenario"] == "STAT" and x["cell"] == "C1" and x["class"] == cl and x["pfa_target"] == p0
                     and x["pd_target"] == 0.5]
                vals.append(r[0]["loss_db"] if r else np.nan)
            ax.bar(np.arange(len(cls)) + 0.15 * (k - 2), vals, width=0.15, color=NCOL.get(nid, "k"), label=nid)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(range(len(cls)), cls)
        ax.set_title(f"{c} {m}: loss vs ORACLE, STAT, C1", fontsize=9)
    axes[0].set_ylabel("detection loss (dB), Pd 0.5, Pfa 1e-3")
    axes[0].legend(fontsize=7)
    _save(fig, out, "s2b2a_fig02_detection_loss.png", names)

    # 3. Pd curves, tone, C1 STAT
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, (c, m) in zip(axes, [("A0", "single"), ("P8-C", "beam_search")]):
        for nid in norms:
            rr = sorted([x for x in pd_rows if x["candidate"] == c and x["mode"] == m and x["normalizer"] == nid
                         and x["scenario"] == "STAT" and x["cell"] == "C1" and x["class"] == "tone"
                         and x["pfa_target"] == p0], key=lambda x: x["snr_db"])
            if rr:
                ax.plot([x["snr_db"] for x in rr], [x["pd"] for x in rr], color=NCOL.get(nid, "k"), label=nid)
        ax.set_xlabel("tone SNR per element (dB re 1 Hz)")
        ax.set_title(f"{c} {m}, tone, C1, STAT", fontsize=9)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Pd at Pfa = 1e-3")
    axes[0].legend(fontsize=7)
    _save(fig, out, "s2b2a_fig03_pd_tone.png", names)

    # 4. estimation error by scenario, P8-C beam search, C1
    fig, ax = plt.subplots(figsize=(11, 4.2))
    adapt = [n["id"] for n in study.norms if n["type"] not in ("oracle", "nominal")]
    for k, nid in enumerate(adapt):
        for i, sc in enumerate(scen):
            r = [x for x in err_rows if x["candidate"] == "P8-C" and x["mode"] == "beam_search" and x["normalizer"] == nid
                 and x["scenario"] == sc and x["cell"] == "C1"]
            if r:
                x0 = i + 0.15 * (k - 1.5)
                ax.plot([x0, x0], [r[0]["p05_db"], r[0]["p95_db"]], color=NCOL.get(nid, "k"), lw=1)
                ax.plot(x0, r[0]["bias_db"], "o", color=NCOL.get(nid, "k"), ms=3, label=nid if i == 0 else None)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(range(len(scen)), scen, rotation=30, fontsize=8)
    ax.set_ylabel("background estimate / true (dB): mean and 5 to 95 %")
    ax.set_title("P8-C beam-search background estimation error, C1", fontsize=9)
    ax.legend(fontsize=7)
    _save(fig, out, "s2b2a_fig04_estimation_error.png", names)

    # 5. A0 CFAR loss against reference count: exact law and measured
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ms = sorted({int(n["M"]) for n in study.a0_extra} | {16})
    from .noise_estimation import cfar_loss_db
    K = study.grid("C1").K
    mm = np.array([2, 4, 8, 16, 32, 64, 128, 256])
    ax.plot(mm, [cfar_loss_db(p0, K, int(m)) for m in mm], "k-", label="exact large-SNR threshold ratio")
    meas = []
    for m in ms:
        nid = "TREF-CA16" if m == 16 else f"TREF-CA{m}-A0"
        r = [x for x in loss_rows if x["candidate"] == "A0" and x["normalizer"] == nid and x["scenario"] == "STAT"
             and x["cell"] == "C1" and x["class"] == "tone" and x["pfa_target"] == p0 and x["pd_target"] == 0.5]
        meas.append(r[0]["loss_db"] if r else np.nan)
    ax.plot(ms, meas, "o", color="#2f6fb0", label="measured, tone, Pd 0.5")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("reference windows M")
    ax.set_ylabel("CFAR loss (dB), Pfa 1e-3, B2 1 s")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)
    _save(fig, out, "s2b2a_fig05_cfar_loss_vs_M.png", names)

    # 6. contamination
    if "CONTAM" in study.scen:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
        for ax, cl in zip(axes, ("tone", "broadband")):
            for nid in ("ORACLE", "TREF-CA16", "TREF-CA16-G8", "TREF-OS16", "FREF-OS8"):
                for sc, ls in (("STAT", ":"), ("CONTAM", "-")):
                    rr = sorted([x for x in pd_rows if x["candidate"] == "P8-C" and x["mode"] == "beam_search"
                                 and x["normalizer"] == nid and x["scenario"] == sc and x["cell"] == "C1"
                                 and x["class"] == cl and x["pfa_target"] == p0], key=lambda x: x["snr_db"])
                    if rr:
                        ax.plot([x["snr_db"] for x in rr], [x["pd"] for x in rr], ls, color=NCOL.get(nid, "k"),
                                label=f"{nid} {sc}" if cl == "tone" else None)
            ax.set_title(f"P8-C beam search, {cl}, C1: STAT (dotted) and CONTAM (solid)", fontsize=9)
            ax.set_xlabel("tone SNR per element (dB re 1 Hz)" if cl == "tone" else "in-band SNR per element (dB)")
            ax.grid(alpha=0.3)
        axes[0].set_ylabel("Pd at Pfa = 1e-3")
        axes[0].legend(fontsize=6)
        _save(fig, out, "s2b2a_fig06_contamination.png", names)
    return names
