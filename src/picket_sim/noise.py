"""Noise coherence models and array gain (extension point, ADR-0007).

Array gain of weights ``w`` for a plane-wave signal with manifold ``a0`` in noise with spatial
coherence ``Gamma`` (unit noise power per sensor, ``Gamma_nn = 1``):

    AG = |w^H a0|^2 / (w^H Gamma w)

* Spatially white (uncorrelated) noise, ``Gamma = I``: white-noise gain ``WNG``; ``N`` for DAS.
* Spherically isotropic (diffuse 3-D) noise, ``Gamma_mn = sin(k r_mn)/(k r_mn)``: directivity
  index ``DI = 10 log10 AG``. Equivalently ``DI = 10 log10(4 pi / integral P dOmega)`` for the
  normalized power pattern ``P`` (identity used as an independent check).

These are *ideal* gains in *model* noise fields. They are not detection performance: real ambient
noise is anisotropic (surface-generated noise is vertically directional, shipping noise is
horizontally concentrated), and sensor self-noise, flow noise and platform noise are not modeled
in SIM-01.
"""

from __future__ import annotations

import numpy as np

from .acoustics import PlaneWaveManifold, wavenumber_rad_per_m
from .beamforming import das_weights
from .geometry import ArrayGeometry

__all__ = [
    "coherence_white",
    "coherence_spherical_isotropic",
    "array_gain",
    "array_gain_db",
    "directivity_index_db",
    "white_noise_gain_db",
    "directivity_index_from_pattern_db",
]


def coherence_white(n_elements: int) -> np.ndarray:
    return np.eye(n_elements)


def coherence_spherical_isotropic(geometry: ArrayGeometry, f_hz: float, c_mps: float) -> np.ndarray:
    """``sinc(k r_mn) = sin(k r_mn) / (k r_mn)`` (unnormalized sinc), ones on the diagonal."""
    k = float(wavenumber_rad_per_m(f_hz, c_mps))
    x = k * geometry.pairwise_distances_m
    return np.sinc(x / np.pi)  # numpy sinc(t) = sin(pi t)/(pi t)


def array_gain(weights: np.ndarray, a0: np.ndarray, coherence: np.ndarray) -> float:
    w = np.asarray(weights, dtype=complex)
    a0 = np.asarray(a0, dtype=complex)
    sig = np.abs(np.vdot(w, a0)) ** 2
    noise = np.real(np.vdot(w, coherence @ w))
    if noise <= 0:
        raise ValueError("non-positive output noise power; coherence matrix not positive definite?")
    return float(sig / noise)


def array_gain_db(weights, a0, coherence) -> float:
    return 10.0 * np.log10(array_gain(weights, a0, coherence))


def directivity_index_db(manifold: PlaneWaveManifold, f_hz: float, steer_u) -> np.ndarray:
    """DAS directivity index (dB) against spherically isotropic noise, closed form.

    ``steer_u`` may be ``(3,)`` or ``(S, 3)``; returns a scalar array or ``(S,)``.
    Uses ``DI = N^2 / (a0^H Gamma a0)`` for ``w = a0/N``.
    """
    if manifold.element_response is not None:
        raise NotImplementedError("closed-form DI assumes omnidirectional elements")
    gam = coherence_spherical_isotropic(manifold.geometry, f_hz, manifold.c_mps)
    a0 = np.atleast_2d(manifold.vectors(np.asarray(steer_u, dtype=float), f_hz))
    n = a0.shape[-1]
    quad = np.real(np.einsum("sm,mn,sn->s", np.conj(a0), gam, a0))
    di = 10.0 * np.log10(n * n / quad)
    return di[0] if np.ndim(steer_u) == 1 else di


def white_noise_gain_db(manifold: PlaneWaveManifold, f_hz: float, steer_u) -> float:
    a0 = manifold.vectors(np.asarray(steer_u, dtype=float), f_hz)
    return array_gain_db(das_weights(a0), a0, coherence_white(a0.shape[-1]))


def directivity_index_from_pattern_db(power: np.ndarray, weights_sr: np.ndarray) -> np.ndarray:
    """Numerical DI = 10 log10(4 pi / sum(P * dOmega)) over a quadrature grid.

    ``power`` ``(..., G)`` normalized to 1 in the steering direction; ``weights_sr`` ``(G,)``
    quadrature weights in steradians summing to 4 pi.
    """
    integral = np.asarray(power) @ np.asarray(weights_sr)
    return 10.0 * np.log10(4.0 * np.pi / integral)
