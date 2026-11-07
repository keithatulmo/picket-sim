# PCK-SIM-001 / SIM-02A Engineering Report

> **DRAFT.** Capitalized placeholders are filled from the run of record when it completes. Do not use this version.

**Sensor, Noise and Error Modeling for Candidate Picket Arrays**

| | |
|---|---|
| Program | Ulmo / Picket, PCK-SIM-001 |
| Increment | SIM-02A (sensor, noise and error modeling), authorized by the SIM-01 technical review (ADR-0009) |
| Run of record | `RUNID` |
| Code | `picket_sim` 0.1.0, git `CODESHA` (clean tree) |
| Configuration | `configs/sim02a/sim02a_baseline.yaml` (sha256 `CFGSHA`) |
| Reproduce | `make sim02a` (equivalently `python -m picket_sim run configs/sim02a/sim02a_baseline.yaml`) |
| Status | Complete for SIM-02A scope. Submitted for review of numerical results. SIM-02B not begun (gate, ADR-0009). No architecture selected. |

All numbers are read from `results/sim02a/RUNID/tables/`; figures are in
`results/sim02a/RUNID/figures/`. **Every sensor, ambient, host and channel-error level in this study
is an assumed scenario** (72 assumed parameters, 1 published constant, 0 measured values;
`tables/parameters_by_provenance.md`). Results that depend on absolute levels are scenario results.
Wherever possible results are expressed as ratios (self-noise to ambient, host to ambient) so that they
remain valid when measured values replace the assumptions. Nothing here is detection performance,
a detection range, or a hardware requirement.

---

## 0. Findings

1. **Realized array gain is set by the spatial coherence of the dominant noise, not by geometry alone.**
   Against diffuse, ambient-limited noise (spherically isotropic, no sensor noise) the band-median
   realized gain relative to A0 is at most 0.07 dB from 20 to 200 Hz for every candidate up to 1.07 m
   (1.08 dB for the 4 m envelope V-D), and 0.6 to 5.2 dB from 200 Hz to 2 kHz. When sensor self-noise
   dominates (self-noise 20 dB above ambient) or the noise is short-correlation (flow-like,
   L = 0.1 m), the same arrays approach the white-noise gain of their equal weights, 10 log10 N, at
   every frequency: for example 4.59 dB for A1 and 8.75 dB for P8-E from 20 to 200 Hz in the
   short-correlation field. Low-frequency array value therefore depends on which noise dominates at
   the sensors, which only measured sensor, ambient and host data can settle. (High, for the model.)
2. **Under the assumed sensor scenarios, ambient noise dominates almost everywhere, so realized gain
   follows the diffuse-field values.** The low-noise scenario S1 sits 20 to 74 dB below all ambient
   scenarios in every band. The mid scenario S2 is sensor-limited only in the exploratory band B4 under
   quiet ambient (+4.0 dB). The low-cost scenario S3 is near or above quiet ambient from 200 Hz up
   (+1.8 dB in B2, +12.1 dB in B3) and cannot acquire B4 at all (32 kHz sampling, 12 kHz declared
   bandwidth). In S2, 16-bit quantization noise exceeds the analog noise in B3 and B4 (-2.7 and -3.2 dB
   margins): gain staging, not the hydrophone, sets its noise floor there. (Moderate: assumed
   scenarios.)
3. **At equal footprint, six and eight elements on a circle widen the conventional band under -3 and
   -6 dB criteria, but much less under -10 dB.** Guaranteed band ratios over horizon steering at the
   0.45 m footprint: 2x2 square 1.28 / 1.14 / 1.03, six-element circle 2.53 / 2.37 / 1.28,
   eight-element circle 3.78 / 2.80 / 1.32 (-3 / -6 / -10 dB). The circles' intrinsic sidelobes, near
   -8 dB, cap the -10 dB band. They also add gain where sensors are uncorrelated: 8.58 dB for the
   eight-element circle against 5.88 dB for the square from 2 to 10 kHz in isotropic noise (band
   medians). (High, for narrowband DAS.)
