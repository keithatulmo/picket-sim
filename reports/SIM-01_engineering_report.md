# PCK-SIM-001 / SIM-01 Engineering Report

> **DRAFT.** Placeholders in capitals (RUNID, CODESHA, CFGSHA, SELFCHECKS, COMPARISON_TABLE,
> PARETO_SUMMARY, SSCHECK, SQ_A4_*, CROSSRUN) are filled from the run of record when it completes.
> Do not use this version.

**Array Geometry and Idealized Acoustic Performance of Candidate Picket Arrays**

| | |
|---|---|
| Program | Ulmo / Picket, PCK-SIM-001 |
| Increment | SIM-01 (array geometry, idealized narrowband performance) |
| Run of record | `RUNID` |
| Code | `picket_sim` 0.1.0, git `CODESHA` (clean tree) |
| Configuration | `configs/sim01/sim01_baseline.yaml` (sha256 `CFGSHA`) |
| Reproduce | `make sim01` (equivalently `python -m picket_sim run configs/sim01/sim01_baseline.yaml`) |
| Status | Complete for SIM-01 scope. Not a design selection. |

All numbers in this report are read from the tables of the run of record
(`results/sim01/RUNID/tables/`). Figures are in `results/sim01/RUNID/figures/`. Confidence levels
refer to the statement *as a property of the stated model*; transfer to hardware is addressed
separately in Section 8.

---

## 0. Bottom line

1. **Four elements buy at most 6.0 dB of ideal array gain, and much less where it matters at low
   frequency.** Uniform DAS white-noise gain is exactly 10 log10 4 = 6.02 dB for every 4-element
   candidate. Against spherically isotropic noise the band-median directivity index (DI) from
   100 Hz to 1 kHz is 0.17 dB (A1), 0.65 dB (A2), 0.27 dB (A3) and 1.73 dB (A4). The compact
   candidates (A1 and A3, at most 0.45 m) are, for gain purposes, single hydrophones below roughly
   1 kHz.
   (Confidence: high for the model; real gain will be lower, see Section 8.)
2. **The useful multichannel product is bearing information, and it exists only in a band set by
   aperture.** No direction is suppressed by even 3 dB below the half-power onset f_HP (median over
   horizon steering): A1 667 Hz, A2 334 Hz, A3 633 Hz, A4 270 Hz. Below these frequencies a
   4-channel DAS array has no directional discrimination at all. (High.)
3. **Four elements leave almost no unambiguous band once they are spread over two or three
   dimensions.** The ratio between the frequency where an ambiguity lobe of -3 dB first appears and
   the frequency where the mainlobe first closes is 3.03 for both lines, 1.44 for the 2x2 square
   and 1.18 for A4. Usable conventional bands (horizon steering): A1 1.47 to 4.43 kHz, A2 0.73 to
   2.22 kHz, A3 1.31 to 1.88 kHz, A4 0.53 to 0.62 kHz. (High.)
4. **Geometric ambiguity is exact and frequency independent.** Lines (A1, A2) see a cone: every
   horizontal target off the array axis has a 0 dB left/right mirror at every frequency. The horizontal square (A3) has a 0 dB
   up/down mirror. Only the volumetric A4 is free of geometric ambiguity, and A0 has no directional
   information at all. (High; mathematical.)
5. **Irregular placement does not save a 4-element volumetric array from aliasing.** Any four
   non-coplanar sensors have exactly three independent baselines, which always generate a lattice;
   A4 therefore has exact 0 dB grating lobes from 857 Hz (worst-case steering), -3 dB ambiguity
   lobes from 596 Hz, and up to 276 lobes within 3 dB of the mainlobe at 10 kHz. (High;
   mathematical, verified numerically.)
6. **A1 and A2 are one design at two scales.** Every A2 metric at frequency f equals the A1 metric at
   2f. Choosing between them is choosing a band, not a geometry. (High.)
7. **No candidate selection is supported by SIM-01.** No candidate is Pareto-dominated on the full
   multichannel attribute set; A1 is dominated by A3 only when aliasing onset is excluded from the
   attributes. The evidence is sufficient to reject *4-element narrowband DAS* as a way to obtain
   wideband, unambiguous, full-azimuth bearing, and insufficient to choose among the candidates
   until the mission band, the processing (narrowband vs broadband/TDOA) and the noise environment
   are specified. (Moderate; depends on requirements not yet defined.)

---

## 1. Scope

