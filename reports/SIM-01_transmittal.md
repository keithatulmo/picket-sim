# SIM-01 Review Transmittal

**Ulmo / Picket, PCK-SIM-001: Acoustic Array Modeling and Simulation Framework, Phase SIM-01**

| | |
|---|---|
| To | Author of the PCK-SIM-001 Claude Code engineering handoff |
| Subject | SIM-01 (array geometry and idealized acoustic performance): delivery for review |
| Date | 2026-11-07 |
| Repository | `keithatulmo/picket-sim`, branch `claude/beautiful-darwin-vbeoue` |
| Run of record | `20261107T203522Z_d64d297c_8043684` (code commit `8043684`, clean tree) |
| Prepared by | Claude Code (AI-generated engineering work product). It requires review by a qualified acoustic engineer before any of it is used to set requirements. |
| Requested action | Technical review of method, verification and conclusions; decisions on the open items in Section 6 |
| Revision | A: Section 2 corrected per the SIM-01 technical review (ADR-0008). Rev 0 is retained in the delivered package. |

## 1. What was asked and what is delivered

The handoff authorized the first increment of a reproducible modeling framework to compare candidate
Picket array geometries (A0 to A4) under idealized narrowband far-field conditions from 100 Hz to
10 kHz. It asked for verification before any hardware recommendation and for an engineering
assessment that stops short of selecting a design.

Delivered in this package:

| Item | Location in package |
|---|---|
| This transmittal (compliance matrix, review guide, decisions requested) | `00_TRANSMITTAL.pdf` |
| Engineering report with assessment, comparative table, Pareto analysis, limitations | `01_SIM-01_Engineering_Report.pdf` (and `.md`) |
| All figures of the run of record (10) | `02_figures/` |
| All tables (CSV for machines, Markdown for people) | `03_tables/` |
| Run record: resolved configuration, hashes of every output, software versions, self-checks; run index; errata | `04_run_record/` |
| Verification evidence: full pytest log and JUnit XML executed at the code commit, test inventory | `05_verification/` |
| Plan, conventions, metric definitions, assumption register, 7 architecture decision records | `06_documentation/` |
| Source archive of the exact code commit, pinned dependency lock file | `07_source/` |
| File manifest and SHA-256 checksums | `MANIFEST.md`, `SHA256SUMS.txt` |

## 2. Bottom line for the reviewer

1. The white-noise gain of four equally weighted elements is 6.02 dB. It is not a bound on array gain
   in general; other weights and noise fields give different gains. Against diffuse noise, uniform DAS
   on the compact candidates gives under 0.3 dB from 100 Hz to 1 kHz (band median).
2. Conventional DAS reaches -3 dB discrimination only above the half-power onset (median horizon
   steering): A1 667 Hz, A2 334 Hz, A3 633 Hz, A4 270 Hz. This is a -3 dB criterion; direction
   information below it is not excluded. A0 has no directional response.
3. The conventional band free of -3 dB ambiguity lobes is narrow. For every horizon steering direction
   (guaranteed) the ratio is 1.77 for the lines, 1.28 for the 2x2 square and 1.06 for A4; for a median
   steering direction it is 3.54, 1.54 and 1.36. Rev 0 quoted a mixed convention (3.03, 1.44, 1.18).
4. Geometric ambiguity is exact. The lines see a cone (total left/right ambiguity for horizontal
   targets), the horizontal square an up/down mirror, and A4 none.
5. Any non-coplanar 4-element array has exact (0 dB) narrowband grating lobes, whatever its placement;
   for A4 the worst case starts at 857 Hz. This does not establish that broadband or TDOA direction
   finding fails; that question is assigned to SIM-02B.
6. SIM-01 does not support selecting an architecture, and its Pareto results, which omit cost and
   installation, are not a basis for eliminating candidates. Under the -3 dB criterion, 4-element
   narrowband delay-and-sum does not provide wideband, unambiguous, full-azimuth bearing.

## 3. Compliance matrix

Status: **Met**, **Met with note**, or **Not met**. Evidence paths are relative to the package root
(report sections refer to `01_SIM-01_Engineering_Report`).

### 3.1 Handoff steps

