# ADR-0012: Channel-error model and Monte Carlo statistics

Status: Accepted (SIM-02A)

## Decision
* Independent zero-mean Gaussian errors per channel: gain (in dB), phase, 3-D position, timing. The
  beamformer uses nominal values. Error levels are assumed scenarios plus one-at-a-time sweeps.
* Random streams are seeded per case from the configured base seed and a stable hash of the case key
  (NumPy `SeedSequence`), so results do not depend on loop order or on which cases run.
* Every Monte Carlo statistic is reported with a 95 % interval: means (normal approximation,
  n >= 200), quantiles (order-statistic binomial interval), proportions (Wilson interval). Rows whose
  relative half-width exceeds the configured target are flagged.
* Closed-form expectations for uniform weights (signal loss and null filling under Gaussian phase
  and log-normal gain errors) are verified in tests and recorded as run self-checks.

## Consequences
Calibration-induced azimuth errors are noise-free biases; errors caused by additive noise belong to
SIM-02B task-level experiments.
