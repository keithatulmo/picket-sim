"""Figures for SIM studies. No physics here: functions receive computed arrays.

Conventions used in every figure:
* Power is normalized DAS power in dB relative to the steered response (0 dB at the steering
  direction). Display floor is stated on the axis; values below it are clamped for display only.
* Azimuth in degrees in [-180, 180), measured from +x toward +y; elevation in degrees, + up.
* Frequency axes are logarithmic in Hz with the same ticks everywhere.
* Each array keeps one colour and line style across all figures.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from .conventions import az_el_deg_from_unit, wrap_deg  # noqa: E402

__all__ = [
    "ARRAY_COLORS",
    "cut_for_plot",
    "vertical_front_for_plot",
    "to_display_db",
    "cone_curve_az_el",
    "equirect_grid",
    "make_sim01_figures",
]

ARRAY_COLORS = {"A0": "#52514e", "A1": "#2a78d6", "A2": "#eb6834", "A3": "#1baf7a", "A4": "#6250d6"}
ARRAY_STYLES = {"A0": ":", "A1": "-", "A2": "--", "A3": "-.", "A4": (0, (6, 1.5, 1.5, 1.5))}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
SEQ = LinearSegmentedColormap.from_list(
    "seq_blue", ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)
FREQ_TICKS = [100, 200, 500, 1000, 2000, 5000, 10000]
FREQ_LABELS = ["100", "200", "500", "1k", "2k", "5k", "10k"]
FLOOR_DB = -40.0
MAP_FLOOR_DB = -30.0
DPI = 160

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5, "legend.fontsize": 7.5,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
    "lines.linewidth": 1.6, "savefig.dpi": DPI,
})


def _color(aid):
    return ARRAY_COLORS.get(aid, INK2)


def _style(aid):
    return ARRAY_STYLES.get(aid, "-")


def _freq_axis(ax, axis="x"):
    if axis == "x":
        ax.set_xscale("log")
        ax.set_xticks(FREQ_TICKS, FREQ_LABELS)
        ax.set_xlim(100, 10000)
        ax.set_xlabel("Frequency (Hz)")
    else:
        ax.set_yscale("log")
        ax.set_yticks(FREQ_TICKS, FREQ_LABELS)
        ax.set_ylim(100, 10000)
        ax.set_ylabel("Frequency (Hz)")
    ax.minorticks_off()


def _save(fig, outdir: Path, name: str, written: list):
    path = outdir / name
    fig.savefig(path, metadata={"Software": None})  # no software/date stamp: reproducible bytes
    plt.close(fig)
    written.append(name)


# ============================================================================ data preparation (tested)
def to_display_db(p, floor_db: float = FLOOR_DB) -> np.ndarray:
    """Normalized power -> dB clamped at ``floor_db`` for display. Raises if P > 1 (normalization)."""
    p = np.asarray(p, dtype=float)
    if np.any(p > 1.0 + 1e-9):
        raise ValueError("normalized power exceeds 1; refusing to plot (normalization error)")
    with np.errstate(divide="ignore"):
        d = 10.0 * np.log10(np.clip(p, 0.0, None))
    return np.maximum(d, floor_db)


def cut_for_plot(gamma_deg, p, az0_deg: float, floor_db: float = FLOOR_DB):
    """Horizon cut (offsets from az0) -> absolute azimuth sorted on [-180, 180), dB."""
    az = wrap_deg(np.asarray(gamma_deg) + az0_deg)
    order = np.argsort(az, kind="stable")
    return az[order], to_display_db(np.asarray(p)[order], floor_db)


def vertical_front_for_plot(gamma_deg, p, el0_deg: float, floor_db: float = FLOOR_DB):
    """Vertical great-circle cut -> elevation on the front meridian ([-90, 90]), dB."""
    el = np.asarray(gamma_deg) + el0_deg
    m = (el >= -90.0) & (el <= 90.0)
    order = np.argsort(el[m], kind="stable")
    return el[m][order], to_display_db(np.asarray(p)[m][order], floor_db)


def equirect_grid(step_deg: float = 1.0):
    """Regular azimuth/elevation grid for full-sphere maps.

    Returns ``(az_deg (n_az,), el_deg (n_el,), u (n_el, n_az, 3))``: rows are elevation (ascending,
    bottom to top with ``pcolormesh``), columns azimuth (ascending).
    """
    from .conventions import unit_vector

    az = np.linspace(-180.0, 180.0, int(round(360 / step_deg)) + 1)
    el = np.linspace(-90.0, 90.0, int(round(180 / step_deg)) + 1)
    aa, ee = np.meshgrid(az, el, indexing="xy")
    return az, el, unit_vector(aa, ee)


def cone_curve_az_el(axis, u0, n: int = 721):
    """Az/el of the cone of directions sharing u0's angle to ``axis`` (rank-1 ambiguity set)."""
    axis = np.asarray(axis, float)
    u0 = np.asarray(u0, float)
    c = float(u0 @ axis)
    perp = u0 - c * axis
    s = np.linalg.norm(perp)
    if s < 1e-12:
        return np.array([]), np.array([])
    e1 = perp / s
    e2 = np.cross(axis, e1)
    t = np.linspace(0, 2 * np.pi, n)
    pts = c * axis + s * (np.cos(t)[:, None] * e1 + np.sin(t)[:, None] * e2)
    az, el = az_el_deg_from_unit(pts)
    return az, el


