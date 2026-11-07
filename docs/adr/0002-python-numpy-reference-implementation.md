# ADR-0002: Python/NumPy reference implementation, minimal dependencies

Status: Accepted (SIM-01)

## Context
SIM-01 needs transparent, verifiable numerics more than speed. The models are closed-form or
cheap (N <= 16 elements, ~10^5 directions per pattern).

## Decision
Python >= 3.11 with NumPy for numerics, Matplotlib (Agg backend) for figures, PyYAML for
configuration, pytest for verification. SciPy is deliberately not used: the needed operations
(Gauss-Legendre nodes, bisection, sinc) are available in NumPy or are a few lines of code, and
avoiding SciPy keeps the dependency surface small. Exact versions of the canonical run are pinned
in `requirements.lock` and recorded in every run record.

## Consequences
* Special functions not in NumPy (e.g. Bessel J0 for cylindrically isotropic noise) will need
  SciPy or a local implementation when that model is added (future work).
* Performance is adequate for SIM-01 (full study in minutes on one CPU).

## Revisit when
Broadband time-domain simulation, large Monte Carlo studies or propagation codes make NumPy-only
performance inadequate.
