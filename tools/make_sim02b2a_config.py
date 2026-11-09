"""Generate configs/sim02b/sim02b2a_baseline.yaml and sim02b2a_smoke.yaml from the SIM-02B.1 baseline.

Candidate geometries, spectra, the S1 chain, signal classes and processing settings are copied verbatim from
configs/sim02b/sim02b1_baseline.yaml so that SIM-02B.2-A shares every model with SIM-02B.1. Run once; edit the
generated YAML only through this script.

    python tools/make_sim02b2a_config.py
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
b1 = yaml.safe_load(open(REPO / "configs/sim02b/sim02b1_baseline.yaml"))

cfg = copy.deepcopy(b1)
cfg["experiment"] = {
    "id": "SIM-02B.2-A",
    "title": "SIM-02B.2-A adaptive noise estimation and false-alarm control",
    "assumptions": [
        "Models, spectra, coherence, S1 chain and signal classes as SIM-02B.1 (ADR-0015 to ADR-0017).",
        "Thresholds are fixed at design time from the nominal model (Wenz nominal, isotropic, S1, stationary); "
        "scenarios change the truth only (ADR-0019, ADR-0020).",
        "Reference windows are independent windows of the same noise process; nonstationarity, interference and "
        "contamination enter only through the scenario definitions.",
        "Stationary Gaussian noise inside every window; no host noise, calibration or synchronization errors "
        "(SIM-02B.2-B and -C).",
    ],
}
cfg["output"] = {"root": "results/sim02b2a"}
cfg["seed"] = 20261109
keep = ["A0", "A1", "P8-C", "A4"]
cfg["candidates"] = [c for c in b1["candidates"] if c["id"] in keep]
assert [c["id"] for c in cfg["candidates"]] == ["A0", "A1", "P8-C", "A4"]

# D03 spectral-shape variants (published equations, assumed parameters)
src = b1["spectra"]["AMB-WENZ"]["model_source"]
for sid, s, w, why in (("AMB-WENZ-HI", 1.0, 10.0, "high shipping (source maximum 1) and 10 m/s wind"),
                       ("AMB-WENZ-LO", 0.0, 2.5, "low shipping (source minimum 0) and 2.5 m/s wind")):
    cfg["spectra"][sid] = {
        "type": "coates_wenz", "valid_range_hz": [20.0, 10000.0], "model_source": src,
        "applicability": b1["spectra"]["AMB-WENZ"]["applicability"],
        "uncertainty": b1["spectra"]["AMB-WENZ"]["uncertainty"],
        "shipping_activity": {"value": s, "provenance": "assumed", "source": f"D03 sensitivity scenario: {why}"},
        "wind_speed_m_per_s": {"value": w, "provenance": "assumed", "source": f"D03 sensitivity scenario: {why}"},
    }
for sid, sn in (("N-AMB-HI", "AMB-WENZ-HI"), ("N-AMB-LO", "AMB-WENZ-LO")):
    cfg["noise_scenarios"].append({"id": sid, "description": f"ambient-limited, isotropic, {sn}",
                                   "components": [{"spectrum": sn, "coherence": {"kind": "spherical"}}],
                                   "self_noise": "SN-S1"})

cfg["experiments"] = []
cfg["mismatch"] = []
cfg["roc_cases"] = []
cfg["waveform_examples"] = []
cfg["trials"] = {0.1: {"cal": 1, "eval": 1, "pos": 1}, 1.0: {"cal": 1, "eval": 1, "pos": 1}}  # unused (SIM-02B.1)
cfg["snr_grid_offsets_db"] = [float(x) for x in range(-16, 7, 2)]

cfg["sim02b2a"] = {
    "nominal_scenario": "N-AMB",
    "cells": [
        {"id": "C1", "band": "B2", "window_s": 1.0},
        {"id": "C2", "band": "B1", "window_s": 1.0},
        {"id": "C3", "band": "B3", "window_s": 0.1},
    ],
    "modes": ["single", "beam_search", "incoherent"],
    "normalizers": [
        {"id": "ORACLE", "type": "oracle"},
        {"id": "NOMINAL", "type": "nominal"},
        {"id": "TREF-CA16", "type": "tref_ca", "M": 16, "guard": 2},
        {"id": "TREF-OS16", "type": "tref_os", "M": 16, "r": 12, "guard": 2},
        {"id": "FREF-CA8", "type": "fref_ca", "L": 8, "G": 2},
        {"id": "FREF-OS8", "type": "fref_os", "L": 8, "G": 2, "r": 12},
    ],
    "contamination_normalizers": [{"id": "TREF-CA16-G8", "type": "tref_ca", "M": 16, "guard": 8}],
    "a0_reference_counts": [4, 8, 16, 32, 64],
    "excluded": [{"normalizer_types": ["fref_ca", "fref_os"], "detector": "energy",
                  "reason": "a broadband signal occupies its own reference bins, so a frequency-reference "
                            "normalizer cancels the signal it is meant to reveal"}],
    "scenarios": [
        {"id": "STAT", "cells": ["C1", "C2", "C3"], "reference": "N-AMB", "test": "N-AMB"},
        {"id": "SHAPE-HI", "cells": ["C1"], "reference": "N-AMB-HI", "test": "N-AMB-HI"},
        {"id": "SHAPE-LO", "cells": ["C1"], "reference": "N-AMB-LO", "test": "N-AMB-LO"},
        {"id": "STEP+1", "cells": ["C1"], "reference": "N-AMB", "test": "N-AMB", "test_offset_db": 1.0},
        {"id": "STEP+3", "cells": ["C1", "C2"], "reference": "N-AMB", "test": "N-AMB", "test_offset_db": 3.0},
        {"id": "INTERF", "cells": ["C1"], "reference": "N-AMB", "test": "N-AMB",
         "interference": {"probability": 0.25, "level_db": 10.0, "spectrum": "AMB-WENZ"}},
        {"id": "COH", "cells": ["C1", "C2"], "reference": "N-FLOW", "test": "N-FLOW"},
        {"id": "CONTAM", "cells": ["C1"], "reference": "N-AMB", "test": "N-AMB",
         "contamination": {"max_onset_windows": 24}, "classes": ["tone", "broadband"]},
    ],
    "pfa": [0.01, 0.001, 0.0001],
    "calibration": {"a0_fast_samples": 100000, "batch": 2000, "max_trials": {"C1": 20000, "C2": 20000, "C3": 20000},
                    "tolerance_db": 0.25, "cmc_samples_per_bin": 64},
    "evaluation": {"null_trials": {"STAT": 10000, "default": 4000}, "positive_trials": 400},
}

hdr = ("# SIM-02B.2-A baseline configuration (study of record). GENERATED by tools/make_sim02b2a_config.py from\n"
       "# configs/sim02b/sim02b1_baseline.yaml; edit the generator, not this file.\n")
(REPO / "configs/sim02b/sim02b2a_baseline.yaml").write_text(hdr + yaml.safe_dump(cfg, sort_keys=False, width=120))

smoke = copy.deepcopy(cfg)
smoke["output"] = {"root": "results/_scratch/sim02b2a_smoke"}
smoke["experiment"]["title"] = "SIM-02B.2-A smoke test (pipeline fixture, not a study)"
smoke["candidates"] = [c for c in cfg["candidates"] if c["id"] in ("A0", "A1")]
s2 = smoke["sim02b2a"]
s2["cells"] = [{"id": "C1", "band": "B2", "window_s": 0.1}, {"id": "C2", "band": "B1", "window_s": 1.0}]
s2["calibration"] = {"a0_fast_samples": 3000, "batch": 300, "max_trials": {"C1": 600, "C2": 600},
                     "tolerance_db": 0.25, "cmc_samples_per_bin": 16}
s2["evaluation"] = {"null_trials": {"STAT": 300, "default": 200}, "positive_trials": 40}
s2["scenarios"] = [
    {"id": "STAT", "cells": ["C1", "C2"], "reference": "N-AMB", "test": "N-AMB"},
    {"id": "STEP+3", "cells": ["C1"], "reference": "N-AMB", "test": "N-AMB", "test_offset_db": 3.0},
    {"id": "INTERF", "cells": ["C1"], "reference": "N-AMB", "test": "N-AMB",
     "interference": {"probability": 0.25, "level_db": 10.0, "spectrum": "AMB-WENZ"}},
    {"id": "CONTAM", "cells": ["C1"], "reference": "N-AMB", "test": "N-AMB",
     "contamination": {"max_onset_windows": 24}, "classes": ["tone", "broadband"]},
]
smoke["sim02b2a"]["pfa"] = [0.01]
(REPO / "configs/sim02b/sim02b2a_smoke.yaml").write_text(
    "# GENERATED by tools/make_sim02b2a_config.py; pipeline test fixture only.\n"
    + yaml.safe_dump(smoke, sort_keys=False, width=120))
print("wrote configs/sim02b/sim02b2a_baseline.yaml and sim02b2a_smoke.yaml")
