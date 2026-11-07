"""Beampatterns: normalization, closed forms, broadside/endfire, symmetry and ambiguity properties."""

import numpy as np
import pytest

from conftest import C, dirichlet_power, manifold
from picket_sim.beamforming import beampattern_power, das_weights, normalized_power
from picket_sim.conventions import unit_vector
from picket_sim.geometry import rotation_matrix_from_axes, uniform_linear

rng = np.random.default_rng(5)


def random_dirs(n):
    u = rng.normal(size=(n, 3))
    return u / np.linalg.norm(u, axis=1, keepdims=True)


FREQS = [100.0, 731.0, 2500.0, 5000.0, 10000.0]


@pytest.mark.parametrize("f", FREQS)
def test_normalization_and_bounds_all_candidates(candidates, f):
    for g in candidates.values():
        man = manifold(g)
        u0 = random_dirs(7)
        # exactly 1 at the steering direction (normalization is to the steered response)
        for s in u0:
            assert beampattern_power(man, f, s, s[None, :])[0] == pytest.approx(1.0, abs=1e-14)
        p = beampattern_power(man, f, u0, random_dirs(500))
        assert p.shape == (7, 500)
        assert np.all(p >= 0) and np.all(p <= 1.0)


def test_multi_steering_matches_single_steering(candidates):
    man = manifold(candidates["A4"])
    u0, look = random_dirs(5), random_dirs(50)
    batch = beampattern_power(man, 3000.0, u0, look)
    for i in range(5):
        np.testing.assert_allclose(batch[i], beampattern_power(man, 3000.0, u0[i], look), atol=1e-14)


def test_single_hydrophone_has_no_directional_discrimination(candidates):
    man = manifold(candidates["A0"])
    for f in FREQS:
        p = beampattern_power(man, f, unit_vector(30, -10), random_dirs(2000))
        np.testing.assert_allclose(p, 1.0, atol=0)


@pytest.mark.parametrize("n, d", [(2, 0.15), (4, 0.15), (4, 0.30), (7, 0.11)])
def test_ula_matches_closed_form(n, d):
    g = uniform_linear(n, d, (1, 0, 0))
    man = manifold(g)
    for f in (300.0, 2000.0, 6000.0):
        k = 2 * np.pi * f / C
        u0 = random_dirs(1)[0]
        look = random_dirs(400)
        x = k * d * (look[:, 0] - u0[0])
        np.testing.assert_allclose(beampattern_power(man, f, u0, look), dirichlet_power(n, x), atol=1e-12)


def test_broadside_symmetry_and_nulls():
    n, d, f = 4, 0.15, 5000.0  # d = lambda/2
    man = manifold(uniform_linear(n, d))
    lam = C / f
    psi = np.linspace(0, 180, 3601)
    look = unit_vector(psi, 0.0)  # azimuth = angle from the +x axis in the horizontal plane
    p = beampattern_power(man, f, unit_vector(90, 0), look)
    np.testing.assert_allclose(p, p[::-1], atol=1e-13)  # P(psi) = P(180 - psi) at broadside
    # first null at cos(psi) = lambda / (N d)
    psi_null = np.rad2deg(np.arccos(lam / (n * d)))
    assert beampattern_power(man, f, unit_vector(90, 0), unit_vector(psi_null, 0)[None, :])[0] < 1e-25


def test_endfire_peak_null_and_broadening():
    n, d, f = 4, 0.30, 2500.0  # d = lambda/2
    man = manifold(uniform_linear(n, d))
    lam = C / f
    look = unit_vector(np.linspace(0, 180, 18001), 0.0)
    p_end = beampattern_power(man, f, unit_vector(0, 0), look)
    assert np.argmax(p_end) == 0  # maximum at psi = 0 (endfire)
    psi_null = np.rad2deg(np.arccos(1 - lam / (n * d)))
    assert beampattern_power(man, f, unit_vector(0, 0), unit_vector(psi_null, 0)[None, :])[0] < 1e-25
    # endfire mainlobe (null-to-null, full cone) is wider than broadside mainlobe
    broad_null = np.rad2deg(np.arccos(lam / (n * d)))
    assert 2 * psi_null > 2 * (90 - broad_null)


