# picket-sim: working instructions for Claude Code

Research simulation framework for Ulmo Picket (PCK-SIM-001). Read `README.md`, `docs/adr/README.md`
and the latest `docs/SIM-*_plan.md` before changing anything.

## Engineering rules (from the program handoffs and reviews)

* Verify before reporting: `make test` must pass; every run of record comes from a clean tree.
* Never alter historical run directories or delivered packages; record problems in
  `results/<study>/ERRATA.md` and decisions in `docs/adr/`.
* Every physical parameter carries provenance (published, measured, assumed) per ADR-0010; never
  present assumed values as measurements.
* Fail visibly on invalid configurations; no clipping or silent defaults.
* Report numbers only from run tables; check quoted ranges programmatically against the tables.
* No architecture selection, detection ranges or hardware requirements unless a review authorizes it.

## Cycle close-out (required at the end of every increment or review cycle)

The program owner asked for this at the end of each cycle:

1. Run of record from a clean commit; confirm self-checks and record the run id.
2. Engineering report and transmittal generated from the run tables, with claims verified by a committed
   script (`tools/check_<increment>_claims.py`, see `tools/check_sim02a_claims.py`) that recomputes every
   quoted number in the findings, transmittal and reviewer message at the precision written. Physical
   statements that are not in a run table (sidelobe levels, margins, scaling laws) must be computed with the
   study code and written to a committed supplement table before they are quoted; never state them from
   memory. Check that a band median is not quoted as a maximum, that a single Monte Carlo case is not
   quoted as representative of a set, and that a combined error scenario is not attributed to one term.
   Numbers from delegated desk research enter configurations only after the quote has been located in the
   downloaded source text; record them in `docs/input_provenance_register.md` with all D01 fields.
3. Review package: `.venv/bin/python tools/build_review_package.py --run results/<study>/<run_id> --label <INCREMENT>
   --report reports/<INCREMENT>_engineering_report.md --transmittal reports/<INCREMENT>_transmittal.md
   [--extra ...] --include-results <every run of record the documented commands read>
   --snapshot-check "make <claims target>" [--snapshot-check ...]`; copy the PDFs to `reports/`; register the zip
   in `deliverables/README.md`. The package must ship both source baselines (the run's code commit and the
   packaging HEAD), run the tests at both, and prove from an unpacked snapshot that every documented
   reproduction command works (SIM-02A review, closeout actions; `docs/source_baselines.md`). Never delete
   files with `rm -rf` in Makefiles or scripts; write new runs to new directories instead.
4. **Reviewer message**: a ready-to-send cover message for the reviewer, written in the program owner's
   voice (use the `keith-voice` skill when available; no em dashes). It lists each attachment with page
   count or size, summarizes what closed and what is new, states the principal findings with their
   assumptions, discloses defects found and corrected, lists the decisions requested, notes that the
   work is AI-generated and needs qualified review, and gives the reproduction command, repository and
   branch, and a `[date]` placeholder. Save it as `reports/<INCREMENT>_reviewer_message.md` and include
   the text in the final reply together with the attached files. Run the claims check again after writing the message; it
   must pass before the message is delivered.
5. Commit and push to the designated branch; send the package and PDFs to the user.
