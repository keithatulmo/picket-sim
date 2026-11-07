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