| Step | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Inspect repository; decide where the package lives | Met | Repository was empty; standalone research package decided (ADR-0001). `06_documentation/SIM-01_plan.md` Section 1 |
| 1 | Short plan: architecture, equations, conventions, inputs/outputs, verification, dependencies, reproducibility, limitations | Met | `06_documentation/SIM-01_plan.md` (written before implementation) |
| 1 | Record major architectural decisions before implementation | Met | `06_documentation/adr/0001` to `0007` |
| 2 | Configurable 3-D sensor coordinates; candidates A0 to A4 | Met | `04_run_record/sim01_baseline.yaml`; report Section 2 |
| 2 | Arbitrary coordinates for future comparisons | Met | `type: coordinates` in the configuration; tests `test_a4_coordinates_are_configurable` |
| 2 | Do not assume a line resolves 3-D direction; identify geometric ambiguities | Met | Exact rank-based classification; report Sections 3.2 and 4.4; tests `test_rank_and_ambiguity_class`, `test_line_array_cone_invariance` |
| 3 | Wavelength, wavenumber, delays, steering vectors, frequency-dependent response, DAS, normalized beampatterns | Met | `07_source` (`acoustics.py`, `beamforming.py`); report Section 3.1 |
| 3 | Mainlobe and sidelobe characteristics where meaningfully defined | Met with note | Defined in the observable space and on great-circle cuts; undefined cases reported as n/a/inf with reasons (ADR-0005, `06_documentation/metrics.md`) |
| 3 | Spatial aliasing and ambiguity; sensitivity to element count, spacing, frequency | Met | Report Sections 4.4 and 4.5; `02_figures/fig04`, `fig05`, `fig08`, `fig09` |
| 3 | Configurable sound speed, 1500 m/s nominal; homogeneous medium; no ocean propagation or self-noise | Met | `physics.sound_speed_mps`; robustness at 1450 and 1550 m/s |
| 4 | Comparison across 100 Hz to 10 kHz | Met | 121 log-spaced frequencies; `03_tables/summary_by_frequency.csv` |
| 4 | Frequency-dependent beampatterns; angular response and ambiguity visualizations; representative-frequency comparisons | Met | `fig02` to `fig05`; `03_tables/representative_frequencies.md` |
| 4 | Aperture and element-spacing sensitivity | Met | `fig08`, `fig09`; `03_tables/sensitivity_*` |
| 4 | Quantitative single-channel versus multichannel comparison | Met | Report Section 4.2; `03_tables/comparison.md` |
| 4 | Frequency regions where conventional resolution is limited | Met | Report Section 4.1 and `fig07` (regime map) |
| 4 | Report undefined or misleading metrics instead of forcing numbers | Met | ADR-0005; tests `test_single_hydrophone_metrics_are_undefined_not_numbers`, `test_line_array_vertical_cut_at_broadside_is_undefined` |
| 4 | Do not equate ideal beamforming gain with detection performance | Met | Stated in report Sections 0, 1 and 4.2, figure titles and table notes |
| 5 | Steering vectors against independent analytic cases | Met | `test_two_element_steering_vector_hand_computed`, `test_steering_vector_on_y_and_z_axes`, `test_far_field_limit_of_spherical_wave`, `test_time_domain_delay_matches_steering_vector` |
| 5 | Broadside and endfire behavior | Met | `test_broadside_symmetry_and_nulls`, `test_endfire_peak_null_and_broadening` |
| 5 | Linear-array symmetry and ambiguity | Met | `test_line_array_cone_invariance`, `test_line_array_left_right_and_up_down_ambiguity` |
| 5 | Effects of increasing aperture | Met | `test_aperture_increases_resolution_and_gain`, `test_increasing_frequency_narrows_the_beam` |
| 5 | Spatial aliasing for relevant frequencies and spacing | Met | `test_grating_lobe_at_half_wavelength_criterion`, `test_worst_case_aliasing_onset_line_array_independent`, `test_worst_case_aliasing_onset_square_brute_force`, `test_exact_grating_onset_lattices`, `test_any_four_noncoplanar_sensors_have_exact_grating_lobes` |
| 5 | Single hydrophone cannot discriminate direction | Met | `test_single_hydrophone_has_no_directional_discrimination`, `test_single_hydrophone_gains_are_zero` |
| 5 | Correct frequency, length, time and angular units | Met | `test_units_wavelength_wavenumber`, `test_arrival_time_sign_and_units`, `test_degrees_not_radians`, `test_unit_errors_rejected`, `test_geometry_unit_errors_rejected` |
| 5 | Consistent results under fixed configurations | Met | `test_full_pipeline_is_bitwise_reproducible` (two full runs, identical bytes), `test_metrics_depend_only_on_f_over_c` |
| 5 | Checks against incorrect normalization, angular-convention errors and plotting artifacts | Met | `test_normalization_and_bounds_all_candidates`, `test_di_closed_form_equals_sphere_quadrature`, `test_unit_vector_cardinal_directions`, `test_horizontal_cut_plot_peak_at_steering_and_no_seam`, `test_sphere_map_orientation`, `test_display_db_floor_and_normalization_guard`; run self-checks in `05_verification/self_checks.json` |
| 5 | Tests pass before output is used | Met | `05_verification/pytest_log.txt` (131 passed at code commit `8043684`); `make sim01` runs the tests first |
| 6 | Version control, dependency specification, machine-readable configuration, tests, reproduction command | Met | Git; `07_source/requirements.lock`; YAML configuration; `make sim01` |
| 6 | Saved figures and tables; experiment records with configuration, assumptions and software version | Met | `02_figures`, `03_tables`, `04_run_record/record.json` |
| 6 | Technical report | Met | `01_SIM-01_Engineering_Report.pdf` |
| 6 | Consistent axes, units, normalization and labels | Met | `plotting.py` conventions; plotting tests |
| 6 | Do not silently overwrite historical results | Met | Immutable run directories (ADR-0006); the first run is retained with an errata entry |
| 7 | Questions 1 to 6 | Met | Report Sections 5.1 to 5.6 |
| 7 | Comparative table; Pareto-dominated candidates on evaluated attributes only | Met | Report Section 6; `03_tables/pareto*.md` |
| 7 | Do not select a production design from idealized simulation | Met | Report Section 7 recommends what to simulate next and selects nothing |

