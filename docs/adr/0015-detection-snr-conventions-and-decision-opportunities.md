# ADR-0015: Detection SNR conventions, decision opportunities and false-alarm estimation

Status: Accepted (SIM-02B.1). Fixed before any detection experiment was run.

## SNR conventions
All SNRs are **input SNRs at a single element**: signal and noise referred to acoustic pressure at the
hydrophone input (the A0 element, or any one element of an array), with the noise including every
modeled component at that element (ambient, sensor self-noise and electronics referred to input,
quantization referred to input, host and flow components where present). Array-output SNR is never an
input variable; array benefit appears as a change in detection performance at the same input SNR.

| Signal class | Convention | Reference bandwidth |
|---|---|---|
| Single tone | SNR_1Hz = tone power / G_n(f_tone) | 1 Hz (dB re 1 Hz) |
| Harmonic set | SNR_1Hz of each harmonic (equal per-harmonic SNR by construction) | 1 Hz per harmonic |
| Broadband | in-band SNR = integral of G_s over the signal band / integral of G_n over the same band | the signal band |
| Transient (LFM chirp) | E/N0_eff = 2 x integral over f > 0 of abs(S(f))^2 / G_n(f) | noise-weighted; equals E/N0 for white noise |

G_n is the one-sided noise PSD at one element (uPa^2/Hz), S(f) the Fourier transform of the pressure
signal. The equal-SNR harmonic construction is a convention for interpretability, not a physical claim.

## Decision opportunity and Pfa
* One decision per **non-overlapping observation window** of duration T (0.1, 1, 10 s; 60 s coherent
  tonal option) per detector and processing mode. Every internal search is inside the decision
  statistic as a maximum: frequency bins (tonal), fundamental frequencies (harmonic), arrival lags
  (matched filter), and steering directions (beam search). Pfa is the probability that this window
  statistic exceeds the threshold under H0. A false-alarm rate per hour for non-overlapping windows is
  Pfa x 3600 / T; overlapping windows are correlated and would need their own calibration (not done).
* H0: noise only, from the stated true noise model. H1: the same noise model plus one signal from the
  stated class, with source parameters (frequency, phase, arrival time, azimuth) drawn per trial.

## Trials and independence
* Every trial is an independent window with its own random stream (`stats.case_rng`, keyed by case,
  set and trial chunk). Bins, beams and lags inside a trial are samples of one realization, not trials.
* Three disjoint trial sets: **calibration** null trials (thresholds), **evaluation** null trials
  (realized Pfa) and **positive** trials (Pd). Detector parameters (search grids, number of harmonics,
  templates, beam set) are fixed in the configuration before any trial is generated; nothing is tuned on
  evaluation or positive trials.
* Common random numbers: within a positive set, the same noise realization and source parameters are
  reused across the SNR grid (so Pd curves are monotone), and the same source parameters are used for
  every candidate (paired comparison under identical source conditions). Pd values at different SNRs of
  one curve are therefore not independent; each Pd value carries its own binomial interval.

## Thresholds
In order of preference for each (detector, processing mode, case):
1. **Exact** null distribution under matched noise where it exists: normalized single-stream energy
   detector (Erlang/Gamma(K, 1)); single-stream tonal maximum over K independent bins
   (1 - (1 - exp(-x))^K).
2. **Empirical** order-statistic quantile of the calibration set when n_cal x Pfa >= 10, with its
   binomial interval.
3. **Union bound** (Bonferroni across correlated streams or lags, exact product across independent
   bins) when neither applies; flagged "bound" and conservative by construction.
Pfa = 1e-4 uses (1) or (3) only and is reported as a sensitivity objective; where an empirical check at
1e-2 and 1e-3 shows the bound's conservatism, it is reported.

## Uncertainty
Realized Pfa: Wilson interval on the evaluation set. Pd: Wilson interval, widened by evaluating Pd at
the two ends of the threshold's order-statistic interval. SNR required for Pd = 0.5 and 0.9 is
interpolated in dB on the curve and on its lower and upper bounds. Detection gain relative to A0 is
SNR_req(A0) - SNR_req(candidate) with the conservative interval [lo_A0 - hi_c, hi_A0 - lo_c].
