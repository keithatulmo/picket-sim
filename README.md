# picket-sim

Acoustic array modeling and simulation framework for Ulmo's Picket program (PCK-SIM-001).
Experimental research software: isolated from production code and from Fathom
([ADR-0001](docs/adr/0001-isolated-simulation-repository.md)).

Increments:

* **SIM-01**, array geometry and idealized acoustic performance (narrowband, far-field plane waves,
  homogeneous medium, conventional delay-and-sum). Closed on report Revision A after technical review
  (ADR-0008): [`reports/SIM-01_engineering_report.md`](reports/SIM-01_engineering_report.md).
* **SIM-02A**, sensor, noise and error modeling (authorized by the SIM-01 review, ADR-0009):
  plan [`docs/SIM-02A_plan.md`](docs/SIM-02A_plan.md), models
  [`docs/sensor_noise_error_models.md`](docs/sensor_noise_error_models.md), report
  [`reports/SIM-02A_engineering_report.md`](reports/SIM-02A_engineering_report.md). SIM-02B (broadband,
  task-level) is gated on review of SIM-02A results.

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.lock && pip install -e . --no-deps
make test        # verification suite (must pass before results are used)
make sim01       # regenerate all SIM-01 results into a new results/sim01/<run_id>/
make sim02a      # regenerate all SIM-02A results into a new results/sim02a/<run_id>/
```

`make sim01` runs `python -m picket_sim run configs/sim01/sim01_baseline.yaml`. It refuses to run
on a working tree with uncommitted changes (use `--allow-dirty` for exploration; the record says
so). Each run creates a new immutable directory; nothing is overwritten
([ADR-0006](docs/adr/0006-immutable-run-records.md)).

## Layout

| Path | Content |
|---|---|
| `src/picket_sim/` | Library: `conventions`, `geometry`, `acoustics`, `beamforming`, `noise`, `grids`, `metrics`, `analysis`, `mismatch`, `plotting`, `records`, `config`, `cli`; SIM-02A: `params` (provenance), `sensor`, `noisefields`, `errors`, `stats`, `rag`, `avs`, `plotting_sim02a` |
| `src/picket_sim/experiments/` | Study orchestration (`sim01.py`, `sim02a.py`) |
| `configs/` | Machine-readable experiment configurations (`*_baseline.yaml` are studies of record; `*_smoke.yaml` are coarse test fixtures) |
| `tests/` | Verification suite |
| `results/sim01/<run_id>/` | Run outputs: `record.json` (provenance and output hashes), `tables/`, `figures/`, `summary.md`; `RUN_INDEX.csv` lists all runs |
| `docs/` | Plan, conventions, metric definitions, assumption register, ADRs |
| `reports/` | Engineering reports |

## Conventions in one paragraph

Right-handed frame, metres, `z` up; azimuth from `+x` toward `+y`; elevation positive up; the
direction vector points toward the source; `exp(+j omega t)`; steering vector
`exp(+j k u . r)`; patterns normalized to 0 dB in the steering direction. Details:
[`docs/conventions.md`](docs/conventions.md). Metric definitions: [`docs/metrics.md`](docs/metrics.md).
Assumptions and limitations: [`docs/assumptions.md`](docs/assumptions.md).

## Adding a geometry

Add an entry under `arrays:` in a configuration (types `single`, `linear`, `rectangular`,
`coordinates`; optional `rotation` and `scale`). Every candidate goes through the same analysis
path. For host-specific layouts use `type: coordinates` with surveyed positions in metres.
