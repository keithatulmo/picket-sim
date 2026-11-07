# SIM-02A results errata

Run directories are immutable; problems found in historical runs are recorded here.

| Run | Affected output | Problem | Corrected in |
|---|---|---|---|
| `20261107T213213Z_c56c0048_5182a6b` | `tables/mc_scenarios.*` (bearing columns), `tables/mc_sweeps.csv` (bearing columns), `figures/s2a_fig08_mc_ambiguity_bearing.png` | (1) Line arrays: the scanned response is exactly symmetric in azimuth for any channel errors, so target and mirror tie; `argmax` returned the first index (the mirror) and the run reported gross-error rates near 1.0. These were tie-breaking artifacts. (2) Cut-based ambiguity and bearing statistics were reported at frequencies where the error-free cut has no half-power discrimination (for example A1, A2, A4 at 100 Hz), where "outside lobes" are the broad pattern, not ambiguities. All other tables (acquisition, realized gain, host noise, thresholds, regression, signal loss and its closed-form verification) are unaffected. | Code after commit `e735bfd`: ties reported as `unresolved_tie_rate` with fine error at the correct-side peak; cut statistics undefined without half-power discrimination (tests `test_line_array_mirror_is_an_unresolved_tie_not_a_gross_error`, `test_cut_statistics_undefined_without_half_power_discrimination`). |
