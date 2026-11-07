# SIM-01 run 20261107T200834Z_cf0574c6_059a354

* Title: Array geometry and idealized acoustic performance
* Created (UTC): 2026-11-07T20:08:34+00:00
* Config: `configs/sim01/sim01_baseline.yaml` (sha256 `cf0574c614ca53f5...`)
* Code: picket_sim 0.1.0, git `059a354ceaeeb132b638ea5b580f4bbb1b392066` (dirty: False)
* Python 3.13.18, NumPy 2.5.4, Matplotlib 3.11.2

## Self-checks

* `di_closed_form_vs_quadrature_max_abs_db`: 1.2967404927621828e-13
* `di_closed_form_vs_quadrature_tolerance_db`: 0.01
* `hpsf_rank1_exact_vs_sphere_grid_max_abs`: 0.0024153656304792825
* `normalization_max_abs_error`: 2.220446049250313e-16
* `sweep_rows_resolution_limited`: 0
* `worstcase_alias_minus_steering_alias_max_rel`: 0.0
* `threshold_scaling_with_c_max_abs_ratio_error`: 0.0004232905633057005

## Warnings

* none

## Assumptions

* Single-frequency (narrowband) plane waves from far-field sources.
* Homogeneous, lossless, unbounded medium; no surface, bottom, multipath or refraction.
* Ideal omnidirectional point hydrophones with identical, perfectly known responses and positions.
* No sensor, electronic, ambient, flow, platform or self-noise in the beampattern metrics.
* Directivity index uses a spherically isotropic noise model; white-noise gain uses spatially white noise.
* Conventional uniformly weighted delay-and-sum beamforming only.
* Array frame is right-handed with z up; linear arrays lie along x; the square array lies in the horizontal x-y plane.
* A4 coordinates are a notional placeholder layout, not derived from any host survey.

## Tables

## Geometry summary

| ID | Configuration | N | Max dimension (m) | Min spacing (m) | Observable dims | Geometric ambiguity | Exact grating onset c/2d (Hz) | Worst-case -1 dB lobe onset (Hz) | Worst-case -3 dB lobe onset (Hz) | WNG (dB) |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | Single hydrophone | 1 | 0.000 | n/a | 0 | omnidirectional | n/a | n/a | n/a | 0.00 |
| A1 | 4-el line, 0.15 m | 4 | 0.450 | 0.150 | 1 | conical | 5,000 | 4,663 | 4,432 | 6.02 |
| A2 | 4-el line, 0.30 m | 4 | 0.900 | 0.300 | 1 | conical | 2,500 | 2,332 | 2,216 | 6.02 |
| A3 | 4-el square, 0.30 m | 4 | 0.424 | 0.300 | 2 | mirror | 2,500 | 2,126 | 1,876 | 6.02 |
| A4 | 4-el distributed (notional) | 4 | 1.070 | 0.901 | 3 | none | n/a | 706 | 596 | 6.02 |

* Worst-case onset: lowest frequency at which some steering/look pair produces a non-mainlobe lobe at or above the level in the observable space (array factor in wavevector space, |q| <= 2k).
* n/a: undefined (single sensor) or no such lobe below the band edge.
* Sound speed 1500 m/s.


## Comparative results (horizon steering ring unless stated)

| ID | N | Max dim (m) | Geometric ambiguity | WNG (dB) | DI 0.1-1 kHz (dB) | DI 1-3 kHz (dB) | DI 3-10 kHz (dB) | HPSF 0.1-1 kHz | HPSF 1-3 kHz | HPSF 3-10 kHz | HPBW_h 1 kHz (deg) | HPBW_h 2.5 kHz (deg) | HPBW_h 5 kHz (deg) | f_HP (Hz) | f_SL (Hz) | f_amb -3 dB horizon (Hz) | f_amb -3 dB any steering (Hz) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1 | 0.00 | omnidirectional | 0.0 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | inf | inf | inf | n/a | n/a | n/a | n/a |
| A1 | 4 | 0.45 | conical | 6.0 | 0.17 | 3.19 | 5.48 | 1.00 | 0.48 | 0.27 | 231 | 116 | 41 | 667 | 1,465 | 4,432 | 4,432 |
| A2 | 4 | 0.90 | conical | 6.0 | 0.65 | 5.09 | 5.81 | 1.00 | 0.31 | 0.24 | 139 | 41 | 19 | 334 | 733 | 2,216 | 2,216 |
| A3 | 4 | 0.42 | mirror | 6.0 | 0.27 | 5.48 | 5.90 | 1.00 | 0.24 | 0.21 | 157 | 59 | 29 | 633 | 1,306 | 1,877 | 1,876 |
| A4 | 4 | 1.07 | none | 6.0 | 1.73 | 5.95 | 6.00 | 0.79 | 0.15 | 0.14 | 64 | 25 | 13 | 270 | 527 | 623 | 596 |

