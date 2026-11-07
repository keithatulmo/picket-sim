# ADR-0005: Metric definitions, observable space, undefined metrics

Status: Accepted (SIM-01)

## Context
Classical metrics (beamwidth, sidelobe level) are defined for linear arrays in one angle. Picket
candidates include a single hydrophone (no pattern), lines (cone ambiguity), a plane (mirror
ambiguity) and a volumetric array. Forcing one metric onto all of them produces misleading
numbers (e.g. a 0 dB "sidelobe" that is really the cone ambiguity of a line array).

## Decision
1. Classify geometric ambiguity exactly from the rank of the sensor-difference span.
2. Compute sidelobe and aliasing metrics in the *observable* space (the projection of the
   direction onto that span), so geometric ambiguity is excluded and reported separately.
3. Report geometry-agnostic quantities that include all ambiguity: half-power sphere fraction,
   pattern minimum, DI, and beamwidths/lobes along the horizontal and vertical great-circle cuts.
4. A metric that is undefined for a configuration (no sidelobe region, half-power region wrapping
   a full cut, any metric of a single omnidirectional sensor) is stored as NaN/empty with a
   reason string, never as a number.
5. Mainlobe of a 1-D profile: the connected region around the steering point bounded by the first
   local minimum on each side. Half-power width: the connected region around the steering point
   with `P >= 0.5`.

## Consequences
Numbers are comparable across geometries only for metrics defined for all of them; the report
states which comparisons are meaningful.