### 3.2 Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | All five candidates simulated through the same interface | Met | One code path (`ArrayGeometry` -> `PlaneWaveManifold` -> DAS -> metrics); `test_all_five_candidates_through_one_interface` |
| 2 | Core numerical methods pass automated verification | Met | 131 tests passing; self-checks embedded in the run |
| 3 | Results reproducible from documented configurations | Met | `make sim01`; two identical end-to-end runs produce byte-identical outputs; numeric tables of the first and final runs agree (report Section 9) |
| 4 | Comparative plots and tables generated | Met | `02_figures`, `03_tables` |
| 5 | Assumptions and limitations documented | Met | `06_documentation/assumptions.md`; report Sections 1 and 8 |
| 6 | Report identifies which candidates warrant further simulation | Met | Report Section 7 |
| 7 | Extensible to sensor noise, propagation and host effects without rewriting the core | Met with note | Extension points in ADR-0007: manifold interface with an element-response hook, noise-coherence interface, explicit weights. Not exercised beyond SIM-01, so the claim is by design, not yet demonstrated |

### 3.3 Engineering principles

| # | Principle | How it was applied |
|---|---|---|
| 1 | First principles, established theory | Plane-wave array theory; every threshold cross-checked against closed forms (c/(Nd), c/(2d), c/(8d), Dirichlet patterns) |
| 2 | Correctness and verification over visualization | 131 tests plus run self-checks; two defects found by checking were fixed before reporting (Section 5) |
| 3 | Modeled effects versus assumptions | `docs/assumptions.md` separates modeled, assumed, excluded and placeholder items |
| 4 | No fabricated results or specifications | Every number in the report comes from the run tables; the A4 coordinates are labelled a placeholder; no hardware specifications are asserted |
| 5 | Numerical and analytical baselines | Closed-form DI versus quadrature; brute-force versus algorithmic sidelobes and aliasing |
| 6 | Supports additional geometries | Arbitrary coordinates, rotation and scale in the configuration |
| 7 | Experimental code separate from production and Fathom | Standalone repository, no production imports (ADR-0001) |
| 8 | Record assumptions, decisions, configurations, results | ADRs, configuration hash, `record.json`, `RUN_INDEX.csv`, `ERRATA.md` |
| 9 | Complete, tested, documented implementation | See Sections 3.1 and 3.2 |
| 10 | Say when evidence is insufficient | Report Sections 0 (item 7), 5.5, 7 and 8 |

