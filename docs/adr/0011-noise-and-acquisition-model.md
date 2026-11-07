# ADR-0011: Noise covariance and acquisition-chain model

Status: Accepted (SIM-02A)

## Decision
* Noise is represented by its narrowband cross-spectral density matrix at each frequency, built
  from components (white, spherically isotropic, horizontally isotropic, directional density on the
  sphere, short-correlation exponential, near-field host point sources, far-field interferers). Each
  homogeneous component has a unit-diagonal coherence matrix scaled by its spectral level.
* Sensor self-noise is input-referred to pressure through the nominal sensitivity: hydrophone
  thermal noise, preamplifier voltage and current noise, and ADC quantization.
* Channel errors act on everything that passes through the channel (acoustic noise and hydrophone
  thermal noise); electronic noise added after the sensitivity element is unaffected by sensitivity
  error; timing error acts on all components after sampling.
* Every matrix is checked for Hermitian symmetry and positive semidefiniteness; directional
  densities are integrated with a Gauss-Legendre sphere grid whose exact degree must exceed
  k x aperture plus a margin, otherwise the run fails rather than returning an inaccurate matrix.
* The comparison metric is the realized array gain relative to a single identical channel (A0) in
  the same noise model, which reduces exactly to WNG (white) and DI (isotropic, no sensor noise).

## Consequences
Array gain and detection performance stay separate: SIM-02A reports SNR ratios only. Detection
statistics at fixed false-alarm rates are SIM-02B.
