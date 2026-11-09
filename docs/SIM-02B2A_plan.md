# PCK-SIM-001 / SIM-02B.2-A Technical Implementation Plan: Adaptive Noise Estimation

Plan of record, written before implementation. Authority: SIM-02B.1 review (ADR-0018). Decisions: ADR-0019
(normalizers, partitions, ground-truth isolation), ADR-0020 (calibration). SIM-02B.2-B and -C start only after the
SIM-02B.2-A results are reviewed.

## 1. Objective and exit requirement

Determine how much of the SIM-02B.1 detection performance remains when detectors estimate the background from data
instead of being told it. Exit requirement (review Section 3): demonstrated false-alarm control with estimated
background statistics, with the detection loss quantified, against the A0 and oracle baselines.

## 2. Governing equations

Stream y (A0 element, DAS beam w^H x, or one element), bin k of the test window. Statistic inputs
u_k = |y_k|^2 / G_hat_k, then the SIM-02B.1 detectors (tonal maximum, harmonic sum, energy sum, matched filter on
y_k / sqrt(G_hat_k)).

* TREF-CA: G_hat_k = (1/M) sum_{m=1..M} |y_k^(t-g-m)|^2. Stationary Gaussian noise: |y_k|^2 / G_hat_k has
  P(> eta) = (1 + eta/M)^(-M) for every true level (CFAR). Beam domain: G_hat = w^H S_hat w, S_hat the sample
  covariance of the M reference windows.
* TREF-OS: G_hat_k = x_(r), the r-th smallest of the M reference powers; P(|y_k|^2 > eta x_(r)) =
  prod_{i=0..r-1} (M - i) / (M - i + eta).
* FREF-CA: G_hat_k = (1/|R_k|) sum_{j in R_k} |y_j|^2, R_k = {k-G-L..k-G-1} union {k+G+1..k+G+L} within the band
  (2L bins taken from one side at band edges).
* FREF-OS: G_hat_k = r-th smallest of the same 2L powers.
* CFAR loss for a tonal maximum over K bins at window Pfa p: per-bin p_b = 1 - (1 - p)^(1/K); oracle threshold
  -ln p_b; TREF-CA threshold M (p_b^(-1/M) - 1); loss 10 log10 of their ratio for a strong tone.
* False alerts per operating hour for one detector on non-overlapping windows: p x 3600 / T.

## 3. Experiment design (configuration `configs/sim02b/sim02b2a_baseline.yaml`)

* Candidates: A0, A1 (line), P8-C (compact planar), A4 (distributed reference).
* Cells: C1 = B2 (200 Hz to 2 kHz), 1 s windows (primary); C2 = B1 (20 to 200 Hz), 1 s; C3 = B3 (2 to 10 kHz), 0.1 s.
* Modes: single (A0), beam search over the 24-beam regression grid, incoherent. Beam-known is not carried forward
  (direction unknown in operation; bearing is SIM-02B.2-B).
* Signal classes and detectors as SIM-02B.1 (tone, four-harmonic set, broadband, chirp in C1 and C3). The energy
  detector is not combined with frequency-reference normalizers: a broadband signal occupies its own reference bins,
  so such a normalizer cancels the signal it is meant to reveal (stated, not simulated).
* Normalizers: ORACLE, NOMINAL, TREF-CA (M = 16, guard g = 2), TREF-OS (M = 16, r = 12, g = 2), FREF-CA (L = 8, G = 2),
  FREF-OS (L = 8, G = 2, r = 12). A0 additionally: TREF-CA with M = 4, 8, 32, 64 (CFAR loss against M).
* Scenarios (truth of reference and test windows; thresholds always from the nominal design):
  * STAT: nominal, stationary (regression with SIM-02B.1).
  * SHAPE-HI / SHAPE-LO: Wenz-type spectrum with shipping 1.0 and wind 10 m/s, and shipping 0.0 and wind 2.5 m/s
    (D03).
  * STEP+1 / STEP+3: test window 1 or 3 dB above its reference windows (rapid level change).
  * INTERF: each reference window independently contains, with probability 0.25, a plane-wave Gaussian interferer
    from a random horizon azimuth at 10 dB above the ambient spectrum (intermittent interference).
  * CONTAM: positive trials whose target started r windows before the test window, r uniform on 0 to 24; reference
    windows inside that interval contain the target. TREF guards of 2 and 8 windows are compared.
  * COH: flow-like truth (exponential coherence, L = 0.1 m) under the isotropic nominal design (C1 and C2).
  * C2 runs STAT, STEP+3 and COH; C3 runs STAT.

## 4. Statistics and reporting

Separate seed streams for calibration, evaluation-null and positive trials; reference windows are generated inside
each trial. Reported separately: false-alarm uncertainty (Wilson interval of realized Pfa), threshold uncertainty
(order-statistic interval or method precision, also in dB), detection uncertainty (binomial Pd interval), and the Pd
range induced by the threshold interval. Pd = 0.5 and 0.9 at Pfa = 1e-3 (continuity), Pfa = 1e-2 and 1e-4 where the
calibration method supports it. Per-hour false-alert rates accompany every Pfa. Detection loss = SNR required with a
normalizer minus SNR required with ORACLE, same mode, class and trials.