def _split_wrap(az, el):
    """Insert NaN where the azimuth wraps so lines are not drawn across the map."""
    if az.size == 0:
        return az, el
    jumps = np.flatnonzero(np.abs(np.diff(az)) > 180)
    return np.insert(az, jumps + 1, np.nan), np.insert(el, jumps + 1, np.nan)


# ============================================================================ figures
def fig_geometries(data, outdir, written):
    arrays = data["arrays"]
    allp = np.vstack([a["positions_m"] for a in arrays])
    span = max(np.ptp(allp, axis=0).max(), 0.5)
    fig, axes = plt.subplots(2, len(arrays), figsize=(2.3 * len(arrays), 4.6), squeeze=False)
    for j, a in enumerate(arrays):
        pos = a["positions_m"]
        ctr = pos.mean(axis=0)
        for i, (ix, iy, lab) in enumerate(((0, 1, ("x (m)", "y (m)")), (0, 2, ("x (m)", "z (m)")))):
            ax = axes[i, j]
            ax.scatter(pos[:, ix], pos[:, iy], s=36, color=_color(a["id"]), edgecolor="white", linewidth=1.0,
                       zorder=3)
            for k, p in enumerate(pos):
                ax.annotate(f"E{k + 1}", (p[ix], p[iy]), textcoords="offset points", xytext=(4, 4), fontsize=6.5,
                            color=INK2)
            h = 0.6 * span
            ax.set_xlim(ctr[ix] - h, ctr[ix] + h)
            ax.set_ylim(ctr[iy] - h, ctr[iy] + h)
            ax.set_aspect("equal")
            ax.set_xlabel(lab[0])
            ax.set_ylabel(lab[1])
            if i == 0:
                ax.set_title(f"{a['id']}: {a['label']}\nambiguity: {a['ambiguity_class']}")
    axes[0, 0].text(-0.45, 0.5, "top view", transform=axes[0, 0].transAxes, rotation=90, va="center", color=INK2)
    axes[1, 0].text(-0.45, 0.5, "side view", transform=axes[1, 0].transAxes, rotation=90, va="center", color=INK2)
    fig.suptitle("Candidate geometries (array frame: z up; identical scale in every panel)", fontsize=10)
    fig.tight_layout()
    _save(fig, outdir, "fig01_geometries.png", written)


def fig_horizontal_cuts(data, outdir, written):
    arrays, freqs = data["arrays"], data["figure_frequencies_hz"]
    fig, axes = plt.subplots(len(arrays), len(freqs), figsize=(2.3 * len(freqs), 1.55 * len(arrays) + 0.8),
                             sharex=True, sharey=True, squeeze=False)
    for i, a in enumerate(arrays):
        for j, f in enumerate(freqs):
            ax = axes[i, j]
            az, d = cut_for_plot(a["cut_h_gamma_deg"], a["cut_h"][f], a["cut_h_az0_deg"])
            ax.plot(az, d, color=_color(a["id"]), linestyle=_style(a["id"]), linewidth=1.3)
            ax.axvline(a["cut_h_az0_deg"], color=INK, linewidth=0.8, linestyle=(0, (2, 2)))
            ax.axhline(-3.0103, color=INK2, linewidth=0.6)
            ax.set_ylim(FLOOR_DB, 2)
            ax.set_xlim(-180, 180)
            ax.set_xticks([-180, -90, 0, 90, 180])
            if i == 0:
                ax.set_title(f"{f:g} Hz (λ = {data['c_mps'] / f:.2f} m)")
            if j == 0:
                ax.set_ylabel(f"{a['id']}\ndB")
            if i == len(arrays) - 1:
                ax.set_xlabel("Azimuth (deg)")
    fig.suptitle(
        f"Horizontal-plane beampatterns, steered to az = {arrays[0]['cut_h_az0_deg']:g} deg, el = 0 (dashed line). "
        f"Normalized DAS power, dB re steered response; grey line -3 dB; floor {FLOOR_DB:g} dB",
        fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "fig02_horizontal_beampatterns.png", written)


