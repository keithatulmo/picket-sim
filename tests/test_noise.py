"""Array gain: DI against spherically isotropic noise, white-noise gain."""

import numpy as np
import pytest

from conftest import C, manifold
from picket_sim.beamforming import beampattern_power
from picket_sim.conventions import unit_vector
from picket_sim.geometry import uniform_linear
from picket_sim.noise import (
    coherence_spherical_isotropic,
    directivity_index_db,
    directivity_index_from_pattern_db,
    white_noise_gain_db,
)


@pytest.mark.parametrize("f", [100.0, 1000.0, 2500.0, 5000.0, 10000.0])
def test_di_closed_form_equals_sphere_quadrature(candidates, sphere, f):
    u0 = np.stack([unit_vector(a, e) for a, e in ((0, 0), (37, 0), (90, 0), (60, -20), (-120, 45))])
    for g in candidates.values():
        man = manifold(g)
        p = beampattern_power(man, f, u0, sphere.flat_unit_vectors)
        np.testing.assert_allclose(directivity_index_from_pattern_db(p, sphere.flat_weights_sr),
                                   directivity_index_db(man, f, u0), atol=1e-8)


def test_quadrature_weights_integrate_sphere(sphere):
    assert sphere.weights_sr.sum() == pytest.approx(4 * np.pi, rel=1e-13)
    # integral of z^2 over the sphere = 4 pi / 3
    z = sphere.unit_vectors[..., 2]
    assert np.sum(z * z * sphere.weights_sr) == pytest.approx(4 * np.pi / 3, rel=1e-12)


def test_two_element_di_closed_form():
    d = 0.2
    man = manifold(uniform_linear(2, d))
    for f in (200.0, 1000.0, 3000.0, 7000.0):
        k = 2 * np.pi * f / C
        for az in (0.0, 45.0, 90.0):
            p0 = np.cos(np.deg2rad(az))
            expect = 10 * np.log10(2.0 / (1.0 + np.sinc(k * d / np.pi) * np.cos(k * d * p0)))
            assert directivity_index_db(man, f, unit_vector(az, 0)) == pytest.approx(expect, abs=1e-12)


def test_di_equals_10logN_at_half_wavelength_line():
    for n in (2, 4, 8):
        d = 0.3
        f = C / (2 * d)  # every pair separated by a multiple of lambda/2: sinc = 0
        man = manifold(uniform_linear(n, d))
        assert directivity_index_db(man, f, unit_vector(90, 0)) == pytest.approx(10 * np.log10(n), abs=1e-10)


def test_di_vanishes_at_low_frequency_for_compact_arrays(candidates):
    for k in ("A1", "A2", "A3", "A4"):
        assert abs(directivity_index_db(manifold(candidates[k]), 1.0, unit_vector(90, 0))) < 1e-4


def test_single_hydrophone_gains_are_zero(candidates):
    man = manifold(candidates["A0"])
    for f in (100.0, 10000.0):
        assert directivity_index_db(man, f, unit_vector(0, 0)) == pytest.approx(0.0, abs=1e-15)
        assert white_noise_gain_db(man, f, unit_vector(0, 0)) == pytest.approx(0.0, abs=1e-15)


def test_white_noise_gain_is_10logN(candidates):
    for g in candidates.values():
        for f in (150.0, 4000.0):
            assert white_noise_gain_db(manifold(g), f, unit_vector(20, -5)) == pytest.approx(10 * np.log10(g.n_elements))


def test_isotropic_coherence_properties(candidates):
    for g in candidates.values():
        gam = coherence_spherical_isotropic(g, 3000.0, C)
        np.testing.assert_allclose(np.diag(gam), 1.0)
        np.testing.assert_allclose(gam, gam.T)
        assert np.min(np.linalg.eigvalsh(gam)) > -1e-12  # positive semi-definite