* DI: directivity index vs spherically isotropic noise (ideal DAS), median over horizon steering, then median over frequencies in the band. Not detection performance.
* HPSF: fraction of all directions within 3 dB of the steered response (includes every ambiguity); 1.0 = no half-power discrimination anywhere.
* HPBW_h: half-power width on the horizontal great circle, median over horizon steering; inf = half-power region wraps the circle for most steering directions (includes merged left/right mirror lobes for line arrays).
* WNG: white-noise gain of uniform DAS = 10 log10 N, independent of geometry and frequency.


## Regime thresholds over steering sets

| ID | Steering set | f_HP best (Hz) | f_HP median (Hz) | f_HP worst (Hz) | f_SL median (Hz) | f_amb(-3 dB) earliest (Hz) | f_amb(-3 dB) median (Hz) | f_amb(-1 dB) earliest (Hz) | Worst-case -3 dB onset, any steering (Hz) |
|---|---|---|---|---|---|---|---|---|---|
| A0 | horizon | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| A1 | horizon | 569 | 667 | 1,139 | 1,465 | 4,432 | 5,192 | 4,664 | 4,432 |
| A2 | horizon | 285 | 334 | 569 | 733 | 2,216 | 2,596 | 2,332 | 2,216 |
| A3 | horizon | 625 | 633 | 644 | 1,306 | 1,877 | 2,010 | 2,126 | 1,876 |
| A4 | horizon | 253 | 270 | 298 | 527 | 623 | 717 | 741 | 596 |
| A0 | depressed30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| A1 | depressed30 | 610 | 706 | 1,139 | 1,551 | 4,751 | 5,500 | 5,000 | 4,432 |
| A2 | depressed30 | 305 | 353 | 569 | 776 | 2,376 | 2,750 | 2,500 | 2,216 |
| A3 | depressed30 | 670 | 679 | 690 | 1,395 | 2,011 | 2,138 | 2,279 | 1,876 |
| A4 | depressed30 | 257 | 273 | 306 | 526 | 608 | 731 | 722 | 596 |

* f_HP: lowest frequency at which some direction is >= 3 dB below the steered response.
* f_SL: lowest frequency at which a sidelobe exists in the observable visible region.
* f_amb(L): lowest frequency at which an observable-space ambiguity lobe reaches L dB (geometric cone/mirror ambiguity excluded).
* '> band': not reached below the upper band edge; n/a: undefined (single sensor).


## Pareto dominance (only attributes evaluated in SIM-01)

| Attribute set | ID | Dominated | Dominated by | Undefined attributes |
|---|---|---|---|---|
| all_candidates | A0 | False |  |  |
| all_candidates | A1 | False |  |  |
| all_candidates | A2 | False |  |  |
| all_candidates | A3 | False |  |  |
| all_candidates | A4 | False |  |  |
| multichannel | A1 | False |  |  |
| multichannel | A2 | False |  |  |
| multichannel | A3 | False |  |  |
| multichannel | A4 | False |  |  |

* A candidate is dominated if another is at least as good on every listed attribute and strictly better on one. Attribute lists are in the configuration (pareto.sets).
* Cost is NOT evaluated; channel count and maximum dimension are proxies only.


## Figures

* `figures/fig01_geometries.png`
* `figures/fig02_horizontal_beampatterns.png`
* `figures/fig03_vertical_beampatterns.png`
* `figures/fig04_frequency_azimuth_maps.png`
* `figures/fig05_sphere_ambiguity_maps.png`
* `figures/fig06_metrics_vs_frequency.png`
* `figures/fig07_regime_map.png`
* `figures/fig08_line_array_sensitivity.png`
* `figures/fig09_aperture_scaling.png`
* `figures/fig10_sound_speed_robustness.png`
