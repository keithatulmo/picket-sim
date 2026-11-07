# SIM-01 results errata

Run directories are immutable. Known problems in historical runs are recorded here instead of
editing them. The engineering report cites the run of record.

| Run | Affected output | Problem | Corrected in |
|---|---|---|---|
| `20261107T200834Z_cf0574c6_059a354` | `tables/pareto.csv`, `tables/pareto.md`, `summary.md` (Pareto section) | Half-power sphere fraction from the sphere quadrature was divided by 4 pi instead of the (rounding-equal) weight sum, so a fully non-directional result could read 1 + 2e-16. Pareto comparison had no tie tolerance, so this rounding residue let A1 appear non-dominated by A3 in the `all_candidates` set. All other numbers are unaffected (HPSF values differ by < 1e-15). | Code after commit `a305745`: HPSF normalized by the weight sum and clipped to [0, 1]; Pareto uses explicit numerical and engineering tie tolerances. |
| `20261107T200834Z_cf0574c6_059a354` | `figures/fig08_line_array_sensitivity.png` panel (b) title; `figures/fig09_aperture_scaling.png` | Title stated DI reaches 10 log10 N only at half-wavelength multiples (DAS DI exceeds it for lambda/2 < d < lambda); fig09 plotted an f_HP value below the band (A4x4) as if measured. | Commit `a305745`. |
| `20261107T200834Z_cf0574c6_059a354` | `tables/geometry_summary.*` | Exact grating onset reported only for declared lattices (n/a for A4, which also has exact grating lobes). | Commit `a305745` (`exact_grating_onset_hz`). |
