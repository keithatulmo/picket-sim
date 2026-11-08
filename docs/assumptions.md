# Assumption and limitation register (SIM-01)

Status column: **Modeled** = represented in the numerics; **Assumed** = idealization adopted for
SIM-01; **Excluded** = explicitly out of scope by the handoff; **Placeholder** = a value with no
engineering basis yet.

| ID | Item | Status | Effect on conclusions |
|---|---|---|---|
| AS-01 | Narrowband, single-frequency plane waves | Assumed | Aliasing ambiguity is overstated for broadband processing; TDOA/broadband performance unknown. |
| AS-02 | Far-field sources (plane waves) | Assumed | Valid at ranges well beyond the Fraunhofer distance 2 L^2 / lambda (at 10 kHz: about 15 m for A4, 2.7 m for A1; proportionally less at lower frequency). Near-field sources are not represented. |
| AS-03 | Homogeneous, lossless, unbounded medium, c = 1500 m/s nominal | Assumed | No refraction, multipath, surface/bottom interference. Thresholds scale exactly with c. |
| AS-04 | Ideal omnidirectional point hydrophones, identical gain/phase, perfectly known positions | Assumed | Real sidelobe floors, nulls and DI will be degraded by calibration and position errors. |
| AS-05 | Conventional uniformly weighted delay-and-sum | Assumed | Adaptive or superdirective processing would change compact-array low-frequency DI (at the cost of white-noise gain and robustness). |
| AS-06 | Spherically isotropic noise for DI; spatially white noise for WNG | Assumed | Ocean ambient noise is anisotropic; platform and flow noise are neither. DI is a geometry figure of merit, not a gain prediction. |
| AS-07 | Linear arrays along x, square array horizontal (x-y plane) | Assumed | Orientation decides which angle is ambiguous (see orientation sensitivity table). |
| AS-08 | A4 coordinates | Placeholder | Notional irregular non-coplanar layout with ~0.9-1.1 m baselines; A4 results are specific to these coordinates. |
| AS-09 | Steering sets: horizon ring (el = 0) and depressed ring (el = -30 deg), 15 deg azimuth step | Assumed | Statistics over steering depend on this choice; worst-case-over-all-steering aliasing is reported separately. |
| AS-10 | Half-power (-3 dB) and ambiguity levels (-1, -3 dB) | Assumed | Conventional thresholds; a detection-oriented requirement may need a stricter ambiguity level (e.g. -6 or -10 dB). |
| EX-01 | BELLHOP / ocean propagation | Excluded | |
| EX-02 | Vessel self-noise, flow noise, structural acoustics, CFD, FEA | Excluded | |
| EX-03 | Machine learning, Fathom integration | Excluded | |
| EX-04 | Detection-range predictions | Excluded | No range or detection claims are made. |

Numerical approximations (all checked):

| ID | Approximation | Check |
|---|---|---|
| NA-01 | Sphere integrals by Gauss-Legendre (181 x 360) quadrature | DI quadrature vs closed form, every run (tolerance 0.01 dB; typical agreement 1e-13 dB). |
| NA-02 | Half-power sphere fraction of an indicator function on a grid | Rank-1 exact 1-D value vs sphere grid recorded every run. |
| NA-03 | Local maxima on sampled grids, refined by local zoom | Brute-force comparisons in tests; `resolution_ok` flag per row. |
| NA-04 | Thresholds by grid scan + bisection | Analytic thresholds (`c/(N d)`, `c/(8 d)`, `c/(2 d)`) reproduced in tests. |

## SIM-02A additions

