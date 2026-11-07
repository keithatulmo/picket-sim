"""Machine-readable experiment configuration: loading, validation, geometry construction.

Configuration keys carry SI units in their names (``_m``, ``_hz``, ``_mps``, ``_deg``). Validation
rejects values that are almost certainly unit errors (e.g. sound speed in km/s, frequencies in
kHz, positions in millimetres).
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from .acoustics import validate_sound_speed
from .geometry import (
    ArrayGeometry,
    envelope_volumetric,
    from_coordinates,
    uniform_circular,
    rotation_matrix_from_axes,
    single_hydrophone,
    uniform_linear,
    uniform_rectangular,
)

__all__ = ["load_config", "validate_config", "build_array", "config_sha256", "ConfigError"]

MAX_COORD_M = 100.0  # |coordinate| limit; larger values are treated as unit errors
MIN_SPACING_M = 1e-3
FREQ_LIMITS_HZ = (1.0, 200_000.0)


class ConfigError(ValueError):
    pass


def load_config(path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    validate_config(cfg)
    return cfg


def config_sha256(cfg: dict) -> str:
    """Hash of the canonical JSON serialization of a configuration."""
    blob = json.dumps(cfg, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _req(d: dict, key: str, ctx: str):
    if key not in d:
        raise ConfigError(f"{ctx}: missing required key '{key}'")
    return d[key]


def _check_freq(v, ctx):
    v = float(v)
    lo, hi = FREQ_LIMITS_HZ
    if not (lo <= v <= hi):
        raise ConfigError(f"{ctx}: frequency {v} Hz outside [{lo}, {hi}] Hz (units must be Hz)")
    return v


def _check_sound_speed(v, ctx):
    try:
        return validate_sound_speed(v)
    except ValueError as exc:
        raise ConfigError(f"{ctx}: {exc}") from None


def build_array(spec: dict) -> ArrayGeometry:
    """Construct an :class:`ArrayGeometry` from a configuration entry."""
    ctx = f"array {spec.get('id', '?')}"
    aid = str(_req(spec, "id", "array"))
    kind = str(_req(spec, "type", ctx))
    desc = str(spec.get("description", "")).strip()
    if kind == "single":
        geom = single_hydrophone(aid, spec.get("position_m", (0.0, 0.0, 0.0)), desc)
    elif kind == "linear":
        n = int(_req(spec, "n_elements", ctx))
        d = float(_req(spec, "spacing_m", ctx))
        if n > 1 and d < MIN_SPACING_M:
            raise ConfigError(f"{ctx}: spacing_m {d} below {MIN_SPACING_M} m")
        geom = uniform_linear(n, d, spec.get("axis", (1.0, 0.0, 0.0)), aid, desc)
    elif kind == "rectangular":
        geom = uniform_rectangular(
            int(_req(spec, "nx", ctx)), int(_req(spec, "ny", ctx)),
            float(_req(spec, "dx_m", ctx)), float(_req(spec, "dy_m", ctx)),
            spec.get("axis_u", (1.0, 0.0, 0.0)), spec.get("axis_v", (0.0, 1.0, 0.0)), aid, desc,
        )
    elif kind == "circular":
        geom = uniform_circular(int(_req(spec, "n_elements", ctx)), float(_req(spec, "diameter_m", ctx)), aid, desc,
                                spec.get("axis_u", (1.0, 0.0, 0.0)), spec.get("axis_v", (0.0, 1.0, 0.0)),
                                float(spec.get("start_angle_deg", 0.0)))
    elif kind == "envelope":
        env = _req(spec, "envelope_m", ctx)
        if len(env) != 3:
            raise ConfigError(f"{ctx}: envelope_m must be [length, width, height]")
        geom = envelope_volumetric(float(env[0]), float(env[1]), float(env[2]), aid, desc)
    elif kind == "coordinates":
        pos = np.asarray(_req(spec, "positions_m", ctx), dtype=float)
        if pos.ndim != 2 or pos.shape[1] != 3:
            raise ConfigError(f"{ctx}: positions_m must be a list of [x, y, z] triples")
        geom = from_coordinates(pos, aid, desc, spec.get("element_ids", ()))
    else:
        raise ConfigError(f"{ctx}: unknown array type '{kind}'")
    if "rotation" in spec:
        rot = spec["rotation"]
        geom = geom.rotated(rotation_matrix_from_axes(rot["axis"], float(rot["angle_deg"])))
    if "scale" in spec:
        geom = geom.scaled(float(spec["scale"]))
    if np.max(np.abs(geom.positions_m)) > MAX_COORD_M:
        raise ConfigError(f"{ctx}: coordinates exceed {MAX_COORD_M} m (units must be metres)")
    if geom.n_elements > 1 and geom.min_spacing_m < MIN_SPACING_M:
        raise ConfigError(f"{ctx}: elements closer than {MIN_SPACING_M} m (coincident sensors?)")
    return geom


def lattice_spacing_m(spec: dict) -> float | None:
    """Lattice period relevant to exact grating lobes (None for non-lattice geometries)."""
    kind = spec.get("type")
    scale = float(spec.get("scale", 1.0))
    if kind == "linear" and int(spec["n_elements"]) > 1:
        return float(spec["spacing_m"]) * scale
    if kind == "rectangular":
        ds = []
        if int(spec["nx"]) > 1:
            ds.append(float(spec["dx_m"]))
        if int(spec["ny"]) > 1:
            ds.append(float(spec["dy_m"]))
        return min(ds) * scale if ds else None
    return None


def validate_config(cfg: dict) -> None:
    if not isinstance(cfg, dict):
        raise ConfigError("configuration must be a mapping")
    exp = _req(cfg, "experiment", "config")
    _req(exp, "id", "experiment")
    phys = _req(cfg, "physics", "config")
    _check_sound_speed(_req(phys, "sound_speed_mps", "physics"), "physics.sound_speed_mps")
    fg = _req(cfg, "frequency_grid", "config")
    f0 = _check_freq(_req(fg, "f_min_hz", "frequency_grid"), "frequency_grid.f_min_hz")
    f1 = _check_freq(_req(fg, "f_max_hz", "frequency_grid"), "frequency_grid.f_max_hz")
    if f1 <= f0:
        raise ConfigError("frequency_grid: f_max_hz must exceed f_min_hz")
    if int(_req(fg, "points_per_decade", "frequency_grid")) < 2:
        raise ConfigError("frequency_grid.points_per_decade must be >= 2")
    for f in cfg.get("representative_frequencies_hz", []):
        _check_freq(f, "representative_frequencies_hz")
    arrays = _req(cfg, "arrays", "config")
    ids = [a.get("id") for a in arrays]
    if len(set(ids)) != len(ids):
        raise ConfigError("array ids must be unique")
    for spec in arrays:
        build_array(spec)
    st = _req(cfg, "steering", "config")
    for ring in _req(st, "rings", "steering"):
        el = float(_req(ring, "el_deg", "steering ring"))
        if not -90.0 <= el <= 90.0:
            raise ConfigError("steering ring el_deg must be within [-90, 90] degrees")
        step = float(_req(ring, "az_step_deg", "steering ring"))
        if not 0 < step <= 180 or (360.0 / step) % 1:
            raise ConfigError("steering ring az_step_deg must divide 360")
    g = _req(cfg, "grids", "config")
    sp = _req(g, "sphere", "grids")
    if int(sp["n_az"]) % 2:
        raise ConfigError("grids.sphere.n_az must be even")
    if int(g.get("cut_points", 3600)) % 2:
        raise ConfigError("grids.cut_points must be even")
    rob = cfg.get("robustness", {})
    for c in rob.get("sound_speeds_mps", []):
        _check_sound_speed(c, "robustness.sound_speeds_mps")
    mm = rob.get("mismatch")
    if mm:
        _check_sound_speed(mm["assumed_mps"], "robustness.mismatch.assumed_mps")
        for c in mm["true_mps"]:
            _check_sound_speed(c, "robustness.mismatch.true_mps")


def resolved_copy(cfg: dict) -> dict:
    return copy.deepcopy(cfg)
