"""SIM-02A figures. No physics: functions receive computed rows. Same conventions as plotting.py."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from . import plotting as P  # noqa: E402  (style, palette, helpers)
from .analysis import _lvl  # noqa: E402

PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GREY = "#8a8985"
FREQ_TICKS = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
FREQ_LABELS = ["20", "50", "100", "200", "500", "1k", "2k", "5k", "10k", "20k"]


def _faxis(ax, axis="x"):
    if axis == "x":
        ax.set_xscale("log")
        ax.set_xticks(FREQ_TICKS, FREQ_LABELS)
        ax.set_xlim(20, 20000)
        ax.set_xlabel("Frequency (Hz)")
    else:
        ax.set_yscale("log")
        ax.set_yticks(FREQ_TICKS, FREQ_LABELS)
        ax.set_ylim(20, 20000)
        ax.set_ylabel("Frequency (Hz)")
    ax.minorticks_off()


def _bands(ax, bands, exploratory):
    for b, (lo, hi) in bands.items():
        ax.axvline(lo, color=P.GRID, linewidth=0.8, zorder=0)
        ax.text(np.sqrt(lo * hi), 1.01, b + (" (expl.)" if b in exploratory else ""), transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=6.5, color=P.INK2)


def _save(fig, outdir, name, written):
    fig.savefig(Path(outdir) / name, metadata={"Software": None})
    plt.close(fig)
    written.append(name)


GROUPS = {
    "Compact (0.42-0.45 m)": ["A1", "A3", "SQ4-C", "P6-C", "P8-C", "V-C"],
    "Extended / intermediate / distributed": ["A2", "SQ4-E", "P6-E", "P8-E", "A4", "V-D", "V-DS"],
}


def _color_map():
    cm = {}
    for ids in GROUPS.values():
        for i, a in enumerate(ids):
            cm[a] = PAL[i % len(PAL)]
    return cm


CMAP = _color_map()


def fig_candidates(study, outdir, written):
    cands = study.cands
    n = len(cands)
    cols = 5
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(2.6 * cols, 2.5 * rows), squeeze=False)
    for ax, (spec, g) in zip(axes.ravel(), cands):
        p = g.positions_m
        sc = ax.scatter(p[:, 0], p[:, 1], c=p[:, 2], cmap="viridis_r", vmin=min(-0.01, p[:, 2].min()), vmax=0.0,
                        s=34, edgecolor=P.INK, linewidth=0.5, zorder=3)
        span = max(np.ptp(p[:, 0]), np.ptp(p[:, 1]), 0.2)
        c = p.mean(axis=0)
        ax.set_xlim(c[0] - 0.65 * span, c[0] + 0.65 * span)
        ax.set_ylim(c[1] - 0.65 * span, c[1] + 0.65 * span)
        ax.set_aspect("equal")
        ax.set_title(f"{g.array_id}: {spec.get('label', '')}", fontsize=7.5)
        ax.text(0.02, 0.02, f"N={g.n_elements}  max {g.aperture_m:.2f} m\nz extent {np.ptp(p[:, 2]):.2f} m",
                transform=ax.transAxes, fontsize=6.5, color=P.INK2)
        ax.set_xlabel("x (m)", fontsize=7)
        ax.set_ylabel("y (m)", fontsize=7)
        ax.tick_params(labelsize=6.5)
    for ax in axes.ravel()[n:]:
        ax.axis("off")
    fig.suptitle("SIM-02A candidates, top views (marker colour: z, darker = deeper). Each panel has its own scale; "
                 "dimensions are annotated", fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig01_candidates.png", written)


def fig_self_noise(study, spec_rows, outdir, written):
    sensors = [c.scenario_id for c in study.sensors]
    fig, axes = plt.subplots(1, len(sensors), figsize=(4.4 * len(sensors), 3.9), sharey=True, squeeze=False)
    for ax, sid in zip(axes[0], sensors):
        rs = [r for r in spec_rows if r["sensor"] == sid]
        f = np.array([r["f_hz"] for r in rs])
        for key, lab, col, ls in (("thermal_db", "hydrophone thermal", PAL[2], "-"), ("preamp_db", "preamplifier", PAL[1], "-"),
                                  ("adc_db", "ADC quantization", PAL[3], "-"), ("self_noise_db", "total self-noise", P.INK, "-")):
            ax.plot(f, [r[key] for r in rs], color=col, linestyle=ls, linewidth=1.8 if key == "self_noise_db" else 1.2,
                    label=lab)
        for amb, ls in zip(study.ambients, (":", "--", "-.")):
            ax.plot(f, [r[f"{amb.scenario_id}_db"] for r in rs], color=GREY, linestyle=ls, linewidth=1.0,
                    label=amb.scenario_id)
        ch = next(c for c in study.sensors if c.scenario_id == sid)
        ax.axvspan(20, max(20, ch.bandwidth_low_hz), color="#f3f2ef", zorder=0)
        if ch.bandwidth_high_hz < 20000:
            ax.axvspan(ch.bandwidth_high_hz, 20000, color="#f3f2ef", zorder=0)
            ax.text(np.sqrt(ch.bandwidth_high_hz * 20000), 0.5, "outside declared\nbandwidth", transform=ax.get_xaxis_transform(),
                    ha="center", fontsize=6.5, color=P.INK2)
        _faxis(ax)
        _bands(ax, study.bands, study.cfg.get("exploratory_bands", []))
        ax.set_title(sid, fontsize=8.5, pad=12)
    axes[0, 0].set_ylabel("Input-referred PSD (dB re 1 uPa^2/Hz)")
    h, lab = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=len(lab), fontsize=7, frameon=False)
    fig.suptitle("Acquisition self-noise components versus ASSUMED ambient scenarios (all levels assumed; ADR-0010)",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    _save(fig, outdir, "s2a_fig02_self_noise.png", written)


def fig_dynamic_range(study, dr_rows, outdir, written):
    amb = [a.scenario_id for a in study.ambients if a.scenario_id.endswith("moderate")][0]
    rows = [r for r in dr_rows if r["ambient"] == amb]
    ylabels = [(s.scenario_id, c[0]) for s in study.sensors for c in study.signal_classes]
    bands = list(study.bands)
    m = np.full((len(ylabels), len(bands)), np.nan)
    for i, (sid, cls) in enumerate(ylabels):
        for j, b in enumerate(bands):
            r = next(x for x in rows if x["sensor"] == sid and x["signal_class"] == cls and x["band"] == b)
            if r["status"] == "ok":
                m[i, j] = r["dr_over_total_noise_db"]
    fig, ax = plt.subplots(figsize=(6.8, 0.33 * len(ylabels) + 1.4))
    im = ax.imshow(m, cmap=P.SEQ, aspect="auto", vmin=np.nanmin(m), vmax=np.nanmax(m))
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            txt = "n/a" if np.isnan(m[i, j]) else f"{m[i, j]:.0f}"
            val = m[i, j]
            dark = (not np.isnan(val)) and val > np.nanmin(m) + 0.6 * (np.nanmax(m) - np.nanmin(m))
            ax.text(j, i, txt, ha="center", va="center", fontsize=6.5, color="white" if dark else P.INK)
    ax.set_xticks(range(len(bands)), [b + (" (expl.)" if b in study.cfg.get("exploratory_bands", []) else "") for b in bands])
    ax.set_yticks(range(len(ylabels)), [f"{s.split('-ASSUMED')[0]} {c}" for s, c in ylabels], fontsize=6.5)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("dB")
    ax.set_title(f"Dynamic range over total noise (clip level minus crest factor, over band noise); ambient {amb}.\n"
                 "n/a: band outside the scenario's declared bandwidth or at/above Nyquist", fontsize=8)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig03_dynamic_range.png", written)


def _rag_series(rag_rows, aid, field, eta):
    rs = sorted([r for r in rag_rows if r["array_id"] == aid and r["field"] == field and r["eta_db"] == eta],
                key=lambda r: r["f_hz"])
    return np.array([r["f_hz"] for r in rs]), np.array([r["rag_median_db"] for r in rs])


def fig_rag_iso(study, rag_rows, outdir, written):
    present = [e for e in study.eta if e is not None]
    etas = ["none"] + ([f"{0.0:g}"] if 0.0 in present else []) + ([f"{max(present):g}"] if present and max(present) != 0 else [])
    fig, axes = plt.subplots(2, len(etas), figsize=(4.4 * len(etas), 7.2), sharey=True, squeeze=False)
    for i, (gname, ids) in enumerate(GROUPS.items()):
        for j, eta in enumerate(etas):
            ax = axes[i, j]
            for aid in ids:
                f, v = _rag_series(rag_rows, aid, "ISO", eta)
                if f.size:
                    ax.plot(f, v, color=CMAP[aid], linewidth=1.4, label=aid)
            for nn, ls in ((4, ":"), (6, "--"), (8, "-.")):
                ax.axhline(10 * np.log10(nn), color=GREY, linewidth=0.7, linestyle=ls)
            _faxis(ax)
            ax.set_ylim(-0.5, 12)
            _bands(ax, study.bands, study.cfg.get("exploratory_bands", []))
            ax.set_title(f"{gname}; eta = " + ("no sensor noise" if eta == "none" else f"{eta} dB"), fontsize=8, pad=12)
            if j == 0:
                ax.set_ylabel("RAG relative to A0 (dB)")
        axes[i, 0].legend(loc="upper left", fontsize=6.5, frameon=False, ncol=2)
    fig.suptitle("Realized array gain in spherically isotropic ambient noise, median over horizon steering. Grey lines: "
                 "10 log10 N for N = 4, 6, 8 (white-noise gain). eta = sensor self-noise / ambient", fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig04_rag_isotropic.png", written)


def fig_rag_fields(study, rag_summary, outdir, written):
    ids = [g.array_id for _, g in study.multichannel]
    fields = [f.field_id for f in study.fields]
    bands = [b for b in study.bands if b not in study.cfg.get("exploratory_bands", [])]
    fig, axes = plt.subplots(1, len(bands), figsize=(4.0 * len(bands), 0.32 * len(ids) + 1.8), sharey=True)
    vmax = 0.0
    mats = []
    for b in bands:
        m = np.array([[next(r for r in rag_summary if r["array_id"] == a and r["field"] == f and r["eta_db"] == "none")[
            f"{b}_median_db"] for f in fields] for a in ids])
        mats.append(m)
        vmax = max(vmax, np.nanmax(m))
    for ax, b, m in zip(axes, bands, mats):
        im = ax.imshow(m, cmap=P.SEQ, vmin=0, vmax=vmax, aspect="auto")
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                ax.text(j, i, f"{m[i, j]:.1f}", ha="center", va="center", fontsize=6.2,
                        color="white" if m[i, j] > 0.6 * vmax else P.INK)
        ax.set_xticks(range(len(fields)), fields, fontsize=7, rotation=30)
        ax.set_yticks(range(len(ids)), ids, fontsize=7)
        ax.set_title(f"{b} {study.bands[b][0]:g}-{study.bands[b][1]:g} Hz", fontsize=8.5)
        ax.grid(False)
    cb = fig.colorbar(im, ax=list(axes), shrink=0.8)
    cb.set_label("RAG relative to A0 (dB)")
    fig.suptitle("Band-median realized array gain by noise-field structure, no sensor noise (ambient-limited). "
                 "Field shapes other than WHITE/ISO/HOR are assumed", fontsize=9)
    _save(fig, outdir, "s2a_fig05_rag_by_field.png", written)


def fig_host(study, host_rows, outdir, written):
    srcs = [s["id"] for s in study.host["sources"]]
    show = ["A1", "A3", "P8-C", "A2", "P8-E", "A4", "V-D"]
    fig, axes = plt.subplots(1, len(srcs), figsize=(4.4 * len(srcs), 3.8), sharey=True)
    for ax, sid in zip(np.atleast_1d(axes), srcs):
        for k, aid in enumerate(show):
            rs = sorted([r for r in host_rows if r["array_id"] == aid and r["host"] == sid and r["hnr_db"] == 10.0],
                        key=lambda r: r["f_hz"])
            if not rs:
                continue
            f = [r["f_hz"] for r in rs]
            ax.plot(f, [r["rag_median_db"] for r in rs], color=PAL[k], marker="o", markersize=3.5, linewidth=1.3,
                    label=aid)
            ax.plot(f, [r["rag_min_db"] for r in rs], color=PAL[k], linewidth=0.8, linestyle=":")
        _faxis(ax)
        ax.set_title(f"{sid}, host-to-ambient +10 dB", fontsize=8.5)
        ax.axhline(0, color=GREY, linewidth=0.7)
    np.atleast_1d(axes)[0].set_ylabel("RAG relative to A0 (dB)")
    np.atleast_1d(axes)[0].legend(fontsize=6.5, frameon=False, ncol=2)
    fig.suptitle("Host-noise scenarios (ASSUMED generic placements): median over horizon steering (solid) and worst "
                 "steering (dotted). A0 receives the full host noise", fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig06_host_noise.png", written)


def fig_mc_verification(study, sw_rows, outdir, written):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    ax = axes[0]
    s = np.logspace(-1, np.log10(120), 300)
    for nn, ls in ((4, "-"), (6, "--"), (8, "-.")):
        sr = np.deg2rad(s)
        ax.plot(s, 10 * np.log10(np.exp(-sr ** 2) + (1 - np.exp(-sr ** 2)) / nn), color=GREY, linestyle=ls, linewidth=1.0,
                label=f"closed form N = {nn}")
    for r in sw_rows:
        if r["error_type"] == "sigma_gain_db":
            continue
        nn = {4: PAL[0], 6: PAL[1], 8: PAL[2]}.get(_n_of(study, r["array_id"]), P.INK)
        y, lo, hi = (10 * np.log10(r[k]) for k in ("mainlobe_power_mean", "mainlobe_power_lo", "mainlobe_power_hi"))
        ax.errorbar(r["sigma_total_phase_deg"], y, yerr=[[y - lo], [hi - y]], fmt="o", markersize=2.5, color=nn,
                    elinewidth=0.6, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("Total phase error sigma (deg): phase, k sigma_pos, 2 pi f sigma_t")
    ax.set_ylabel("Mean signal power (dB re error-free)")
    ax.set_title("(a) Signal loss: Monte Carlo (dots, 95 % CI) vs closed form", fontsize=8.5)
    ax.legend(fontsize=6.5, frameon=False)
    ax = axes[1]
    gs = np.linspace(0, 2.2, 200)
    for nn, ls in ((4, "-"), (6, "--"), (8, "-.")):
        sl = np.log(10) / 20 * gs
        eg, eg2 = np.exp(0.5 * sl ** 2), np.exp(2 * sl ** 2)
        ax.plot(gs, 10 * np.log10((nn * eg2 + nn * (nn - 1) * eg ** 2) / nn ** 2), color=GREY, linestyle=ls, linewidth=1.0)
    for r in sw_rows:
        if r["error_type"] != "sigma_gain_db":
            continue
        col = {4: PAL[0], 6: PAL[1], 8: PAL[2]}.get(_n_of(study, r["array_id"]), P.INK)
        y, lo, hi = (10 * np.log10(r[k]) for k in ("mainlobe_power_mean", "mainlobe_power_lo", "mainlobe_power_hi"))
        ax.errorbar(r["error_level"], y, yerr=[[y - lo], [hi - y]], fmt="o", markersize=2.5, color=col, elinewidth=0.6,
                    alpha=0.7)
    ax.set_xlabel("Gain error sigma (dB)")
    ax.set_ylabel("Mean signal power (dB re error-free)")
    ax.set_title("(b) Gain errors only (log-normal): Monte Carlo vs closed form", fontsize=8.5)
    handles = [Line2D([0], [0], color=PAL[i], marker="o", linestyle="none", label=f"N = {n}") for i, n in enumerate((4, 6, 8))]
    ax.legend(handles=handles, fontsize=6.5, frameon=False)
    fig.suptitle("Verification of the channel-error Monte Carlo against closed forms (uniform DAS, i.i.d. errors)",
                 fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig07_mc_verification.png", written)


def _n_of(study, aid):
    return next(g.n_elements for _, g in study.cands if g.array_id == aid)


def fig_mc_ambiguity(study, mc_rows, outdir, written):
    ids = [g.array_id for _, g in study.multichannel]
    scen = [e.scenario_id for e in study.errors]
    freqs = [float(f) for f in study.mc["frequencies_hz"]]
    fig, axes = plt.subplots(2, len(freqs), figsize=(3.4 * len(freqs), 8.0), sharey=True)
    for j, f in enumerate(freqs):
        for row, (key, lab) in enumerate((("p_amb_ge_m6db", "P(lobe >= -6 dB outside mainlobe)"),
                                          ("gross_error_rate", "Gross error rate (x at 1.0: structural ambiguity)"))):
            ax = axes[row, j]
            for k, sid in enumerate(scen):
                for i, aid in enumerate(ids):
                    r = next((x for x in mc_rows if x["array_id"] == aid and x["f_hz"] == f and x["scenario"] == sid
                              and x["target_az_deg"] == 30.0), None)
                    if r is not None and row == 1 and r.get("structural_ambiguity"):
                        ax.plot(1.0, i + (k - 1.5) * 0.18, marker="x", markersize=4, color=PAL[k], linestyle="none")
                        continue
                    if r is None or key not in r or not np.isfinite(r.get(key, np.nan)):
                        continue
                    lo = r[f"{key}_lo"] if f"{key}_lo" in r else r.get("gross_error_lo")
                    hi = r[f"{key}_hi"] if f"{key}_hi" in r else r.get("gross_error_hi")
                    y = i + (k - 1.5) * 0.18
                    ax.errorbar(r[key], y, xerr=[[r[key] - lo], [hi - r[key]]], fmt="o", markersize=3, color=PAL[k],
                                elinewidth=0.7)
            ax.set_yticks(range(len(ids)), ids, fontsize=7)
            ax.set_xlim(-0.03, 1.03)
            ax.invert_yaxis()
            if row == 0:
                ax.set_title(f"{f:g} Hz", fontsize=8.5)
            ax.set_xlabel(lab, fontsize=7.5)
    handles = [Line2D([0], [0], color=PAL[k], marker="o", linestyle="none", label=s) for k, s in enumerate(scen)]
    fig.legend(handles=handles, loc="lower center", ncol=len(scen), frameon=False, fontsize=7)
    fig.suptitle("Channel-error Monte Carlo, horizon target at az = 30 deg (95 % Wilson intervals). Missing points: "
                 "undefined (no half-power discrimination on the error-free horizontal cut)", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    _save(fig, outdir, "s2a_fig08_mc_ambiguity_bearing.png", written)


def fig_bands(study, thr_sum, outdir, written):
    ids = [r["array_id"] for r in thr_sum]
    fig, ax = plt.subplots(figsize=(10, 0.5 * len(ids) + 1.6))
    cols = {-3.0: PAL[0], -6.0: PAL[2], -10.0: PAL[6]}
    for i, r in enumerate(thr_sum):
        for k, L in enumerate(study.levels):
            lv = _lvl(L)
            y = i + (k - 1) * 0.25
            mlo, mhi = r["f_sl_median_hz"], min(r[f"f_amb_{lv}_median_hz"], 20000.0)
            if mlo < mhi:
                ax.plot([mlo, mhi], [y, y], color=cols[L], linewidth=2.0, alpha=0.35, solid_capstyle="butt")
            glo, ghi = r[f"guaranteed_{lv}_lo_hz"], r[f"guaranteed_{lv}_hi_hz"]
            if np.isfinite(glo):
                ax.plot([glo, min(ghi, 20000.0)], [y, y], color=cols[L], linewidth=5.0, solid_capstyle="butt")
        ax.plot([r["f_hp_median_hz"]], [i], marker="|", color=P.INK, markersize=12)
    ax.set_yticks(range(len(ids)), ids)
    ax.invert_yaxis()
    _faxis(ax)
    ax.grid(axis="y", visible=False)
    handles = [Line2D([0], [0], color=cols[L], linewidth=5, label=f"guaranteed band, {L:g} dB") for L in study.levels]
    handles += [Line2D([0], [0], color=GREY, linewidth=2, alpha=0.5, label="median band (light)"),
                Line2D([0], [0], color=P.INK, marker="|", linestyle="none", markersize=12, label="median f_HP")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False, fontsize=7)
    ax.set_title("Conventional DAS bands (closed mainlobe, no ambiguity lobe at the level) under -3/-6/-10 dB criteria, "
                 "horizon steering.\nNarrowband criteria only; not limits on broadband or other estimators", fontsize=8.5)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig09_bands_by_criterion.png", written)


def fig_pareto(study, par_rows, outdir, written):
    sets = sorted({r["set"] for r in par_rows}, key=lambda s: (not s.startswith("SIM-01"), s))
    ids = sorted({a.split(" (by")[0] for r in par_rows for a in r["dominated"].split(";") if r["dominated"] != "none"}
                 | {g.array_id for _, g in study.multichannel if not g.array_id.startswith("A0")})
    labels, mat = [], []
    for s in sets:
        for r in [x for x in par_rows if x["set"] == s]:
            labels.append(f"{s}, scale {r['tolerance_scale']:g}")
            dom = {a.split(" (by")[0] for a in r["dominated"].split(";")} if r["dominated"] != "none" else set()
            mat.append([1.0 if a in dom else 0.0 for a in ids])
    m = np.array(mat)
    fig, ax = plt.subplots(figsize=(0.55 * len(ids) + 3.5, 0.3 * len(labels) + 1.6))
    ax.imshow(m, cmap=matplotlib.colors.ListedColormap(["#f3f2ef", "#eb6834"]), aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(ids)), ids, rotation=45, fontsize=7)
    ax.set_yticks(range(len(labels)), labels, fontsize=6.8)
    ax.grid(False)
    ax.set_title("Pareto tolerance sensitivity (D06): orange = dominated at that tolerance scale.\n"
                 "Conditional on evaluated attributes; cost and installation not modeled; no candidate eliminated",
                 fontsize=8.5)
    fig.tight_layout()
    _save(fig, outdir, "s2a_fig10_pareto_tolerance.png", written)


def make_figures(study, outdir, geo_rows, spec_rows, dr_rows, rag_rows, host_rows, mc_rows, sw_rows, thr_sum,
                 par_rows) -> list[str]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    rag_summary = study.rag_band_summary(rag_rows)
    fig_candidates(study, outdir, written)
    fig_self_noise(study, spec_rows, outdir, written)
    fig_dynamic_range(study, dr_rows, outdir, written)
    fig_rag_iso(study, rag_rows, outdir, written)
    fig_rag_fields(study, rag_summary, outdir, written)
    fig_host(study, host_rows, outdir, written)
    fig_mc_verification(study, sw_rows, outdir, written)
    fig_mc_ambiguity(study, mc_rows, outdir, written)
    fig_bands(study, thr_sum, outdir, written)
    fig_pareto(study, par_rows, outdir, written)
    return written
