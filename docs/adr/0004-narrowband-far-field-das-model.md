# ADR-0004: Narrowband far-field plane-wave model with conventional DAS

Status: Accepted (SIM-01)

## Decision
SIM-01 models single-frequency plane waves in a homogeneous, lossless, unbounded medium with
configurable sound speed (nominal 1500 m/s), ideal omnidirectional point hydrophones, and
conventional (uniformly weighted) delay-and-sum beamforming. Patterns are normalized to the
steered response (`P(u0) = 1` exactly), never to the maximum of a sampled grid.

## Rationale
This is the textbook baseline against which every non-ideal effect will later be measured. It
isolates geometry from everything else, which is the purpose of SIM-01.

## Consequences
* Results are upper bounds or idealizations: they are not detection performance and do not
  include sensor noise, calibration errors, element directivity, self-noise, multipath or
  boundaries.
* Narrowband aliasing results overstate ambiguity for broadband processing (grating lobes move
  with frequency, the mainlobe does not); broadband/TDOA analysis is future work.
* Adaptive and superdirective processing can exceed DAS directivity for compact arrays at the cost
  of white-noise gain; not evaluated in SIM-01.
