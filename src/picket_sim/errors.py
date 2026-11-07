"""Channel errors: gain, phase, position and timing (ADR-0012).

Per channel n, independent zero-mean Gaussian draws:
    gain:     20 log10 g_n ~ N(0, sigma_gain_db^2)      (log-normal amplitude)
    phase:    phi_n ~ N(0, sigma_phase^2)
    position: delta_n ~ N(0, sigma_pos^2 I_3)           (true = nominal + delta)
    timing:   tau_n ~ N(0, sigma_t^2)                    (phase -2 pi f tau_n after sampling)

Closed forms for uniform weights (used as verification and self-checks), with total phase variance
sigma^2 = sigma_phi^2 + (k sigma_pos)^2 + (2 pi f sigma_t)^2 and log-normal gain moments:
    E|B(u_s)|^2 = [N E g^2 + N (N - 1) (E g)^2 exp(-sigma^2)] / N^2
    E|B_null|^2 = [E g^2 - (E g)^2 exp(-sigma^2)] / N
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .params import Param, ParamError, collect

__all__ = ["ErrorModel", "ErrorDraw", "error_model_from_config"]

_LN10_20 = np.log(10.0) / 20.0


@dataclass(frozen=True)
class ErrorDraw:
    gain: np.ndarray  # (T, N) linear amplitude
    phase_rad: np.ndarray  # (T, N)
    position_m: np.ndarray  # (T, N, 3)
    timing_s: np.ndarray  # (T, N)

    def channel(self, f_hz: float) -> np.ndarray:
        """Complex per-channel transfer error (T, N): gain, phase and timing."""
        return self.gain * np.exp(1j * self.phase_rad) * np.exp(-2j * np.pi * f_hz * self.timing_s)


@dataclass(frozen=True)
class ErrorModel:
    scenario_id: str
    sigma_gain_db: float
    sigma_phase_deg: float
    sigma_position_m: float
    sigma_timing_s: float

    def __post_init__(self):
        for name in ("sigma_gain_db", "sigma_phase_deg", "sigma_position_m", "sigma_timing_s"):
            v = getattr(self, name)
            if not np.isfinite(v) or v < 0:
                raise ParamError(f"{self.scenario_id}: {name} must be finite and non-negative")

    @property
    def is_ideal(self) -> bool:
        return not any((self.sigma_gain_db, self.sigma_phase_deg, self.sigma_position_m, self.sigma_timing_s))

    def sample(self, rng: np.random.Generator, n_trials: int, n_elements: int) -> ErrorDraw:
        if n_trials < 1:
            raise ParamError("n_trials must be >= 1")
        t, n = n_trials, n_elements
        gain = 10.0 ** (rng.normal(0.0, 1.0, (t, n)) * self.sigma_gain_db / 20.0)
        phase = rng.normal(0.0, 1.0, (t, n)) * np.deg2rad(self.sigma_phase_deg)
        pos = rng.normal(0.0, 1.0, (t, n, 3)) * self.sigma_position_m
        tau = rng.normal(0.0, 1.0, (t, n)) * self.sigma_timing_s
        return ErrorDraw(gain, phase, pos, tau)

    def phase_variance_rad2(self, f_hz: float, c_mps: float) -> float:
        k = 2 * np.pi * f_hz / c_mps
        return (np.deg2rad(self.sigma_phase_deg) ** 2 + (k * self.sigma_position_m) ** 2
                + (2 * np.pi * f_hz * self.sigma_timing_s) ** 2)

    def gain_moments(self) -> tuple[float, float]:
        s = _LN10_20 * self.sigma_gain_db
        return float(np.exp(0.5 * s * s)), float(np.exp(2.0 * s * s))

    def expected_mainlobe_power(self, n: int, f_hz: float, c_mps: float) -> float:
        eg, eg2 = self.gain_moments()
        e = np.exp(-self.phase_variance_rad2(f_hz, c_mps))
        return float((n * eg2 + n * (n - 1) * eg * eg * e) / n ** 2)

    def expected_null_power(self, n: int, f_hz: float, c_mps: float) -> float:
        eg, eg2 = self.gain_moments()
        e = np.exp(-self.phase_variance_rad2(f_hz, c_mps))
        return float((eg2 - eg * eg * e) / n)


def error_model_from_config(spec: dict) -> tuple[ErrorModel, list[Param]]:
    p = collect(spec, spec["id"], ["sigma_gain_db", "sigma_phase_deg", "sigma_position_m", "sigma_timing_s"])
    return ErrorModel(spec["id"], *(p[k].value for k in ("sigma_gain_db", "sigma_phase_deg", "sigma_position_m",
                                                          "sigma_timing_s"))), list(p.values())