## 4. Additions beyond the handoff (for the reviewer to accept or reject)

| Addition | Why |
|---|---|
| Exact rank-based ambiguity classification and observable-space metrics | Keeps a geometric cone or mirror image from being misreported as a "0 dB sidelobe" |
| Worst-case aliasing onset over all steering (wavevector space) and exact grating onset (reciprocal lattice) | Steering-independent aliasing limits; revealed that A4's aliasing is structural |
| Regime thresholds f_HP, f_SL, f_amb | Turns "where does resolution become limited" into numbers with a closed-form check |
| Sound-speed mismatch bias | Q5 asks for robustness to sound speed; mismatch produced the one non-robust finding (planar elevation) |
| Orientation variants (vertical line, vertical square) | Shows that orientation decides which angle is lost |
| Pareto analysis with numerical and engineering tie tolerances, plus a leave-one-out table | Without tolerances, rounding at the 1e-16 level changed a dominance result (Section 5) |

Not done, as out of scope or deferred: sensor position, gain and phase error Monte Carlo; broadband and
TDOA processing; adaptive and superdirective weights; acoustic vector sensors; cylindrically isotropic
and directional noise; host shading. All are listed as future work in the report.

## 5. Errors found and corrected during the work

Recorded in `04_run_record/ERRATA.md`. The first complete run (`20261107T200834Z_cf0574c6_059a354`) is
retained unmodified in the repository. A floating-point residue (half-power sphere fraction
1 + 2e-16) combined with a Pareto comparison that had no tie tolerance made A1 appear non-dominated by
A3 in one attribute set. The code was corrected (normalization by the quadrature weight sum, explicit
tie tolerances) and both fixes are covered by tests. Two figure annotations were also corrected.
The first complete run (`20261107T200834Z_cf0574c6_059a354`, code `059a354`) and the run of record share 26 tables. 16 are byte-identical, including the full 29,040-row sweep, all regime thresholds, the sensitivity sweeps and the robustness tables. The other 10 differ only by the added exact-grating column, the corrected Pareto result and their Markdown renderings. Every numeric value present in both runs is identical.

## 6. Decisions requested from the reviewer

1. **Mission band and signals.** Every SIM-01 threshold scales with array size, so aperture cannot be
   chosen until the band (and tonal versus broadband content) is set.
2. **Bearing requirement.** Is horizontal bearing with left/right ambiguity acceptable (lines), or is
   full-azimuth (planar) or 3-D (volumetric) bearing required? Can host maneuvering be assumed to
   resolve ambiguity?
3. **Ambiguity criterion.** SIM-01 used -3 dB (and -1 dB). A detection-oriented requirement may need
   -6 or -10 dB, which narrows every reported band.
4. **A4 coordinates.** Provide surveyed host positions, or accept the placeholder as a generic
   "distributed" case.
5. **Candidate set for SIM-02.** Recommended additions: planar arrays with 6 to 8 elements, acoustic
   vector sensors, and a broadband/TDOA model for distributed layouts (report Section 7).
6. **Pareto tolerances.** Confirm or replace the engineering tie tolerances in the configuration
   (0.05 m footprint, 0.25 dB DI, 0.02 HPSF, 5 % on frequencies).

## 7. Suggested review path (about 45 minutes)

1. This transmittal, Sections 2 and 6.
2. Report Section 0 (bottom line), Figure 2 (regime map) and Section 4.1.
3. Report Section 5 (assessment) and Section 6 (comparative table, Pareto).
4. Spot-check the verification: `05_verification/pytest_log.txt`, then
   `06_documentation/metrics.md` for definitions you may disagree with.
5. Optional: reproduce. Unpack `07_source`, install from `requirements.lock`, then run `make test` and
   `make sim01` (about 20 minutes on one CPU). Compare the new tables with `03_tables` using
   `SHA256SUMS.txt`.

Integrity: `sha256sum -c SHA256SUMS.txt` from the package root verifies every file.
