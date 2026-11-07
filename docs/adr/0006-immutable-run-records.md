# ADR-0006: Immutable run records and provenance

Status: Accepted (SIM-01)

## Decision
Each experiment run writes to a new directory `results/<study>/<run_id>/`, where
`run_id = <UTC timestamp>_<config sha256[:8]>_<git sha[:7]>`. The directory is assembled in a
temporary location and renamed into place; an existing directory is never overwritten.
`record.json` holds the resolved configuration, its hash, git commit and dirty flag, Python and
package versions, platform, command line, timing, self-check results, warnings, and the SHA-256 of
every output file. `RUN_INDEX.csv` is append-only. Runs refuse a dirty working tree unless
`--allow-dirty` is passed, in which case the record says so.

## Consequences
Historical results are preserved; the report cites a specific run id. Disk use grows with runs;
superseded runs may be pruned only by an explicit, reviewed commit.
