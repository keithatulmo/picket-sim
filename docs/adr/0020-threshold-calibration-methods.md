# ADR-0020: Threshold calibration methods for low false-alarm probabilities

Status: Accepted (SIM-02B.2-A, reviewer decision D06)

## Decision
Thresholds are calibrated under the nominal design model and verified on independent evaluation trials. In order of
preference:

1. **Exact laws** (no sampling error):
   * TREF-CA, single stream, per bin: P(|y|^2 / G_hat > eta) = (1 + eta / M)^(-M).
   * TREF-OS (r-th of M), per bin: P = prod_{i=0}^{r-1} (M - i) / (M - i + eta).
   * Tonal maximum over K bins with independent per-bin estimates: 1 - (1 - p_bin)^K.
   * ORACLE single stream: Erlang (energy) and maximum of exponentials (tonal), as in SIM-02B.1.
   * ORACLE incoherent tonal: per-bin quadratic form (1/N) sum_i lambda_i E_i with lambda the eigenvalues of the
     normalized coherence, a hypoexponential law. Its survival function is evaluated exactly as the first-row sum
     of the matrix exponential of the bidiagonal phase-type generator (stable for equal or nearly equal weights),
     product over bins. Implementation note: this replaced the numerical characteristic-function (Imhof) inversion
     named in the draft, because for non-negative weights it is exact up to floating point and has no truncation or
     oscillatory-integrand error.
2. **Fast null simulation** for single-stream statistics without an exact law (energy, harmonic and matched-filter
   statistics with time or frequency references; FREF tonal): the statistic depends only on the complex test-window
   bins of one stream, independent CN(0, G) under the nominal model, and on the per-bin background estimates, whose
   nominal laws are known (G Gamma(M, 1/M) for TREF-CA; G (-ln(1 - B)), B ~ Beta(r, M - r + 1), for TREF-OS; FREF
   uses the test-window bins themselves). Drawing these directly is exact in distribution, costs far less than
   window synthesis, and supports 10^5 to 10^6 null samples. A test compares it with full synthesis.
3. **Conditional Monte Carlo** (Adler, Blanchet and Liu type) for maxima of correlated Gaussian magnitudes (oracle
   or nominal beam-search tonal statistic): sample an index in proportion to its marginal tail probability, sample
   the vector conditional on that exceedance, and average the inverse number of exceedances. Unbiased with bounded
   relative error. Used for the ORACLE and NOMINAL beam-search tonal thresholds at every Pfa, with common random
   numbers across trial thresholds (fixed draws, so the bisection sees no sampling noise between thresholds; the
   e^-eta factor makes the estimate decrease in eta), and checked against
   the sequential empirical threshold wherever that exists.
4. **Sequential empirical calibration** with full array synthesis for multichannel statistics without the above:
   draw batches until the order-statistic interval of the threshold is within the stated tolerance in dB
   (stopping rule) or the budget cap is reached; both are recorded.
5. **Union bounds** only where nothing else applies, always labeled as bounds.

Every threshold row records its method, sample size, interval and stopping reason. Pfa = 1e-4 is reported only from
methods 1 to 3.

## Consequences
Single-stream adaptive detectors get exact or high-precision thresholds at negligible cost; array synthesis budget
goes to multichannel statistics and evaluation sets (`docs/SIM-02B2A_plan.md` Section 6).