4. **Four-element volumetric envelopes have no band free of -6 dB narrowband ambiguity lobes for every
   horizon steering direction**; their guaranteed -3 dB bands are 1.06 to 1.14. Scaling the envelope to
   4 m moves the band down to 146 to 182 Hz and raises low-band gain, at the cost of narrowband
   ambiguity above that. Broadband and TDOA processing, which may resolve these ambiguities, is SIM-02B.
   (High for the narrowband statements.)
5. **Calibration and synchronization tolerances scale with frequency, and bearing statistics are a
   stricter constraint than signal loss.** MC_FINDING
6. **Line arrays remain structurally ambiguous left/right under any channel errors.** Their scanned
   response is exactly symmetric in azimuth because the beamformer's steering vectors depend only on the
   angle to the axis; calibration errors cannot break the tie (D02: unresolved ambiguity identified).
   (High; mathematical.)
7. **Arrays reject host noise only when the target is away from the host direction and the frequency is
   high enough.** With a host source at +10 dB relative to ambient, the median realized gain at 100 Hz
   is 0.0 to 0.2 dB for every candidate up to 1.07 m (2.7 to 3.2 dB for V-D). At 2 kHz it reaches 5.4 to
   12.0 dB for typical target directions, but the worst steering direction stays at 0.3 to 1.7 dB.
   Assumed generic host placements; no vessel geometry. (Moderate.)
8. **Pareto results change with the provisional tolerances and are not a basis for elimination.**
   Doubling the SIM-01 engineering tolerances adds A2 to the dominated set; in the SIM-02A attribute
   set V-D is dominated by V-DS only at 1x and 2x tolerance. Cost, installation, calibration burden and
   power are not modeled (D06).

---

## 1. Scope and gating

SIM-02A implements the authorized sensor, noise and error modeling: hydrophone sensitivity and
self-noise, preamplifier and ADC noise, clipping and dynamic range; white, diffuse, horizontally
isotropic, directional and short-correlation noise fields; scenario-based host noise; gain, phase,
position and timing errors; Monte Carlo sensitivity with statistical uncertainty. Analyses span 20 Hz to
20 kHz with summaries for the D01 study bands: B1 20-200 Hz, B2 200 Hz-2 kHz, B3 2-10 kHz and
B4 10-20 kHz (exploratory, contingent on acquisition). Conventional DAS remains the baseline. Not in
SIM-02A: broadband processing, TDOA, detection experiments, false-alarm analysis (SIM-02B), and
acoustic vector sensor modeling beyond a feasibility assessment (`docs/avs_feasibility.md`).

## 2. Candidates

`tables/candidates.md`; `figures/s2a_fig01_candidates.png`. Footprint classes by maximum dimension:
C = 0.45 m (the A1 aperture), E = 0.90 m (the A2 aperture), I = A4 envelope, D = 4 m class (assumed).

| ID | Family | Footprint | N | Max dim (m) | Geometric ambiguity | Exact grating onset (Hz) | Worst-case -3 / -6 / -10 dB ambiguity onset (Hz) |
|---|---|---|---|---|---|---|---|
CAND_TABLE

A1 and A2 form the linear family L4(d), d = 0.15 and 0.30 m (D05). The intermediate envelope
reproduces A4 exactly (self-check). The 8-element circle has no exact grating lobe below 20 kHz (its
baselines are not commensurate); its narrowband ambiguity onsets are set by high near-grating lobes.

## 3. Models and verification

Model reference: `docs/sensor_noise_error_models.md`; decisions ADR-0010 to ADR-0013.

* **Acquisition chain:** element thermal noise 4kT Re(Z) for a lossy capacitance, preamplifier voltage
  noise (with 1/f corner) and current noise, ideal ADC quantization, clipping at the first stage to
  saturate; all input-referred to pressure through the element sensitivity.
* **Noise fields:** unit-power spatial coherence models; directional densities integrated by sphere
  quadrature with a two-grid convergence check; every covariance checked for Hermitian positive
  semidefiniteness and unit diagonal.
* **Realized array gain (RAG):** narrowband output SNR of uniform DAS divided by the SNR of a single
  identical channel (A0) in the same noise model; self-noise to ambient ratio eta and host to ambient
  ratio as parameters.
