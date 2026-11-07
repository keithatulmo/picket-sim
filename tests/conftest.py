from pathlib import Path

import numpy as np
import pytest

from picket_sim.acoustics import PlaneWaveManifold
from picket_sim.config import build_array, load_config
from picket_sim.grids import SphereGrid

REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / "configs" / "sim01" / "sim01_baseline.yaml"
SMOKE = REPO / "configs" / "sim01" / "sim01_smoke.yaml"
C = 1500.0


@pytest.fixture(scope="session")
def baseline_cfg():
    return load_config(BASELINE)


@pytest.fixture(scope="session")
def candidates(baseline_cfg):
    return {a["id"]: build_array(a) for a in baseline_cfg["arrays"]}


@pytest.fixture(scope="session")
def sphere():
    return SphereGrid(181, 360)


def manifold(geom, c=C):
    return PlaneWaveManifold(geom, c)


def dirichlet_power(n, x):
    """|sin(n x/2) / (n sin(x/2))|^2, the uniform N-element line-array power pattern (independent formula)."""
    x = np.asarray(x, dtype=float)
    num = np.sin(n * x / 2.0)
    den = n * np.sin(x / 2.0)
    out = np.ones_like(x)
    m = np.abs(den) > 1e-12
    out[m] = (num[m] / den[m]) ** 2
    return out


def bisect(fun, lo, hi, iters=200):
    """Root of a scalar function with a sign change on [lo, hi] (independent of the package)."""
    flo = fun(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = fun(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)