## 5. Verification

Independent tests: exact CFAR laws against simulation (TREF-CA, TREF-OS, tonal maximum); FREF estimators against
direct sliding-window computation; conditional Monte Carlo against brute force; the hypoexponential survival function (matrix exponential of the phase-type
generator) against closed forms and simulation; sequential stopping rule; nonstationary, interference and contamination generators against
their definitions; ground-truth isolation (normalizer functions take data arrays only). Run self-checks: exact and
fast-simulation thresholds against full-synthesis evaluation sets (STAT), conditional Monte Carlo against
empirical calibration. After the run, `tools/sim02b2a_b1_regression.py` compares ORACLE results in STAT C1 with
the SIM-02B.1 run of record (same candidate, mode, class, Pfa and Pd).

## 6. Compute budget and prioritized comparisons (D06)

Priority 1 (architecture-relevant, accurate calibration at Pfa = 1e-3): A0, A1, P8-C, A4 in C1; tone and broadband;
beam search and incoherent; TREF-CA, TREF-OS, FREF-OS against ORACLE; STAT, STEP+1, INTERF, COH. Priority 2: harmonic
and chirp, FREF-CA, NOMINAL, SHAPE and STEP+3, CONTAM. Priority 3: C2 and C3.

Budget rule: thresholds are calibrated once per candidate, cell, normalizer, mode and detector under the nominal
design (exact or fast methods where possible; sequential array calibration otherwise, stopping when the threshold
interval at Pfa = 1e-3 is within 0.25 dB or at the cap), and every scenario then needs only evaluation trials. The
numerical budget, measured on this machine before the run of record, is in Section 7.

## 7. Measured budget

Measured on the 4-core run machine with four concurrent single-thread processes (the run's own load), after two
implementation speedups (batched matrix products for beamforming; time-reference estimates computed once per positive
trial and reused for every SNR point, since they do not depend on the test window when the target is absent from the
reference windows). The run's `tables/case_timings.csv` is the authoritative record.

| Unit of work | C1 (K = 1801) | C2 (K = 181) | C3 (K = 801) |
|---|---|---|---|
| Array noise-only trial (test + 18 reference windows, all normalizers, modes, detectors): P8-C; A1, A4 | 98 ms; 97, 99 ms | 11 ms | 38 ms |
| Array positive trial (4 classes x 12 SNR points): P8-C; A1, A4 | 1.34 s; 1.13, 1.11 s | 0.15 s | 0.37 s |
| ORACLE exact quadratic form and conditional Monte Carlo thresholds, one array | 40 to 50 s | 8 s | 18 s |
| A0 fast null simulation, 10,000 samples (10 normalizers, 4 detectors) | 50 s | | |

Projection for the baseline configuration (12 calibration and 48 evaluation cases): sequential array calibration runs
to the 20,000-trial cap in C1 (about 2,000 s per array; 20 expected exceedances at Pfa = 1e-3 give an order-statistic
interval wider than 0.25 dB), about 9,500 core-seconds of calibration in total; evaluation about 27,000 core-seconds,
dominated by C1 positive trials (about 500 s per array and scenario) and C1 noise-only trials (980 s per array for
STAT at 10,000 trials, 390 s for the other scenarios at 4,000). Total about 10 core-hours, 2.5 to 3 hours on 4 cores.

What is deliberately not bought (D06):

* Adaptive array thresholds at Pfa = 1e-4. Empirical calibration needs n p >= 10, so at least 100,000 nominal trials
  per array and cell; in C1 that is about 9,800 core-seconds per array for the bare minimum and several times more
  for a 0.25 dB interval. These rows are reported as "not estimated". ORACLE and NOMINAL array thresholds at 1e-4 come
  from the exact quadratic form and conditional Monte Carlo; A0 thresholds at 1e-4 come from exact laws or the fast
  null simulation (100,000 samples, n p = 10 at the minimum).
* Repeating all 139 SIM-02B.1 cases with larger trial counts. The SIM-02B.1 run took about 100 minutes on 4 cores
  at its counts; a tenfold expansion would cost about 17 hours and would buy precision on comparisons that this stage
  supersedes (oracle normalization).
* Beam-known mode (direction is unknown in operation) and the 0.1 s and 10 s windows in B2 (the 1 s cell carries the
  comparison; window-length dependence of the CFAR loss is given exactly by the closed form in Section 2).

## 8. Other reviewer decisions in this stage

D02: `docs/coherence_collection_plan.md` (collection plan; no collection performed). D03: SHAPE and STEP scenarios.
D04: SIM-02B.2-C. D05: evidence file kept current; loaned-sensor bench proposal outline in `docs/avs_feasibility.md`.
D07: aperture-aware search grid in SIM-02B.2-B; SIM-02B.2-A keeps the 24-beam regression grid.
