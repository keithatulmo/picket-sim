"""Geometry, candidate definitions and exact geometric-ambiguity classification."""

import numpy as np
import pytest

from picket_sim.geometry import (
    ArrayGeometry,
    from_coordinates,
    rotation_matrix_from_axes,
    uniform_linear,
    uniform_rectangular,
)


def test_all_five_candidates_through_one_interface(candidates):
    assert list(candidates) == ["A0", "A1", "A2", "A3", "A4"]
    for g in candidates.values():
        assert isinstance(g, ArrayGeometry)
        assert g.positions_m.shape == (g.n_elements, 3)
    assert [g.n_elements for g in candidates.values()] == [1, 4, 4, 4, 4]


def test_candidate_dimensions(candidates):
    a1, a2, a3, a4 = (candidates[k] for k in ("A1", "A2", "A3", "A4"))
    assert a1.min_spacing_m == pytest.approx(0.15) and a1.aperture_m == pytest.approx(0.45)
    assert a2.min_spacing_m == pytest.approx(0.30) and a2.aperture_m == pytest.approx(0.90)
    assert a3.min_spacing_m == pytest.approx(0.30) and a3.aperture_m == pytest.approx(0.30 * np.sqrt(2))
    np.testing.assert_allclose(a3.extent_m, [0.30, 0.30, 0.0], atol=1e-15)
    np.testing.assert_allclose(a4.positions_m[1], [1.0, 0.0, 0.0])  # coordinates taken verbatim from config


def test_rank_and_ambiguity_class(candidates):
    expect = {"A0": (0, "omnidirectional"), "A1": (1, "conical"), "A2": (1, "conical"), "A3": (2, "mirror"),
              "A4": (3, "none")}
    for k, (r, cls) in expect.items():
        obs = candidates[k].observability
        assert obs.rank == r, k
        assert obs.ambiguity_class == cls, k
    np.testing.assert_allclose(candidates["A1"].observability.axis, [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(candidates["A3"].observability.plane_normal, [0, 0, 1], atol=1e-12)


def test_rank_invariant_to_rigid_motion():
    g = uniform_rectangular(2, 2, 0.3, 0.3)
    rng = np.random.default_rng(2)
    for _ in range(10):
        r = rotation_matrix_from_axes(rng.normal(size=3), rng.uniform(0, 360))
        g2 = g.rotated(r).translated(rng.normal(size=3))
        assert g2.observability.rank == 2
        np.testing.assert_allclose(np.sort(g2.pairwise_distances_m.ravel()), np.sort(g.pairwise_distances_m.ravel()),
                                   atol=1e-12)


def test_rotated_line_axis():
    g = uniform_linear(4, 0.15, axis=(0, 0, 1))
    np.testing.assert_allclose(g.observability.axis, [0, 0, 1], atol=1e-12)


def test_nearly_coplanar_is_volumetric_and_exactly_coplanar_is_planar():
    base = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    assert from_coordinates(base).observability.rank == 2
    off = [list(p) for p in base]
    off[3][2] = 1e-6  # 1 micrometre out of plane: geometrically 3-D (physically marginal)
    assert from_coordinates(off).observability.rank == 3


def test_reduced_positions_reproduce_projections(candidates):
    rng = np.random.default_rng(3)
    for g in candidates.values():
        obs = g.observability
        if obs.rank == 0:
            continue
        u = rng.normal(size=(20, 3))
        u /= np.linalg.norm(u, axis=1, keepdims=True)
        # phases relative to the centroid are fully determined by the reduced coordinates
        np.testing.assert_allclose(g.centered_positions_m @ u.T, g.reduced_positions_m @ obs.reduce(u).T, atol=1e-12)


def test_mirror_operator(candidates):
    obs = candidates["A3"].observability
    u = np.array([0.3, 0.4, np.sqrt(1 - 0.25)])
    np.testing.assert_allclose(obs.mirror(u), [0.3, 0.4, -np.sqrt(0.75)], atol=1e-15)
    with pytest.raises(ValueError):
        candidates["A4"].observability.mirror(u)


def test_invalid_geometry_rejected():
    with pytest.raises(ValueError):
        ArrayGeometry("bad", np.zeros((3, 2)))
    with pytest.raises(ValueError):
        ArrayGeometry("bad", [[0, 0, np.nan]])
    with pytest.raises(ValueError):
        uniform_linear(4, -0.1)