def fig_vertical_cuts(data, outdir, written):
    arrays, freqs, sc = data["arrays"], data["figure_frequencies_hz"], data["showcase"]
    fig, axes = plt.subplots(len(arrays), len(freqs), figsize=(2.3 * len(freqs), 1.55 * len(arrays) + 0.8),
                             sharex=True, sharey=True, squeeze=False)
    for i, a in enumerate(arrays):
        for j, f in enumerate(freqs):
            ax = axes[i, j]
            el, d = vertical_front_for_plot(a["cut_h_gamma_deg"], a["cut_v"][f], a["cut_v_el0_deg"])
            ax.plot(el, d, color=_color(a["id"]), linestyle=_style(a["id"]), linewidth=1.3)
            ax.axvline(sc["el_deg"], color=INK, linewidth=0.8, linestyle=(0, (2, 2)))
            ax.axvline(-sc["el_deg"], color=INK2, linewidth=0.6, linestyle=":")
            ax.axhline(-3.0103, color=INK2, linewidth=0.6)
            ax.set_ylim(FLOOR_DB, 2)
            ax.set_xlim(-90, 90)
            ax.set_xticks([-90, -45, 0, 45, 90])
            if i == 0:
                ax.set_title(f"{f:g} Hz")
            if j == 0:
                ax.set_ylabel(f"{a['id']}\ndB")
            if i == len(arrays) - 1:
                ax.set_xlabel("Elevation (deg)")
    fig.suptitle(
        f"Vertical-plane beampatterns at az = {sc['az_deg']:g} deg, steered to el = {sc['el_deg']:g} deg (dashed); "
        f"dotted line marks the up/down mirror direction el = {-sc['el_deg']:g} deg. dB re steered response",
        fontsize=9)
    fig.tight_layout()
    _save(fig, outdir, "fig03_vertical_beampatterns.png", written)


def fig_freq_az_maps(data, outdir, written):
    arrays = data["arrays"]
    fig, axes = plt.subplots(1, len(arrays), figsize=(2.4 * len(arrays), 3.6), sharey=True, squeeze=False)
    mesh = None
    L3 = data["levels"][-1]
    for j, a in enumerate(arrays):
        ax = axes[0, j]
        d = to_display_db(a["fa_map"], MAP_FLOOR_DB)
        az = a["fa_az_deg"]
        mesh = ax.pcolormesh(az, a["fa_f_hz"], d, cmap=SEQ, vmin=MAP_FLOOR_DB, vmax=0, shading="nearest",
                             rasterized=True)
        ax.contour(az, a["fa_f_hz"], d, levels=[-3.0103], colors="#eb6834", linewidths=0.7)
        ax.axvline(a["cut_h_az0_deg"], color=INK, linewidth=0.9, linestyle=(0, (2, 2)))
        fa = a["alias_worst_db"].get(L3)
        if fa is not None:
            ax.axhline(fa, color=INK, linewidth=0.8, linestyle=(0, (4, 2)))
        _freq_axis(ax, "y")
        if j:
            ax.set_ylabel("")
        ax.set_xlim(-180, 180)
        ax.set_xticks([-180, -90, 0, 90, 180])
        ax.set_xlabel("Azimuth (deg)")
        ax.set_title(f"{a['id']}: {a['label']}")
        ax.grid(False)
    cb = fig.colorbar(mesh, ax=axes[0, :].tolist(), shrink=0.9, pad=0.01)
    cb.set_label(f"dB re steered response (floor {MAP_FLOOR_DB:g})")
    fig.suptitle(f"Horizontal-plane response vs frequency, steered to az = {arrays[0]['cut_h_az0_deg']:g} deg "
                 f"(vertical dashed). Orange contour: -3 dB. Horizontal dashed: worst-case (any steering) {L3:g} dB "
                 "ambiguity onset", fontsize=9)
    _save(fig, outdir, "fig04_frequency_azimuth_maps.png", written)