**Modeled:** single-frequency plane waves from far-field sources; homogeneous, lossless, unbounded
medium (c = 1500 m/s nominal, 1450 to 1550 m/s for robustness); ideal identical omnidirectional
point hydrophones at exactly known positions; conventional uniformly weighted delay-and-sum (DAS);
ideal array gain against spherically isotropic and spatially white noise; sound-speed mismatch
between data and beamformer.

**Not modeled (by the handoff's exclusions or as SIM-01 idealizations):** ocean propagation and
boundaries, vessel self-noise and flow noise, structural acoustics, element directivity and hull
baffling, calibration and position errors, sensor electronic noise, broadband or time-difference
processing, adaptive or superdirective beamforming, detection range. Full register:
`docs/assumptions.md`.

**What the numbers are not:** none of the gains, beamwidths or thresholds here is detection
performance. DI is a geometry figure of merit in a model noise field.

---

## 2. Candidates

All candidates are defined in the configuration and pass through the same interface
(`ArrayGeometry` -> `PlaneWaveManifold` -> DAS -> metrics).

| ID | Configuration | N | Max dimension (m) | Min spacing (m) | Observable dims | Geometric ambiguity |
|---|---|---|---|---|---|---|
| A0 | Single hydrophone | 1 | 0 | n/a | 0 | omnidirectional |
| A1 | Line along x, 0.15 m spacing | 4 | 0.450 | 0.150 | 1 | conical |
| A2 | Line along x, 0.30 m spacing | 4 | 0.900 | 0.300 | 1 | conical |
| A3 | 2x2 square in the horizontal x-y plane, 0.30 m side | 4 | 0.424 | 0.300 | 2 | mirror (up/down) |
| A4 | Distributed, non-coplanar, irregular (notional placeholder) | 4 | 1.070 | 0.901 | 3 | none |

A4 coordinates (m): (0, 0, 0), (1.00, 0, 0), (0.35, 0.85, 0), (0.40, 0.30, -0.75). They are a
placeholder for elements spread around a small host and have no survey basis; Section 5.6 shows
how A4 conclusions scale with size. Orientation is an assumption: lines along x, square
horizontal. Figure: `fig01_geometries.png`.

![Figure 1. Candidate geometries, top and side views at a common scale.](../results/sim01/RUNID/figures/fig01_geometries.png)
*Figure 1. Candidate geometries, top and side views at a common scale.*

---

## 3. Method

### 3.1 Governing equations

Right-handed frame, metres, z up; azimuth from +x toward +y; elevation positive up; `u` is the unit
vector toward the source; time convention exp(+j omega t) (`docs/conventions.md`).

* wavelength lambda = c / f, wavenumber k = 2 pi f / c
* arrival-time offset tau_n = -(u . r_n) / c (sensors nearer the source receive first)
* steering vector a_n(u) = exp(+j k u . r_n)
* DAS weights steered to u0: w = a(u0) / N; normalized power P(u; u0) = |w^H a(u)|^2 / |w^H a(u0)|^2,
  so P = 1 (0 dB) in the steering direction by construction, never normalized to a grid maximum
* equivalently P = |W(k(u - u0))|^2 with array factor W(q) = (1/N) sum_n exp(j q . r_n)
* array gain AG = |w^H a0|^2 / (w^H Gamma w): Gamma = I gives WNG = N; Gamma_mn = sin(k r_mn)/(k r_mn)
  (spherically isotropic) gives DI

### 3.2 Geometric ambiguity, exactly

A phase common to all channels is unobservable, so P depends on u only through its projection onto
the span of the sensor difference vectors. The rank of that span (0 to 3) fixes the ambiguity
exactly and independently of frequency: rank 1 = cone about the line axis, rank 2 = mirror image
through the plane, rank 3 = none. Sidelobe and aliasing metrics are computed in this observable
space, so that a 0 dB cone or mirror image is reported as geometric ambiguity, not as a sidelobe.

### 3.3 Metrics (full definitions: `docs/metrics.md`)

* **DI** (dB), closed form; **WNG** = 10 log10 N.
* **HPSF**, the half-power sphere fraction: share of all directions within 3 dB of the steered
  response. Includes every ambiguity; 1.0 means no half-power discrimination anywhere.
* **HPBW_h / HPBW_v**: -3 dB widths on the horizontal and vertical great circles through the
  steering direction; undefined (shown as `inf` in medians) when the half-power region wraps the
  circle.
* **PSL_obs**: highest non-mainlobe lobe in the observable space; undefined when no sidelobe exists
  in the visible region.
* **Regime thresholds per steering direction**: f_HP (first direction 3 dB down), f_SL (first
  sidelobe region; the mainlobe no longer fills the visible region), f_amb(L) (first observable
  ambiguity lobe at or above L dB).
* **Worst case over all steering**: f_alias(L) from the array factor in wavevector space
  (|q| <= 2k), and the exact (0 dB) grating onset from the reciprocal lattice of the baselines.

Statistics are taken over a horizon ring (el = 0, 24 azimuths) and a depressed ring (el = -30 deg).
The frequency grid is 121 log-spaced points from 100 Hz to 10 kHz; thresholds are refined by
bisection to 0.1 %.

### 3.4 Numerical methods and verification

* Sphere integrals: Gauss-Legendre (181 nodes in sin el) x 360 azimuths, exact for the band-limited
  patterns involved. Cuts: 0.1 deg. Line arrays: 4001-point grid in the observable coordinate.
* Local maxima: neighbour comparison on the grid (wrapping azimuth and poles), then iterative zoom
  refinement.
* **Verification suite: 131 tests, all passing on the run-of-record commit.** Highlights:
  hand-computed steering vectors on all three axes; the far-field limit of an exact spherical
  wave; a time-domain delayed-pulse FFT check of the delay sign; closed-form Dirichlet patterns;
  broadside symmetry; broadside and endfire null positions; cone and mirror invariances under
  random rotations and reflections; translation invariance; DI quadrature vs closed form for all
  candidates; DI = 10 log10 N at half-wavelength spacing; single-hydrophone non-directionality at
  every frequency; the exact half-power beamwidth from an independent root; the N = 4 first
  sidelobe (-11.30 dB) against brute force; grating lobe exactly at c/(2d); worst-case aliasing
  onset against independent line and square derivations; f_SL = c/(Nd); f_HP = c/(8d) for a pair at
  endfire; f/c scaling; sound-speed mismatch against closed form; unit-error rejection; plotting
  orientation and normalization; byte-identical outputs from two identical end-to-end runs.
* **Self-checks embedded in the run of record** (`record.json`): SELFCHECKS

### 3.5 Errors found and corrected during SIM-01

Recorded for traceability (`results/sim01/ERRATA.md`). The first complete run
(`20261107T200834Z_cf0574c6_059a354`, retained unmodified) contained a floating-point artifact.
The sphere-quadrature HPSF could read 1 + 2e-16, and without a tie tolerance in the Pareto
comparison this kept A1 off the dominated list. It also had two figure annotation errors and
lacked the exact grating onset for A4. All other numbers in that run are identical to the run of
record (Section 9).

---

## 4. Results

### 4.1 Directional regimes (the central result)

`fig07_regime_map.png`; `tables/thresholds_summary.md`.

![Figure 2. Directional regimes versus frequency (horizon steering).](../results/sim01/RUNID/figures/fig07_regime_map.png)
*Figure 2. Directional regimes versus frequency (horizon steering).*

| ID | f_HP best / median / worst (Hz) | f_SL median (Hz) | f_amb -3 dB earliest horizon steering (Hz) | f_amb -3 dB any steering (Hz) | Exact grating, any steering (Hz) | f_amb / f_SL |
|---|---|---|---|---|---|---|
| A1 | 569 / 667 / 1,139 | 1,465 | 4,432 | 4,432 | 5,000 | 3.03 |
| A2 | 285 / 334 / 569 | 733 | 2,216 | 2,216 | 2,500 | 3.03 |
| A3 | 625 / 633 / 644 | 1,306 | 1,877 | 1,876 | 2,500 | 1.44 |
| A4 | 253 / 270 / 298 | 527 | 623 | 596 | 857 | 1.18 |

Reading the regimes:

* **f < f_HP:** no direction is 3 dB below the look direction. DAS provides no directional
  discrimination.
* **f_HP to f_SL:** a broad beam with no nulls in the visible region.
* **f_SL to f_amb:** conventional beamforming, a closed mainlobe and no ambiguity lobe at -3 dB
  (within the geometric ambiguity class).
* **Above f_amb:** ambiguity lobes within 3 dB of the mainlobe for at least one horizon steering
  direction. Above the exact grating onset they are 0 dB copies of the mainlobe for some steering.

For a line steered broadside the thresholds have closed forms that the run reproduces. f_SL = c/(Nd)
(measured f_SL x N d / c = 1.0005 for every N and d in the sensitivity study). Half-power
discrimination begins when the aperture (N - 1) d reaches 0.25 lambda (N = 2), 0.34 lambda (N = 4) or
0.42 lambda (N = 16). Endfire steering halves both thresholds.

### 4.2 Array gain: single channel versus multichannel

`fig06_metrics_vs_frequency.png` (a); `tables/comparison.md`.

![Figure 3. DI, horizontal half-power width, half-power sphere fraction and worst observable ambiguity lobe versus frequency.](../results/sim01/RUNID/figures/fig06_metrics_vs_frequency.png)
*Figure 3. DI, horizontal half-power width, half-power sphere fraction and worst observable ambiguity lobe versus frequency.*

| ID | WNG (dB) | DI median 0.1-1 kHz (dB) | DI median 1-3 kHz (dB) | DI median 3-10 kHz (dB) |
|---|---|---|---|---|
| A0 | 0.00 | 0.00 | 0.00 | 0.00 |
| A1 | 6.02 | 0.17 | 3.19 | 5.48 |
| A2 | 6.02 | 0.65 | 5.09 | 5.81 |
| A3 | 6.02 | 0.27 | 5.48 | 5.90 |
| A4 | 6.02 | 1.73 | 5.95 | 6.00 |

* The 6.02 dB WNG is the ceiling for incoherent sensor noise and is independent of geometry. Doubling
  N adds 3 dB; going from 4 to 16 elements adds 6 dB.
* Against diffuse noise, gain collapses when sensors are closer than about lambda/2, because the
  noise at the sensors is then correlated. DAS DI can exceed 10 log10 N for spacings between lambda/2
  and lambda (negatively correlated noise). The line-array study reaches about 7.7 dB for N = 4 and
  14.3 dB for N = 16 at d/lambda near 0.8 to 0.93 on the analysis grid (`fig08` (b)), consistent with
  the classical long-line value 2L/lambda. That regime sits immediately below grating-lobe onset.
* DI says nothing about ambiguity. A4 holds a median DI between 5.9 and 6.1 dB at 2, 2.5, 5 and
  10 kHz while carrying 12 to 276 ambiguity lobes within 3 dB of the mainlobe. Gain and direction
  finding must be assessed separately.

### 4.3 Beampatterns and resolution

`fig02_horizontal_beampatterns.png`, `fig03_vertical_beampatterns.png`,
`fig04_frequency_azimuth_maps.png`, `fig05_sphere_ambiguity_maps.png`;
`tables/representative_frequencies.md`.

![Figure 4. Horizontal-plane beampatterns at representative frequencies, steered to az = 60 deg.](../results/sim01/RUNID/figures/fig02_horizontal_beampatterns.png)
*Figure 4. Horizontal-plane beampatterns at representative frequencies, steered to az = 60 deg.*

![Figure 5. Horizontal-plane response versus frequency (steered to az = 60 deg) with the -3 dB contour.](../results/sim01/RUNID/figures/fig04_frequency_azimuth_maps.png)
*Figure 5. Horizontal-plane response versus frequency (steered to az = 60 deg) with the -3 dB contour.*

![Figure 6. Full-sphere response for a target at az = 60, el = -20 deg: cone (lines), mirror (square) and lattice aliasing (A4).](../results/sim01/RUNID/figures/fig05_sphere_ambiguity_maps.png)
*Figure 6. Full-sphere response for a target at az = 60, el = -20 deg: cone (lines), mirror (square) and lattice aliasing (A4).*

![Figure 7. Vertical-plane beampatterns through the same target; dotted line marks the up/down mirror elevation.](../results/sim01/RUNID/figures/fig03_vertical_beampatterns.png)
*Figure 7. Vertical-plane beampatterns through the same target; dotted line marks the up/down mirror elevation.*

Median horizontal half-power width over horizon steering (deg):

| ID | 500 Hz | 1 kHz | 2.5 kHz | 5 kHz | 10 kHz |
|---|---|---|---|---|---|
| A1 | undefined | 231 | 116 | 40.5 | 18.8 |
| A2 | 231 | 139 | 40.5 | 18.8 | 9.3 |
| A3 | undefined | 157 | 58.8 | 29.1 | 14.5 |
| A4 | 135 | 63.9 | 25.2 | 12.6 | 6.3 |

* Widths above 180 deg for the lines are not errors. The half-power region on the horizon merges
  the target with its left/right mirror, so the 0 dB mirror lobe makes "width" a measure of the
  merged lobe pair. The step changes in `fig06` (b) occur where the mainlobe separates from the
  mirror lobe for successive steering directions.
* The horizontal-plane width falls as lambda/aperture. A4 is narrowest because it has the largest
  aperture, which is the same property that makes it alias earliest.
* Vertical resolution of the horizontal square is poor near the horizon. The median HPBW_v for
  horizon steering is 137 deg at 2 kHz and 83 deg at 5 kHz, because cos(el) is stationary at el = 0.

### 4.4 Ambiguity and aliasing

* **A1, A2 (cone).** For every horizon steering direction except exact endfire (where the mirror
  coincides with the target), and at every one of the 121 frequencies, the horizontal cut carries a
  lobe outside the mainlobe at 0 dB to within 2e-15 dB: the mirror at -az. On the depressed ring the
  vertical cut shows the 0 dB up/down image. A line array alone cannot provide unambiguous
  horizontal bearing or any 3-D direction. Aliasing: -3 dB lobes from 4,432 Hz (A1) and 2,216 Hz (A2)
  for near-endfire steering; at broadside the A1 -3 dB ambiguity onset is 8,865 Hz (line-array
  sensitivity table).
* **A3 (mirror).** Azimuth is geometrically unambiguous. For every source 30 deg below the horizon,
  at every frequency, the vertical cut has a 0 dB lobe (to within 2e-15 dB) at the mirror elevation
  +30 deg. Aliasing from 1,877 Hz (-3 dB) and
  2,500 Hz (0 dB); the number of -3 dB ambiguity lobes reaches 20 at 10 kHz (horizon ring maximum).
* **A4 (none, but lattice aliasing).** From 900 Hz to 10 kHz the worst observable ambiguity lobe over
  horizon steering is within 0.08 dB of the mainlobe at every analysed frequency. The maximum number of lobes at or above -3 dB is 3 at 1 kHz, 12 at 2 kHz,
  71 at 5 kHz and 276 at 10 kHz. The exact grating lobes follow from the reciprocal lattice of A4's
  three baselines (onset 857 Hz). This holds for *any* 4-element non-coplanar layout: irregularity
  changes where the lattice points lie, not whether they exist (tests draw random layouts and find
  |W| = 1 exactly). Aperiodic layouts suppress grating lobes only when N is well above rank + 1;
  a generic 5-element volumetric layout has none (test).
* **A0.** Omnidirectional at every frequency (HPSF = 1.0, all pattern metrics undefined).

Narrowband caveat: for broadband signals, grating lobes move with frequency while the mainlobe does
not, so broadband or TDOA processing can suppress ambiguity that narrowband analysis declares fatal.
This matters most for A4-like distributed layouts and is not evaluated in SIM-01.

### 4.5 Sensitivity to element count, spacing and aperture

`fig08_line_array_sensitivity.png`, `fig09_aperture_scaling.png`;
`tables/sensitivity_*.md`.

![Figure 8. Line-array sensitivity to element count and spacing.](../results/sim01/RUNID/figures/fig08_line_array_sensitivity.png)
*Figure 8. Line-array sensitivity to element count and spacing.*

![Figure 9. Threshold scaling with aperture for the A4 layout and the 2x2 square.](../results/sim01/RUNID/figures/fig09_aperture_scaling.png)
*Figure 9. Threshold scaling with aperture for the A4 layout and the 2x2 square.*

* **Aperture sets resolution; spacing sets aliasing; element count sets the ratio between them.**
  For lines, broadside HPBW collapses onto a single curve of aperture/lambda for each N (`fig08` (a)).
  The broadside first-sidelobe onset is c/(Nd) and the worst-case grating onset c/(2d), so the
  conventional band ratio is N/2 for worst-case steering: 2 for N = 4, 8 for N = 16.
* **Scaling a fixed shape moves every threshold as 1/size and leaves their ratios unchanged.**
  A4 scaled from 0.27 m to 4.28 m maximum dimension moves f_SL from SQ_A4_FSL_LO to SQ_A4_FSL_HI and the -3 dB ambiguity onset
  from SQ_A4_AMB_LO to SQ_A4_AMB_HI. The square with side 0.15, 0.30, 0.60 m has f_SL 2,680 / 1,340 / 670 Hz and
  -3 dB onset 3,754 / 1,877 / 938 Hz (30 deg steering step). No choice of scale widens a 4-element
  array's conventional band. Only more elements do.
* **Orientation decides which angle is lost** (`tables/sensitivity_orientation.md`). A vertical line
  (A1-V) has no azimuth discrimination at any frequency (HPBW_h undefined for every horizon
  steering at 1, 2 and 5 kHz). A square in the vertical x-z plane (A3-V) trades the up/down mirror
  for a 0 dB port/starboard mirror on the horizon.

### 4.6 Robustness to sound speed

`fig10_sound_speed_robustness.png`; `tables/robustness_sound_speed*.md`.

![Figure 10. Sound-speed scaling of thresholds and peak bias under sound-speed mismatch.](../results/sim01/RUNID/figures/fig10_sound_speed_robustness.png)
*Figure 10. Sound-speed scaling of thresholds and peak bias under sound-speed mismatch.*

* **Thresholds scale exactly with c**, as the model depends only on f/c. Over 1450 to 1550 m/s every
  threshold moves by -3.3 % to +3.3 % (largest deviation from the exact ratio: SSCHECK). The ordering
  of candidates on every threshold is unchanged across the range.
* **Mismatch between the true and assumed sound speed biases the peak deterministically**, matching
  the closed form p_est = (c_assumed / c_true) p_true in the observable space:
    * Lines: zero bias at broadside and growing toward endfire. For c_true = 1550 m/s with 1500 assumed,
      the bias is +1.06 deg at 60 deg from the axis, +3.06 deg at 30 deg and +14.59 deg at endfire.
      For c_true = 1450, sources within 14.8 deg of endfire are reported at endfire.
    * Horizontal square: azimuth is unbiased (0.00 deg). Elevation is strongly biased near the horizon:
      a horizon source is reported at |el| = 14.59 deg when c_true = 1550, and a source at -10 deg is
      reported at the horizon when c_true = 1450.
    * A4: direction error at most 0.36 deg over the cases evaluated.

Elevation from a horizontal planar array therefore needs in-situ sound speed: a cheap sensor, but a
real requirement.

---

## 5. Engineering assessment

### 5.1 How much useful spatial performance is gained by adding array elements?

* **SNR gain is small and logarithmic.** Ideal gain against uncorrelated noise is 10 log10 N
  (6.02 dB at N = 4). Against diffuse noise, compact 4-element arrays deliver 0.2 to 1.7 dB below
  1 kHz (band medians) and approach 6 dB only above roughly 2 to 3 kHz. Confidence: high (model);
  realized gain lower.
* **Going from 1 to 4 elements buys direction information in a band, not everywhere.** A0 provides
  none at any frequency. The 4-element candidates provide half-power discrimination only above
  270 to 667 Hz (median steering) and unambiguous conventional beamforming only in 1.2:1 to 3:1
  frequency bands (Section 4.1). High.
* **More elements at fixed spacing** extend the aperture and lower f_HP and f_SL in proportion,
  without moving the aliasing onset. **More elements at fixed aperture** raise the aliasing onset
  without improving resolution. **Every doubling of N doubles the unambiguous band ratio** (N/2 for
  lines) and adds 3 dB of WNG. High.

### 5.2 Which geometries show meaningful advantages in which frequency regions?

| Band | Observations (horizon targets) |
|---|---|
| 100 to ~250 Hz | None of the candidates discriminates direction (every f_HP is above the band; A4's best is 253 Hz). Only A0-level detection capability exists. |
| ~250 to ~700 Hz | A4 and A2 are directional. A4 is unambiguous in 3-D only up to ~600 Hz (623 Hz earliest horizon onset); A2's beam is broad (HPBW_h 231 deg at 500 Hz) and conical. |
| ~0.7 to ~2.2 kHz | A2 is the only candidate in its conventional regime throughout (conical ambiguity remains). A3 is conventional only from 1.31 to 1.88 kHz but is the only candidate with unambiguous full-circle azimuth there. |
| ~1.5 to ~4.4 kHz | A1 is conventional (conical). A2, A3 and A4 are aliased for some steering. |
| > 4.4 kHz | Every multichannel candidate has -3 dB ambiguity lobes for some horizon steering. A1 stays clean only for steering away from endfire (until 8.9 kHz at broadside). |

No candidate covers more than a factor of about 3 in frequency in the conventional regime, and the
candidates that remove left/right ambiguity (A3, A4) cover factors of 1.44 and 1.18. Confidence:
high for the stated model and criteria (-3 dB).

### 5.3 Where do compact arrays fundamentally lose directional discrimination?

Below f_HP, where the aperture is less than about 0.25 to 0.42 wavelengths for a broadside line
(half that at endfire). For the candidates (best to worst horizon steering): A1 below 569 to
1,139 Hz, A3 below 625 to 644 Hz, A2 below 285 to 569 Hz, A4 below 253 to 298 Hz. Between f_HP
and f_SL (aperture below about one wavelength) the beam is wider than the visible region and has no
nulls, so it can neither reject a strong interferer nor resolve two sources. These limits are
fundamental to conventional processing of pressure sensors; they do not depend on electronics. The
only ways around them change the physics or the processing: larger aperture, superdirective or
adaptive weighting (which trades away white-noise gain and robustness to calibration error), or
sensors with intrinsic directivity such as acoustic vector sensors. None was evaluated here.
Confidence: high.

### 5.4 Which configurations have serious ambiguity or aliasing problems?

* **A4: severe.** Exact 0 dB grating lobes from 857 Hz (worst case) and -3 dB lobes from 596 Hz;
  hundreds of near-0 dB lobes at 10 kHz. Narrowband DAS on A4 is unusable for bearing above about
  0.6 kHz. This is generic to 4-element volumetric arrays, not a consequence of these coordinates.
* **A1, A2: severe geometric ambiguity** (cone: total left/right ambiguity for horizontal targets) at
  all frequencies, plus aliasing above 4.4 kHz (A1) and 2.2 kHz (A2) for near-endfire steering
  (A1 at broadside: -3 dB ambiguity onset 8,865 Hz).
* **A3: mirror ambiguity** at all frequencies (benign only if all targets are known to be on one side
  of the plane; surface-reflected arrivals come from the mirror side) and aliasing from 1.9 kHz.
* **A0: no direction at all.**

Confidence: high.

### 5.5 Which conclusions are robust to reasonable changes in sound speed and geometry?

| Conclusion | Robust to c (1450 to 1550 m/s) | Robust to scale | Robust to orientation / A4 coordinates |
|---|---|---|---|
| Geometric ambiguity class of each candidate | Yes (independent of c) | Yes | Class yes; *which* angle is lost depends on orientation |
| Existence of exact grating lobes for 4-element arrays | Yes | Yes | Yes for any 4-element layout (mathematical) |
| Conventional band ratio (f_amb / f_SL) | Yes (exactly invariant) | Yes (invariant) | Depends on shape, not on size |
| Absolute threshold frequencies | Shift by +-3.3 % | No: scale as 1/size | A4 values specific to placeholder coordinates |
| Ordering of candidates on each threshold | Yes (verified) | Only for these sizes | Not established for other layouts |
| DI fine structure (dips and peaks) | Shifts with f/c | Shifts with size | Not robust; do not use for selection |
| Elevation estimates from horizontal planar arrays | **No**: 3 % sound-speed error gives up to ~15 deg near the horizon | | |

### 5.6 Which additional physical parameters must be modeled before selecting a preliminary architecture?

In priority order:

1. **Mission requirements:** frequency band(s) of interest, signal type (tonal versus broadband),
   required bearing accuracy and coverage (azimuth only versus 3-D), acceptable ambiguity. Without a
   band, aperture cannot be chosen, because every SIM-01 threshold scales with size.
2. **Processing model:** broadband and TDOA (cross-correlation) direction finding, bandwidth and
   integration time. These determine whether narrowband aliasing (A4, and A1 to A3 above their
   onsets) is fatal or manageable.
3. **Noise field:** sensor and preamplifier self-noise against ambient levels (low-frequency
   ambient often dominates, so 6 dB of WNG may be unusable); ambient directionality (surface and
   shipping noise); flow noise at host speeds; host machinery and propeller noise and its spatial
   coherence across the array. Real array gain is AG with these coherence matrices, not DI.
4. **Host installation:** available mounting area and orientation per host class, baffling and
   shadowing by the hull, element directivity, scattering from nearby structure, and the near-field
   range for large apertures (Fraunhofer distance 15 m for A4 at 10 kHz).
5. **Calibration and synchronization:** gain and phase matching, position knowledge (phase error k
   times position error), and for distributed modules clock synchronization (a timing error dt is a
   phase error 2 pi f dt). These set the achievable sidelobe floor and null depth.
6. **Propagation and boundaries:** surface image arrivals (which arrive from the up/down mirror
   direction of a horizontal plane), multipath and refraction; in-situ sound speed for elevation
   (Section 4.6).
7. **Alternatives the candidate set omits:** acoustic vector sensors (directional from a single
   point, with an ideal first-order DI limit of 10 log10 4 = 6.02 dB that does not depend on
   aperture); planar or volumetric arrays with N > 4 (for example 6 to 8 elements on a circle);
   superdirective processing with explicit WNG constraints.
8. **Cost and complexity per channel and per module**, needed for a real Pareto analysis. SIM-01
   uses channel count and maximum dimension only as proxies.

---

## 6. Comparative results and Pareto analysis

`tables/comparison.md`, `tables/pareto.md`, `tables/pareto_leave_one_out.md`.

COMPARISON_TABLE

**Pareto dominance** (attributes evaluated in SIM-01 only; cost not evaluated; attribute lists in
the configuration):

PARETO_SUMMARY

Interpretation: on the attributes defined for every candidate (channels, maximum dimension,
observable dimensions, DI and HPSF band medians) A3 is at least as good as A1 everywhere. A1 survives
only when the worst-case aliasing onset is included (4.43 kHz versus 1.88 kHz for A3). A0 is never
dominated because it has the fewest channels and no size, which says nothing about its usefulness for
bearing. The absence of further dominance reflects real trade-offs: aperture versus aliasing, and
geometric observability versus usable band.

---

## 7. Candidates that warrant further simulation

These recommendations cover what to simulate next. They are not a design selection.

1. **A0 (single hydrophone)**: keep as the detection-only, lowest-cost reference against which every
   multichannel option must justify its channels.
2. **The line family (A1/A2) as one candidate parameterized by spacing**: keep only if the
   requirement tolerates left/right ambiguity, or if host motion or a second orthogonal line can
   resolve it. Treat spacing as the band-selection parameter.
3. **The planar family (A3 class)**: keep for full-azimuth bearing, but the 2x2 configuration is too
   sparse (1.44:1 conventional band). Add planar candidates with more elements (for example uniform
   circular arrays of 6 to 8 elements, or a 3x3 grid) at the same footprint.
4. **The distributed/volumetric family (A4 class)**: keep only together with broadband/TDOA processing
   and a synchronization model. With narrowband DAS it fails above about 0.6 kHz at this size. Replace
   the placeholder coordinates with surveyed host positions.
5. **Add acoustic vector sensors** as a candidate class before architecture selection, because they
   attack the low-frequency aperture limit that dominates every pressure-array result here.

Insufficient evidence: SIM-01 cannot rank these families without the mission band, the processing
approach and the noise environment (Section 5.6).

---

## 8. Limitations and unresolved questions

* **Idealization:** no noise model beyond the isotropic and white references, perfect calibration,
  point omnidirectional elements, free field. Real sidelobe floors, null depths and gains will be
  worse; the size of that loss is unknown until SIM-02 adds error and noise models.
* **Narrowband only.** The aliasing conclusions are conservative for broadband processing.
* **Metric thresholds** (-3 dB half power, -1/-3 dB ambiguity) are conventions. A detection-oriented
  requirement may need stricter ambiguity levels (-6 or -10 dB), which would narrow every conventional
  band reported here.
* **Steering statistics** use horizon and 30 deg-depressed rings. Worst-case-over-all-steering
  quantities are reported separately and are independent of this choice.
* **A4 is a placeholder.** Its generic conclusion (exact grating lobes for N = 4) is robust; its
  specific thresholds are not.
* **Open questions for the program:** mission band and signal types; whether bearing must be
  unambiguous in full azimuth or 3-D; whether hosts can turn to resolve ambiguity; acceptable
  per-channel cost; achievable inter-module timing synchronization for distributed installations.

---

## 9. Reproducibility and provenance

* `make sim01` runs the verification suite and then the experiment into a new directory
  `results/sim01/<run_id>/`. Runs refuse a dirty working tree and never overwrite.
* `record.json` in the run directory lists the resolved configuration and its hash, git commit,
  Python, NumPy and Matplotlib versions, platform, timings, self-checks and the SHA-256 of every
  output file. Pinned dependencies: `requirements.lock`.
* `results/sim01/RUN_INDEX.csv` lists every run. `results/sim01/ERRATA.md` records known problems
  in historical runs.
* Cross-run consistency: CROSSRUN
