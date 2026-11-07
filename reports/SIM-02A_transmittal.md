# SIM-01 Closure and SIM-02A Review Transmittal

**Ulmo / Picket, PCK-SIM-001: SIM-01 documentation corrections and SIM-02A sensor, noise and error modeling**

| | |
|---|---|
| To | Author of the SIM-01 technical review and SIM-02 authorization |
| Subject | SIM-01 closure (report Revision A) and SIM-02A numerical results for review |
| Date | 2026-11-07 |
| Repository | `keithatulmo/picket-sim`, branch `claude/beautiful-darwin-vbeoue` |
| SIM-02A run of record | `20261107T214846Z_c56c0048_31da01b` (code commit `31da01b`, clean tree) |
| Prepared by | Claude Code (AI-generated engineering work product). Requires review by a qualified acoustic engineer before any of it informs requirements. |
| Requested action | Confirm SIM-01 closure; review the SIM-02A numerical results; decide the items in Section 6 before SIM-02B is authorized |
| Revision | A: SIM-02A report and this transmittal corrected before sending (Section 4, last group). Rev 0 package retained unchanged. |

## 1. SIM-01 documentation corrections (review Section 1)

All five corrections are made without altering any experimental result, and recorded in ADR-0008,
`results/sim01/ERRATA.md` and the report's revision history. The Rev 0 review package is retained
unchanged.

| # | Correction | Where |
|---|---|---|
| 1 | 6.02 dB qualified as the white-noise gain of four equally weighted elements, not an absolute bound | SIM-01 report Rev A Sections 0, 4.2, 5.1; SIM-01 transmittal Rev A |
| 2 | f_HP described as a -3 dB discrimination criterion, not a limit on direction information | Report Rev A Sections 0, 4.1, 5.1 to 5.3, 8; `docs/metrics.md` |
| 3 | Median-steering bands separated from bands guaranteed across the steering set | `reports/SIM-01_band_definitions.md` (derived from the existing tables by `tools/sim01_band_definitions.py`); report Rev A Sections 0, 4.1, 5.2 |
| 4 | Exact narrowband grating lobes separated from broadband direction finding | Report Rev A Sections 0, 4.1, 4.4, 5.4, 7, 8 |
| 5 | Pareto conclusions conditional; no elimination of hardware candidates | Report Rev A Sections 0, 6, 7, 8 |

Correction 3 changes the headline band ratios. Over the horizon steering set the bands guaranteed for
every direction are 1.77 (lines), 1.28 (A3) and 1.06 (A4). The median-direction bands are 3.54, 1.54
and 1.36. The Rev 0 values (3.03, 1.44, 1.18) used a mixed convention.

## 2. SIM-02A deliverables (review Section 5)

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | Updated technical implementation plan | Delivered | `docs/SIM-02A_plan.md`; ADR-0009 to ADR-0013 (written before implementation) |
| 2 | SIM-02A source, configuration, automated tests | Delivered | `src/picket_sim/{params,sensor,noisefields,errors,stats,rag,avs}.py`, `experiments/sim02a.py`; `configs/sim02a/`; 166 tests passing |
| 3 | Sensor, noise and error model documentation | Delivered | `docs/sensor_noise_error_models.md` |
| 4 | Comparative results, retained and new candidates | Delivered | SIM-02A report Sections 2 and 4; run tables and figures |
| 5 | Sensitivity and uncertainty analysis | Delivered | Report Sections 4.2 (eta sweep), 4.4 (Monte Carlo with 95 % intervals, one-at-a-time sweeps), 4.5 (-3/-6/-10 dB), 4.6 (tolerance scales) |
| 6 | Updated limitations and assumption register | Delivered | `docs/assumptions.md` (AS-11 to AS-19); report Section 6 |
| 7 | Reproducible engineering report | Delivered | `reports/SIM-02A_engineering_report.md` / `.pdf`; `make sim02a` |
| 8 | Recommendations for SIM-02B | Delivered | Report Section 7 |

