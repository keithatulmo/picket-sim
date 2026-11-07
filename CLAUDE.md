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
2. Engineering report and transmittal generated from the run tables, with claims verified.
3. Review package: `python tools/build_review_package.py --run results/<study>/<run_id> --label <INCREMENT>
   --report reports/<INCREMENT>_engineering_report.md --transmittal reports/<INCREMENT>_transmittal.md
   [--extra ...]`; copy the PDFs to `reports/`; register the zip in `deliverables/README.md`.
4. **Reviewer message**: a ready-to-send cover message for the reviewer, written in the program owner's
   voice (use the `keith-voice` skill when available; no em dashes). It lists each attachment with page
   count or size, summarizes what closed and what is new, states the principal findings with their
   assumptions, discloses defects found and corrected, lists the decisions requested, notes that the
   work is AI-generated and needs qualified review, and gives the reproduction command, repository and
   branch, and a `[date]` placeholder. Save it as `reports/<INCREMENT>_reviewer_message.md` and include
   the text in the final reply together with the attached files.
5. Commit and push to the designated branch; send the package and PDFs to the user.
