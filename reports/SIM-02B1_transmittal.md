# SIM-02A Closeout and SIM-02B.1 Review Transmittal

**Ulmo / Picket, PCK-SIM-001: SIM-02A reproducibility closeout and SIM-02B.1 signal and detection-model foundation**

| | |
|---|---|
| To | Author of the SIM-02A technical review and SIM-02B authorization |
| Subject | SIM-02A closeout actions and SIM-02B.1 numerical results for review |
| Date | 2026-11-08 |
| Repository | `keithatulmo/picket-sim`, branch `claude/beautiful-darwin-vbeoue` |
| SIM-02B.1 run of record | `20261108T125126Z_1c70e065_8dbe019` (code commit `8dbe019`, clean tree) |
| Prepared by | Claude Code (AI-generated engineering work product). Requires review by a qualified acoustic engineer before any of it informs requirements. |
| Requested action | Confirm the SIM-02A closeout; review the SIM-02B.1 results; decide the items in Section 7 before SIM-02B.2 begins |

## 1. SIM-02A closeout actions (review Section 2)

| # | Action | Evidence |
|---|---|---|
| 1 | Include the source of the Revision A claims checker and criterion-margin generator | Both are in the final-baseline source archive `07_source/picket-sim_<head>_baseline.tar.gz` (head commit named in `07_source/SOURCE.md`); `tools/check_sim02a_claims.py`, `tools/sim02a_criterion_margin.py` |
| 2 | Make `make sim02a-claims` and `make sim02a-margin` work from the supplied snapshot | The baseline archive embeds the SIM-01, SIM-02A and SIM-02B.1 run-of-record records and tables. The package builder unpacked it (no `.git`) and ran `make sim02a-claims`, `make sim02a-margin-check` (regenerates the supplement and requires byte-identical CSV files) and `make sim02a-repro-check` (reruns SIM-02A and requires every run table to be byte-identical to the run of record). Log: `05_verification/snapshot_checks.txt`. `make sim02a-margin` still writes into `reports/`; the `-check` form is the one to use in a snapshot |
| 3 | Keep the 59 claims checks; add automated verification of the supplementary tools | `tests/test_supplementary_tools.py` (15 tests): the 59 checks pass and are counted; the checker fails on the Revision 0 documents (kept as fixtures) and on a single changed number; plateau, knife-edge, reproduction self-check, byte comparison and snapshot provenance of the margin generator; an end-to-end generator run on the smoke configuration; the table-comparison tool |
| 4 | Document the code commit, later report-generation tools and the final source baseline | `docs/source_baselines.md`; `07_source/SOURCE.md` (generated: both archives, commit list and changed files); tests run at both commits (`05_verification/pytest_log.txt`, `pytest_log_baseline.txt`) |
| 5 | Preserve all errata and immutable results | No run directory or delivered package was changed. `results/sim02a/ERRATA.md` unchanged in this cycle |

D06 criterion sensitivity on the SIM-02A run of record: `reports/SIM-02A_criteria_D06.md` (self-checked
against the run tables). See Section 5.

## 2. SIM-02B.1 deliverables (review Section 7)

| # | Required output | Evidence |
|---|---|---|
| 1 | Updated implementation plan and architecture decisions | `docs/SIM-02B_plan.md`; ADR-0014 to ADR-0017 (written before implementation) |
| 2 | Verified SIM-02B.1 results before SIM-02B.2 | Run of record `20261108T125126Z_1c70e065_8dbe019` with self-checks; SIM-02B.2 not started |
| 3 | Published/assumed/measured provenance register | `docs/input_provenance_register.md`; evidence `docs/research/D01_input_sources.md`; run table `parameters_by_provenance.csv` with frequency range, applicability and uncertainty |
| 4 | Detection ROC or equivalent curves with uncertainty | `tables/pd_curves.csv.gz` (Pd with 95 % intervals on SNR grids, every case); `tables/roc_curves.csv`; report Figures 1 and 7 |
| 5 | Comparisons against A0 | `tables/detection_gain_vs_a0.csv`; report Section 3 |
| 6 | Broadband bearing and ambiguity results where applicable | Not applicable to SIM-02B.1 (detection only); SIM-02B.2 |
| 7 | Sensitivity to synchronization and environmental assumptions | Environmental: noise scenarios and mismatch tests (report Sections 3.3 and 4). Synchronization: SIM-02B.2 (D04) |
| 8 | Comparative results by frequency band and signal class | Report Section 3; `reports/SIM-02B1_summary_tables.md` |
| 9 | Updated findings, limitations and unresolved risks | Report Sections 0 and 6; `docs/assumptions.md` (AS-20 to AS-29) |
| 10 | Recommendations for the next increment | Report Section 7 |

