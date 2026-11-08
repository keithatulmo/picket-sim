# PCK-SIM-001 / SIM-02B Technical Implementation Plan

Signal and detection modeling, broadband and synchronization trades. Plan of record, written before
implementation. Authority: SIM-02A technical review and SIM-02B authorization (ADR-0014). SIM-02B runs
in two stages; SIM-02B.2 starts only after SIM-02B.1 results are verified and reviewed.

## 1. Objective and boundaries

Determine, under stated and provenance-labeled assumptions, whether additional sensors, alternative
geometries and conventional processing give a measurable detection benefit over a single hydrophone
(A0), by frequency band, signal class and integration time, with statistical uncertainty. The program
question is whether that benefit justifies the size, cost, power, calibration and integration burden;
SIM-02B supplies the acoustic half of that trade and does not optimize for one geometry or one metric.

Not in SIM-02B.1: bearing and TDOA estimation, synchronization models, joint calibration and noise
errors, expanded steering studies (all SIM-02B.2); adaptive processing; detection ranges; hardware
requirements; Fathom.

## 2. SIM-02B.1 work breakdown

| # | Item | Module / output |
|---|---|---|
| 1 | Published-reference and assumption-labeled environmental inputs (D01, ADR-0017) | `configs/sim02b/inputs_published.yaml`, `params` provenance fields, `docs/input_provenance_register.md` |
| 2 | Broadband signal generation: tone, harmonic set, band-limited Gaussian, LFM chirp; defined spectra, timing, direction and amplitude | `signals.py` |
| 3 | Broadband multichannel acquisition using the SIM-02A sensor and noise models; waveform export | `synthesis.py` (ADR-0016) |
| 4 | A0 conventional detection baseline | `detectors.py` |
| 5 | Multichannel conventional detectors and beamformers: DAS beam at the true direction (bound), DAS beam search over the 24-azimuth horizon set, incoherent channel-power sum | `detectors.py` |
| 6 | Threshold estimation under defined null hypotheses: exact, empirical, union bound (ADR-0015) | `detection.py` |
| 7 | Monte Carlo evaluation with confidence intervals; disjoint calibration, evaluation and positive sets | `experiments/sim02b1.py` |
| 8 | Numerical and analytical verification | `tests/test_sim02b1_*.py`, run self-checks |

## 3. Detectors (fixed before experimentation)

All statistics use bins normalized by the **assumed** noise model: for a stream with weights w,
z_k = w^H x_k / sqrt(w^H C_assumed(f_k) w). Under matched noise abs(z_k)^2 is a unit exponential.

| Class | Detector | Statistic per window |
|---|---|---|
| Tone | tonal (single coherent DFT over T) | max over band bins and streams of abs(z_k)^2 |
| Harmonic (H = 4) | harmonic sum | max over fundamentals (grid step 1/(H T)) and streams of the sum of abs(z)^2 at the nearest bins to h f0, h = 1..H |
| Broadband | whitened energy detector | max over streams of the sum over band bins of abs(z_k)^2 |
| Chirp | whitened matched filter, unknown arrival | max over lags (2x oversampled) and streams of abs(sum z_k s_k* exp(j 2 pi f_k tau))^2 / sum abs(s_k)^2, with s_k the whitened replica |

Streams: A0, one element; beam-known, one DAS beam at the true azimuth (an upper bound that assumes the
direction is known); beam-search, 24 DAS beams at 15 deg on the horizon; incoherent, the mean over
elements of abs(x_n,k)^2 / C_assumed,nn(f_k) (no beamforming).

## 4. Primary experiment (SIM-02B.1 run of record)

* Candidates: A0, A1, A2, P6-C, P8-C, A4 (primary); P8-E, SQ4-C, V-C, V-D, V-DS (secondary). Original
  candidates remain configurable.
* Bands: B1 20 to 200 Hz, B2 200 Hz to 2 kHz, B3 2 to 10 kHz (B4 exploratory, not in the primary run).
* Windows: 0.1, 1, 10 s; 60 s coherent tonal in B1.
* Noise scenarios (truth = assumption in the primary experiment): ambient-limited diffuse (spherically
  isotropic coherence), sensor-limited, and short-correlation flow-like. Levels from published-reference
  inputs where available (ADR-0017), otherwise the SIM-02A assumed envelopes.
* Source: plane wave on the horizon, azimuth uniform per trial; tone and fundamental frequencies uniform in
  the search band; random phases; chirp arrival uniform inside the window.
* Pfa 0.01 and 0.001 (primary), 0.0001 (sensitivity). Pd on an SNR grid placed around the A0 operating
  point; outputs include Pd curves with intervals, ROC curves for selected cases, SNR required for
  Pd = 0.5 and 0.9, and detection gain relative to A0.
* Scenarios where A0 is expected to compete are included by design (ambient-limited low band, beam-search
  penalty, short windows).

## 5. Verification (review section 6)

Independent tests for: signal spectra against direct time-domain DFTs (tone, harmonic, chirp, broadband
power); spectral power and Parseval scaling; noise covariance against the time-series cross-spectral
estimate; acquisition gain and input-referred noise; detector null distributions against exact
distributions; false-alarm calibration on independent evaluation sets; TDOA sign conventions; timing-error
propagation (closed form against synthesized delays). Run self-checks repeat the covariance, null
distribution and Pfa checks on the run's own cases. False-alarm calibration is tested under matched and
mismatched noise (level, spectral slope, coherence).

## 6. Statistics (ADR-0015)

Calibration, evaluation and positive trial sets are disjoint and independently seeded. Pfa = 1e-3 empirical
thresholds require n_cal x Pfa >= 10; otherwise exact or union-bound thresholds are used and labeled.
Every proportion carries a Wilson interval; thresholds carry order-statistic intervals propagated to Pd.

## 7. SIM-02B.2 (after SIM-02B.1 review)

Broadband beamforming and TDOA estimators; shared-clock and distributed-clock acquisition (offset,
sample-rate mismatch, drift, jitter, resynchronization, interruptions) reported as conditional budgets;
noise- and calibration-induced errors together, including persistent and correlated calibration errors;
bearing ambiguity, circular angular error and gross-error statistics over at least 24 horizon azimuths
plus worst-case directions; model mismatch and environmental sensitivity; compact versus extended
configurations. Broadband processing is not assumed to resolve narrowband ambiguities; it must be shown
under defined bandwidth, SNR, source and synchronization conditions.

## 8. Reproducibility

Immutable run directories and records (ADR-0006), configuration and dependency versions in every record,
clean-tree runs of record, claims check (`tools/check_sim02b1_claims.py`) before any report is sent, review
package with both source baselines (ADR-0014).
