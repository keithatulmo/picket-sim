# Sensor, noise and error models (SIM-02A)

Reference for the models implemented in `sensor.py`, `noisefields.py`, `errors.py`, `stats.py` and
`rag.py`. Decisions: ADR-0010 (provenance), ADR-0011 (noise and acquisition), ADR-0012 (errors and
Monte Carlo). Every equation below has an automated test (Section 6).

## 1. Units and provenance

Pressure spectral densities are one-sided, in uPa^2/Hz; levels in dB re 1 uPa^2/Hz. Hydrophone
sensitivity is in dB re 1 V/uPa. Every configured physical value is a record
`{value, provenance, source}` with provenance `published`, `measured` or `assumed` (ADR-0010). In
SIM-02A all sensor, ambient, host and error levels are **assumed** and illustrative; the only
published value is the SI-defined Boltzmann constant. The run writes
`tables/parameters_by_provenance.csv`.

## 2. Acquisition chain (`sensor.py`)

| Element | Model | Noise referred to pressure (uPa^2/Hz) |
|---|---|---|
| Hydrophone element | Capacitance C with dielectric loss tan d: Z = 1 / (j w C (1 - j tan d)) | Thermal: 4 k T Re(Z) / M^2, Re(Z) = tan d / (w C (1 + tan^2 d)) |
| Preamplifier | Voltage gain G; input voltage noise e_n with 1/f corner f_c; input current noise i_n | [e_n^2 (1 + f_c / f) + i_n^2 |Z|^2] / M^2 |
| ADC | N bits (ideal quantization), full scale +-V_fs, sample rate f_s | (Delta^2 / 12) / (f_s / 2) / (G M)^2, Delta = 2 V_fs / 2^N |

M is the element (open-circuit) sensitivity in V/uPa. Using the element sensitivity both to refer the
thermal noise and to define the signal keeps the two consistent; a sensitivity that includes an
integral preamplifier must not be combined with the bare element's thermal noise.

* Clipping: peak pressure p_clip = min(V_fs, V_pre,max) / (G M).
* Dynamic range for a signal class with crest factor CF over band B:
  DR = 20 log10(p_clip) - CF - 10 log10(integral over B of the noise PSD).
* Crest factors: tonal sqrt(2) (3.01 dB), K equal in-phase harmonics sqrt(2K), broadband Gaussian and
  transient classes from assumed peak criteria.
* Self-noise to ambient ratio: eta(f) = S_self(f) / S_ambient(f). It connects the absolute acquisition
  scenarios to the gain results, which are parameterized by eta.

Validity checks (raise `ParamError`): declared bandwidth at or above Nyquist; analysis band outside
the declared bandwidth (reported as "not acquirable" for the contingent band B4, never extrapolated);
values outside unit-guard ranges.

## 3. Noise fields (`noisefields.py`)

Ambient spatial structure is a unit-power field: R_ac = sum_c fraction_c Gamma_c with unit diagonal.

| Component | Gamma_mn | Notes |
|---|---|---|
| white | delta_mn | spatially uncorrelated |
| spherical | sin(k r)/(k r) | 3-D isotropic; SIM-01 DI field |
| horizontal | J0(k r_horizontal) | all azimuths at el = 0; J0 by trapezoid on its integral representation (exact to J_M(x), M > x + 40) |
| directional | integral of D(u) a a^H / integral of D | Gauss-Legendre sphere quadrature on two grids; fails if they differ by more than 2e-4 |
| exponential | exp(-r / L) | short-correlation (flow-like); positive definite in 3-D |
| far_field | a(u) a(u)^H | rank 1 interferer |
| near field (host) | h h^H, h_n = (r0/rho_n) exp(-j k (rho_n - r0)) | level defined at the centroid; fails if the source is within 0.1 m of an element |

Assumed directional shapes: upward-weighted ((1 + sin el)/2)^m and horizontal band
exp(-el^2/(2 sigma^2)). They are smooth so that quadrature converges; they are not fitted to ocean data.

Every covariance is checked for Hermitian symmetry and positive semidefiniteness relative to its trace;
every field coherence is checked for a unit diagonal. Violations raise `NoiseModelError`.

## 4. Realized array gain (`rag.py`)

Relative to a single identical channel (A0) at the array reference point in the same noise model.
Without errors, with DAS weights w = a/N, ambient power 1, sensor noise eta and host noise ratio hnr:

    RAG = (1 + eta + hnr) / (w^H (Gamma + eta I + hnr h h^H) w)

