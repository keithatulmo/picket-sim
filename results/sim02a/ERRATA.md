# SIM-02A results errata

Run directories are immutable; problems found in historical runs are recorded here.

| Run | Affected output | Problem | Corrected in |
|---|---|---|---|
| `20261107T213213Z_c56c0048_5182a6b` | `tables/mc_scenarios.*` (bearing columns), `tables/mc_sweeps.csv` (bearing columns), `figures/s2a_fig08_mc_ambiguity_bearing.png` | (1) Line arrays: the scanned response is exactly symmetric in azimuth for any channel errors, so target and mirror tie; `argmax` returned the first index (the mirror) and the run reported gross-error rates near 1.0. These were tie-breaking artifacts. (2) Cut-based ambiguity and bearing statistics were reported at frequencies where the error-free cut has no half-power discrimination (for example A1, A2, A4 at 100 Hz), where "outside lobes" are the broad pattern, not ambiguities. All other tables (acquisition, realized gain, host noise, thresholds, regression, signal loss and its closed-form verification) are unaffected. | Code after commit `e735bfd`: ties reported as `unresolved_tie_rate` with fine error at the correct-side peak; cut statistics undefined without half-power discrimination (tests `test_line_array_mirror_is_an_unresolved_tie_not_a_gross_error`, `test_cut_statistics_undefined_without_half_power_discrimination`). |
| `20261107T214103Z_c56c0048_8e20ef8` | `tables/mc_scenarios.*`, `tables/mc_sweeps.csv` (bearing columns), `figures/s2a_fig08_mc_ambiguity_bearing.png` | The tie test introduced to fix the first run (`outside peak >= inside peak`) also captured outright gross errors (outside peak strictly larger), so every gross-error rate read 0 and "unresolved tie rates" mixed exact ties with gross errors. Exact ties also occur for lattice arrays above their exact grating onset, where float comparisons on the scan grid are grid-dependent. All other tables are unaffected and identical to the first run. | Code after commit `8e20ef8`: structural ambiguity decided on the error-free cut (outside lobe within 1 dB of the mainlobe), gross error = outside peak strictly above the mainlobe otherwise (test `test_bearing_statistics_structural_ambiguity_and_gross_errors`). |

## Documentation errata (delivered Rev 0 report and transmittal)

The run of record `20261107T214846Z_c56c0048_31da01b` and all its tables and figures are correct. The
following prose statements in the Rev 0 SIM-02A engineering report and transmittal (review package
`deliverables/PCK-SIM-001_SIM-02A_Review_Package_20261107T214846Z_c56c0048_31da01b.zip`, retained
unchanged) did not match the tables or the physics. They were found by a programmatic check of every
Section 0 and transmittal claim before the package was sent to the reviewer, and are corrected in
Revision A.

| Document, location | Rev 0 statement | Fact (source) | Rev A |
|---|---|---|---|
| Report Section 0 item 3 | Circles' intrinsic sidelobes "near -8 dB" | Worst-steering peak sidelobe plateau is -6.02 dB for P6-C and -7.77 dB for P8-C. P6-C's plateau lies 0.02 dB below the -6 dB criterion, so its -6 dB guaranteed band (ratio 2.37) collapses at -6.1 dB (`reports/SIM-02A_criterion_margin.md`, computed with the study code; nominal bands reproduce the run tables) | Per-circle values and the knife-edge caveat stated |
| Report Section 0 item 1; transmittal Section 5 item 1 | "At most 0.07 dB from 20 to 200 Hz" (transmittal drops "band-median") | 0.07 dB is the largest band median (A4); gain grows roughly as f squared and reaches 0.73 dB at 200 Hz (A4, steering median) (`rag_band_summary.csv`, `rag_by_frequency.csv.gz`) | Band median and top-of-band value both stated |
| Report Section 0 item 1, Section 4.2; transmittal Section 5 item 1 | In short-correlation noise the arrays "approach 10 log10 N at every frequency" / "even at 20 Hz" | A1, P6-C and P8-C fall 0.9 to 1.7 dB short below 2 kHz; all others within 0.5 dB; all within 0.16 dB or above above 2 kHz (`rag_band_summary.csv`, field FLOW) | Measured gaps stated |
| Report Section 0 item 5; transmittal Section 5 item 5 | 65 % gross azimuth errors (no target azimuth given); transmittal attributes it to "10 us timing error" | 65 % is the 30 deg target; across the four Monte Carlo target azimuths 65 to 81 %, signal loss 4.3 to 4.4 dB. E3 combines gain, phase, position and timing errors; timing supplies about two thirds of the phase variance at 15 kHz (`mc_scenarios.csv`) | Range, target azimuth and scenario composition stated |