* **Channel errors:** independent Gaussian gain (dB), phase, 3-D position and timing errors per channel;
  nominal beamformer; Monte Carlo with 1,000 trials per scenario case and 400 per sweep case, with
  95 % intervals on every statistic.

**Verification.** 166 automated tests pass at the run-of-record commit, including closed-form
acquisition noise, tabulated J0 values, coherence models against independent quadrature, RAG limits,
Monte Carlo means against closed forms for five error types, statistical interval coverage,
structural-ambiguity classification, provenance and Nyquist enforcement, and bitwise reproducibility of
the pipeline.

**Self-checks embedded in the run of record** (`record.json`):

SELFCHECKS

---

## 4. Results

### 4.1 Acquisition chain and dynamic range (D01)

`tables/acquisition_*.md`; `figures/s2a_fig02_self_noise.png`, `figures/s2a_fig03_dynamic_range.png`.

![Figure 1. Self-noise components versus assumed ambient scenarios.](../results/sim02a/RUNID/figures/s2a_fig02_self_noise.png)
*Figure 1. Input-referred self-noise components of the three assumed sensor scenarios against the three assumed ambient scenarios.*

Self-noise to ambient ratio eta, band medians (dB), for the moderate and quiet ambient scenarios:

ETA_TABLE

* **Ambient-limited operation is the norm in these scenarios.** Only S3 (low-sensitivity element,
  noisier input stage) approaches or exceeds quiet ambient above 200 Hz. When eta is below about
  -10 dB, Section 4.2 shows the realized gain is within 0.4 dB of its no-sensor-noise value.
* **The exploratory band B4 depends on acquisition choices (D01).** S3 cannot acquire it (Nyquist
  16 kHz; declared usable band to 12 kHz). The pipeline reports such bands as "not acquirable" rather
  than extrapolating.
* **Gain staging matters.** In S2 the ADC quantization noise exceeds the analog noise in B3 and B4
  (analog minus ADC: -2.7 and -3.2 dB), so more preamplifier gain would lower the noise floor at the
  cost of clipping headroom. S1 and S3 keep the ADC more than 23 dB below the analog noise.
* **Dynamic range (moderate ambient)** over the total in-band noise, for the broadband class
  (12.04 dB crest factor): DR_SENTENCE Transients with a 25 dB crest factor lose a further 13 dB of
  headroom relative to broadband signals. Clip levels: 173.0 dB re 1 uPa peak (S1, S2) and
  165.0 dB (S3), set by the ADC full scale.

### 4.2 Realized array gain versus noise structure and sensor noise

`tables/rag_*.md`, `tables/rag_band_summary.csv`; `figures/s2a_fig04_rag_isotropic.png`,
`figures/s2a_fig05_rag_by_field.png`.

![Figure 2. Realized array gain in isotropic noise for three sensor-noise ratios.](../results/sim02a/RUNID/figures/s2a_fig04_rag_isotropic.png)
*Figure 2. Realized array gain relative to A0 in spherically isotropic ambient noise, median over horizon steering, for no sensor noise, eta = 0 dB and eta = +20 dB.*

![Figure 3. Band-median realized gain by noise-field structure.](../results/sim02a/RUNID/figures/s2a_fig05_rag_by_field.png)
*Figure 3. Band-median realized gain by noise-field structure, no sensor noise.*

Band-median RAG (dB) with no sensor noise, selected candidates:

RAG_TABLE

* **Diffuse fields (ISO, HOR, upward-weighted, horizontal band) give similar values**: the field's
  directional shape changes band medians by under about 1 dB for most candidates. Spatial coherence
  over the aperture is what matters.
* **Short-correlation noise behaves like sensor noise**: with L = 0.1 m smaller than most element
  spacings, it is nearly uncorrelated between sensors and the gain approaches 10 log10 N even at
  20 Hz.
* **Sensor noise raises gain relative to A0.** In isotropic ambient, A1's B1 median rises from 0.01 dB
  (no sensor noise) to 2.05 dB at eta = 0 dB and 5.89 dB at eta = +20 dB. This is not an improvement
  in absolute sensitivity: the single-channel reference is degraded by the same sensor noise, and the
  array averages it down.
