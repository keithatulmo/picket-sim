# Source baselines: code commits, report-generation tools and the final source baseline

SIM-02A technical review, closeout action 4: document the distinction between the original code commit, later
report-generation tools and the final source baseline.

## Definitions

| Baseline | What it is | Where it is recorded |
|---|---|---|
| **Code commit of a run** | The commit that produced a run of record. The run refuses to start on a dirty tree, so the run's numbers come from exactly this code. | `results/<study>/<run_id>/record.json` (`software.git_commit`, `git_dirty`) |
| **Report-generation tools** | Code committed after a run that reads its tables but never writes into the run directory: claims checkers, criterion-margin generators, band-definition derivations, the package builder. Their outputs live in `reports/` and record the commit that produced them. | headers of `reports/SIM-02A_criterion_margin.md`, `reports/SIM-02A_criteria_D06.md`, `reports/SIM-02A_claims_check.txt` |
| **Final source baseline** | The repository HEAD when a review package is built. It contains the run's code commit as an ancestor, every later tool, and the documents. | `07_source/SOURCE.md` and `MANIFEST.md` in each package |

Review packages from SIM-02B.1 on ship both source archives: `picket-sim_<code>.tar.gz` (the run's code commit)
and `picket-sim_<head>_baseline.tar.gz` (the final source baseline, with the run-of-record records and tables
embedded so that documented commands run from it). The verification suite runs at both commits, and the
documented commands are executed in an unpacked copy of the baseline archive; logs are in `05_verification/`.

## SIM-02A history

* Run of record `20261107T214846Z_c56c0048_31da01b`, code commit `31da01b` (clean tree).
* Report-generation tools added afterwards (no change to SIM-02A library code paths):
  * `tools/sim02a_criterion_margin.py` (first `723bc27`, plateau and knife-edge `8fee2dd`, software versions
    `48c4cfc`, testable refactor and `--levels`/`--expect` modes `c074841`);
  * `tools/check_sim02a_claims.py` (`ba5117d`, importable refactor `c074841`), with the Revision 0 documents kept
    as test fixtures in `tests/fixtures/sim02a_rev0/`;
  * `tools/build_review_package.py` (generalized `74f0507`, snapshot exclusions `a34511d`, both baselines and
    snapshot checks `c074841`).
* Library change after `31da01b` that touches SIM-02A modules: `src/picket_sim/params.py` gained optional
  provenance fields (frequency range, applicability, uncertainty) for SIM-02B. `Param.row()`, which writes the
  SIM-02A provenance table, is unchanged; the reproduction check below confirms the SIM-02A tables are
  unaffected.
* The Revision 0 SIM-02A package was built from HEAD `b89a8c3`; Revision A from HEAD `b1b59bc`. Both are
  retained unchanged in `deliverables/`.

## Reproduction checks shipped with the SIM-02B.1 package

Executed in an unpacked copy of the final-baseline archive (no `.git` directory):

* `make sim02a-claims`: the 59 SIM-02A Revision A claims checks.
* `make sim02a-margin-check`: regenerates the criterion-margin supplement and requires byte-identical CSV files.
* `make sim02a-repro-check`: reruns the SIM-02A study from the final baseline and requires every run table to
  be byte-identical to the run of record, except the Monte Carlo bearing columns documented in
  `results/sim02a/ERRATA.md` (none expected; any difference fails the check).

## SIM-02B.2-A

* Run of record `20261109T003718Z_27abcd69_73fbe35`, code commit `73fbe35` (clean tree).
* Changes after `73fbe35` that touch the study code (none changes a value in the run tables; the partial
  reproduction check below proves it for the recomputed work units):
  * `src/picket_sim/experiments/sim02b2a.py`: exact predictive tails and an exact false-alarm status added as new
    columns of `realized_pfa.csv` and carried into the loss and gain tables; the method-agreement self-check counts
    distinct ORACLE statistics (`results/sim02b2a/ERRATA.md`).
  * `src/picket_sim/plotting_sim02b2a.py`: axis labels.
* Report-generation tools added afterwards: `tools/sim02b2a_summary.py`, `tools/sim02b2a_supplement.py`,
  `tools/sim02b2a_b1_regression.py`, `tools/sim02b2a_repro_check.py`, `tools/check_sim02b2a_claims.py`,
  `tools/d02_collection_design.py`.

## Reproduction checks shipped with the SIM-02B.2-A package

Executed in an unpacked copy of the final-baseline archive (no `.git` directory):

* `make sim02b2a-claims`: every number quoted in the SIM-02B.2-A report, transmittal and reviewer message.
* `make sim02b2a-repro-check`: recomputes two calibration and three evaluation work units from the resolved
  configuration in the run record and requires every table row to match the run as text (a full rerun takes
  about 2.3 hours on 4 cores: `make sim02b2a`).
* `make sim02b2a-regression`: regenerates the SIM-02B.1 regression table and requires an identical CSV file.
* `make sim02b2a-d02`: regenerates the D02 design tables and requires identical CSV files.
* `make sim02b1-claims` and `make sim02a-claims`: the earlier increments' claims still pass.
