"""Regenerate configs/sim02a/sim02a_smoke.yaml from the baseline (coarse grids, candidate subset)."""

import yaml

cfg = yaml.safe_load(open("configs/sim02a/sim02a_baseline.yaml"))
cfg["experiment"]["description"] = ("Fast smoke configuration (coarse grids, subset of candidates) for automated tests. "
                                    "Not for engineering use.")
cfg["frequency_grid"]["points_per_decade"] = 5
cfg["steering"]["horizon_az_step_deg"] = 90.0
cfg["grids"] = {"sphere": {"n_el": 61, "n_az": 120}, "cut_points": 720, "reduced_1d_points": 801}
keep = {"A0", "A1", "A3", "A4", "P6-C", "V-DS"}
cfg["candidates"] = [c for c in cfg["candidates"] if c["id"] in keep]
cfg["noise_fields"] = [f for f in cfg["noise_fields"] if f["id"] in ("WHITE", "ISO", "HOR", "UP2")]
cfg["eta_db"] = [None, 0.0, 20.0]
cfg["host_scenarios"]["frequencies_hz"] = [500.0, 2000.0]
cfg["host_scenarios"]["hnr_db"] = [10.0]
for k, v in {"sigma_phase_deg": [3.0, 30.0], "sigma_gain_db": [0.5, 2.0], "sigma_position_m": [0.003, 0.03],
             "sigma_timing_s": [1.0e-6, 1.0e-4]}.items():
    cfg["error_sweeps"][k] = v
cfg["monte_carlo"].update({"trials": 200, "trials_sweep": 200, "frequencies_hz": [1000.0, 5000.0],
                           "target_az_deg": [30.0]})
cfg["regression"] = {}
cfg["output"]["root"] = "results/_scratch/sim02a_smoke"
hdr = ("# SMOKE configuration for automated tests only (coarse grids, candidate subset).\n"
       "# Generated from sim02a_baseline.yaml by tools/make_sim02a_smoke.py. Not for engineering conclusions.\n")
open("configs/sim02a/sim02a_smoke.yaml", "w").write(hdr + yaml.safe_dump(cfg, sort_keys=False, width=120))