* The SIM-01 statement that 6.02 dB is the white-noise gain of four equal weights (ADR-0008) is
  reproduced exactly: RAG in the white field equals 10 log10 N for every candidate (self-check).

### 4.3 Host-noise scenarios

`tables/host_noise.md`; `figures/s2a_fig06_host_noise.png`. Generic host sources (assumed): near
field at 3 m and 15 m (az 180 deg, el +20 and +10 deg) and a far-field source (az 180, el +5 deg).
Ambient isotropic, eta = -10 dB, host to ambient ratio +10 dB.

![Figure 4. Realized gain with host noise.](../results/sim02a/RUNID/figures/s2a_fig06_host_noise.png)
*Figure 4. Realized gain relative to A0 with a host source at +10 dB, median (solid) and worst (dotted) over horizon steering.*

HOST_TABLE

* A0 receives the full host noise, so arrays that place the host in a sidelobe or null gain more than
  their no-host value (median RAG above the no-host column).
* When the target azimuth coincides with the host azimuth, compact arrays give 0.1 to 2.1 dB: DAS
  cannot separate a target from a host source in the same direction. At high frequency larger arrays
  separate them by elevation (for example A4 toward the H-near azimuth at 15 kHz, where the source is
  20 deg above the horizontal target).
* At 100 Hz no candidate up to 1.07 m rejects host noise (median RAG 0.0 to 0.2 dB). Low-frequency
  host noise reaches compact arrays essentially unattenuated by beamforming.

### 4.4 Channel errors: signal loss, ambiguity and bearing

MC_SECTION

### 4.5 Ambiguity-criterion sensitivity (D03)

`tables/thresholds_bands.md`, `tables/thresholds_summary.csv`; `figures/s2a_fig09_bands_by_criterion.png`.

![Figure 6. Conventional bands under three ambiguity criteria.](../results/sim02a/RUNID/figures/s2a_fig09_bands_by_criterion.png)
*Figure 6. Guaranteed (dark) and median (light) conventional bands under -3, -6 and -10 dB criteria, horizon steering.*

BANDS_TABLE

* **The -3 dB results reproduce SIM-01** (32 thresholds, maximum relative difference 2.7e-4).
* **Stricter criteria shrink bands unevenly.** Line arrays keep most of their band (sidelobes of a
  4-element line are -11.3 dB below the mainlobe). Squares and circles lose most of it at -10 dB.
  Volumetric 4-element envelopes have no guaranteed band at -6 or -10 dB.
* These are criteria for narrowband DAS. No threshold is proposed as a requirement (D03).

### 4.6 Pareto tolerance sensitivity (D06)

`tables/pareto_tolerance_sensitivity.md`, `tables/pareto_sim02a_attributes.csv`;
`figures/s2a_fig10_pareto_tolerance.png`.

PARETO_TABLE

* Dominance depends on the provisional tolerances. It can appear and then disappear as tolerances grow
  (V-D at 1x and 2x but not at 4x), because wider tolerances turn strict advantages into ties.
* The SIM-02A attribute set includes realized gain at eta = 0 dB, half-power onset, worst-case -3 dB
  ambiguity onset and the probability of a -6 dB outside lobe under E2 at 5 kHz. It omits cost,
  installation, calibration burden, power and broadband performance. **No candidate is eliminated.**

---

## 5. Traceability to the reviewer decisions

| Decision | How SIM-02A addresses it | Where |
|---|---|---|
| D01 study bands and signal classes | 20 Hz to 20 kHz with B1 to B4 summaries; B4 flagged exploratory and checked against acquisition; tonal, harmonic, broadband and transient classes in the dynamic-range analysis; no bearing assumed for every class | Sections 4.1, 4.2; `tables/acquisition_dynamic_range.*` |
| D02 detection first, bearing secondary | Gain relative to A0 is the primary figure of merit; bearing statistics reported for horizontal azimuth only, with unresolved ambiguities identified; no maneuver-based disambiguation | Sections 4.2, 4.4 |
| D03 ambiguity criteria | -3 dB kept (regression against SIM-01), -6 and -10 dB added; median and guaranteed bands; no threshold adopted as a requirement | Section 4.5 |
| D04 A4 notional | Parametric envelopes (compact, intermediate = A4 regression, distributed, draft-limited distributed) reported with their dimensions; no vessel geometry | Sections 2, 4.2, 4.5 |
| D05 candidates | A0 to A4 retained; 6- and 8-element circles and 2x2 squares at two footprints; linear family; AVS feasibility assessment | Section 2; `docs/avs_feasibility.md` |
| D06 tolerances | Tolerances kept and treated as provisional; sensitivity at 0, 0.5, 1, 2, 4x; no elimination | Section 4.6 |
| Provenance | Every parameter tagged; 72 assumed, 1 published, 0 measured | `tables/parameters_by_provenance.md` |
| Fail visibly | Nyquist, bandwidth, provenance, PSD, convergence and normalization checks raise errors; undefined statistics reported as n/a with reasons | `docs/sensor_noise_error_models.md` |

