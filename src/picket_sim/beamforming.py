"""Conventional delay-and-sum (DAS) beamforming and normalized beampatterns (ADR-0004).

* DAS weights steered to u0: ``w = a(u0) / N`` so that ``w^H a(u0) = 1``.
* Array response: ``y(u) = w^H a(u)``.
* Normalized power pattern: ``P(u; u0) = |w^H a(u)|^2 / |w^H a(u0)|^2``.

Normalization is always to the response in the steering direction, never to the maximum of a
sampled grid (a grid maximum can hide steering or convention errors).
"""

from __future__ import annotations

import numpy as np

from .acoustics import PlaneWaveManifold

__all__ = [
    "das_weights",
    "array_response",
    "normalized_power",
    "beampattern_power",
    "power_to_db",
]


def das_weights(a0: np.ndarray) -> np.ndarray:
    """Uniform DAS weights for steering vector(s) ``a0`` (shape ``(..., N)``)."""
    a0 = np.asarray(a0, dtype=complex)
    return a0 / a0.shape[-1]


def array_response(weights: np.ndarray, a: np.ndarray) -> np.ndarray:
    """``w^H a`` for weights ``(S, N)`` and manifold vectors ``(..., N)`` -> ``(S, ...)``.

    A single weight vector ``(N,)`` returns shape ``a.shape[:-1]``.
    """
    w = np.asarray(weights, dtype=complex)
    a = np.asarray(a, dtype=complex)
    if w.ndim == 1:
        return a @ np.conj(w)
    flat = a.reshape(-1, a.shape[-1])
    out = np.conj(w) @ flat.T
    return out.reshape((w.shape[0],) + a.shape[:-1])


def normalized_power(weights: np.ndarray, a: np.ndarray, a0: np.ndarray) -> np.ndarray:
    """``|w^H a|^2 / |w^H a0|^2`` for general weights.

    ``weights`` ``(N,)`` with ``a0`` ``(N,)``, or ``weights`` ``(S, N)`` with ``a0`` ``(S, N)``
    (one steering vector per weight vector). ``a`` is ``(..., N)``. Returns ``a.shape[:-1]`` or
    ``(S,) + a.shape[:-1]``.
    """
    w = np.asarray(weights, dtype=complex)
    a0 = np.asarray(a0, dtype=complex)
    if a0.shape != w.shape:
        raise ValueError(f"a0 shape {a0.shape} must match weights shape {w.shape}")
    num = np.abs(array_response(w, a)) ** 2
    ref = np.abs(np.sum(np.conj(w) * a0, axis=-1)) ** 2
    if np.any(ref <= 0):
        raise ValueError("weights have zero response in the steering direction")
    if w.ndim == 1:
        return num / ref
    return num / ref.reshape((-1,) + (1,) * (num.ndim - 1))


def beampattern_power(manifold: PlaneWaveManifold, f_hz: float, steer_u, look_u) -> np.ndarray:
    """Normalized DAS power pattern.

    ``steer_u`` ``(3,)`` or ``(S, 3)``; ``look_u`` ``(..., 3)``. Returns ``look.shape[:-1]`` for a
    single steering direction, else ``(S,) + look.shape[:-1]``.
    """
    steer_u = np.asarray(steer_u, dtype=float)
    a0 = manifold.vectors(steer_u, f_hz)
    w = das_weights(a0)
    a = manifold.vectors(look_u, f_hz)
    p = normalized_power(w, a, a0)
    # Uniform DAS with unit-modulus manifold vectors satisfies 0 <= P <= 1 (Cauchy-Schwarz).
    # Anything above 1 beyond rounding indicates a normalization or manifold error.
    if manifold.element_response is None and np.any(p > 1.0 + 1e-9):
        raise FloatingPointError("normalized DAS power exceeds 1: normalization error")
    return np.clip(p, 0.0, 1.0) if manifold.element_response is None else p


def power_to_db(p, floor_db: float | None = None) -> np.ndarray:
    """10 log10(p), optionally clamped below at ``floor_db`` (for display only)."""
    p = np.asarray(p, dtype=float)
    with np.errstate(divide="ignore"):
        db = 10.0 * np.log10(np.where(p > 0, p, 0.0))
    if floor_db is not None:
        db = np.maximum(db, floor_db)
    return db