Additional items: acoustic vector sensor feasibility assessment (D05), `docs/avs_feasibility.md`;
criterion-margin supplement (D03), `reports/SIM-02A_criterion_margin.md` (Rev A); claims check,
`tools/check_sim02a_claims.py` with its output `reports/SIM-02A_claims_check.txt` (Rev A).
SIM-02B work has not started.

## 3. Verification requirements (review Section 4)

| Requirement | Evidence |
|---|---|
| Positive-semidefinite noise covariance | `check_covariance` on every coherence and total covariance (raises); `test_coherence_models_are_psd_with_unit_diagonal`, `test_invalid_covariances_and_fields_fail_visibly` |
| Correct noise normalization | Unit-diagonal check on every field; gain limits self-checked each run (white field 10 log10 N; isotropic field equals SIM-01 DI, agreement 5e-15 dB) |
| Array gain versus detection performance | Gain reported only as narrowband SNR ratios relative to A0; detection deferred to SIM-02B (ADR-0011) |
| Calibration and timing-error propagation | Closed forms for signal loss and null filling verified by Monte Carlo (5 error types in tests; 1,664 cases in the run, largest deviation 3.33 standard errors) |
| Broadband processing assumptions | None made in SIM-02A; narrowband scope stated in every result |
| Statistical uncertainty in Monte Carlo results | 95 % intervals on means, quantiles and proportions; coverage tested; order-independent seeded streams |
| Consistent comparison of geometries | Footprint classes C (0.45 m) and E (0.90 m); identical steering, noise and error models for every candidate |
| Fail visibly | Provenance, unit, Nyquist, bandwidth, PSD, convergence and normalization violations raise; undefined statistics reported as n/a with reasons; no clipping in error paths |

## 4. Errors found and corrected during SIM-02A

Recorded in `results/sim02a/ERRATA.md`; both earlier runs are retained unchanged.

* Run 1: line-array bearing statistics were a tie-breaking artifact. The scanned response of a line is
  exactly symmetric in azimuth, and `argmax` picked the mirror. Cut statistics were also reported where
  the error-free pattern has no half-power discrimination.
* Run 2: the first fix classified outright gross errors as ties.
* Run of record: structural ambiguity is decided on the error-free cut (outside lobe within 1 dB of the
  mainlobe). Gross errors are counted only where no structural ambiguity exists.
* Before any run, the assumed sensor scenario S1 was corrected to be physically consistent. Its element
  sensitivity had been set as if it included preamplifier gain, while the same value was used to refer
  the element's thermal noise.

Every table other than the Monte Carlo bearing columns is byte-identical across the three runs.

Documentation errors found by a programmatic check of every quantitative claim
(`tools/check_sim02a_claims.py`) before this package was sent, corrected in report and transmittal
Revision A; no run, table or figure changed:

* The circles' sidelobes were stated as "near -8 dB". The six-element circle's plateau is -6.02 dB
  (eight-element: -7.77 dB). That is 0.02 dB below the -6 dB criterion, so P6-C's -6 dB guaranteed
  band is knife-edge (`reports/SIM-02A_criterion_margin.md`).
* "At most 0.07 dB from 20 to 200 Hz" is a band median; the gain reaches 0.73 dB at 200 Hz.
* "Approach 10 log10 N" in short-correlation noise overstated the result for A1, P6-C and P8-C, which
  fall 0.9 to 1.7 dB short below 2 kHz.
* The 65 % gross-error rate is one of four target azimuths (range 65 to 81 %), and it comes from the
  combined E3 scenario, not from a 10 us timing error alone.
* Two statements were imprecise in scope: the 2 kHz host-noise range (4.7 dB is the 4 m envelope;
  candidates up to 1.07 m give 5.6 to 12.0 dB), and the line-array ambiguity, which has one exception
  at exact endfire, where target and mirror coincide.