def fig_sphere_maps(data, outdir, written):
    arrays = data["arrays"]
    freqs = [f for f in data["figure_frequencies_hz"] if f in (1000.0, 2500.0, 5000.0)] or \
        data["figure_frequencies_hz"][:3]
    sc = data["showcase"]
    az, el = data["sphere_map_az_deg"], data["sphere_map_el_deg"]
    fig, axes = plt.subplots(len(arrays), len(freqs), figsize=(3.2 * len(freqs), 1.75 * len(arrays) + 0.7),
                             sharex=True, sharey=True, squeeze=False)
    mesh = None
    from .conventions import unit_vector

    u0 = unit_vector(sc["az_deg"], sc["el_deg"])
    for i, a in enumerate(arrays):
        for j, f in enumerate(freqs):
            ax = axes[i, j]
            d = to_display_db(a["sphere_maps"][f], MAP_FLOOR_DB)
            mesh = ax.pcolormesh(az, el, d, cmap=SEQ, vmin=MAP_FLOOR_DB, vmax=0, shading="nearest", rasterized=True)
            if np.ptp(d) > 1e-6:
                ax.contour(az, el, d, levels=[-3.0103], colors="#f0efec", linewidths=0.6)
            ax.plot(sc["az_deg"], sc["el_deg"], marker="*", markersize=9, color="#eb6834", markeredgecolor="white",
                    markeredgewidth=0.6, linestyle="none")
            if a["mirror_dir"] is not None:
                maz, mel = az_el_deg_from_unit(a["mirror_dir"])
                ax.plot(maz, mel, marker="o", markersize=7, markerfacecolor="none", markeredgecolor="#eb6834",
                        markeredgewidth=1.2, linestyle="none")
            if a["rank"] == 1:
                axis = a["positions_m"][-1] - a["positions_m"][0]
                axis = axis / np.linalg.norm(axis)
                caz, cel = _split_wrap(*cone_curve_az_el(axis, u0))
                ax.plot(caz, cel, color="#eb6834", linewidth=0.8, linestyle=(0, (3, 2)))
            ax.set_xlim(-180, 180)
            ax.set_ylim(-90, 90)
            ax.set_xticks([-180, -90, 0, 90, 180])
            ax.set_yticks([-90, -45, 0, 45, 90])
            ax.grid(False)
            if i == 0:
                ax.set_title(f"{f:g} Hz")
            if j == 0:
                ax.set_ylabel(f"{a['id']}\nel (deg)")
            if i == len(arrays) - 1:
                ax.set_xlabel("Azimuth (deg)")
    cb = fig.colorbar(mesh, ax=axes.ravel().tolist(), shrink=0.6, pad=0.01)
    cb.set_label(f"dB re steered response (floor {MAP_FLOOR_DB:g})")
    fig.suptitle(f"Full-sphere response, steered to az = {sc['az_deg']:g}, el = {sc['el_deg']:g} deg (star). "
                 "Dashed curve: cone ambiguity (lines); open circle: mirror ambiguity (plane); "
                 "light contour: -3 dB", fontsize=9)
    _save(fig, outdir, "fig05_sphere_ambiguity_maps.png", written)


def _series(summary, aid, ring, key):
    rs = sorted([r for r in summary if r["array_id"] == aid and r["ring"] == ring], key=lambda r: r["f_hz"])
    return np.array([r["f_hz"] for r in rs]), np.array([r[key] for r in rs], dtype=float)


