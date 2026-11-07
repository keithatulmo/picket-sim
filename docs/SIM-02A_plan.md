# PCK-SIM-001 / SIM-02A Technical Implementation Plan

Sensor, noise and error modeling. Plan of record, written before implementation. Authority: SIM-01
technical review and SIM-02 authorization (ADR-0009). SIM-02B (broadband and task-level performance)
is out of scope until the SIM-02A numerical results are reviewed.

## 1. Objective and boundaries

Quantify how sensor self-noise, acquisition noise and dynamic range, spatially structured noise
(including host noise scenarios) and channel errors (gain, phase, position, timing) change the
idealized SIM-01 picture, for the retained and new candidate geometries, across the provisional
study bands of D01. Outputs are narrowband, per-frequency figures of merit with explicit statistical
uncertainty. They are not detection performance, detection range, or hardware requirements.

Not in SIM-02A: broadband beamforming, TDOA, detection experiments, false-alarm analysis, adaptive
beamforming, acoustic vector sensor modeling beyond a feasibility assessment, Fathom.

## 2. Parameter provenance (ADR-0010)

Every physical parameter carries `provenance` in {published, measured, assumed} and a mandatory
`source` (published: citation; measured: data reference; assumed: rationale). Loading fails if the
field is missing or inconsistent. Every report lists parameters grouped by provenance. In SIM-02A no
measured values exist; published values are limited to defined physical constants; all sensor,
ambient, host and error levels are assumed scenarios and are reported as such, never as
representative measurements.

## 3. Models and governing equations

Units: pressure spectral density in uPa^2/Hz (levels in dB re 1 uPa^2/Hz), voltage in V, sensitivity in
dB re 1 V/uPa, frequency in Hz, time in s.

### 3.1 Acquisition chain (input-referred to pressure)

* Hydrophone: sensitivity M (V/uPa), capacitance C, loss tangent tan d, temperature T. Thermal
  (Johnson) noise of the lossy capacitance: e_th^2 = 4 k T Re(Z), Z = 1 / (j w C (1 - j tan d)), so
  Re(Z) = tan d / (w C (1 + tan^2 d)).
* Preamplifier: voltage gain G; input voltage noise e_n (white, optional 1/f corner f_c:
  e_n^2 (1 + f_c / f)); input current noise i_n acting on |Z|.
* ADC: N_bits (or ENOB), full-scale peak voltage V_fs, sample rate f_s. Quantization noise
  PSD (one-sided) (Delta^2 / 12) / (f_s / 2), Delta = 2 V_fs / 2^N.
* Input-referred self-noise PSD:
  S_self(f) = [e_th^2 + e_n^2 (1 + f_c/f) + i_n^2 |Z|^2] / M^2 + S_q / (G^2 M^2).
* Clipping: p_clip = min(V_fs / (G M), V_pre_max / (G M)) (peak pressure).
* Dynamic range in a band B for a signal class with crest factor CF (peak / rms):
  max rms signal p_clip / CF; noise power integral of (S_self [+ S_ambient]) over B.
  Signal classes (D01): tonal (CF = sqrt 2), harmonic with K equal in-phase partials
  (CF = sqrt(2K)), broadband Gaussian (CF set by an assumed peak criterion), transient (assumed CF).
* Validity checks (fail visibly): f_s <= 2 f_max (Nyquist), non-physical parameters, any band edge
  above the hydrophone or acquisition bandwidth declared in the scenario.

### 3.2 Noise fields (spatial cross-spectral density)

R_ac(f) = sum_c S_c(f) Gamma_c(f), each Gamma_c Hermitian positive semidefinite with unit diagonal for
homogeneous fields:

| Component | Coherence | Check |
|---|---|---|
| Spatially white | I | trivial |
| Spherically isotropic | sin(k r)/(k r) | SIM-01 closed form; quadrature of uniform density |
| Horizontally (cylindrically) isotropic | J0(k r_h) | quadrature of a horizontal ring; tabulated J0 values |
| Directional density D(u) (surface-like, horizontal band, user-defined) | integral of D(u) a(u) a(u)^H dOmega / integral of D | reduces to the two above for uniform / ring densities |
| Short-correlation (flow-like) | exp(-r / L_c) | positive definite in 3-D (Matern, nu = 1/2) |
| Host point source (near field) | h h^H, h_n = (r_0 / |x_s - r_n|) exp(-j k |x_s - r_n|) | rank 1; level defined at the array reference point |
| Far-field interferer | a(u_i) a(u_i)^H | rank 1 |

Total input-referred covariance with channel errors (Section 3.3):
R = T D (R_ac + S_th I) D^H T^H + S_elec I, where D holds the per-channel complex sensitivity
error, T the timing phase exp(-j 2 pi f tau_n), S_th the hydrophone thermal noise and S_elec the
preamplifier and ADC noise (both referred with the nominal sensitivity). Every matrix is checked for
Hermitian symmetry and positive semidefiniteness (relative tolerance); violations raise. No clipping or
silent regularization.

### 3.3 Channel errors

