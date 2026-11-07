# PCK-SIM-001 / SIM-01 Technical Plan

Array Geometry and Idealized Acoustic Performance

Status: plan of record for the first increment. Written before implementation; deviations are
recorded in `docs/adr/` and in the final report.

## 1. Repository inspection

The `picket-sim` repository was empty at the start of SIM-01 (no commits, no source, no CI, no
configuration). There is therefore no reusable infrastructure and nothing from production
software or Fathom in this repository. Decision (ADR-0001): this repository *is* the isolated
experimental simulation package. It contains no production code, imports nothing from Fathom,
and must not be imported by production software.

## 2. Software architecture

Python package `picket_sim` (src layout). Each module has one responsibility; downstream code
depends only on the interfaces of upstream modules.

| Module | Responsibility |
|---|---|
| `conventions` | Coordinate frame, azimuth/elevation to unit vector, great-circle cuts, angle utilities. The only place angles are converted. |
| `geometry` | `ArrayGeometry`: arbitrary 3-D sensor coordinates (metres), factories for single, linear, rectangular and arbitrary arrays, rigid transforms, and the *observability analysis* (rank of the sensor-difference span, which determines geometric ambiguity). |
| `acoustics` | Wavelength, wavenumber, arrival-time offsets, plane-wave steering vectors (`PlaneWaveManifold`). The manifold object is the extension point for element directivity, near field, and propagation models. |
| `beamforming` | Conventional delay-and-sum (DAS) weights, array response, normalized power pattern, dB conversion. |
| `noise` | Noise coherence models (spatially white; spherically isotropic) and array gain, directivity index (DI), white-noise gain (WNG). Extension point for sensor and ambient noise models. |
| `grids` | Gauss-Legendre sphere quadrature grid, 1-D reduced grids, great-circle cut grids, frequency grids. |
| `metrics` | Beamwidths on great-circle cuts, half-power sphere fraction, peak sidelobe level in the observable (reduced) space, local-maximum detection and refinement, worst-case aliasing onset in wavevector space, regime thresholds. |
| `mismatch` | Sound-speed mismatch (assumed vs true) peak-direction bias. |
| `experiments.sim01` | Orchestration of the SIM-01 study from a YAML configuration. |
| `plotting` | All figures; consistent axes, units, normalization and labels. No physics. |
| `records` | Immutable run directories, provenance (git commit, versions, config hash, output hashes), run index. |
| `config` | Loading and validation of machine-readable configurations (unit-suffixed keys). |
| `cli` | `python -m picket_sim run <config>`. |

## 3. Governing equations (narrowband, far field, homogeneous medium)

* Wavelength `lambda = c / f`, wavenumber `k = 2*pi*f / c`.
* Direction of arrival (DOA) unit vector `u` points from the array **toward the source**.
* Time convention `exp(+j*omega*t)`. A plane wave from direction `u` reaches the element at
  `r_n` at time `tau_n = -(u . r_n) / c` relative to the origin (elements nearer the source,
  larger `u . r_n`, receive the wavefront earlier).
* Steering vector: `a_n(u, f) = exp(+j * k * u . r_n)`.
* DAS weights steered to `u0`: `w = a(u0) / N`, so `w^H a(u0) = 1` (distortionless).
* Normalized power pattern: `P(u; u0) = |w^H a(u)|^2 / |w^H a(u0)|^2`, with `0 <= P <= 1` for
  uniform DAS and `P(u0; u0) = 1` exactly.
* Equivalent wavevector form: `P = |W(k (u - u0))|^2` with array factor
  `W(q) = (1/N) * sum_n exp(j q . r_n)`. Grating lobes are points `q != 0` with `|W(q)| = 1`
  outside the geometric-ambiguity null space.
* Array gain against a noise field with spatial coherence `Gamma`:
  `AG = |w^H a0|^2 / (w^H Gamma w)`. Spatially white noise (`Gamma = I`) gives the white-noise
  gain `WNG = N` for DAS. Spherically isotropic noise gives `Gamma_mn = sin(k r_mn) / (k r_mn)`
  and the directivity index `DI = 10 log10(AG)`, equivalently `DI = 10 log10(4*pi / integral P dOmega)`.

## 4. Coordinate and angle conventions

Right-handed array frame, metres, `z` up. Azimuth `az` is measured in the `x-y` plane from `+x`
toward `+y` (counter-clockwise viewed from above); elevation `el` is positive above the `x-y`
plane. `u = [cos(el) cos(az), cos(el) sin(az), sin(el)]`. API arguments carry their unit in the
name (`_deg`, `_rad`, `_hz`, `_m`, `_mps`, `_s`). Host-specific mappings (bow, starboard,
depression angle) are deferred to platform integration; `docs/conventions.md` gives the mapping
for one example host frame.

Default orientations (assumptions, configurable): linear arrays lie along `x`; the square array
lies in the horizontal `x-y` plane.

