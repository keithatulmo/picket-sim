# ADR-0010: Parameter provenance (published, measured, assumed)

Status: Accepted (SIM-02A)

## Context
SIM-02 introduces sensor, acquisition, ambient, host and error parameters. The authorization requires
a strict distinction between published, measured and assumed values and forbids presenting assumed
noise curves as representative measurements.

## Decision
* Every physical parameter in a SIM-02 configuration is a record `{value, unit, provenance, source}`.
  `provenance` is one of `published`, `measured`, `assumed`. `source` is mandatory: a citation for
  published values, a data reference for measured values, a rationale for assumed values.
* Loading rejects missing or unknown provenance, missing source, unit mismatches and out-of-range
  values. Scenario names for assumed sets start with a label that marks them as assumptions.
* Each run writes `parameters_by_provenance.csv` and the report reproduces the table.
* SIM-02A contains no measured values. Published values are limited to defined physical constants
  (Boltzmann constant, SI definition). Ambient, sensor, host and error levels are assumed scenarios,
  and results are presented as functions of their ratios wherever possible.

## Consequences
Numbers that depend on assumed levels are labeled as scenario results. Replacing an assumed value
with a measured or published one changes its provenance tag and the configuration hash.
