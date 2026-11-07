"""Hydrophone and acquisition-chain noise, clipping and dynamic range (ADR-0011).

All noise is input-referred to acoustic pressure through the nominal hydrophone sensitivity and
expressed as a one-sided power spectral density in uPa^2/Hz.

* Hydrophone thermal noise: e_th^2 = 4 k T Re(Z), Z = 1 / (j w C (1 - j tan d)).
* Preamplifier: e_n^2 (1 + f_c / f) + i_n^2 |Z|^2 (voltage noise with 1/f corner, current noise into
  the source impedance).
* ADC quantization: (Delta^2 / 12) / (f_s / 2) with Delta = 2 V_fs / 2^bits, referred through G and M.
* Clipping: peak pressure p_clip = min(V_fs, V_pre_max) / (G M).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .params import BOLTZMANN_J_PER_K, Param, ParamError, collect

__all__ = ["Hydrophone", "Preamplifier", "ADC", "AcquisitionChain", "PowerLawSpectrum", "chain_from_config",
           "band_power", "db10"]


def db10(x):
    x = np.asarray(x, dtype=float)
    if np.any(x <= 0):
        raise ValueError("dB of a non-positive power")
    return 10.0 * np.log10(x)


def _f(f_hz):
    f = np.asarray(f_hz, dtype=float)
    if np.any(~np.isfinite(f)) or np.any(f <= 0):
        raise ValueError("frequencies must be positive and finite (Hz)")
    return f


@dataclass(frozen=True)
class Hydrophone:
    sensitivity_db_re_1v_per_upa: float
    capacitance_f: float
    loss_tangent: float
    temperature_k: float

    @property
    def sensitivity_v_per_upa(self) -> float:
        return 10.0 ** (self.sensitivity_db_re_1v_per_upa / 20.0)

    def impedance_ohm(self, f_hz) -> np.ndarray:
        w = 2 * np.pi * _f(f_hz)
        return 1.0 / (1j * w * self.capacitance_f * (1.0 - 1j * self.loss_tangent))

    def thermal_noise_v2_per_hz(self, f_hz) -> np.ndarray:
        return 4.0 * BOLTZMANN_J_PER_K * self.temperature_k * np.real(self.impedance_ohm(f_hz))


@dataclass(frozen=True)
class Preamplifier:
    gain_db: float
    voltage_noise_v_per_rthz: float
    current_noise_a_per_rthz: float
    flicker_corner_hz: float
    max_output_v_peak: float

    @property
    def gain(self) -> float:
        return 10.0 ** (self.gain_db / 20.0)

    def input_noise_v2_per_hz(self, f_hz, source_impedance_ohm) -> np.ndarray:
        f = _f(f_hz)
        en2 = self.voltage_noise_v_per_rthz ** 2 * (1.0 + self.flicker_corner_hz / f)
        return en2 + self.current_noise_a_per_rthz ** 2 * np.abs(source_impedance_ohm) ** 2


@dataclass(frozen=True)
class ADC:
    bits: float
    full_scale_v_peak: float
    sample_rate_hz: float

    @property
    def lsb_v(self) -> float:
        return 2.0 * self.full_scale_v_peak / 2.0 ** self.bits

    @property
    def quantization_psd_v2_per_hz(self) -> float:
        return (self.lsb_v ** 2 / 12.0) / (self.sample_rate_hz / 2.0)


@dataclass(frozen=True)
class AcquisitionChain:
    """Hydrophone + preamplifier + ADC with a declared usable band [bandwidth_low, bandwidth_high]."""

    scenario_id: str
    hydrophone: Hydrophone
    preamp: Preamplifier
    adc: ADC
    bandwidth_low_hz: float
    bandwidth_high_hz: float

    def __post_init__(self):
        if not self.bandwidth_low_hz < self.bandwidth_high_hz:
            raise ParamError(f"{self.scenario_id}: bandwidth_low_hz must be below bandwidth_high_hz")
        if self.bandwidth_high_hz >= self.adc.sample_rate_hz / 2.0:
            raise ParamError(f"{self.scenario_id}: declared bandwidth reaches or exceeds Nyquist "
                             f"({self.adc.sample_rate_hz / 2:g} Hz)")

    def check_band(self, f_lo: float, f_hi: float) -> None:
        """Fail visibly if an analysis band is outside what the scenario can acquire."""
        if f_hi >= self.adc.sample_rate_hz / 2.0:
            raise ParamError(f"{self.scenario_id}: band edge {f_hi:g} Hz at or above Nyquist "
                             f"{self.adc.sample_rate_hz / 2:g} Hz")
        if f_lo < self.bandwidth_low_hz or f_hi > self.bandwidth_high_hz:
            raise ParamError(f"{self.scenario_id}: band [{f_lo:g}, {f_hi:g}] Hz outside declared usable bandwidth "
                             f"[{self.bandwidth_low_hz:g}, {self.bandwidth_high_hz:g}] Hz")

    def covers(self, f_lo: float, f_hi: float) -> bool:
        try:
            self.check_band(f_lo, f_hi)
            return True
        except ParamError:
            return False

    # ---- input-referred noise components, uPa^2/Hz
    def thermal_upa2_per_hz(self, f_hz) -> np.ndarray:
        m = self.hydrophone.sensitivity_v_per_upa
        return self.hydrophone.thermal_noise_v2_per_hz(f_hz) / m ** 2

    def preamp_upa2_per_hz(self, f_hz) -> np.ndarray:
        m = self.hydrophone.sensitivity_v_per_upa
        z = self.hydrophone.impedance_ohm(f_hz)
        return self.preamp.input_noise_v2_per_hz(f_hz, z) / m ** 2

    def adc_upa2_per_hz(self, f_hz) -> np.ndarray:
        m, g = self.hydrophone.sensitivity_v_per_upa, self.preamp.gain
        return np.full(np.shape(_f(f_hz)), self.adc.quantization_psd_v2_per_hz / (g * m) ** 2)

    def electronic_upa2_per_hz(self, f_hz) -> np.ndarray:
        """Noise added after the sensitivity element (preamplifier + ADC): not scaled by sensitivity errors."""
        return self.preamp_upa2_per_hz(f_hz) + self.adc_upa2_per_hz(f_hz)

    def self_noise_upa2_per_hz(self, f_hz) -> np.ndarray:
        return self.thermal_upa2_per_hz(f_hz) + self.electronic_upa2_per_hz(f_hz)

    @property
    def clip_pressure_upa_peak(self) -> float:
        m, g = self.hydrophone.sensitivity_v_per_upa, self.preamp.gain
        return min(self.adc.full_scale_v_peak, self.preamp.max_output_v_peak) / (g * m)

    @property
    def clipping_stage(self) -> str:
        return "adc" if self.adc.full_scale_v_peak <= self.preamp.max_output_v_peak else "preamplifier"

    def dynamic_range_db(self, f_lo: float, f_hi: float, crest_factor_db: float, ambient=None) -> dict:
        """Largest rms signal before clipping (for the crest factor) over the band noise power."""
        self.check_band(f_lo, f_hi)
        self_pow = band_power(self.self_noise_upa2_per_hz, f_lo, f_hi)
        amb_pow = band_power(ambient, f_lo, f_hi) if ambient is not None else 0.0
        max_rms_db = 20 * np.log10(self.clip_pressure_upa_peak) - crest_factor_db
        return {
            "self_noise_band_db": float(db10(self_pow)),
            "ambient_band_db": float(db10(amb_pow)) if amb_pow > 0 else float("nan"),
            "total_noise_band_db": float(db10(self_pow + amb_pow)),
            "max_rms_signal_db_re_1upa": float(max_rms_db),
            "dr_over_self_noise_db": float(max_rms_db - db10(self_pow)),
            "dr_over_total_noise_db": float(max_rms_db - db10(self_pow + amb_pow)),
            "ambient_minus_self_band_db": float(db10(amb_pow) - db10(self_pow)) if amb_pow > 0 else float("nan"),
        }


@dataclass(frozen=True)
class PowerLawSpectrum:
    """S(f) = 10^((L + slope * log10(f / f_ref)) / 10) uPa^2/Hz (assumed scenario shape)."""

    scenario_id: str
    level_db_re_1upa2_per_hz: float
    reference_frequency_hz: float
    slope_db_per_decade: float

    def __call__(self, f_hz) -> np.ndarray:
        f = _f(f_hz)
        lvl = self.level_db_re_1upa2_per_hz + self.slope_db_per_decade * np.log10(f / self.reference_frequency_hz)
        return 10.0 ** (lvl / 10.0)


def band_power(psd, f_lo: float, f_hi: float, n: int = 2001) -> float:
    """Integral of a PSD over [f_lo, f_hi] (trapezoid on a log-spaced grid, uPa^2)."""
    if psd is None:
        return 0.0
    if not 0 < f_lo < f_hi:
        raise ValueError("band must satisfy 0 < f_lo < f_hi")
    f = np.logspace(np.log10(f_lo), np.log10(f_hi), n)
    s = np.asarray(psd(f), dtype=float)
    if np.any(~np.isfinite(s)) or np.any(s < 0):
        raise ValueError("PSD must be finite and non-negative")
    return float(np.sum(0.5 * (s[1:] + s[:-1]) * np.diff(f)))


def chain_from_config(spec: dict) -> tuple[AcquisitionChain, list[Param]]:
    sid = spec["id"]
    h = collect(spec["hydrophone"], f"{sid}.hydrophone",
                ["sensitivity_db_re_1v_per_upa", "capacitance_f", "loss_tangent", "temperature_k"])
    p = collect(spec["preamp"], f"{sid}.preamp",
                ["gain_db", "voltage_noise_v_per_rthz", "current_noise_a_per_rthz", "flicker_corner_hz",
                 "max_output_v_peak"])
    a = collect(spec["adc"], f"{sid}.adc", ["bits", "full_scale_v_peak", "sample_rate_hz"])
    b = collect(spec["bandwidth"], f"{sid}.bandwidth", ["bandwidth_low_hz", "bandwidth_high_hz"])
    chain = AcquisitionChain(
        sid,
        Hydrophone(*(h[k].value for k in ("sensitivity_db_re_1v_per_upa", "capacitance_f", "loss_tangent",
                                          "temperature_k"))),
        Preamplifier(*(p[k].value for k in ("gain_db", "voltage_noise_v_per_rthz", "current_noise_a_per_rthz",
                                            "flicker_corner_hz", "max_output_v_peak"))),
        ADC(a["bits"].value, a["full_scale_v_peak"].value, a["sample_rate_hz"].value),
        b["bandwidth_low_hz"].value, b["bandwidth_high_hz"].value,
    )
    return chain, [*h.values(), *p.values(), *a.values(), *b.values()]