## 3. Verification and reproducibility (review Section 6)

| Requirement | Evidence |
|---|---|
| Broadband signal generation | Tone, harmonic and chirp bins equal direct DFTs of sampled waveforms; broadband power and cross-channel phase (tests) |
| Spectral power | Parseval scaling of normalized bins; waveform variance equals band power (tests and run self-check) |
| Covariance | Synthesized bins against the model (sample covariance); exported waveforms against the model by Welch cross-spectra (tests; run self-check over three scenarios and three geometries) |
| Acquisition gain | Input referral of the S1 chain reproduces output-referred noise; a rounding quantizer matches Delta^2/12 (test) |
| Detector null distributions | Tonal and energy statistics against exact laws; matched-filter lags unit-exponential; normalized streams unit-variance and white (tests); exact thresholds on independent evaluation sets (run self-check) |
| False-alarm calibration | Disjoint calibration and evaluation sets; matched and mismatched noise (level, shape, coherence) |
| TDOA sign convention | Cross-correlation of synthesized waveforms: the element nearer the source leads by exactly the geometric delay (test) |
| Timing-error propagation | Synthesized random delays reproduce the closed-form coherent loss (test) |
| Trials versus independent samples | ADR-0015: windows are independent trials; bins, beams and lags are samples within a trial; common random numbers across SNR and candidates are stated |
| Low Pfa | Empirical thresholds only when n_cal x Pfa >= 10; otherwise exact laws or labeled union bounds; Pfa 1e-4 is a sensitivity objective |
| Unvalidated assumptions identified | Report Section 6 and `docs/assumptions.md`: noise spectra, spatial coherence, sensor transfer functions, host noise (not modeled), synchronization (not modeled) |
| Configuration, source revision, dependencies | `record.json` (resolved configuration, git state, package versions); requirements locks |
| No tuning on evaluation trials | Detector parameters fixed in the configuration; thresholds from calibration sets only |

## 4. Defects found and corrected during this cycle

* **Run self-check definition (recorded in `results/sim02b1/ERRATA.md`).** The run compared realized Pfa with a
  Wilson interval that covers only the evaluation set. For empirical thresholds the threshold is itself an order
  statistic of the calibration set, so the realized count is beta-binomial; the recorded figures (largest z 5.72,
  14.1 % of intervals excluding the target, bound upper limits up to 3.09 times the target) overstate the scatter. The
  exact test on the same rows shows calibration is consistent (Section 6, finding 8). No threshold, Pd or gain value is
  affected; the run self-checks use the exact laws from commit `7b63a3b` on.
* **Chirp leakage caught before the run.** The first B1 chirp (40 to 160 Hz, Tukey 0.2) put 0.59 % of its energy
  outside the 20 to 200 Hz band; the fail-visibly check refused it. The configuration of record uses 50 to 150 Hz with
  a 0.5 taper.
* **Trial budget.** The run took 98 minutes against a 75-minute estimate; B3 and 10 s windows use fewer calibration
  trials, so their Pfa 1e-3 thresholds rest on conservative union bounds. Reports flag these cells.

## 5. Reviewer decisions D01 to D06: disposition

| Decision | Disposition in SIM-02B.1 |
|---|---|
| D01 input provenance | Wenz-type ambient formulas (Stojanovic 2007, Eq. 6, citing Coates 1989) used with assumed shipping and wind; 64 sourced inputs registered with source, units, frequency range, applicability, uncertainty and provenance (`docs/input_provenance_register.md`); no integrated hydrophone used as a noise source because none publishes a self-noise spectrum; coherence kept assumption-labeled; Wenz 1962 and Coates not opened (publisher access) |
| D02 candidate set | Primary A0, A1, A2, P6-C, P8-C, A4 in every band and window; secondary P8-E, SQ4-C (four-element planar reference), V-C, V-D, V-DS at 1 s; all original candidates still configurable; none eliminated |
| D03 detection | Pfa 0.01 and 0.001 per window, 0.0001 as sensitivity (exact laws or bounds only); 0.1, 1, 10 s windows and 60 s coherent tonal; four signal classes; SNR conventions fixed in ADR-0015 before the run; independent positive and negative trials; searches inside the window statistic; no detection ranges |
| D04 synchronization | Deferred to SIM-02B.2 as planned |
| D05 AVS | Desk research and supplier data only (`docs/research/D05_avs_supplier_data.md`); recommendation: conditional go for a limited bench test (`docs/avs_feasibility.md` Section 6) |
| D06 criteria | -6.00 dB nominal; `reports/SIM-02A_criteria_D06.md` reports -6.0206 dB and changes of 0.5 and 1 dB around each criterion: the six-element circles fall from 2.37 to 1.73 at -6.0206 dB, every other candidate is stable; -1 dB structural ambiguity and the four Monte Carlo azimuths are kept for regression only; SIM-02B.1 uses 24 horizon azimuths for the beam search |