def test_line_array_cone_invariance(candidates):
    man = manifold(candidates["A2"])
    for f in (500.0, 3000.0, 9000.0):
        u0 = random_dirs(1)[0]
        look = random_dirs(300)
        p = beampattern_power(man, f, u0, look)
        for ang in (17.0, 90.0, 180.0, 271.0):
            r = rotation_matrix_from_axes((1, 0, 0), ang)  # rotation about the array axis
            np.testing.assert_allclose(beampattern_power(man, f, u0, look @ r.T), p, atol=1e-12)


def test_line_array_left_right_and_up_down_ambiguity(candidates):
    man = manifold(candidates["A1"])
    az = np.linspace(-180, 180, 721)
    for el in (-40.0, 0.0, 25.0):
        p = beampattern_power(man, 2000.0, unit_vector(60, 0), unit_vector(az, el))
        np.testing.assert_allclose(p, beampattern_power(man, 2000.0, unit_vector(60, 0), unit_vector(-az, el)), atol=1e-13)
        np.testing.assert_allclose(p, beampattern_power(man, 2000.0, unit_vector(60, 0), unit_vector(az, -el)), atol=1e-13)
    # the mirror direction az = -60 has exactly the steered response
    assert beampattern_power(man, 2000.0, unit_vector(60, 0), unit_vector(-60, 0)[None, :])[0] == pytest.approx(1.0)


def test_planar_mirror_ambiguity_and_volumetric_resolves_it(candidates):
    u0 = unit_vector(60, -20)
    mir = unit_vector(60, 20)
    for f in (500.0, 1500.0, 2400.0):
        assert beampattern_power(manifold(candidates["A3"]), f, u0, mir[None, :])[0] == pytest.approx(1.0, abs=1e-12)
        look = random_dirs(200)
        m = look * np.array([1, 1, -1])
        man3 = manifold(candidates["A3"])
        np.testing.assert_allclose(beampattern_power(man3, f, u0, look), beampattern_power(man3, f, u0, m), atol=1e-12)
    # volumetric A4 below its aliasing onset: the mirror direction is suppressed
    assert beampattern_power(manifold(candidates["A4"]), 400.0, u0, mir[None, :])[0] < 0.9


def test_translation_invariance_of_power(candidates):
    g = candidates["A4"]
    look, u0 = random_dirs(100), random_dirs(1)[0]
    p1 = beampattern_power(manifold(g), 3000.0, u0, look)
    p2 = beampattern_power(manifold(g.translated([12.3, -4.0, 7.0])), 3000.0, u0, look)
    np.testing.assert_allclose(p1, p2, atol=1e-11)


def test_general_weights_normalization_and_shape_check(candidates):
    man = manifold(candidates["A3"])
    a0 = man.vectors(unit_vector(10, 0), 1000.0)
    w = das_weights(a0) * np.array([1.0, 0.5, 0.5, 1.0])  # tapered
    p = normalized_power(w, man.vectors(unit_vector(10, 0)[None, :], 1000.0), a0)
    assert p[0] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        normalized_power(np.stack([w, w]), man.vectors(random_dirs(3), 1000.0), a0)


def test_increasing_frequency_narrows_the_beam(candidates):
    man = manifold(candidates["A2"])
    look = unit_vector(np.linspace(0, 180, 1801), 0)
    widths = []
    for f in (1500.0, 2000.0, 2400.0):
        p = beampattern_power(man, f, unit_vector(90, 0), look)
        widths.append(np.sum(p >= 0.5))
    assert widths[0] > widths[1] > widths[2]
