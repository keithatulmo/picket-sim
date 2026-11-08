# SIM-02A Closeout and SIM-02B.1 Review Transmittal

**Ulmo / Picket, PCK-SIM-001: SIM-02A reproducibility closeout and SIM-02B.1 signal and detection-model foundation**

| | |
|---|---|
| To | Author of the SIM-02A technical review and SIM-02B authorization |
| Subject | SIM-02A closeout actions and SIM-02B.1 numerical results for review |
| Date | 2026-11-08 |
| Repository | `keithatulmo/picket-sim`, branch `claude/beautiful-darwin-vbeoue` |
| SIM-02B.1 run of record | `{RUN_ID}` (code commit `{CODE7}`, clean tree) |
| Prepared by | Claude Code (AI-generated engineering work product). Requires review by a qualified acoustic engineer before any of it informs requirements. |
| Requested action | Confirm the SIM-02A closeout; review the SIM-02B.1 results; decide the items in Section 7 before SIM-02B.2 begins |

## 1. SIM-02A closeout actions (review Section 2)

| # | Action | Evidence |
|---|---|---|
| 1 | Include the source of the Revision A claims checker and criterion-margin generator | Both are in the final-baseline source archive `07_source/picket-sim_{HEAD7}_baseline.tar.gz`; `tools/check_sim02a_claims.py`, `tools/sim02a_criterion_margin.py` |
| 2 | Make `make sim02a-claims` and `make sim02a-margin` work from the supplied snapshot | The baseline archive embeds the SIM-01, SIM-02A and SIM-02B.1 run-of-record records and tables. The package builder unpacked it (no `.git`) and ran `make sim02a-claims`, `make sim02a-margin-check` (regenerates the supplement and requires byte-identical CSV files) and `make sim02a-repro-check` (reruns SIM-02A and requires every run table to be byte-identical to the run of record). Log: `05_verification/snapshot_checks.txt`. `make sim02a-margin` still writes into `reports/`; the `-check` form is the one to use in a snapshot |
| 3 | Keep the 59 claims checks; add automated verification of the supplementary tools | `tests/test_supplementary_tools.py` (16 tests): the 59 checks pass and are counted; the checker fails on the Revision 0 documents (kept as fixtures) and on a single changed number; plateau, knife-edge, reproduction self-check, byte comparison and snapshot provenance of the margin generator; an end-to-end generator run on the smoke configuration; the table-comparison tool |
| 4 | Document the code commit, later report-generation tools and the final source baseline | `docs/source_baselines.md`; `07_source/SOURCE.md` (generated: both archives, commit list and changed files); tests run at both commits (`05_verification/pytest_log.txt`, `pytest_log_baseline.txt`) |
| 5 | Preserve all errata and immutable results | No run directory or delivered package was changed. `results/sim02a/ERRATA.md` unchanged in this cycle |

D06 criterion sensitivity on the SIM-02A run of record: `reports/SIM-02A_criteria_D06.md` (self-checked
against the run tables). See Section 5.

## 2. SIM-02B.1 deliverables (review Section 7)

| # | Required output | Evidence |
|---|---|---|
| 1 | Updated implementation plan and architecture decisions | `docs/SIM-02B_plan.md`; ADR-0014 to ADR-0017 (written before implementation) |
| 2 | Verified SIM-02B.1 results before SIM-02B.2 | Run of record `{RUN_ID}` with self-checks; SIM-02B.2 not started |
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

{DEFECTS}

## 5. Reviewer decisions D01 to D06: disposition

{DISPOSITION}

## 6. Principal SIM-02B.1 findings

{FINDINGS}

## 7. Decisions requested before SIM-02B.2

{DECISIONS}

## 8. Suggested review path (about 60 minutes)

1. This transmittal, Sections 6 and 7.
2. SIM-02B.1 report Section 0 (findings), Figures 1, 2 and 6, Section 6 (limitations) and Section 7.
3. `docs/input_provenance_register.md` and `tables/parameters_by_provenance.csv`, to confirm what is published and
   what is assumed.
4. `05_verification/snapshot_checks.txt` and `07_source/SOURCE.md`, for the SIM-02A closeout.
5. `docs/avs_feasibility.md` Section 6, for the D05 recommendation.
6. Optional: reproduce with `make sim02b1` (about 75 minutes on 4 cores) and `make sim02b1-claims`.