## 5. Principal SIM-02A findings

1. Realized gain is governed by the spatial coherence of the dominant noise. In diffuse, ambient-limited
   noise, arrays up to 1.07 m gain at most 0.07 dB over A0 as a 20 to 200 Hz band median, and at most
   0.73 dB at 200 Hz. With sensor self-noise 20 dB above ambient they come within 0.29 dB of
   10 log10 N in every band. In short-correlation noise they come within 0.5 dB, except A1, P6-C and
   P8-C, which fall 0.9 to 1.7 dB short below 2 kHz.
2. Under the assumed sensors, ambient noise dominates almost everywhere. B4 is not acquirable by the
   low-cost scenario, and 16-bit quantization limits the mid scenario in B3 and B4.
3. At equal footprint, 6- and 8-element circles widen the -3 dB guaranteed band from 1.28 (square) to
   2.53 and 3.78, but only to 1.28 and 1.32 under -10 dB, because their sidelobe plateaus sit at
   -6.02 and -7.77 dB. The six-element -6 dB ratio (2.37) is knife-edge: it falls to 1.65 at -6.1 dB.
   No other guaranteed ratio moves by more than 0.03 across +/- 0.1 dB.
4. Four-element volumetric envelopes have no guaranteed band at -6 or -10 dB (narrowband).
5. Bearing statistics are stricter than signal loss. For example, under the loose scenario E3 (1 dB,
   10 deg, 1 cm, 10 us) at 15 kHz the 8-element compact circle loses 4.3 to 4.4 dB of signal but makes
   gross azimuth errors in 65 to 81 % of trials across the four target azimuths. Timing supplies about
   two thirds of E3's phase variance at 15 kHz.
6. Line arrays stay structurally ambiguous left/right under any channel errors.
7. Pareto dominance changes with the provisional tolerances; no candidate is eliminated.

All sensor, ambient, host and error levels are assumed. Ratio-based results transfer; scenario-specific
numbers do not.

## 6. Decisions requested before SIM-02B

1. **Inputs with provenance.** Which published or measured sources to adopt for hydrophone and
   preamplifier self-noise, ambient noise, host noise and vibration, and flow-noise correlation (report
   Section 7, item 4). SIM-02B results cannot inform requirements without them.
2. **SIM-02B candidate subset and priorities** (report Section 7, item 5).
3. **Detection experiment design:** false-alarm probabilities, integration times and the signal classes
   to carry forward from D01.
4. **Synchronization model** for distributed modules (timing dominates at high frequency).
5. **Whether to fund the acoustic vector sensor data collection** in `docs/avs_feasibility.md`.
6. **Criterion conventions.** The structural-ambiguity level (-1 dB) used for bearing statistics and
   the Monte Carlo steering set (4 azimuths), if a different convention is preferred. Also whether the
   -6 dB criterion is applied at -6.00 dB in power or at half amplitude (-6.02 dB): P6-C's -6 dB band
   depends on that choice (`reports/SIM-02A_criterion_margin.md`).

## 7. Suggested review path (about 45 minutes)

1. This transmittal, Sections 5 and 6.
2. SIM-02A report Section 0 (findings), Figures 2, 5 and 6, and Section 7 (SIM-02B recommendations).
3. `tables/parameters_by_provenance.md`, to confirm that nothing is presented as measured.
4. SIM-01 report Rev A Section 0 and `reports/SIM-01_band_definitions.md`, for the closure corrections.
5. `reports/SIM-02A_criterion_margin.md` and `reports/SIM-02A_claims_check.txt`, for the Rev A corrections.
6. Optional: reproduce with `make sim02a` (about 6 minutes including the test suite) and compare against
   `SHA256SUMS.txt`; `make sim02a-claims` rechecks every quoted number in seconds, and `make sim02a-margin`
   regenerates the criterion-margin supplement (about 10 minutes).
