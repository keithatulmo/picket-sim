"""D02 coherence collection plan: design numbers computed with the study code (no number in the plan from memory).

Writes ``reports/SIM-02B2A_d02_design.md`` and ``reports/SIM-02B2A_d02_design_*.csv``:

1. Spacing set of the proposed line (Golomb marks 0, 1, 4, 10, 18, 23, 25 times a unit), checked to be all distinct,
   against the inter-element spacings of the SIM-02B.2-A candidates.
2. Model coherence at each spacing and frequency from the study's own coherence functions (spherical isotropic,
   horizontally isotropic, exponential flow-like with the assumed 0.1 m correlation length): the contrast that lets
   a short-spacing pair separate flow-associated noise from acoustic noise.
3. Magnitude-squared coherence (MSC) estimator statistics for n independent segments: the null exceedance law
   P(MSC_hat > x) = (1 - x)^(n - 1) and the large-sample variance 2 g (1 - g)^2 / n (g the true MSC), each checked by
   Monte Carlo with independent Gaussian segments before it is quoted.
4. Inter-channel timing error that produces a given phase error, dt = dphi / (360 f).

    python tools/d02_collection_design.py [--out reports/SIM-02B2A_d02_design]
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from picket_sim.experiments.sim02b2a import Sim02B2AStudy  # noqa: E402
from picket_sim.noisefields import coherence_exponential, coherence_horizontal, coherence_spherical  # noqa: E402
from picket_sim.tables import write_csv  # noqa: E402

MARKS = (0, 1, 4, 10, 18, 23, 25)
UNIT_M = 0.08
FREQS = (20.0, 100.0, 200.0, 1000.0, 2000.0, 5000.0, 10000.0)
L_FLOW = 0.1  # assumed flow-like correlation length of SIM-02A/B (N-FLOW), not a measurement


def msc_hat(n_seg, g, rng, reps):
    """MSC estimates from n_seg independent segments of a complex Gaussian pair with true MSC g."""
    a = (rng.standard_normal((reps, n_seg)) + 1j * rng.standard_normal((reps, n_seg))) / math.sqrt(2)
    w = (rng.standard_normal((reps, n_seg)) + 1j * rng.standard_normal((reps, n_seg))) / math.sqrt(2)
    b = math.sqrt(g) * a + math.sqrt(1 - g) * w
    sab = np.mean(a * b.conj(), axis=1)
    return np.abs(sab) ** 2 / (np.mean(np.abs(a) ** 2, axis=1) * np.mean(np.abs(b) ** 2, axis=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "reports/SIM-02B2A_d02_design"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(open(REPO / "configs/sim02b/sim02b2a_baseline.yaml"))
    st = Sim02B2AStudy(cfg, log=lambda m: None)
    c0 = float(st.c0)
    rng = np.random.default_rng(20261109)

    # 1. spacings
    diffs = sorted(abs(i - j) for i, j in itertools.combinations(MARKS, 2))
    if len(set(diffs)) != len(diffs):
        raise SystemExit("marks are not a Golomb ruler (repeated spacing)")
    spacings = [round(d * UNIT_M, 6) for d in diffs]
    cand = []
    for c in ("A1", "P8-C", "A4"):
        p = st.b1.geoms[c].positions_m
        d = np.linalg.norm(p[:, None] - p[None], axis=-1)[np.triu_indices(len(p), 1)]
        cand.append({"candidate": c, "elements": len(p), "min_spacing_m": float(d.min()), "max_spacing_m": float(d.max())})
    sp_rows = [{"pair_spacing_m": s} for s in spacings]

    # 2. model coherence (study functions; two-element positions on the x axis)
    coh = []
    for f in FREQS:
        k = 2 * math.pi * f / c0
        for s in [0.04] + spacings[:1] + [0.16, 0.48, 1.04, 2.0]:
            pos = np.array([[0.0, 0.0, 0.0], [s, 0.0, 0.0]])
            coh.append({"f_hz": f, "spacing_m": s, "half_wavelength_m": c0 / f / 2,
                        "spherical": float(np.real(coherence_spherical(pos, k)[0, 1])),
                        "horizontal": float(np.real(coherence_horizontal(pos, k)[0, 1])),
                        "exponential_L0p1": float(np.real(coherence_exponential(pos, L_FLOW)[0, 1]))})

    # 3. MSC estimator statistics, formula against Monte Carlo
    msc = []
    for n in (16, 64, 256, 1024):
        for alpha in (0.05, 0.01):
            thr = 1 - alpha ** (1 / (n - 1))
            sim = msc_hat(n, 0.0, rng, 20000)
            p_mc = float(np.mean(sim > thr))
            se = math.sqrt(alpha * (1 - alpha) / sim.size)
            if abs(p_mc - alpha) > 4 * se:
                raise SystemExit(f"null MSC law fails at n={n}, alpha={alpha}: {p_mc} vs {alpha}")
            msc.append({"segments": n, "kind": "null threshold", "alpha_or_true_msc": alpha, "formula": thr,
                        "monte_carlo": p_mc, "monte_carlo_se": se, "bias_mean_null": float(np.mean(sim))})
        for g in (0.3, 0.6, 0.9):
            sim = msc_hat(n, g, rng, 20000)
            sd_f = math.sqrt(2 * g * (1 - g) ** 2 / n)
            sd_mc = float(np.std(sim))
            if n >= 64 and abs(sd_mc / sd_f - 1) > 0.15:
                raise SystemExit(f"MSC variance approximation fails at n={n}, g={g}: {sd_mc} vs {sd_f}")
            msc.append({"segments": n, "kind": "standard deviation", "alpha_or_true_msc": g, "formula": sd_f,
                        "monte_carlo": sd_mc, "monte_carlo_se": float("nan"), "bias_mean_null": float(np.mean(sim) - g)})

    # 4. timing
    tim = [{"f_hz": f, "phase_error_deg": dp, "timing_error_us": dp / (360 * f) * 1e6}
           for f in (200.0, 2000.0, 10000.0) for dp in (1.0, 5.0)]

    write_csv(Path(f"{out}_spacings.csv"), sp_rows)
    write_csv(Path(f"{out}_coherence.csv"), coh)
    write_csv(Path(f"{out}_msc.csv"), msc)
    write_csv(Path(f"{out}_timing.csv"), tim)
    write_csv(Path(f"{out}_candidates.csv"), cand)

    L = ["# D02 coherence collection plan: design numbers", "",
         "Generated by `tools/d02_collection_design.py` with the study code (coherence functions from "
         "`picket_sim.noisefields`, sound speed from the SIM-02B.2-A configuration). Every number in "
         "`docs/coherence_collection_plan.md` comes from these tables.", "",
         f"Sound speed {c0:g} m/s. Line: marks {MARKS} x {UNIT_M:g} m, aperture {MARKS[-1] * UNIT_M:g} m, "
         f"{len(spacings)} pair spacings, all distinct: {min(spacings):g} to {max(spacings):g} m.", "",
         "## Candidate spacings (SIM-02B.2-A geometry)", "", "| Candidate | Elements | Min spacing (m) | Max spacing (m) |",
         "|---|---|---|---|"]
    L += [f"| {r['candidate']} | {r['elements']} | {r['min_spacing_m']:.3f} | {r['max_spacing_m']:.3f} |" for r in cand]
    L += ["", "## Model coherence between two points", "",
          "Coherence function values (real; the magnitude-squared coherence is their square). The 0.04 m row is the "
          "optional close pair; the other spacings belong to the line.", "",
          "| f (Hz) | spacing (m) | lambda/2 (m) | spherical | horizontal | exponential, L = 0.1 m (assumed) |",
          "|---|---|---|---|---|---|"]
    L += [f"| {r['f_hz']:g} | {r['spacing_m']:g} | {r['half_wavelength_m']:.3g} | {r['spherical']:.3f} | "
          f"{r['horizontal']:.3f} | {r['exponential_L0p1']:.3f} |" for r in coh]
    L += ["", "## MSC estimator with n independent segments (formula checked by Monte Carlo, 20,000 replicates)", "",
          "| n | quantity | alpha or true MSC | formula | Monte Carlo | mean bias |", "|---|---|---|---|---|---|"]
    L += [f"| {r['segments']} | {r['kind']} | {r['alpha_or_true_msc']:g} | {r['formula']:.4f} | {r['monte_carlo']:.4f} | "
          f"{r['bias_mean_null']:+.4f} |" for r in msc]
    L += ["", "For the null threshold rows, 'Monte Carlo' is the simulated exceedance probability of the formula "
          "threshold; for the standard-deviation rows it is the simulated standard deviation. The large-sample "
          "variance formula is checked only for n >= 64.", "",
          "## Inter-channel timing error for a given phase error", "", "| f (Hz) | phase error (deg) | timing error (us) |",
          "|---|---|---|"]
    L += [f"| {r['f_hz']:g} | {r['phase_error_deg']:g} | {r['timing_error_us']:.3g} |" for r in tim]
    Path(f"{out}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}.md and CSV tables")


if __name__ == "__main__":
    main()
