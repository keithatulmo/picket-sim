"""Realized array gain relative to a single identical channel (A0), with and without channel errors.

Normalized units: ambient field power at the reference point = 1 (coherence Gamma with unit
diagonal), sensor self-noise eta (ratio to ambient), split into a part scaled by channel sensitivity
errors (eta_th, hydrophone thermal) and a part added after it (eta_el, electronics), host-noise
ratio hnr with near-field vector h. Signal: plane wave, unit power at every sensor.

Without errors, DAS weights w = a/N:
    RAG = (1 + eta + hnr) / (w^H (Gamma + eta I + hnr h h^H) w)
which equals N for white noise and the SIM-01 DI for isotropic noise with eta = hnr = 0.

With errors (D = diag(d), d = gain * exp(j phase) * exp(-j 2 pi f tau), true positions r + delta):
    s = d * a(u; r + delta),   R = D (Gamma(r + delta) + eta_th I) D^H + eta_el I
    RAG = |w^H s|^2 (1 + eta_th + eta_el) / (w^H R w)
These are SNR ratios, not detection performance.
"""

from __future__ import annotations

import numpy as np

from .acoustics import steering_vectors
from .errors import ErrorDraw
from .noisefields import check_covariance, coherence_spherical

__all__ = ["rag_db", "rag_with_errors_db", "horizontal_scan_with_errors"]


def _db(x):
    x = np.asarray(x, dtype=float)
    if np.any(x <= 0) or np.any(~np.isfinite(x)):
        raise FloatingPointError("non-positive or non-finite gain")
    return 10 * np.log10(x)


def rag_db(positions_m, f_hz: float, c_mps: float, steer_u, gamma, eta: float = 0.0, hnr: float = 0.0,
           host_vector=None) -> np.ndarray:
    """RAG (dB) for steering directions ``steer_u`` (S, 3); target in the steering direction."""
    if eta < 0 or hnr < 0:
        raise ValueError("noise ratios must be non-negative")
    n = len(positions_m)
    r = np.array(gamma, dtype=complex) + eta * np.eye(n)
    if hnr > 0:
        h = np.asarray(host_vector, dtype=complex)
        r = r + hnr * np.outer(h, h.conj())
    check_covariance(r, "RAG covariance")
    a = steering_vectors(positions_m, np.atleast_2d(steer_u), f_hz, c_mps)  # (S, N)
    w = a / n
    den = np.real(np.einsum("sm,mn,sn->s", w.conj(), r, w))
    return _db((1.0 + eta + hnr) / den)


def rag_with_errors_db(positions_m, f_hz: float, c_mps: float, u_s, draw: ErrorDraw, eta_th: float,
                       eta_el: float) -> np.ndarray:
    """RAG (dB) per Monte Carlo trial in spherically isotropic ambient noise, with channel errors."""
    if eta_th < 0 or eta_el < 0:
        raise ValueError("noise ratios must be non-negative")
    r0 = np.asarray(positions_m, dtype=float)
    k = 2 * np.pi * f_hz / c_mps
    u_s = np.asarray(u_s, dtype=float)
    w = steering_vectors(r0, u_s, f_hz, c_mps) / len(r0)  # nominal DAS weights (N,)
    true = r0[None, :, :] + draw.position_m  # (T, N, 3)
    d = draw.channel(f_hz)  # (T, N)
    s = d * np.exp(1j * k * (true @ u_s))
    num = np.abs(s @ w.conj()) ** 2
    v = d.conj() * w[None, :]  # D^H w
    out = np.empty(len(d))
    eye = np.eye(len(r0))
    for t in range(len(d)):
        g = coherence_spherical(true[t], k) + eta_th * eye
        out[t] = np.real(v[t].conj() @ g @ v[t]) + eta_el * np.real(w.conj() @ w)
    return _db(num * (1.0 + eta_th + eta_el) / out)


def horizontal_scan_with_errors(positions_m, f_hz: float, c_mps: float, az_true_deg: float, scan_az_deg,
                                draw: ErrorDraw) -> np.ndarray:
    """Noise-free scanned DAS power on the horizon for a horizon source at ``az_true_deg``.

    Returns (T, A) power normalized to the error-free steered response (= 1). Values may exceed 1 in
    the presence of gain errors; nothing is clipped.
    """
    from .conventions import unit_vector

    r0 = np.asarray(positions_m, dtype=float)
    k = 2 * np.pi * f_hz / c_mps
    u_s = unit_vector(az_true_deg, 0.0)
    true = r0[None, :, :] + draw.position_m
    s = draw.channel(f_hz) * np.exp(1j * k * (true @ u_s))  # (T, N)
    a_scan = steering_vectors(r0, unit_vector(np.asarray(scan_az_deg), 0.0), f_hz, c_mps)  # (A, N)
    w = a_scan / len(r0)
    return np.abs(s @ w.conj().T) ** 2
