"""Provenance-tagged physical parameters (ADR-0010).

Every SIM-02 physical parameter is written in the configuration as

    key_with_unit_suffix: {value: <number>, provenance: published|measured|assumed, source: "<text>"}

* ``published`` requires a citation in ``source``;
* ``measured`` requires a data reference in ``source``;
* ``assumed`` requires a rationale in ``source``.

Loading fails on missing or unknown provenance, empty source, non-finite values or values outside the
key's plausibility range (which catches unit errors). Nothing is defaulted silently.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["Param", "ParamError", "PROVENANCE", "parse_param", "BOLTZMANN_J_PER_K", "CONSTANTS", "collect"]

PROVENANCE = ("published", "measured", "assumed")


class ParamError(ValueError):
    pass


@dataclass(frozen=True)
class Param:
    name: str
    value: float
    unit: str
    provenance: str
    source: str
    context: str = ""
    frequency_range: str = ""
    applicability: str = ""
    uncertainty: str = ""

    def row(self) -> dict:
        return {"context": self.context, "parameter": self.name, "value": self.value, "unit": self.unit,
                "provenance": self.provenance, "source": self.source}

    def row_full(self) -> dict:
        """Register row with the D01 fields (ADR-0017); ``row`` keeps the SIM-02A table format."""
        return {**self.row(), "frequency_range": self.frequency_range, "applicability": self.applicability,
                "uncertainty": self.uncertainty}


#: Boltzmann constant, exact by the 2019 SI definition.
BOLTZMANN_J_PER_K = 1.380649e-23
CONSTANTS = [
    Param("boltzmann_constant", BOLTZMANN_J_PER_K, "J/K", "published",
          "SI Brochure, 9th edition (BIPM, 2019): exact defining constant k = 1.380649e-23 J/K", "constants"),
]

# key -> (unit, low, high). Ranges are unit-error guards, not claims about products.
SCHEMA: dict[str, tuple[str, float, float]] = {
    "sensitivity_db_re_1v_per_upa": ("dB re 1 V/uPa", -260.0, -100.0),
    "capacitance_f": ("F", 1e-12, 1e-5),
    "loss_tangent": ("1", 0.0, 0.5),
    "temperature_k": ("K", 250.0, 320.0),
    "gain_db": ("dB", -20.0, 100.0),
    "voltage_noise_v_per_rthz": ("V/sqrt(Hz)", 0.0, 1e-5),
    "current_noise_a_per_rthz": ("A/sqrt(Hz)", 0.0, 1e-9),
    "flicker_corner_hz": ("Hz", 0.0, 1e4),
    "max_output_v_peak": ("V", 1e-3, 1e3),
    "bits": ("bit", 4.0, 32.0),
    "full_scale_v_peak": ("V", 1e-3, 1e3),
    "sample_rate_hz": ("Hz", 1e2, 1e7),
    "bandwidth_low_hz": ("Hz", 0.0, 1e6),
    "bandwidth_high_hz": ("Hz", 1.0, 1e6),
    "level_db_re_1upa2_per_hz": ("dB re 1 uPa^2/Hz", -50.0, 200.0),
    "reference_frequency_hz": ("Hz", 1.0, 1e6),
    "slope_db_per_decade": ("dB/decade", -60.0, 60.0),
    "crest_factor_db": ("dB", 0.0, 60.0),
    "sigma_gain_db": ("dB", 0.0, 20.0),
    "sigma_phase_deg": ("deg", 0.0, 180.0),
    "sigma_position_m": ("m", 0.0, 1.0),
    "sigma_timing_s": ("s", 0.0, 1.0),
    "ratio_db": ("dB", -100.0, 100.0),
    "range_m": ("m", 0.0, 1e4),
    "correlation_length_m": ("m", 1e-4, 1e3),
    # SIM-02B.1 (ADR-0017)
    "shipping_activity": ("1", 0.0, 1.0),
    "wind_speed_m_per_s": ("m/s", 0.0, 40.0),
    "duration_s": ("s", 1e-4, 100.0),
    "frequency_hz": ("Hz", 1.0, 1e6),
}

#: Optional D01 fields; required (non-empty) for published or measured records when ``require_d01`` is set.
D01_FIELDS = ("frequency_range", "applicability", "uncertainty")


def parse_param(name: str, spec, context: str = "", require_d01: bool = False) -> Param:
    """Parse one ``{value, provenance, source}`` record for schema key ``name``.

    Optional keys ``frequency_range``, ``applicability`` and ``uncertainty`` are carried into the record;
    with ``require_d01`` they are mandatory for published and measured values (ADR-0017).
    """
    where = f"{context}.{name}" if context else name
    if name not in SCHEMA:
        raise ParamError(f"{where}: unknown parameter key (no unit/range schema)")
    if not isinstance(spec, dict):
        raise ParamError(f"{where}: must be a mapping {{value, provenance, source}}, got {spec!r}")
    missing = {"value", "provenance", "source"} - set(spec)
    if missing:
        raise ParamError(f"{where}: missing {sorted(missing)}")
    prov = spec["provenance"]
    if prov not in PROVENANCE:
        raise ParamError(f"{where}: provenance must be one of {PROVENANCE}, got {prov!r}")
    src = str(spec["source"]).strip()
    if len(src) < 8:
        raise ParamError(f"{where}: source must state a citation, data reference or rationale")
    try:
        val = float(spec["value"])
    except (TypeError, ValueError):
        raise ParamError(f"{where}: value must be numeric") from None
    unit, lo, hi = SCHEMA[name]
    if not math.isfinite(val) or not (lo <= val <= hi):
        raise ParamError(f"{where}: value {val} outside plausible range [{lo}, {hi}] {unit} (unit error?)")
    extra = {k: str(spec.get(k, "")).strip() for k in D01_FIELDS}
    if require_d01 and prov in ("published", "measured"):
        miss = [k for k, v in extra.items() if not v]
        if miss:
            raise ParamError(f"{where}: {prov} values must state {miss} (ADR-0017)")
    return Param(name, val, unit, prov, src, context, **extra)


def collect(block: dict, context: str, keys: list[str]) -> dict[str, Param]:
    """Parse required keys of a configuration block; unknown extra keys are rejected."""
    extra = set(block) - set(keys) - {"id", "label", "description"}
    if extra:
        raise ParamError(f"{context}: unexpected keys {sorted(extra)}")
    return {k: parse_param(k, block.get(k, None) if k in block else _missing(context, k), context) for k in keys}


def _missing(context, key):
    raise ParamError(f"{context}: missing required parameter '{key}'")
