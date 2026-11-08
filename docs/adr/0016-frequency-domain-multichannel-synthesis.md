# ADR-0016: Frequency-domain multichannel synthesis with waveform access

Status: Accepted (SIM-02B.1)

## Decision
* A trial is one observation window of T seconds sampled at the band's processing rate fs
  (N = round(T fs) samples). It is represented by the DFT bins inside the analysis band,
  f_k = k / T, scaled so that a stationary noise bin has covariance equal to the cross-spectral density
  matrix C(f_k) in uPa^2/Hz: x_k = X[k] / (fs sqrt(T / 2)).
* **Noise**: x_k ~ CN(0, C(f_k)) independently per bin, with
  C(f) = G_amb(f) Gamma_field(f) + G_self(f) I (+ G_flow(f) Gamma_flow(f)) (+ host terms). This is exact for a
  periodic (circular) stationary process band-limited to the analysis band. Gamma_field uses the closed
  forms of SIM-02A (spherical sinc, horizontal J0, exponential, white), evaluated per bin. Every C(f_k) passes
  `noisefields.check_covariance`; the square root is taken by eigendecomposition after that check.
* **Signals** are computed exactly as sampled-data DFTs: tones and harmonics by the Dirichlet kernel of the
  sampled finite sinusoid (positive- and negative-frequency terms), broadband signals as rank-one
  Gaussian bins along the steering vector, chirps by the DFT of the sampled, tapered waveform. A plane
  wave from unit direction u reaches element n with delay tau_n = -(u . r_n) / c (ADR-0003), i.e. bin factor
  exp(-j 2 pi f_k tau_n) = exp(+j k u . r_n).
* **Waveform access**: any trial can be rebuilt from its seed key and converted to a real multichannel time
  series by an inverse real FFT of the band bins (`synthesis.to_waveform`), which is the ideally band-pass
  filtered sampled waveform. Example waveforms are written with every run.
* **Verification**: the time-series cross-spectral matrix (Welch estimate) of synthesized noise is
  compared with C(f) as a run self-check and a test; tone and chirp spectra are compared with direct
  time-domain DFTs; the TDOA sign is checked by cross-correlating synthesized waveforms.

## Consequences
Linear processing (beamforming, matched filtering) operates on the same bins without re-sampling.
Out-of-band leakage of real windows is excluded by construction; detectors see only band bins.
Non-stationary noise and non-circular edge effects are outside this model.