def fig_metrics_vs_frequency(data, outdir, written):
    summ, ring = data["summary"], data["horizon_ring"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    handles = []
    for a in data["arrays"]:
        aid, col, ls = a["id"], _color(a["id"]), _style(a["id"])
        f, di = _series(summ, aid, ring, "di_median_db")
        _, lo = _series(summ, aid, ring, "di_min_db")
        _, hi = _series(summ, aid, ring, "di_max_db")
        ax = axes[0, 0]
        ax.plot(f, di, color=col, linestyle=ls)
        ax.fill_between(f, lo, hi, color=col, alpha=0.12, linewidth=0)
        _, bw = _series(summ, aid, ring, "hpbw_h_median_deg")
        bw = np.where(np.isfinite(bw), bw, np.nan)
        axes[0, 1].plot(f, bw, color=col, linestyle=ls)
        _, hp = _series(summ, aid, ring, "hpsf_median")
        axes[1, 0].plot(f, hp, color=col, linestyle=ls)
        _, psl = _series(summ, aid, ring, "psl_obs_max_db")
        axes[1, 1].plot(f, psl, color=col, linestyle=ls)
        handles.append(Line2D([0], [0], color=col, linestyle=ls, label=f"{aid}: {a['label']}"))
    axes[0, 0].axhline(10 * np.log10(4), color=INK2, linewidth=0.7, linestyle=":")
    axes[0, 0].text(110, 10 * np.log10(4) + 0.15, "10 log10(4) = 6.02 dB", fontsize=7, color=INK2)
    axes[0, 0].set_ylabel("DI, isotropic noise (dB)")
    axes[0, 0].set_title("(a) Directivity index: median over horizon steering, band = min-max")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_yticks([5, 10, 20, 45, 90, 180, 360], ["5", "10", "20", "45", "90", "180", "360"])
    axes[0, 1].set_ylim(5, 400)
    axes[0, 1].set_ylabel("Half-power width (deg)")
    axes[0, 1].set_title("(b) Horizontal-cut -3 dB width, median over horizon steering\n"
                         "(gap = undefined: half-power region wraps the circle)")
    axes[1, 0].set_ylim(0, 1.02)
    axes[1, 0].set_ylabel("Fraction of sphere within 3 dB")
    axes[1, 0].set_title("(c) Half-power sphere fraction (all ambiguities included)")
    axes[1, 1].set_ylim(-20, 0.5)
    axes[1, 1].axhline(-3.0103, color=INK2, linewidth=0.7)
    axes[1, 1].set_ylabel("dB re mainlobe")
    axes[1, 1].set_title("(d) Highest observable-space sidelobe / ambiguity lobe,\n"
                         "worst over horizon steering (gap = no sidelobe in visible region)")
    for ax in axes.ravel():
        _freq_axis(ax)
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), frameon=False)
    fig.suptitle("Idealized DAS performance vs frequency (c = %g m/s). Not detection performance." % data["c_mps"],
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    _save(fig, outdir, "fig06_metrics_vs_frequency.png", written)


REGIME_COLORS = {"none": "#d9d8d4", "weak": "#9ec5f4", "conv": "#256abf", "amb": "#eb6834"}


def fig_regime_map(data, outdir, written):
    thr = {r["array_id"]: r for r in data["thr_summary"] if r["ring"] == data["horizon_ring"]}
    L3 = data["levels"][-1]
    from .analysis import _lvl

    arrays = data["arrays"]
    fig, ax = plt.subplots(figsize=(10, 0.65 * len(arrays) + 1.6))
    fmin, fmax = 100.0, 10000.0
    for i, a in enumerate(arrays):
        y = len(arrays) - 1 - i
        t = thr.get(a["id"])
        if a["rank"] == 0 or t is None:
            ax.barh(y, fmax - fmin, left=fmin, color=REGIME_COLORS["none"], height=0.6)
            ax.text(fmin * 1.05, y, "no directional discrimination at any frequency", va="center", fontsize=7.5,
                    color=INK)
        else:
            fhp = np.clip(t["f_hp_median_hz"], fmin, fmax)
            fsl = np.clip(t["f_sl_median_hz"], fmin, fmax)
            fam = np.clip(t[f"f_amb_{_lvl(L3)}_min_hz"], fmin, fmax)
            edges = [fmin, fhp, max(fhp, fsl), max(fhp, fsl, min(fam, fmax)), fmax]
            fam_eff = edges[3]
            segs = [("none", edges[0], edges[1]), ("weak", edges[1], edges[2]), ("conv", edges[2], fam_eff),
                    ("amb", fam_eff, fmax)]
            # ambiguity can begin before f_SL (e.g. sparse arrays): then it overrides later regimes
            if t[f"f_amb_{_lvl(L3)}_min_hz"] < max(fhp, fsl):
                famc = max(np.clip(t[f"f_amb_{_lvl(L3)}_min_hz"], fmin, fmax), fhp)
                segs = [("none", fmin, fhp), ("weak", fhp, famc), ("amb", famc, fmax)]
            for kind, lo, hi in segs:
                if hi > lo:
                    ax.barh(y, hi - lo, left=lo, color=REGIME_COLORS[kind], height=0.6, edgecolor="white",
                            linewidth=1.0)
            fw = t.get(f"f_alias_worstcase_{_lvl(L3)}_hz")
            if fw is not None and np.isfinite(fw) and fw <= fmax:
                ax.plot([fw, fw], [y - 0.38, y + 0.38], color=INK, linewidth=1.4)
        ax.text(fmax * 1.04, y, f"geometric ambiguity: {a['ambiguity_class']}", va="center", fontsize=7.5,
                color=INK2)
    ax.set_yticks(range(len(arrays)), [f"{a['id']}: {a['label']}" for a in arrays][::-1])
    _freq_axis(ax)
    ax.set_xlim(fmin, fmax)
    ax.grid(axis="y", visible=False)
    leg = [Patch(color=REGIME_COLORS["none"], label="no direction suppressed by 3 dB (f < f_HP)"),
           Patch(color=REGIME_COLORS["weak"], label="broad beam, no sidelobes in visible region (f_HP to f_SL)"),
           Patch(color=REGIME_COLORS["conv"], label="conventional: closed mainlobe, no -3 dB ambiguity lobe"),
           Patch(color=REGIME_COLORS["amb"], label=f"ambiguity lobe >= {L3:g} dB for some horizon steering"),
           Line2D([0], [0], color=INK, linewidth=1.4, label=f"worst-case (any steering) {L3:g} dB onset")]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.45, -0.28), ncol=2, frameon=False)
    ax.set_title("Directional regimes vs frequency, horizon steering\n(f_HP, f_SL: median over steering; ambiguity: "
                 "earliest steering; observable-space metrics, geometric ambiguity at right)", fontsize=9)
    fig.tight_layout()
    fig.subplots_adjust(right=0.78)
    _save(fig, outdir, "fig07_regime_map.png", written)


