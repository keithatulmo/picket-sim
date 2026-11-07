# Coordinate, angle, sign and unit conventions

Normative reference for all `picket_sim` code (ADR-0003). Every test in `tests/test_conventions.py`
and `tests/test_acoustics.py` enforces a statement on this page.

## Frame

* Right-handed Cartesian array frame; coordinates in metres; `+z` is up.
* Azimuth `az`: angle in the `x-y` plane from `+x` toward `+y` (counter-clockwise viewed from
  above). Reported in `[-180, 180)` degrees.
* Elevation `el`: angle above the `x-y` plane, `[-90, 90]` degrees (negative = below).
* Direction vector `u = [cos el cos az, cos el sin az, sin el]` points from the array **toward the
  source** (direction of arrival, DOA).

Example host mapping (not used inside the physics): if a host defines `x` = bow, `y` = port,
`z` = up, then relative bearing clockwise from the bow is `(-az) mod 360` and the depression angle
(positive down) is `-el`.

## Waves and signs

* Time dependence `exp(+j omega t)`; NumPy forward FFT `X(f) = sum_t x(t) exp(-j 2 pi f t)`.
* A plane wave from `u` reaches the sensor at `r_n` at `tau_n = -(u . r_n) / c` relative to the
  origin. Sensors closer to the source (larger `u . r_n`) receive it earlier.
* Steering vector `a_n(u, f) = exp(+j k u . r_n)`, `k = 2 pi f / c`. This equals the far-field
  limit of the spherical-wave phase `exp(-j k (|R u - r_n| - R))` and the FFT phase of a delayed
  pulse `s(t - tau_n)` (both verified by tests).

## Named directions for a line along `x`

* Endfire: `u` parallel to the axis (`az = 0` or `180`, `el = 0`).
* Broadside: `u` perpendicular to the axis (`u_x = 0`), e.g. `az = +-90` on the horizon, or any
  elevation in the `y-z` plane.
* Cone angle `psi = arccos(u . axis)`: the only observable angle of a line array.

## Units

All public arguments and configuration keys carry the unit in the name: `_m`, `_hz`, `_mps`,
`_deg`, `_rad`, `_s`, `_db`, `_sr`. Configuration validation rejects values that are almost
certainly unit errors (sound speed outside 1300-1700 m/s, frequencies below 1 Hz or above
200 kHz, coordinates beyond 100 m, sensors closer than 1 mm).

## Normalization and dB

Beampatterns are normalized DAS power `P(u; u0) = |w^H a(u)|^2 / |w^H a(u0)|^2`, i.e. 0 dB in the
steering direction. "-3 dB" means exactly `P = 0.5` (-3.0103 dB). Figures clamp at a stated floor
for display only; tables store unclamped values (exact nulls are stored as -300 dB).
