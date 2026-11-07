# ADR-0008: SIM-01 review disposition and documentation corrections

Status: Accepted (SIM-01 technical review, review baseline commit `8043684`)

## Context
The SIM-01 technical review accepted the verification approach, reproducibility controls, analytical
comparisons, handling of geometric ambiguity and preservation of historical results. It accepted the
principal findings within the model assumptions, selected no architecture, and required five
documentation corrections before closing SIM-01, without altering historical experimental results.

## Decision
SIM-01 is closed on report Revision A. The corrections and where they are applied:

| # | Correction | Applied in |
|---|---|---|
| 1 | 6.02 dB is the white-noise gain of four equally weighted elements, not an absolute bound on array gain | Report Rev A Sections 0, 4.2, 5.1; transmittal Rev A Section 2 |
| 2 | f_HP is a -3 dB discrimination criterion for conventional DAS, not a boundary below which direction information cannot exist | Report Rev A Sections 0, 4.1, 5.1 to 5.3, 8; `docs/metrics.md` |
| 3 | Median-steering bands are distinguished from bands guaranteed across the modeled steering set | `reports/SIM-01_band_definitions.md` (derived from existing tables by `tools/sim01_band_definitions.py`); report Rev A Sections 0, 4.1, 5.2 |
| 4 | Exact narrowband grating lobes do not establish broadband direction-finding failure | Report Rev A Sections 0, 4.1, 4.4, 5.4, 7, 8; transmittal Rev A |
| 5 | Pareto conclusions are conditional and are not used to eliminate hardware candidates whose cost and installation constraints are not modeled | Report Rev A Sections 0, 6, 7, 8; transmittal Rev A |

Run directories, tables and figures under `results/sim01/` are unchanged. The Rev 0 review package
(`deliverables/PCK-SIM-001_SIM-01_Review_Package_20261107T203522Z_d64d297c_8043684.zip`) is retained
unchanged as the reviewed baseline.

## Consequences
* The SIM-01 band ratios quoted in Rev 0 (3.03, 1.44, 1.18) are superseded by two explicit
  definitions: guaranteed (1.77, 1.28, 1.06) and median (3.54, 1.54, 1.36), horizon steering set.
* Later reports state every band with its aggregation rule and every gain with its weighting and
  noise field.