def fig_ula_sensitivity(data, outdir, written):
    rows, thr, geo = data["ula_rows"], data["ula_thr"], data["ula_geo"]
    from .analysis import _lvl

    L3 = data["levels"][-1]
    ns = sorted({r["n_elements"] for r in geo})
    ds = sorted({r["spacing_m"] for r in geo})
    cmap = LinearSegmentedColormap.from_list("ord", ["#86b6ef", "#0d366b"])
    ncol = {n: cmap(i / max(len(ns) - 1, 1)) for i, n in enumerate(ns)}
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for n in ns:
        for d in ds:
            rs = sorted([r for r in rows if r["n_elements"] == n and r["spacing_m"] == d and r["ring"] == "broadside"],
                        key=lambda r: r["f_hz"])
            x = np.array([r["aperture_over_lambda"] for r in rs])
            bw = np.array([r["hpbw_h_deg"] for r in rs], dtype=float)
            di = np.array([r["di_db"] for r in rs])
            dl = np.array([d * r["f_hz"] / data["c_mps"] for r in rs])
            axes[0].plot(x, bw, color=ncol[n], linewidth=1.0)
            axes[1].plot(dl, di, color=ncol[n], linewidth=1.0)
    axes[0].set_xscale("log")
    axes[0].set_xticks([0.03, 0.1, 0.3, 1, 3, 10, 30], ["0.03", "0.1", "0.3", "1", "3", "10", "30"])
    axes[0].minorticks_off()
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Aperture / wavelength")
    axes[0].set_ylabel("Horizontal -3 dB width at broadside (deg)")
    axes[0].set_yticks([1, 3, 10, 30, 90, 180], ["1", "3", "10", "30", "90", "180"])
    axes[0].set_title("(a) Broadside -3 dB width vs aperture/λ\n(all N and d plotted; curves for one N "
                      "coincide)")
    axes[1].set_xscale("log")
    axes[1].set_xticks([0.01, 0.03, 0.1, 0.3, 1, 3], ["0.01", "0.03", "0.1", "0.3", "1", "3"])
    axes[1].minorticks_off()
    axes[1].set_xlabel("Element spacing / wavelength")
    axes[1].set_ylabel("DI at broadside, isotropic noise (dB)")
    axes[1].set_title("(b) Broadside DI vs spacing/λ: equals 10 log10 N (dotted) at d = λ/2;\n"
                      "exceeds it for λ/2 < d < λ (classical limit ~2Nd/λ); grating lobes beyond")
    for n in ns:
        axes[1].axhline(10 * np.log10(n), color=ncol[n], linewidth=0.5, linestyle=":")
    # (c) thresholds vs spacing
    for n in ns:
        ts = sorted([t for t in thr if t["n_elements"] == n and t["ring"] == "broadside"], key=lambda t: t["spacing_m"])
        axes[2].plot([t["spacing_m"] for t in ts], [t["f_sl_hz"] for t in ts], color=ncol[n], marker="o",
                     markersize=4, linewidth=1.0)
    ga = sorted([g for g in geo if g["n_elements"] == 4], key=lambda g: g["spacing_m"])
    axes[2].plot([g["spacing_m"] for g in ga], [g["f_grating_exact_worst_hz"] for g in ga], color=INK, linewidth=1.4,
                 linestyle="--", label="exact grating onset c/(2d), any steering")
    axes[2].plot([g["spacing_m"] for g in ga], [g[f"f_alias_{_lvl(L3)}_hz"] or np.nan for g in ga], color="#eb6834",
                 linewidth=1.4, label=f"worst-case {L3:g} dB ambiguity onset (N = 4)")
    axes[2].set_xscale("log")
    axes[2].set_xticks(ds, [f"{d:g}" for d in ds])
    axes[2].minorticks_off()
    _freq_axis(axes[2], "y")
    axes[2].set_ylim(50, 20000)
    axes[2].set_xlabel("Element spacing d (m)")
    axes[2].set_title("(c) First-sidelobe onset f_SL at broadside (dots, per N)\nvs aliasing onset (lines)")
    axes[2].legend(loc="lower left", frameon=False)
    handles = [Line2D([0], [0], color=ncol[n], label=f"N = {n}") for n in ns]
    fig.legend(handles=handles, loc="lower center", ncol=len(ns), frameon=False)
    fig.suptitle("Line-array sensitivity to element count N and spacing d (c = %g m/s)" % data["c_mps"], fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    _save(fig, outdir, "fig08_line_array_sensitivity.png", written)


def fig_scale_sensitivity(data, outdir, written):
    from .analysis import _lvl

    L3 = data["levels"][-1]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    for ax, rows, title in ((axes[0], data["a4_rows"], "(a) A4 layout scaled (aperture on x)"),
                            (axes[1], data["sq_rows"], "(b) 2x2 square, side length varied (aperture on x)")):
        rows = sorted(rows, key=lambda r: r["aperture_m"])
        x = [r["aperture_m"] for r in rows]
        spec = [("f_hp_median_hz", "f_HP (median steering)", "#86b6ef", "-"),
                ("f_sl_median_hz", "f_SL (median steering)", "#256abf", "-"),
                (f"f_amb_{_lvl(L3)}_min_hz", f"f_amb {L3:g} dB (earliest horizon steering)", "#eb6834", "-"),
                (f"f_alias_worstcase_{_lvl(L3)}_hz", f"worst-case {L3:g} dB onset (any steering)", INK, "--")]
        for key, lab, col, ls in spec:
            y = np.array([r[key] for r in rows], dtype=float)
            y = np.where(np.isfinite(y), y, np.nan)
            base = key.replace("_median_hz", "").replace("_min_hz", "")
            below = np.array([bool(r.get(f"{base}_below_grid", 0)) for r in rows])
            ax.plot(x, np.where(below, np.nan, y), color=col, linestyle=ls, marker="o", markersize=4, label=lab)
            if below.any():  # value is only an upper bound (threshold lies below the analysed band)
                ax.plot(np.array(x)[below], y[below], linestyle="none", marker="v", markersize=7,
                        markerfacecolor="white", markeredgecolor=col)
        gx = np.array([r.get("f_grating_exact_worst_hz", np.nan) for r in rows], dtype=float)
        ax.plot(x, np.where(np.isfinite(gx), gx, np.nan), color=INK2, linestyle=":", marker="x", markersize=5,
                label="exact (0 dB) grating onset")
        ax.set_xscale("log")
        ax.set_xticks(x, [f"{v:.2f}" for v in x])
        ax.minorticks_off()
        _freq_axis(ax, "y")
        ax.set_ylim(30, 10000)
        ax.set_xlabel("Maximum dimension (m)")
        ax.set_title(title)
    axes[0].legend(loc="lower left", frameon=False)
    axes[0].text(0.98, 0.98, "open triangle: threshold below 100 Hz\n(plotted at band edge, upper bound)",
                 transform=axes[0].transAxes, ha="right", va="top", fontsize=7, color=INK2)
    fig.suptitle("Aperture scaling: every threshold scales as 1/size, so the band in which a 4-element array is both "
                 "directional and unambiguous moves but does not widen", fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _save(fig, outdir, "fig09_aperture_scaling.png", written)


def fig_sound_speed(data, outdir, written):
    ss, mm = data["ss_rows"], data["mm_rows"]
    c0 = data["c_mps"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    ax = axes[0]
    for a in data["arrays"]:
        rs = [r for r in ss if r["array_id"] == a["id"]]
        for key, mk in (("f_hp_median_hz", "o"), ("f_sl_median_hz", "s")):
            pts = [(r["c_mps"] / c0, r[key] / [b for b in rs if b["c_mps"] == c0][0][key]) for r in rs
                   if np.isfinite(r[key])]
            if pts:
                ax.plot(*zip(*pts), marker=mk, linestyle="none", color=_color(a["id"]), markersize=5)
    xs = np.linspace(0.95, 1.05, 3)
    ax.plot(xs, xs, color=INK2, linewidth=0.8, linestyle="--")
    ax.set_xlabel("c / c_nominal")
    ax.set_ylabel("threshold / threshold at c_nominal")
    ax.set_title("(a) Thresholds scale exactly with c (circles f_HP, squares f_SL)")
    ax = axes[1]
    alphas = sorted({r["c_assumed_mps"] / r["c_true_mps"] for r in mm})
    t = np.linspace(0, 90, 361)
    for al in alphas:
        est = np.rad2deg(np.arccos(np.clip(al * np.cos(np.deg2rad(t)), -1, 1)))
        ax.plot(t, est - t, color=INK2, linewidth=0.8,
                linestyle="-" if al > 1 else "--")
        ax.text(91, (est - t)[-1], f"c_assumed/c_true = {al:.3f}", fontsize=6.5, va="center", color=INK2)
    msize = {"A1": 9, "A2": 5}
    for r in mm:
        if r["rank"] == 1 and np.isfinite(r["cone_angle_error_deg"]):
            ax.plot(r["cone_angle_true_deg"], r["cone_angle_error_deg"], marker="o", linestyle="none",
                    markerfacecolor="none" if r["array_id"] == "A1" else _color(r["array_id"]),
                    markeredgecolor=_color(r["array_id"]), markersize=msize.get(r["array_id"], 6), markeredgewidth=1.2)
        elif r["rank"] == 2 and np.isfinite(r["abs_el_error_deg"]):
            ax.plot(abs(r["el_true_deg"]), r["abs_el_error_deg"], marker="s", linestyle="none",
                    color=_color(r["array_id"]), markersize=5)
    ax.set_xlim(0, 90)
    ax.set_xlabel("True angle (deg): cone angle from the axis for lines (circles); "
                  "angle from the plane for the square (squares)")
    ax.set_ylabel("Estimated minus true angle (deg)")
    ax.set_title("(b) Peak bias when the beamformer assumes the wrong c\n(curves: closed form; markers: numerical "
                 "peak search)")
    handles = [Line2D([0], [0], color=_color(a["id"]), marker="o" if a["rank"] == 1 else "s", linestyle="none",
                      markerfacecolor="none" if a["id"] == "A1" else _color(a["id"]), label=a["id"])
               for a in data["arrays"] if a["rank"] in (1, 2)]
    ax.legend(handles=handles, loc="lower left", frameon=False)
    fig.tight_layout()
    _save(fig, outdir, "fig10_sound_speed_robustness.png", written)


def make_sim01_figures(data: dict, outdir) -> list[str]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    fig_geometries(data, outdir, written)
    fig_horizontal_cuts(data, outdir, written)
    fig_vertical_cuts(data, outdir, written)
    fig_freq_az_maps(data, outdir, written)
    fig_sphere_maps(data, outdir, written)
    fig_metrics_vs_frequency(data, outdir, written)
    fig_regime_map(data, outdir, written)
    fig_ula_sensitivity(data, outdir, written)
    fig_scale_sensitivity(data, outdir, written)
    fig_sound_speed(data, outdir, written)
    return written