Per channel n, independent: gain error 20 log10 g_n ~ N(0, sigma_g dB); phase error ~ N(0, sigma_phi);
position error delta_n ~ N(0, sigma_p^2 I_3); timing error tau_n ~ N(0, sigma_t^2). The beamformer
uses nominal positions and assumes no errors. The signal vector is
s = T D a(u_s; r + delta) sqrt(S_s).

Closed forms used for verification (uniform weights, i.i.d. Gaussian phase with total variance
sigma^2 = sigma_phi^2 + (k sigma_p)^2 + (2 pi f sigma_t)^2, log-normal gain):
E|B(u_s)|^2 = [N E g^2 + N (N - 1) (E g)^2 e^{-sigma^2}] / N^2, and at an ideal null
E|B|^2 = (E g^2 - (E g)^2 e^{-sigma^2}) / N.

### 3.4 Figures of merit

* Realized array gain relative to A0 (RAG): SNR at the DAS output divided by the SNR of a single
  identical channel at the array reference point in the same noise model. RAG(A0) = 0 dB by
  definition. Limits: white noise only gives 10 log10 N; isotropic noise without sensor noise gives
  the SIM-01 DI (regression check).
* Signal (mainlobe) loss from channel errors; sidelobe and ambiguity statistics on the horizontal
  cut (probability that a lobe outside the ideal mainlobe exceeds -3, -6, -10 dB); noise-free
  calibration-induced azimuth error (fine error and gross-error rate, including unresolved
  left/right selection for lines).
* Regime thresholds f_HP, f_SL, f_amb at -3, -6, -10 dB (D03), with median and guaranteed band
  definitions (ADR-0008), worst-case ambiguity onset, exact grating onset.

### 3.5 Monte Carlo statistics (ADR-0012)

Seeded, order-independent random streams (seed derived from the base seed and the case key).
Means with 95 % confidence intervals (normal approximation, n >= 200), quantiles with
distribution-free order-statistic intervals, proportions with Wilson intervals. Each reported
statistic carries its interval; rows whose relative interval half-width exceeds the configured
target are flagged.

## 4. Candidates (ADR-0013)

Retained references: A0 to A4 exactly as SIM-01 (regression). Linear family L4(d) with d in
{0.15, 0.30} m (A1, A2). Footprint classes by maximum dimension: compact C = 0.45 m, extended
E = 0.90 m. New planar candidates in the horizontal plane: 2x2 square, 6-element and 8-element uniform
circular arrays, each at C and E. Volumetric family: parametric envelopes (L, W, H) with the A4 element
pattern scaled into the box; the intermediate envelope equals A4 exactly; compact and distributed
envelopes (including a shallow variant representing a draft-limited mounting) are labeled assumed.

## 5. Bands and grids

Analysis grid 20 Hz to 20 kHz, 30 points per decade. Band summaries for D01: B1 20-200 Hz,
B2 200 Hz-2 kHz, B3 2-10 kHz, B4 10-20 kHz (exploratory; contingent on acquisition assumptions,
checked against the sensor scenario's sample rate and declared bandwidth). Steering: horizon ring,
15 deg (gain, thresholds); Monte Carlo on a subset.

## 6. Analyses and outputs

1. Acquisition chain: self-noise spectra, ADC versus analog noise, clip level, per-band dynamic
   range for each signal class, per sensor scenario.
2. Realized array gain versus frequency for every candidate in white, isotropic, horizontal,
   surface-like and flow-like fields, swept over the self-noise-to-ambient ratio eta.
3. Host-noise scenarios: RAG versus target azimuth with near-field and far-field host sources at
   host-to-ambient ratios of 0, 10, 20 dB.
4. Channel-error Monte Carlo: scenario sets and one-at-a-time sweeps; verification against the
   closed forms.
5. Ambiguity-criterion sensitivity: thresholds at -3, -6, -10 dB; guaranteed and median bands.
6. Pareto tolerance sensitivity (D06) on the SIM-01 and SIM-02A attribute sets; no elimination.

All under an immutable run directory `results/sim02a/<run_id>/` with the SIM-01 record format.

## 7. Verification

Automated tests for every model: closed-form and independently computed comparisons (Section 3),
positive semidefiniteness and normalization of every coherence model, PSD limits of RAG,
Monte Carlo means against closed forms within their confidence intervals, provenance enforcement,
invalid-configuration rejection, regression against SIM-01 (DI, thresholds at -3 dB, A4 geometry),
end-to-end reproducibility. The pipeline embeds self-checks and fails on violation.

## 8. Dependencies

Unchanged (NumPy, Matplotlib, PyYAML, pytest). Bessel J0 is computed by quadrature of its integral
representation (no SciPy), verified against tabulated values.

## 9. Deliverables

Plan (this document); source, configurations and tests; sensor/noise/error model documentation
(`docs/sensor_noise_error_models.md`); comparative results; sensitivity and uncertainty analysis;
updated assumption and limitation register; reproducible engineering report; recommendations for
SIM-02B; acoustic vector sensor feasibility assessment (`docs/avs_feasibility.md`).
