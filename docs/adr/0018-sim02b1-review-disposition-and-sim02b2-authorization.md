# ADR-0018: SIM-02B.1 review disposition and SIM-02B.2 authorization

Status: Accepted (SIM-02B.1 technical review; run of record `20261108T125126Z_1c70e065_8dbe019`, reviewed commit
`8dbe019`, packaging baseline `a394c5e`)

## Context
The review accepted the SIM-02A closeout and SIM-02B.1 for its stated numerical scope. Its findings (compact-array
performance, coherence-dependent gain, beam-search penalties, false-alarm sensitivity) are conditional results of
the documented simulations. No measured Picket performance, architecture, detection range or hardware requirement
is established. The reviewer did not independently rerun the full SIM-02B.1 run of record.

## Decisions
1. **D01 adaptive noise estimation (approved; first SIM-02B.2 activity).** Compare reference-window, reference-bin
   and robust multichannel covariance estimation. Evaluate estimation loss, signal contamination, nonstationarity,
   mismatch, false-alarm stability and processing cost. The true simulated covariance is used only as an oracle
   upper bound. Training (reference), calibration and evaluation data are independent partitions with guard
   intervals (ADR-0019).
2. **D02 measured coherence (limited collection approved).** Prepare a synchronized multihydrophone collection plan
   that separates ambient coherence, structure-related interference and flow-associated effects. Published
   coherence measurements are interim references and are never labeled as Picket measurements. Numerical SIM-02B.2
   work does not wait for the collection; coherence-sensitive predictions may not set hardware requirements without
   empirical evidence.
3. **D03 ambient model (approved as nominal).** Wenz-type model, pressure PSD in dB re 1 uPa^2/Hz, shipping 0.5,
   wind 5 m/s nominal; sensitivity extended to other shipping, wind, spectral-shape and level conditions;
   provenance and limitations retained.
4. **D04 synchronization (assumption-labeled model approved, SIM-02B.2-C).** Shared and distributed clocks; residual
   offset, jitter, relative sample-rate error, drift, resynchronization, interruptions, persistent delay mismatch.
   Initial study ranges: shared clock offset 0 to 10 us, jitter 0.01 to 1 us; distributed clock offset 0.1 to
   100 us, jitter 0.01 to 10 us; relative frequency error 0.1, 1, 10, 50 ppm; resynchronization 1, 10, 60, 600 s;
   interruptions 0, 1, 10 s. Provisional analysis ranges, not hardware requirements.
5. **D05 AVS (direct expenditure deferred).** Continue evidence collection; no purchase or dedicated collection
   without separate authorization; a borrowed or loaned sensor may be proposed for a limited bench evaluation with
   explicit objectives and cost.
6. **D06 trial budget (targeted expansion).** Keep regression scenarios; prioritize accurate Pfa = 1e-3 calibration
   for architecture-relevant comparisons; use exact quadratic-form laws, validated numerical tail methods and
   importance sampling where appropriate; sequential Monte Carlo with explicit stopping rules; label any union bound;
   produce a compute budget and prioritized comparison list first; do not scale all 139 cases uniformly (ADR-0020,
   `docs/SIM-02B2A_plan.md` Section 6).
7. **D07 beam search (aperture-aware grid approved).** Keep the 24-beam horizon search for regression; develop
   frequency- and aperture-aware spacing with at most 0.5 dB worst-case straddle loss against a dense reference;
   include endfire, broadside, high-curvature regions, predicted ambiguity directions and directions between grid
   points; recalibrate thresholds whenever the search space changes; keep structural, noise-induced and
   calibration-induced errors distinct.
8. **Staging.** SIM-02B.2-A (adaptive noise estimation) first; its results are submitted for review before
   SIM-02B.2-B (broadband detection and bearing) and SIM-02B.2-C (timing and calibration robustness).
9. **Additional requirements.** A0 retained in every comparison; Pd 0.5 and Pfa 1e-3 reported for continuity, with
   Pd 0.9 and other Pfa where justified; per-window Pfa distinguished from false alerts per operating hour; no
   operational conclusions from stationary Gaussian noise alone; background estimates protected from target-bearing
   evaluation data; false-alarm, threshold and detection uncertainty reported separately; no detector access to
   simulation ground truth unavailable in operation.

## Consequences
SIM-02B.2-A detectors must operate on estimated statistics; oracle and nominal-model normalizers remain only as
baselines. Results stay conditional on the assumed coherence and Gaussian noise models.