Limits (verified each run): white field gives 10 log10 N; spherical field with eta = hnr = 0 gives the
SIM-01 DI. For uniform DAS on a plane-wave signal RAG >= 0 dB because w^H Gamma w <= 1.

With channel errors (Section 5) the signal is s = d o a(u; r + delta) and the noise
R = D (Gamma(r + delta) + eta_th I) D^H + eta_el I, where eta_th is the share of sensor noise that
passes through the channel error (hydrophone thermal) and eta_el the share added after it
(electronics). SIM-02A uses an assumed 50/50 split.

RAG is a ratio of narrowband SNRs. It is not detection probability, detection range, or bearing
accuracy in noise.

## 5. Channel errors and Monte Carlo (`errors.py`, `stats.py`)

Independent per channel and trial: 20 log10 g ~ N(0, sigma_g^2) dB; phase ~ N(0, sigma_phi^2);
position delta ~ N(0, sigma_p^2 I_3) m; timing tau ~ N(0, sigma_t^2) s. The beamformer uses
nominal values. Total signal phase variance:

    sigma^2 = sigma_phi^2 + (k sigma_p)^2 + (2 pi f sigma_t)^2

Closed forms for uniform weights (log-normal gain moments E g = exp(s^2/2), E g^2 = exp(2 s^2),
s = sigma_g ln10/20):

    E|B(u_s)|^2 = [N E g^2 + N (N - 1) (E g)^2 exp(-sigma^2)] / N^2
    E|B_null|^2 = [E g^2 - (E g)^2 exp(-sigma^2)] / N

Implications that hold for any geometry: phase errors from timing grow linearly with frequency
(2 pi f sigma_t: 36 deg at 10 kHz for 10 us), position errors as k sigma_p (24 deg at 10 kHz for
1 cm); the null and sidelobe floor fill to about (1 - exp(-sigma^2))/N.

Monte Carlo: each case has its own generator seeded from the base seed and a SHA-256 hash of the case
key (order independent). Means use a normal-approximation 95 % interval (n >= 200), quantiles an
order-statistic interval, proportions the Wilson interval. The run fails if any Monte Carlo mean
signal power deviates from the closed form by more than 5 standard errors, and warns when an interval
half-width exceeds the configured fraction of the mean.

Horizontal-cut statistics per case (noise-free, calibration only): the ideal mainlobe region is the
region between the first minima of the error-free cut; "ambiguity level" is the largest lobe outside
it relative to the largest inside it; the azimuth estimate is the global peak (parabolic refinement),
classed as a gross error when it falls outside the ideal mainlobe region. For line arrays the ideal
left/right mirror is a 0 dB lobe, so these statistics expose that unresolved ambiguity.

## 6. Verification (tests)

| Model | Tests (`tests/test_sim02a_models.py`, `tests/test_sim02a_pipeline.py`) |
|---|---|
| Provenance | `test_provenance_is_enforced`, `test_invalid_provenance_fails_visibly`, `test_baseline_config_builds_and_tags_every_parameter` |
| Chain | `test_hydrophone_thermal_noise_hand_calculation`, `test_preamp_and_adc_noise_and_clip_level`, `test_dynamic_range_for_a_tone_is_clip_minus_3db_minus_noise`, `test_band_power_matches_analytic_power_law`, `test_acquisition_rejects_nyquist_and_bandwidth_violations`, `test_nyquist_inconsistent_sensor_fails_visibly` |
| Noise fields | `test_bessel_j0_tabulated_values`, `test_coherence_models_are_psd_with_unit_diagonal`, `test_uniform_directional_density_reproduces_sinc`, `test_horizontal_coherence_equals_ring_average`, `test_upward_density_against_independent_fibonacci_quadrature`, `test_near_field_vector_level_and_far_field_limit`, `test_invalid_covariances_and_fields_fail_visibly` |
| Gain | `test_rag_limits`, `test_rag_with_interferer_in_a_null`, `test_ideal_draw_reproduces_error_free_results` |
| Errors and statistics | `test_mainlobe_and_null_power_match_closed_form` (5 error types), `test_error_model_validation`, `test_statistics_helpers` (Wilson value, 95 % coverage), `test_case_rng_is_order_independent_and_reproducible` |
| Pipeline | `test_sim02a_smoke_is_bitwise_reproducible` |
