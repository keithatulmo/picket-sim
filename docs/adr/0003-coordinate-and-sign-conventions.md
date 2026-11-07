# ADR-0003: Coordinate, angle and sign conventions

Status: Accepted (SIM-01)

## Decision
* Right-handed Cartesian array frame, metres, `+z` up.
* Azimuth measured in the `x-y` plane from `+x` toward `+y` (counter-clockwise seen from
  above), reported in `[-180, 180)` degrees. Elevation positive above the `x-y` plane, in
  `[-90, 90]` degrees.
* Direction vector `u` points from the array toward the source (direction of arrival).
* Time dependence `exp(+j omega t)`; FFT conventions follow NumPy (`X(f) = sum x e^{-j...}`),
  consistent with this.
* Steering vector `a_n = exp(+j k u . r_n)`; arrival-time offset `tau_n = -(u . r_n)/c`.
* All public function arguments carry unit suffixes (`_deg`, `_rad`, `_m`, `_hz`, `_mps`, `_s`).

## Rationale
A z-up mathematical spherical convention minimizes sign errors. Marine conventions (relative
bearing clockwise from the bow, depression angle positive down) differ by host and are applied at
the platform-integration layer, not inside the physics.

## Verification
Hand-computed steering vectors on all three axes, a spherical-wave far-field limit, and a
time-domain delayed-pulse FFT test (`tests/test_acoustics.py`).