## 5. Geometric ambiguity

Because a common phase across all channels is unobservable, the beampattern depends on `u` only
through its projection onto the span `S` of the sensor difference vectors `r_n - r_m`. With
`r = rank(S)`:

| rank | Class | Exact ambiguity |
|---|---|---|
| 0 | omnidirectional | none of the direction is observable |
| 1 | conical | only the angle from the array axis is observable (cone of ambiguity: left/right and up/down for a horizontal line) |
| 2 | mirror | reflection through the array plane is unobservable (up/down for a horizontal plane) |
| 3 | none | full direction observable; frequency-dependent aliasing can still occur |

Sidelobe and aliasing metrics are computed in the *observable* (reduced) space so that geometric
ambiguity and aliasing are reported separately.

## 6. Inputs and outputs

Inputs: one YAML file per experiment (`configs/sim01/*.yaml`) with SI, unit-suffixed keys:
sound speed, frequency grid, steering sets, numerical grids, array definitions, sensitivity and
robustness studies, Pareto attributes.

Outputs: an immutable run directory `results/sim01/<run_id>/` containing `record.json`
(provenance), `tables/` (CSV and Markdown), `figures/` (PNG), and `summary.md`; plus an
append-only `results/sim01/RUN_INDEX.csv`.

## 7. Metrics (all for conventional DAS, per array, frequency and steering direction)

* `DI` (dB) against spherically isotropic noise, closed form; checked against sphere quadrature
  in every run.
* `WNG` (dB) = 10 log10 N (constant for uniform DAS).
* Half-power sphere fraction `HPSF`: fraction of all directions with `P >= 0.5`. Includes the
  mainlobe and every ambiguity. 1.0 means no half-power discrimination anywhere.
* Minimum of `P` over all directions (whether any direction is suppressed by 3 dB).
* `-3 dB` beamwidths on the horizontal and vertical great-circle cuts through the steering
  direction (undefined when the half-power region wraps the whole cut).
* Largest lobe outside the mainlobe on each cut (includes geometric ambiguity, e.g. the
  left/right mirror of a horizontal line array).
* Peak sidelobe level in the observable space (`PSL_obs`): excludes geometric ambiguity,
  undefined when no sidelobe exists in the visible region.
* Regime thresholds per steering: `f_HP` (first direction suppressed by 3 dB), `f_SL` (first
  sidelobe region appears, mainlobe no longer fills the visible region), `f_amb(L)` (first
  ambiguity lobe at or above level `L` in the observable space).
* Worst case over all steering directions: aliasing onset `f_alias(L)` from the array factor in
  wavevector space (`|q| <= 2k` is the realizable set).

Undefined metrics are stored as empty/NaN with a reason, never forced to a number.

## 8. Numerical methods

* Closed forms where they exist (steering vectors, DI, ULA patterns for tests).
* Sphere integrals by Gauss-Legendre quadrature in `sin(el)` times uniform azimuth (exact for
  band-limited integrands; adequacy checked by the DI closed-form/quadrature agreement).
* Local maxima by neighbourhood comparison on 1-D or sphere grids, refined by iterative local
  zoom. Thresholds by bracketing on the frequency grid followed by bisection.
* Grid resolution versus lobe width is recorded per row; rows below the adequacy limit are
  flagged.

## 9. Verification

Pytest suite (Step 5 of the handoff): analytic steering vectors (including an independent
spherical-wave far-field limit and a time-domain delay test), broadside/endfire behaviour,
closed-form ULA patterns, cone and mirror symmetries, aperture trends, aliasing at `c/(2d)`,
single-hydrophone non-directionality, DI quadrature versus closed form, units and configuration
validation, normalization, plotting data orientation, and bitwise reproducibility of tables.
Every experiment run also embeds self-checks (normalization, DI agreement) and refuses to finish
if they fail.

## 10. Dependencies

Python 3.11+, NumPy, Matplotlib, PyYAML, pytest. No SciPy (not required; avoids a large
dependency). Exact versions used for the canonical run are pinned in `requirements.lock` and
recorded in each run record.

## 11. Reproducibility

`make sim01` (or `python -m picket_sim run configs/sim01/sim01_baseline.yaml`) regenerates all
SIM-01 outputs into a new run directory. Existing run directories are never modified; the run
refuses to start on a dirty working tree unless `--allow-dirty` is given (and then records it).
No random numbers are used in SIM-01.

## 12. Known limitations (by design for this increment)

Narrowband single-frequency analysis; plane waves; homogeneous, lossless, unbounded medium;
isotropic point hydrophones with identical, perfectly known responses and positions; no
sensor/electronic noise, ambient noise directionality, self-noise, multipath, surface/bottom
boundaries, host structure, flow, element directivity or baffling; conventional DAS only (no
adaptive or superdirective processing); no broadband/TDOA processing; no detection or range
predictions. These are recorded in `docs/assumptions.md` and the report.
