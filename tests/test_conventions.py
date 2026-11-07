"""Coordinate and angular conventions (ADR-0003)."""

import numpy as np
import pytest

from picket_sim.conventions import (
    angle_between_rad,
    az_el_deg_from_unit,
    azimuth_tangent,
    elevation_tangent,
    horizontal_cut,
    unit_vector,
    vertical_cut,
    wrap_deg,
)


@pytest.mark.parametrize(
    "az, el, expected",
    [
        (0, 0, [1, 0, 0]),  # +x
        (90, 0, [0, 1, 0]),  # azimuth increases from +x toward +y
        (180, 0, [-1, 0, 0]),
        (-90, 0, [0, -1, 0]),
        (0, 90, [0, 0, 1]),  # positive elevation is up (+z)
        (37, -90, [0, 0, -1]),
        (45, 0, [np.sqrt(0.5), np.sqrt(0.5), 0]),
        (0, 30, [np.cos(np.pi / 6), 0, 0.5]),
    ],
)
def test_unit_vector_cardinal_directions(az, el, expected):
    np.testing.assert_allclose(unit_vector(az, el), expected, atol=1e-15)


def test_degrees_not_radians():
    # A radian value passed as degrees must NOT give the radian result.
    assert not np.allclose(unit_vector(np.pi / 2, 0), [0, 1, 0])
    np.testing.assert_allclose(unit_vector(90.0, 0.0), [0, 1, 0], atol=1e-15)


def test_round_trip_and_unit_norm():
    rng = np.random.default_rng(0)
    az = rng.uniform(-180, 180, 1000)
    el = rng.uniform(-89.9, 89.9, 1000)
    u = unit_vector(az, el)
    np.testing.assert_allclose(np.linalg.norm(u, axis=-1), 1.0, atol=1e-14)
    a2, e2 = az_el_deg_from_unit(u)
    np.testing.assert_allclose(wrap_deg(a2 - az), 0, atol=1e-9)
    np.testing.assert_allclose(e2, el, atol=1e-9)


def test_wrap_range():
    w = wrap_deg(np.array([-540.0, -180.0, 179.999, 180.0, 360.0, 725.0]))
    assert np.all(w >= -180) and np.all(w < 180)
    np.testing.assert_allclose(w, [-180, -180, 179.999, -180, 0, 5], atol=1e-12)


def test_tangents_orthonormal():
    rng = np.random.default_rng(1)
    for _ in range(50):
        az, el = rng.uniform(-180, 180), rng.uniform(-80, 80)
        u, ta, te = unit_vector(az, el), azimuth_tangent(az, el), elevation_tangent(az, el)
        for v in (ta, te):
            assert abs(np.linalg.norm(v) - 1) < 1e-14
            assert abs(v @ u) < 1e-14
        assert abs(ta @ te) < 1e-14
        # finite-difference directions agree with the tangents
        h = 1e-6
        np.testing.assert_allclose((unit_vector(az + h, el) - u) / np.deg2rad(h) / np.cos(np.deg2rad(el)), ta, atol=1e-6)
        np.testing.assert_allclose((unit_vector(az, el + h) - u) / np.deg2rad(h), te, atol=1e-6)


def test_horizontal_cut_on_horizon_is_azimuth_offset():
    g = np.linspace(-179, 179, 37)
    a, e = az_el_deg_from_unit(horizontal_cut(60.0, 0.0, g))
    np.testing.assert_allclose(wrap_deg(a - (60.0 + g)), 0, atol=1e-9)
    np.testing.assert_allclose(e, 0, atol=1e-12)


def test_vertical_cut_is_elevation_offset_on_front_meridian():
    g = np.linspace(-60, 100, 33)
    a, e = az_el_deg_from_unit(vertical_cut(60.0, -20.0, g))
    front = (g - 20.0) <= 90.0
    np.testing.assert_allclose(e[front], -20.0 + g[front], atol=1e-9)
    np.testing.assert_allclose(wrap_deg(a[front & (np.abs(e) < 89.99)] - 60.0), 0, atol=1e-9)


def test_angle_between():
    assert abs(angle_between_rad(unit_vector(0, 0), unit_vector(90, 0)) - np.pi / 2) < 1e-15
    assert abs(angle_between_rad(unit_vector(0, 0), unit_vector(180, 0)) - np.pi) < 1e-15
    assert angle_between_rad(unit_vector(10, 10), unit_vector(10, 10)) < 1e-15
