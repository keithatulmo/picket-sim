## Geometry summary

| ID | Configuration | N | Max dimension (m) | Min spacing (m) | Observable dims | Geometric ambiguity | Exact (0 dB) grating onset (Hz) | Worst-case -1 dB lobe onset (Hz) | Worst-case -3 dB lobe onset (Hz) | WNG (dB) |
|---|---|---|---|---|---|---|---|---|---|---|
| A0 | Single hydrophone | 1 | 0.000 | n/a | 0 | omnidirectional | n/a | n/a | n/a | 0.00 |
| A1 | 4-el line, 0.15 m | 4 | 0.450 | 0.150 | 1 | conical | 5,000 | 4,663 | 4,432 | 6.02 |
| A2 | 4-el line, 0.30 m | 4 | 0.900 | 0.300 | 1 | conical | 2,500 | 2,332 | 2,216 | 6.02 |
| A3 | 4-el square, 0.30 m | 4 | 0.424 | 0.300 | 2 | mirror | 2,500 | 2,126 | 1,876 | 6.02 |
| A4 | 4-el distributed (notional) | 4 | 1.070 | 0.901 | 3 | none | 857 | 706 | 596 | 6.02 |

* Worst-case onset: lowest frequency at which some steering/look pair produces a non-mainlobe lobe at or above the level in the observable space (array factor in wavevector space, |q| <= 2k).
* Exact grating onset: smallest reciprocal-lattice vector of the baselines (equals c/2d for the line and square lattices; exists for A4 because any 4 non-coplanar sensors form a lattice).
* n/a: undefined (single sensor) or no such lobe below the band edge.
* Sound speed 1500 m/s.