## 6. Principal SIM-02B.1 findings

All results are input-SNR ratios at one element under a published Wenz-type ambient shape with assumed coherence,
self-noise and signals; gains are at Pd = 0.5 and Pfa = 1e-3 with exact or empirical thresholds (report Section 0).

1. In ambient-limited isotropic noise below 200 Hz, no candidate up to 1.07 m beats A0: gains -0.2 to 0.8 dB, and 119
   of 120 intervals contain zero. Only the 4 m envelopes gain there (V-D 2.1 to 4.0 dB).
2. Above 200 Hz the arrays gain: 1.5 to 5.0 dB in B2 (0.1 and 1 s) and 3.5 to 7.4 dB in B3 (0.1 s) with beam search;
   P8-C reaches 8.0 to 9.0 dB in B3 with the direction known (limit 9.03 dB).
3. When sensor or flow-like noise dominates, the arrays gain in every band (B1, 1 s: 4.3 to 7.8 dB flow-like, 5.7 to
   9.0 dB sensor-limited). The low-band value of an array depends on measured noise coherence.
4. False-alarm control needs the noise level to well under 1 dB, for A0 and arrays alike: +1 dB turns a 0.01 target
   into 0.075 to 0.332 (energy detector 1.0). A wrong coherence assumption breaks array false-alarm control (realized
   Pfa 1.0 for beams when white noise is assumed under isotropic truth) while A0 is unaffected.
5. Thresholds are calibrated on independent evaluation sets (exact predictive tests; Bonferroni-adjusted smallest
   p-values 0.645 for exact and 1.0 for empirical thresholds).
6. P8-C's beam-search gain in B2 at 1 s equals integrating 2.06 times longer on A0 for tones and 5.36 times for
   broadband signals (stationary signals only).

No calibration, synchronization or host-noise effects are included yet (SIM-02B.2). Nothing here selects an
architecture or estimates a detection range.

## 7. Decisions requested before SIM-02B.2

1. **Adaptive noise estimation as the first SIM-02B.2 item**, with gains reported net of estimation loss (finding 4).
2. **Multi-sensor coherence data.** Whether to obtain measured coherence for Picket-like spacings (even a four-hydrophone
   collection) or to designate published data; until then the low-band array value stays assumption-bound.
3. **Ambient inputs.** Confirm reading the Coates formulas as dB re 1 uPa^2/Hz, and the shipping (0.5) and wind
   (5 m/s) scenario values, or name other scenarios.
4. **Synchronization model ranges** for shared and distributed clocks (offset, sample-rate mismatch, drift, jitter,
   resynchronization interval, interruptions), or approval to use assumption-labeled ranges.
5. **AVS bench test:** go or no-go on the conditional recommendation in `docs/avs_feasibility.md` Section 6.
6. **Trial budget at Pfa 1e-3** for 10 s windows and B3: accept conservative bounds there, fund larger calibration sets
   (roughly 3 to 5 times this run's compute), or approve a validated tail-estimation method.
7. **Beam search definition for SIM-02B.2:** beam spacing tied to beamwidth for the 1.07 m and 4 m layouts, and the
   worst-case directions to add to the 24 horizon azimuths.

## 8. Suggested review path (about 60 minutes)

1. This transmittal, Sections 6 and 7.
2. SIM-02B.1 report Section 0 (findings), Figures 1, 2 and 6, Section 6 (limitations) and Section 7.
3. `docs/input_provenance_register.md` and `tables/parameters_by_provenance.csv`, to confirm what is published and
   what is assumed.
4. `05_verification/snapshot_checks.txt` and `07_source/SOURCE.md`, for the SIM-02A closeout.
5. `docs/avs_feasibility.md` Section 6, for the D05 recommendation.
6. Optional: reproduce with `make sim02b1` (about 75 minutes on 4 cores) and `make sim02b1-claims`.
