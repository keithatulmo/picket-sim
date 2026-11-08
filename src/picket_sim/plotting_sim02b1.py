"""SIM-02B.1 figures (all values read from the run's own rows)."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PAL = {"A0": "#0b0b0b", "A1": "#2f6fb0", "A2": "#7aa6d6", "A4": "#8a5a2b", "P6-C": "#c9781f", "P8-C": "#c2410c",
       "P8-E": "#7c3aed", "SQ4-C": "#15803d", "V-C": "#6b7280", "V-D": "#9ca3af", "V-DS": "#d1d5db"}
MODE_LS = {"single": "-", "beam_known": "--", "beam_search": "-", "incoherent": ":"}
CLASSES = ("tone", "harmonic", "broadband", "chirp")


def _save(fig, out: Path, name: str, names: list):
    fig.savefig(out / name, dpi=130, bbox_inches="tight")
    plt.close(fig)
    names.append(name)


def make_figures(study, out: Path, pd_rows, gain_rows, thr_rows, roc_rows, cov_rows, wave_dir: Path, wave_rows):
    out.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    p0 = 0.001

    # 1. Pd curves, B2, 1 s, N-AMB, per class
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    sel = [("A0", "single"), ("P8-C", "beam_known"), ("P8-C", "beam_search"), ("P8-C", "incoherent"),
           ("A1", "beam_search"), ("A4", "beam_search")]
    for ax, cls in zip(axes.flat, CLASSES):
        for cand, mode in sel:
            rows = [r for r in pd_rows if r["candidate"] == cand and r["mode"] == mode and r["band"] == "B2"
                    and r["window_s"] == 1.0 and r["scenario"] == "N-AMB" and r["class"] == cls
                    and r["pfa_target"] == p0]
            if not rows:
                continue
            rows.sort(key=lambda r: r["snr_db"])
            s = [r["snr_db"] for r in rows]
            ax.plot(s, [r["pd"] for r in rows], MODE_LS[mode], color=PAL.get(cand, "k"), label=f"{cand} {mode}")
            ax.fill_between(s, [r["pd_lo"] for r in rows], [r["pd_hi"] for r in rows], color=PAL.get(cand, "k"),
                            alpha=0.12, lw=0)
        ax.set_title(f"{cls}, B2, T = 1 s, ambient-limited (N-AMB)")
        ax.set_xlabel({"tone": "SNR (dB re 1 Hz) per element", "harmonic": "SNR per harmonic (dB re 1 Hz)",
                       "broadband": "in-band SNR per element (dB)", "chirp": "E/N0_eff per element (dB)"}[cls])
        ax.set_ylabel("Pd at Pfa = 1e-3")
        ax.grid(alpha=0.3)
    axes.flat[0].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    _save(fig, out, "s2b1_fig01_pd_curves_B2_1s.png", names)

    # 2. detection gain vs A0 heatmaps (N-AMB, beam search and beam known), Pfa 1e-3, Pd 0.5
    cands = [c for c in study.cand_specs if c != "A0"]
    cols = [(b, w) for b in ("B1", "B2", "B3") for w in (0.1, 1.0, 10.0)]
    for mode, fname in (("beam_search", "s2b1_fig02_gain_beam_search.png"),
                        ("beam_known", "s2b1_fig03_gain_beam_known.png"),
                        ("incoherent", "s2b1_fig04_gain_incoherent.png")):
        fig, axes = plt.subplots(1, 4, figsize=(16, 4.6), sharey=True)
        for ax, cls in zip(axes, CLASSES):
            m = np.full((len(cands), len(cols)), np.nan)
            for r in gain_rows:
                if (r["mode"] == mode and r["scenario"] == "N-AMB" and r["class"] == cls and r["pfa_target"] == p0
                        and r["pd_target"] == 0.5 and r["candidate"] in cands and (r["band"], r["window_s"]) in cols):
                    m[cands.index(r["candidate"]), cols.index((r["band"], r["window_s"]))] = r["gain_db"]
            im = ax.imshow(m, cmap="RdBu_r", vmin=-9, vmax=9, aspect="auto")
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    if np.isfinite(m[i, j]):
                        ax.text(j, i, f"{m[i, j]:.1f}", ha="center", va="center", fontsize=6.5)
            ax.set_xticks(range(len(cols)), [f"{b}\n{w:g}s" for b, w in cols], fontsize=7)
            ax.set_yticks(range(len(cands)), cands, fontsize=8)
            ax.set_title(f"{cls}: {mode}", fontsize=9)
        fig.colorbar(im, ax=axes, shrink=0.8, label="gain over A0 (dB), Pd 0.5, Pfa 1e-3")
        _save(fig, out, fname, names)

    # 5. noise scenarios at T = 1 s, beam search, Pd 0.5, Pfa 1e-3
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    prim = [c for c in ("A1", "A2", "P6-C", "P8-C", "A4") if c in study.cand_specs]
    scen = ("N-AMB", "N-FLOW", "N-SENS")
    for ax, cls in zip(axes, CLASSES):
        for k, sc in enumerate(scen):
            for b_i, b in enumerate(("B1", "B2", "B3")):
                vals = []
                for c in prim:
                    v = [r["gain_db"] for r in gain_rows if r["candidate"] == c and r["mode"] == "beam_search"
                         and r["scenario"] == sc and r["band"] == b and r["window_s"] == 1.0 and r["class"] == cls
                         and r["pfa_target"] == p0 and r["pd_target"] == 0.5]
                    vals.append(v[0] if v else np.nan)
                x = b_i * 4 + k + np.linspace(-0.3, 0.3, len(prim))
                ax.scatter(x, vals, c=[PAL[c] for c in prim], s=14, marker="os^"[k])
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks([1, 5, 9], ["B1", "B2", "B3"])
        ax.set_title(f"{cls}: beam search, T = 1 s (o AMB, s FLOW, ^ SENS)", fontsize=8)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("gain over A0 (dB)")
    _save(fig, out, "s2b1_fig05_scenarios.png", names)

    # 6. false-alarm calibration: matched (empirical and exact) and mismatched
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    ax = axes[0]
    for meth, col in (("exact", "#2f6fb0"), ("empirical", "#c2410c")):
        rr = [r for r in thr_rows if r["kind"] == "primary" and r["method"] == meth and r["n_eval"] * r["pfa_target"] >= 10]
        for r in rr:
            ax.errorbar(r["pfa_target"] * (1 + 0.15 * np.random.default_rng(len(r["candidate"])).standard_normal()),
                        r["realized_pfa"], yerr=[[r["realized_pfa"] - r["realized_lo"]],
                                                 [r["realized_hi"] - r["realized_pfa"]]], fmt=".", color=col, ms=2,
                        alpha=0.4, lw=0.5)
    ax.plot([1e-3, 1e-2], [1e-3, 1e-2], "k-", lw=0.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("target Pfa")
    ax.set_ylabel("realized Pfa (independent evaluation set, 95 %)")
    ax.set_title("matched noise: exact (blue) and empirical (orange) thresholds", fontsize=9)
    ax = axes[1]
    mm = [r for r in thr_rows if r["kind"] == "mismatch" and r["pfa_target"] == 0.01 and math.isfinite(r["eta"])]
    labels = sorted({(r["experiment"], r["candidate"], r["mode"], r["band"]) for r in mm})
    det_col = {"tonal": "#2f6fb0", "harmonic": "#15803d", "energy": "#c2410c", "mf": "#7c3aed"}
    for i, lab in enumerate(labels):
        for r in mm:
            if (r["experiment"], r["candidate"], r["mode"], r["band"]) == lab:
                ax.plot(max(r["realized_pfa"], 1e-5), i, "o", color=det_col[r["detector"]], ms=3)
    ax.axvline(0.01, color="k", lw=0.8)
    ax.set_xscale("log")
    ax.set_yticks(range(len(labels)), [" ".join(map(str, lab)) for lab in labels], fontsize=5)
    ax.set_xlabel("realized Pfa at target 0.01 (tonal blue, harmonic green, energy orange, mf purple)")
    ax.set_title("mismatched noise assumptions (B1/B2, T = 1 s)", fontsize=9)
    fig.tight_layout()
    _save(fig, out, "s2b1_fig06_pfa_calibration.png", names)

    # 7. ROC
    if roc_rows:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        for key in sorted({(r["candidate"], r["mode"]) for r in roc_rows}):
            rr = sorted([r for r in roc_rows if (r["candidate"], r["mode"]) == key], key=lambda r: r["pfa"])
            ax.plot([r["pfa"] for r in rr], [r["pd"] for r in rr], MODE_LS[key[1]], color=PAL.get(key[0], "k"),
                    label=f"{key[0]} {key[1]}")
        ax.set_xscale("log")
        ax.set_xlabel("Pfa (calibration set)")
        ax.set_ylabel("Pd")
        ax.set_title(f"ROC, tone, B2, T = 1 s, N-AMB, SNR {roc_rows[0]['snr_db']:.1f} dB re 1 Hz", fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
        _save(fig, out, "s2b1_fig07_roc.png", names)

    # 8. waveform examples
    if wave_rows:
        fig, axes = plt.subplots(len(wave_rows), 1, figsize=(10, 2.2 * len(wave_rows)), squeeze=False)
        for ax, w in zip(axes[:, 0], wave_rows):
            d = np.load(wave_dir / w["file"])
            t = np.arange(d["noise"].shape[1]) / float(d["fs"])
            ax.plot(t, d["noise"][0] + d["signal"][0], lw=0.4, color="#6b7280", label="element 0: noise + signal")
            ax.plot(t, d["signal"][0], lw=0.6, color="#c2410c", label="signal alone")
            ax.set_title(f"{w['class']}, {w['candidate']}, {w['band']}, {w['window_s']:g} s, input SNR "
                         f"{w['snr_db']:g} dB, azimuth {w['azimuth_deg']:.0f} deg", fontsize=8)
            ax.set_ylabel("uPa")
        axes[0, 0].legend(fontsize=7)
        axes[-1, 0].set_xlabel("time (s)")
        fig.tight_layout()
        _save(fig, out, "s2b1_fig08_waveforms.png", names)
    return names
