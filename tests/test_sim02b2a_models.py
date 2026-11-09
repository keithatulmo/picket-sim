"""Independent verification of the SIM-02B.2-A estimators, exact CFAR laws and tail methods."""

from __future__ import annotations

import math

import numpy as np
import pytest

from picket_sim import noise_estimation as ne
from picket_sim import qforms

RNG = np.random.default_rng(20261109)


def _band(k, n, p):  # 4-standard-error band for a binomial count
    return abs(k - n * p) <= 4 * math.sqrt(n * p * (1 - p)) + 1


# ------------------------------------------------------------------------------------------- estimators
def test_time_reference_estimators_match_direct_computation():
    ref = RNG.exponential(size=(3, 16, 50))
    np.testing.assert_allclose(ne.tref_ca(ref), ref.mean(axis=1))
    np.testing.assert_allclose(ne.tref_os(ref, 12), np.sort(ref, axis=1)[:, 11, :])
    with pytest.raises(ValueError):
        ne.tref_os(ref, 17)


def test_reference_bin_layout_guards_and_edges():
    K, L, G = 40, 4, 2
    idx = ne.fref_index(K, L, G)
    assert idx.shape == (K, 2 * L)
    for k in range(K):
        assert len(set(idx[k])) == 2 * L
        assert all(abs(j - k) > G for j in idx[k])  # guard respected everywhere
    np.testing.assert_array_equal(idx[20], [14, 15, 16, 17, 23, 24, 25, 26])
    p = RNG.exponential(size=(2, K))
    np.testing.assert_allclose(ne.fref_ca(p, idx), p[:, idx].mean(axis=-1))
    np.testing.assert_allclose(ne.fref_os(p, idx, 6), np.sort(p[:, idx], axis=-1)[..., 5])
    with pytest.raises(ValueError):
        ne.fref_index(10, 4, 2)


def test_estimators_are_scale_free():
    """CFAR: scaling the data scales the estimate (no hidden dependence on the true level)."""
    ref = RNG.exponential(size=(16, 30))
    idx = ne.fref_index(30, 4, 1)
    for f in (ne.tref_ca, lambda x: ne.tref_os(x, 12)):
        np.testing.assert_allclose(f(7.3 * ref), 7.3 * f(ref))
    np.testing.assert_allclose(ne.fref_os(7.3 * ref[0], idx, 6), 7.3 * ne.fref_os(ref[0], idx, 6))


# ------------------------------------------------------------------------------------------- exact laws
@pytest.mark.parametrize("M", [4, 16])
def test_ca_cfar_law_matches_simulation(M):
    n = 200000
    y = RNG.exponential(size=n) * 3.0
    g = RNG.exponential(size=(n, M)).mean(axis=1) * 3.0
    for p in (0.1, 0.01):
        eta = ne.ca_cfar_isf(p, M)
        assert ne.ca_cfar_sf(eta, M) == pytest.approx(p, rel=1e-12)
        assert _band(int(np.sum(y / g > eta)), n, p)


def test_os_cfar_law_matches_simulation():
    n, M, r = 200000, 16, 12
    y = RNG.exponential(size=n)
    xr = np.sort(RNG.exponential(size=(n, M)), axis=1)[:, r - 1]
    for p in (0.1, 0.01):
        eta = ne.os_cfar_isf(p, M, r)
        assert _band(int(np.sum(y > eta * xr)), n, p)


def test_tonal_maximum_with_ca_references_is_exact():
    n, K, M, p = 40000, 30, 8, 0.01
    eta = ne.ca_cfar_isf(ne.per_bin_pfa(p, K), M)
    y = RNG.exponential(size=(n, K))
    g = RNG.exponential(size=(n, M, K)).mean(axis=1)
    assert _band(int(np.sum((y / g).max(axis=1) > eta)), n, p)


def test_cfar_loss_decreases_with_reference_count():
    losses = [ne.cfar_loss_db(1e-3, 1801, M) for M in (4, 8, 16, 32, 64, 256)]
    assert all(a > b > 0 for a, b in zip(losses, losses[1:]))
    assert losses[-1] < 0.25


# ------------------------------------------------------------------------------------------- quadratic forms
def test_hypoexponential_survival_against_closed_forms():
    assert qforms.hypoexp_sf(2.0, np.array([1.0]))[0] == pytest.approx(math.exp(-2.0), rel=1e-12)
    # Gamma(3, 1): e^-x (1 + x + x^2 / 2), equal weights (degenerate case)
    x = 4.0
    assert qforms.hypoexp_sf(x, np.ones(3))[0] == pytest.approx(math.exp(-x) * (1 + x + x * x / 2), rel=1e-11)
    # distinct weights: sum_i prod_{j != i} l_i / (l_i - l_j) exp(-x / l_i)
    lam = np.array([2.0, 0.5, 0.1])
    ref = sum(math.exp(-x / li) * np.prod([li / (li - lj) for lj in lam if lj != li]) for li in lam)
    assert qforms.hypoexp_sf(x, lam)[0] == pytest.approx(ref, rel=1e-10)


def test_hypoexponential_tail_matches_simulation_for_coherence_eigenvalues():
    lam = np.array([3.2, 0.6, 0.15, 0.05]) / 4
    q = (RNG.exponential(size=(400000, 4)) * lam).sum(axis=1)
    for x in (2.0, 4.0):
        p = qforms.hypoexp_sf(x, lam)[0]
        assert _band(int(np.sum(q > x)), q.size, p)


def test_conditional_monte_carlo_matches_brute_force():
    s = 6
    a = RNG.standard_normal((s, 3)) + 1j * RNG.standard_normal((s, 3))
    cov = a @ a.conj().T
    d = np.sqrt(np.real(np.diag(cov)))
    cov = cov / np.outer(d, d)  # unit diagonal, rank 3 (like 24 beams from 8 elements)
    eta = 4.0
    est, se = qforms.conditional_max_sf(eta, cov, 20000, RNG)
    fac = np.linalg.cholesky(cov + 1e-12 * np.eye(s))
    z = ((RNG.standard_normal((400000, s)) + 1j * RNG.standard_normal((400000, s))) / np.sqrt(2)) @ fac.T
    brute = np.mean(np.max(np.abs(z) ** 2, axis=1) > eta)
    assert est == pytest.approx(brute, abs=4 * se + 4 * math.sqrt(brute / 400000))
    assert se / est < 0.02  # bounded relative error: far more precise than brute force at this cost
