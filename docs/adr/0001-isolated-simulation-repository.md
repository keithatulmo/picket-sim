# ADR-0001: Isolated simulation repository

Status: Accepted (SIM-01)

## Context
The `picket-sim` repository was empty when SIM-01 started. The handoff requires experimental
simulation code to stay separate from production software and from Fathom.

## Decision
`picket-sim` is a standalone, experimental research package (`picket_sim`). It contains no
production or embedded code, has no dependency on Fathom, and exposes no runtime service. Results
are evidence for trade studies, not deployable artefacts.

## Consequences
* Production code must not import `picket_sim`. If a numerical routine is later promoted to
  production it is re-implemented or copied under production review, with these tests as the
  reference.
* The repository can evolve quickly (new studies, new models) without production change control.

## Revisit when
A production signal-processing chain needs a shared, versioned reference library.
