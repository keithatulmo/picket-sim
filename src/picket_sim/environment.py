"""SIM-02B.1 environmental and sensor inputs with provenance (ADR-0017).

Spectrum types (configuration ``spectra``):

* ``coates_wenz``: the Wenz-type empirical ambient-noise formulas attributed to Coates (1989) and printed
  by Stojanovic (2007), Eq. (6), f in kHz, levels in dB re 1 uPa^2/Hz (published, secondary source):
      10 log Nt  = 17 - 30 log f
      10 log Ns  = 40 + 20 (s - 0.5) + 26 log f - 60 log(f + 0.03)
      10 log Nw  = 50 + 7.5 w^(1/2) + 20 log f - 40 log(f + 0.4)
      10 log Nth = -15 + 20 log f
      N = Nt + Ns + Nw + Nth (linear power sum)
  The shipping activity s (0 to 1) and wind speed w (m/s) are scenario choices with their own provenance.
  Evaluation outside the configured frequency range fails visibly.
* ``power_law``: the SIM-02A assumed envelope L + slope log10(f / f_ref).
* ``scaled``: another spectrum times 10^(offset/10) (assumption-labeled level offsets for mismatch tests).

Self-noise types (configuration ``self_noise``): ``chain`` (SIM-02A acquisition chain, input-referred),
``relative`` (a spectrum times 10^(ratio/10), an assumed sensor-limited condition), ``none``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .params import Param, ParamError, parse_param
from .sensor import PowerLawSpectrum, chain_from_config

__all__ = ["CoatesWenz", "RangeLimited", "Scaled", "spectrum_from_config", "self_noise_from_config"]


@dataclass(frozen=True)
class CoatesWenz:
    """Coates (1989) Wenz-type ambient noise, as printed by Stojanovic (2007) Eq. (6); uPa^2/Hz."""

    shipping: float
    wind_m_per_s: float

    def components_db(self, f_hz) -> dict:
        f = np.asarray(f_hz, dtype=float) / 1000.0  # the formulas take f in kHz
        lf = np.log10(f)
        return {
            "turbulence": 17.0 - 30.0 * lf,
            "shipping": 40.0 + 20.0 * (self.shipping - 0.5) + 26.0 * lf - 60.0 * np.log10(f + 0.03),
            "wind": 50.0 + 7.5 * np.sqrt(self.wind_m_per_s) + 20.0 * lf - 40.0 * np.log10(f + 0.4),
            "thermal": -15.0 + 20.0 * lf,
        }

    def __call__(self, f_hz) -> np.ndarray:
        return sum(10.0 ** (v / 10.0) for v in self.components_db(f_hz).values())


@dataclass(frozen=True)
class RangeLimited:
    """Wrap a spectrum so that evaluation outside [f_lo, f_hi] raises (no silent extrapolation)."""

    inner: Callable
    f_lo: float
    f_hi: float
    name: str

    def __call__(self, f_hz) -> np.ndarray:
        f = np.asarray(f_hz, dtype=float)
        if f.size and (np.min(f) < self.f_lo * (1 - 1e-12) or np.max(f) > self.f_hi * (1 + 1e-12)):
            raise ParamError(f"{self.name}: evaluated at {np.min(f):g} to {np.max(f):g} Hz, outside its stated "
                             f"range {self.f_lo:g} to {self.f_hi:g} Hz")
        return self.inner(f)


@dataclass(frozen=True)
class Scaled:
    inner: Callable
    offset_db: float

    def __call__(self, f_hz) -> np.ndarray:
        return self.inner(f_hz) * 10.0 ** (self.offset_db / 10.0)


def _p(block: dict, key: str, ctx: str, out: list) -> Param:
    if key not in block:
        raise ParamError(f"{ctx}: missing required parameter '{key}'")
    prm = parse_param(key, block[key], ctx, require_d01=True)
    out.append(prm)
    return prm


def spectrum_from_config(sid: str, spec: dict, known: dict, params: list) -> Callable:
    """Build one spectrum (callable G(f) in uPa^2/Hz); ``known`` holds spectra defined earlier."""
    ctx = f"spectra.{sid}"
    kind = spec.get("type")
    if kind == "coates_wenz":
        s = _p(spec, "shipping_activity", ctx, params).value
        w = _p(spec, "wind_speed_m_per_s", ctx, params).value
        rng = spec.get("valid_range_hz")
        if not (isinstance(rng, list) and len(rng) == 2 and 0 < rng[0] < rng[1]):
            raise ParamError(f"{ctx}: valid_range_hz [f_lo, f_hi] is required")
        src = str(spec.get("model_source", "")).strip()
        if len(src) < 20:
            raise ParamError(f"{ctx}: model_source must cite the document the equations were read from")
        params.append(Param("coates_wenz_equations", float("nan"), "dB re 1 uPa^2/Hz", "published", src, ctx,
                            f"{rng[0]:g} to {rng[1]:g} Hz (as used)", str(spec.get("applicability", "")),
                            str(spec.get("uncertainty", ""))))
        return RangeLimited(CoatesWenz(s, w), float(rng[0]), float(rng[1]), ctx)
    if kind == "power_law":
        lvl = _p(spec, "level_db_re_1upa2_per_hz", ctx, params).value
        fr = _p(spec, "reference_frequency_hz", ctx, params).value
        sl = _p(spec, "slope_db_per_decade", ctx, params).value
        return PowerLawSpectrum(sid, lvl, fr, sl)
    if kind == "scaled":
        base = spec.get("base")
        if base not in known:
            raise ParamError(f"{ctx}: base spectrum {base!r} is not defined earlier")
        return Scaled(known[base], _p(spec, "ratio_db", ctx, params).value)
    raise ParamError(f"{ctx}: unknown spectrum type {kind!r}")


def self_noise_from_config(sid: str, spec: dict, spectra: dict, params: list):
    """Input-referred self-noise callable (uPa^2/Hz) and, for chains, the chain object."""
    ctx = f"self_noise.{sid}"
    kind = spec.get("type")
    if kind == "chain":
        chain, ps = chain_from_config(spec["chain"])
        params.extend(ps)
        return chain.self_noise_upa2_per_hz, chain
    if kind == "relative":
        base = spec.get("spectrum")
        if base not in spectra:
            raise ParamError(f"{ctx}: spectrum {base!r} is not defined")
        return Scaled(spectra[base], _p(spec, "ratio_db", ctx, params).value), None
    if kind == "none":
        return None, None
    raise ParamError(f"{ctx}: unknown self-noise type {kind!r}")
