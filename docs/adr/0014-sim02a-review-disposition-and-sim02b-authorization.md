# ADR-0014: SIM-02A review disposition and SIM-02B authorization

Status: Accepted (SIM-02A technical review, reviewed baseline `31da01b`)

## Context
The SIM-02A technical review closed SIM-01, accepted SIM-02A as a numerical research increment for
its stated scope, and authorized SIM-02B in controlled stages. No production architecture, hardware
specification or operational detection claim is approved.

## Decision
1. **Closeout actions before the next review package** (reproducibility only; SIM-02A is not rerun):
   ship the source of the Revision A claims checker and criterion-margin generator; make the documented
   `make sim02a-claims` and `make sim02a-margin` commands work from the supplied snapshot; keep the 59
   claims checks and add automated verification of the supplementary tools; document the distinction
   between the run's code commit, later report-generation tools and the final source baseline; preserve
   all errata and immutable results. Implemented by `tools/build_review_package.py` (final-baseline
   archive with embedded run-of-record tables, tests at both commits, `--snapshot-check`),
   `tests/test_supplementary_tools.py`, `make sim02a-margin-check` and `docs/source_baselines.md`.
2. **D01 input provenance.** Published-reference scenarios from Wenz-derived envelopes, calibrated
   passive-acoustic datasets, manufacturer documentation, vessel-noise experiments and flow-noise
   measurements. Each numerical input records source, units, frequency range, applicability,
   uncertainty and provenance (ADR-0017). An integrated active hydrophone is not equated with the
   bare-element model without a documented equivalent transfer function. Spatial coherence is never
   inferred from single-channel spectra. Assumption-labeled envelopes remain where published data are
   insufficient.
3. **D02 candidate set.** Primary: A0, the A1/A2 linear family, P6-C, P8-C, A4. Secondary: P8-E, a
   four-element planar reference (SQ4-C, footprint-matched to the compact circles; A3 remains
   configurable), and the volumetric envelopes V-C, V-D, V-DS. No elimination on incomplete Pareto
   attributes.
4. **D03 detection experiments.** Pfa 0.01 and 0.001 per explicitly defined decision opportunity;
   0.0001 as a sensitivity objective with justified estimation; 0.1, 1 and 10 s integration windows and an
   optional 60 s coherent tonal experiment; single-tone, harmonic, broadband and transient/chirp signal
   classes; Pd at fixed Pfa with uncertainty; SNR conventions fixed before experimentation (ADR-0015);
   independent positive and negative trials; overlapping windows, frequency searches and beam searches
   accounted for. No detection-range estimates.
5. **D04 synchronization.** Shared-clock and distributed-clock models (offset, sample-rate mismatch,
   drift, jitter, periodic resynchronization, interruptions) are SIM-02B.2 work. Requirements are
   reported as conditional performance budgets.
6. **D05 acoustic vector sensors.** Desk research and documented supplier data only; a go/no-go
   recommendation for a future bench test. No purchase and no dedicated collection.
7. **D06 criteria.** -1 dB structural ambiguity is a regression convention only. The original four
   Monte Carlo azimuths are kept for regression; principal studies use at least 24 horizon azimuths plus
   targeted worst-case directions. The nominal -6 dB criterion is exactly -6.00 dB in power; sensitivity
   to -6.0206 dB (half amplitude) and to larger criterion changes is reported
   (`reports/SIM-02A_criteria_D06.md`). Narrowband sidelobe criteria are not substitutes for task-level
   performance.
8. **Staging.** SIM-02B.1 (signal and detection-model foundation) is implemented, verified and submitted
   for review before SIM-02B.2 (broadband bearing, TDOA, synchronization, joint error effects, expanded
   steering) begins.

## Consequences
SIM-02B.1 results are research results under stated assumptions. Hardware requirements and production
architecture selection remain gated on evidence with demonstrated applicability to the intended
physical system.