| ID | Item | Status | Effect on conclusions |
|---|---|---|---|
| AS-11 | Sensor scenarios S1 to S3 (element sensitivity, capacitance, loss tangent, preamplifier noise and gain, ADC bits, full scale, sample rate, declared bandwidth) | Assumed (illustrative) | Absolute self-noise, dynamic range and acquirability of B4 are scenario results, not product properties. Gain results are parameterized by eta to stay independent of them. |
| AS-12 | Ambient scenarios: power laws 45/60/75 dB re 1 uPa^2/Hz at 1 kHz, -17 dB/decade | Assumed (illustrative, not fitted to data) | Only the acquisition analysis and the eta bridge use absolute ambient levels. Published ambient models are to be introduced with provenance when sensing applications are defined. |
| AS-13 | Ambient spatial structure: white, spherical, horizontal, upward-weighted, horizontal-band, exponential (L = 0.1 m) | WHITE/ISO/HOR modeled as limiting cases; other shapes assumed | Realized gain depends strongly on the field; no field is claimed representative of a Picket environment. |
| AS-14 | Host noise: generic point sources at 3 m and 15 m (near field) and a far-field source aft, host-to-ambient ratios 0/10/20 dB | Assumed (generic; no vessel geometry) | Shows how geometry and frequency govern host rejection with DAS; not a prediction for any host. |
| AS-15 | Channel errors independent, zero-mean Gaussian; scenarios E1 to E4 and one-at-a-time sweeps | Assumed | Correlated errors (common-mode drift, systematic position bias) are not modeled. |
| AS-16 | Sensor-noise split between thermal (scaled by channel errors) and electronic (not scaled): 50/50 | Assumed | Second-order effect on gain-with-errors results. |
| AS-17 | Signal-class crest factors: tonal and harmonic analytic; broadband 12.04 dB (4-sigma criterion); transient 25 dB | Tonal and harmonic analytic; others assumed | Sets clipping headroom only. |
| AS-18 | Noise-free calibration-induced bearing statistics | Modeled (noise-free) | Bearing errors caused by additive noise are SIM-02B. |
| AS-19 | Volumetric envelopes V-C, V-D, V-DS | Assumed (parametric; not host surveys; V-DS represents a draft-limited mounting) | Results are reported against envelope dimensions; A4 (envelope 1.00 x 0.85 x 0.75 m) remains the regression case. |

## SIM-02B.1 additions

| ID | Item | Status | Effect on conclusions |
|---|---|---|---|
| AS-20 | Ambient level and shape: Coates/Wenz-type formulas (Stojanovic 2007, Eq. 6) with shipping s = 0.5 and wind w = 5 m/s | Equations published (secondary); s and w assumed; units read as dB re 1 uPa^2/Hz | Detection results are expressed as input SNR relative to the total element noise, so the absolute level matters only through the ambient-to-self-noise ratio and the spectral shape inside each band. |
| AS-21 | Spatial coherence: spherically isotropic (N-AMB, N-SENS), exponential with L = 0.1 m (N-FLOW), white (mismatch assumption only) | Assumed; never inferred from single-channel spectra (ADR-0017) | Array gain and beam-search false-alarm behaviour are governed by coherence; this is the dominant unvalidated assumption. |
| AS-22 | Sensor self-noise: SIM-02A S1 chain (N-AMB, N-FLOW); self-noise 20 dB above ambient (N-SENS) | Assumed | Sets whether noise is ambient- or sensor-limited. |
| AS-23 | Noise statistics: stationary circular Gaussian within each window; windows independent | Assumed (ADR-0016) | Non-Gaussian, impulsive or non-stationary noise (biologics, transients, flow bursts) would change false-alarm behaviour, especially at Pfa 1e-3 and 1e-4. |
| AS-24 | Host noise | Not modeled in SIM-02B.1 | Host-noise directionality could favour arrays (nulling) or hurt A0; deferred to later increments with measured host data. |
| AS-25 | Channel calibration and synchronization errors | Not modeled in SIM-02B.1 (SIM-02B.2) | Beam-known and beam-search results are upper bounds with respect to calibration and timing. |
| AS-26 | Sources: single plane wave on the horizon, azimuth uniform per trial; no propagation, multipath or Doppler | Assumed | No detection range is implied; elevated or multipath arrivals are not studied. |
| AS-27 | Signal parameters: tone frequency uniform in band; four equal-SNR harmonics; flat-spectrum broadband source over the analysis band; LFM chirps (B1 50 to 150 Hz, 80 ms; B2 0.5 to 1.5 kHz, 50 ms; B3 3 to 8 kHz, 50 ms; Tukey tapers) | Assumed signal-class definitions | Results apply to these classes; other spectra or durations change the numbers. |
| AS-28 | Detectors: conventional, fixed before experimentation (tonal maximum, harmonic sum, whitened energy, whitened matched filter); noise PSD and coherence assumed known (clairvoyant normalization) except in mismatch tests | Assumed processing | Practical detectors must estimate noise; the mismatch tests bound the consequences of getting it wrong. |
| AS-29 | Trial counts per band and window (calibration, evaluation, positive) | Chosen for a run of about 75 minutes | Sets interval widths; thresholds at Pfa 1e-3 use exact or bound methods where the calibration set is too small (ADR-0015). |
