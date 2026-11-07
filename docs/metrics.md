# Metric definitions (SIM-01)

All metrics are for conventional (uniformly weighted) delay-and-sum beamforming on ideal
omnidirectional point sensors, narrowband, far field, homogeneous medium. They are properties of
the geometry and the frequency, not detection performance. Implementation: `metrics.py`,
`analysis.py`, `noise.py`. Rationale: ADR-0005.

## Geometric ambiguity (frequency independent, exact)

`rank` of the span of sensor difference vectors (SVD of centred positions, tolerance 1 nm).
0 = omnidirectional, 1 = conical (line), 2 = mirror (plane), 3 = none (volumetric). The
*observable space* is the projection of `u` onto that span; sidelobe/aliasing metrics are computed
there so that geometric ambiguity is not double counted as a "sidelobe".

## Gains

| Metric | Definition | Notes |
|---|---|---|
| `di_db` | `10 log10(N^2 / a0^H Gamma a0)`, `Gamma_mn = sin(k r_mn)/(k r_mn)` | Ideal array gain vs spherically isotropic noise. Self-checked against `4 pi / integral P dOmega` on a Gauss-Legendre sphere grid in every run. Can exceed `10 log10 N` when some `sinc` terms are negative. |
| `wng_db` | `10 log10 N` | Gain vs spatially uncorrelated noise; constant for uniform DAS. |

## Whole-sphere quantities (include every ambiguity)

| Metric | Definition |
|---|---|
| `hpsf` | Fraction of all directions (solid-angle weighted) with `P >= 0.5`. Exact 1-D integral for rank 1 (`u . axis` is uniform on `[-1, 1]`), Gauss-Legendre quadrature otherwise. 1.0 = no half-power discrimination anywhere. |
| `min_power_db` | Minimum of `P` over the visible region. |

## Great-circle cuts through the steering direction

* Horizontal cut: great circle through `u0` tangent to azimuth (the horizon itself when `el0 = 0`).
* Vertical cut: great circle through `u0` and the zenith.

| Metric | Definition |
|---|---|
| `hpbw_{h,v}_deg` | Width of the connected region around `u0` with `P >= 0.5` (linear interpolation at the edges). NaN when that region covers the whole circle. |
| `max_outside_{h,v}_db` | Largest `P` on the cut outside the mainlobe (mainlobe = between the first local minima on each side). Includes geometric ambiguity, e.g. the left/right mirror lobe of a horizontal line array. NaN when no region outside the mainlobe exists. |

## Observable-space lobes

| Metric | Definition |
|---|---|
| `psl_obs_db` | Highest local maximum of `P` other than the mainlobe (and, for rank 2, other than the mirror image of the mainlobe). Rank 1: on a 1-D grid of `p = u . axis` in `[-1, 1]` (end points included as boundary maxima). Rank 2/3: on the sphere grid with 8-neighbour detection (wrapping azimuth and poles), then iterative local zoom refinement. NaN when no such lobe exists in the visible region. |
| `n_amb_lobes_ge_<L>` | Number of distinct non-mainlobe lobes with peak at or above `L` dB. |
| `resolution_ok` | False when the grid has fewer than 4 samples across `lambda / aperture`. |

## Regime thresholds (per steering direction)

Found by scanning the frequency grid to the first frequency where the predicate holds, then
bisection in log-frequency (relative tolerance 1e-3).

| Threshold | Predicate | Meaning |
|---|---|---|
| `f_hp_hz` | `min P <= 0.5` | Below it no direction is suppressed by 3 dB: no half-power discrimination by conventional DAS. This is a -3 dB criterion; it does not bound the direction information available to other estimators (ADR-0008). |
| `f_sl_hz` | a sidelobe exists in the observable visible region | Below it the mainlobe fills the whole visible region (no nulls, broad beam). For a broadside line, `f_SL = c / (N d)`. |
| `f_amb_<L>_hz` | `psl_obs >= L` | An ambiguity lobe at or above `L` dB has entered the visible region. |

## Aggregating thresholds over steering directions

Statistics over a steering set must state their rule (ADR-0008). Median band: median f_SL to median
f_amb (a typical direction). Guaranteed band: latest f_SL to earliest f_amb (every direction in the
set). `tools/sim01_band_definitions.py` derives both from a run's `thresholds_summary.csv`.

## Worst case over all steering directions

`f_alias_<L>_hz`: the smallest `|q|` outside the mainlobe of the array factor
`W(q) = mean_n exp(j q . s_n)` (observable space) with `|W|^2 >= L`, converted with
`f = c |q| / (4 pi)` because every `|q| <= 2k` is realized by some steering/look pair. For a line or
square lattice of spacing `d`, the exact grating lobe (`L = 0 dB`) appears at `c / (2 d)`; the
-1 and -3 dB onsets are slightly lower. The pipeline asserts `f_alias <= f_amb` for every steering.

## What these metrics do not tell you

* Detection range or probability: requires source level, propagation loss, ambient and platform
  noise, sensor self-noise, processing gain, bandwidth and integration time. Not modeled.
* Broadband or time-difference-of-arrival performance: narrowband aliasing overstates broadband
  ambiguity, and exact narrowband grating lobes do not establish broadband direction-finding failure.
* Bounds on array gain: WNG = 10 log10 N is the gain of equal weights in spatially white noise only.
* Robustness to calibration, position, gain/phase errors, element directivity or host shading.