---

## 6. Limitations

* **All levels are assumed.** Absolute self-noise, ambient, host and error levels are illustrative.
  The ratio-based results (gain versus eta, versus host ratio, versus error sigma) transfer; the
  scenario-specific numbers do not.
* **Narrowband only.** Ambiguity conclusions describe single-frequency patterns; broadband processing
  is SIM-02B.
* **Noise-free bearing statistics.** Calibration-induced biases only; errors from additive noise need
  task-level experiments (SIM-02B).
* **Independent Gaussian channel errors.** Correlated errors (temperature drift common to channels,
  systematic position bias, clock drift) are not modeled.
* **Idealized elements.** Point, omnidirectional elements; no element directivity, host baffling or
  scattering; no near-field effects on the signal (host sources only).
* **Steering statistics** use the horizon ring (24 directions); Monte Carlo uses 4 target azimuths.
* **The Pareto analysis** covers evaluated attributes only.

---

## 7. Recommendations for SIM-02B (based on the verified SIM-02A results)

These recommendations need the reviewer's decision before SIM-02B begins (ADR-0009).

1. **Detection experiments against A0 in both noise regimes.** Finding 1 shows the array's value
   reverses between ambient-limited diffuse noise and sensor- or flow-limited noise. SIM-02B detection
   experiments at fixed false-alarm probability should span eta from about -40 to +20 dB and include the
   short-correlation field, for tonal, harmonic, broadband and transient classes.
2. **Broadband beamforming and TDOA for the candidates with narrowband ambiguity.** Priority: the
   volumetric envelopes (A4, V-C, V-D, V-DS), the 2x2 squares above their grating onsets, and the
   circles under the -10 dB criterion. Measure task-level ambiguity (probability of a wrong-lobe
   estimate) and bearing error statistics rather than sidelobe levels (D03).
3. **Carry channel errors into task-level metrics,** with the E1 to E4 scenarios and an explicit
   synchronization model for distributed modules. Timing error is the dominant term at high frequency
   and directly limits TDOA.
4. **Replace assumed inputs with published or measured values before any result informs requirements:**
   candidate hydrophone and preamplifier noise data, published ambient-noise models with provenance,
   host noise and vibration measurements, and flow-noise correlation at host speeds.
5. **Candidate set for SIM-02B:** A0 as the baseline; the linear family (bearing with known left/right
   ambiguity); the 6- and 8-element circles at both footprints; A4 and the distributed envelopes for
   broadband tests. The 2x2 squares remain as references. Feasibility data collection for acoustic
   vector sensors in parallel (`docs/avs_feasibility.md`).
6. **Correlated-error and drift models** if the reviewer considers long-duration calibration stability
   relevant to proliferated hosts.

---

## 8. Reproducibility and provenance

* `make sim02a` runs the test suite and the experiment into a new immutable directory. `record.json`
  holds the resolved configuration and hash, git commit, software versions, timings, self-checks and
  SHA-256 hashes of every output. `tables/parameters_by_provenance.*` lists every parameter's provenance.
* `results/sim02a/RUN_INDEX.csv` lists all SIM-02A runs. Two earlier runs are retained unchanged with
  errata (`results/sim02a/ERRATA.md`). Both contained defects in the Monte Carlo bearing statistics only
  (a tie-breaking artifact for line arrays, then a tie test that absorbed gross errors). Every other table
  is byte-identical across all three runs (CROSSRUN).
