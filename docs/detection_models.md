# SIM-02B.1 signal, noise and detection models

Model documentation for `signals.py`, `synthesis.py`, `detectors.py`, `detection.py`, `environment.py` and
`experiments/sim02b1.py`. Decisions: ADR-0015 (SNR conventions, decision opportunities, thresholds),
ADR-0016 (synthesis), ADR-0017 (inputs). Units: pressure uPa, PSD uPa^2/Hz (one-sided), frequency Hz, time s.

## 1. Observation model

A window of T seconds sampled at the band rate fs gives N = T fs samples and DFT bins f_k = k / T. Only
bins inside the analysis band are kept. Bins are scaled to *normalized units*

    x_k = X[k] / (fs sqrt(T / 2)),   X[k] = sum_n x[n] exp(-j 2 pi k n / N),

so that stationary noise has E[x_k x_k^H] = C(f_k), the cross-spectral density matrix, and for a deterministic
signal sum_k |x_k|^2 / G_n(f_k) = E/N0_eff (ADR-0015). The exported waveform is the inverse real FFT of the band
bins: the ideally band-pass-filtered sampled waveform.

## 2. Noise

    C(f) = G_amb(f) Gamma(f) + G_self(f) I

* G_amb: Coates/Wenz-type envelope (Stojanovic 2007, Eq. 6), f in kHz, linear sum of
  17 - 30 log f; 40 + 20 (s - 0.5) + 26 log f - 60 log(f + 0.03); 50 + 7.5 w^(1/2) + 20 log f - 40 log(f + 0.4);
  -15 + 20 log f (dB re 1 uPa^2/Hz), with s = 0.5 and w = 5 m/s (assumed). At 1 kHz this gives 60.95 dB.
* Gamma: spherically isotropic sinc(2 f d / c); exponential exp(-d / L), L = 0.1 m; white I (mismatch tests).
* G_self: SIM-02A S1 chain referred to input, or 100 G_amb (sensor-limited condition).
* x_k = F_k w_k with F_k F_k^H = C(f_k) (eigendecomposition after a Hermitian positive-semidefinite check),
  w_k standard circular complex Gaussian, independent across bins and windows.

## 3. Signals (0 dB input SNR at one element, then scaled by 10^(SNR/20))

| Class | Definition | Exact bins |
|---|---|---|
| Tone | A cos(2 pi f0 (t - tau_n) + phi), A = sqrt(2 G_n(f0)), f0 uniform in [f_lo + 2/T, f_hi - 2/T], phi uniform | Dirichlet kernel of the sampled finite sinusoid, both frequency terms |
| Harmonic | four tones at h f0 (h = 1..4), each with A_h = sqrt(2 G_n(h f0)), independent phases | sum of tone bins |
| Broadband | Gaussian plane wave with flat PSD G_s over the band, G_s = (1/B) integral of G_n (band SNR = 1) | s_k ~ CN(0, G_s) times exp(-j 2 pi f_k tau_n) |
| Chirp | Tukey-tapered LFM, scaled so that 2 integral abs(S)^2 / G_n df = 1, arrival t0 uniform in the window (6 ms margins) | DFT of the sampled pulse times exp(-j 2 pi f_k (t0 + tau_n)) |

tau_n = -(u . r_n) / c, u the unit vector toward the source (horizon, azimuth uniform per trial).

## 4. Processing modes and detectors

Normalization with the assumed covariance C_a: z_k = w^H x_k / sqrt(w^H C_a(f_k) w).

* single: w = e_0 (A0).
* beam_known: w = a(u_true) / N, the DAS beam at the true direction (upper bound; the direction is not known
  in practice).
* beam_search: 24 DAS beams at 0, 15, ..., 345 deg azimuth; the statistic is the maximum over beams.
* incoherent: each element normalized by its own PSD; per-bin powers averaged over elements.

| Detector | Statistic | Exact H0 law (single stream, matched noise) |
|---|---|---|
| tonal | max_k abs(z_k)^2 | P(> x) = 1 - (1 - e^-x)^K |
| harmonic | max over f0 (grid 1/(4T)) of sum_h abs(z)^2 at round(h f0 T) | none (overlapping sums); empirical or union bound Gamma(4,1) over fundamentals |
| energy | sum_k abs(z_k)^2 | Gamma(K, 1) |
| mf | max over 2K lags of abs(sum_k z_k s_k^* e^(j 2 pi f_k tau))^2 / sum abs(s_k)^2 | none (correlated lags); union bound Exp(1) over lags |

Beam search adds a Bonferroni factor of 24 for bounds. Incoherent bounds use q_k <= (lambda_max,k / N) Gamma(N, 1)
with lambda_max,k the largest eigenvalue of the normalized coherence (valid, conservative when channels
are correlated).

## 5. Thresholds, false alarms and detection statistics

* Calibration (thresholds), evaluation (realized Pfa) and positive (Pd) trial sets are disjoint and independently
  seeded. Threshold preference: exact, then empirical order statistic when n_cal Pfa >= 10, then union bound.
* Realized Pfa: exceedances on the evaluation set, Wilson 95 % interval.
* Pd: exceedances on the positive set at each SNR, Wilson interval widened by evaluating Pd at the ends of the
  threshold's order-statistic interval.
* SNR required for Pd = 0.5 and 0.9: linear interpolation in dB; intervals from the Pd interval curves.
* Detection gain over A0 = SNR_req(A0) - SNR_req(candidate, mode), interval [lo_A0 - hi_c, hi_A0 - lo_c].
* SNR grids are centred on an analytic A0 operating point at Pfa 1e-3 and span -18 to +8 dB around it in 2 dB
  steps; points outside the grid are reported as censored, never extrapolated.

## 6. Verification

`tests/test_sim02b1_models.py` and `tests/test_sim02b1_pipeline.py` (signals against direct DFTs, Parseval,
covariance against sample and Welch estimates, acquisition-chain referral and quantization, TDOA sign by
cross-correlation, timing-error closed form, null laws, false-alarm calibration, bound conservatism,
configuration failures, common source parameters, identical results for 1 and 2 worker processes). Run
self-checks: covariance against the time-series CSD, exact-threshold and empirical-threshold calibration on the
evaluation sets, bound conservatism, clipping headroom, provenance counts.
