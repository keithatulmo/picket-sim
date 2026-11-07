# ADR-0013: SIM-02A candidate set and footprint classes

Status: Accepted (SIM-02A)

## Decision
* Retain A0 to A4 unchanged as reference and regression candidates.
* Treat A1 and A2 as members of one linear family L4(d), d = 0.15 m and 0.30 m.
* Compare planar candidates at equal maximum dimension: compact class C = 0.45 m (the A1 aperture)
  and extended class E = 0.90 m (the A2 aperture). Planar members per class: 2x2 square, 6-element
  and 8-element uniform circular arrays, all horizontal. A3 (0.424 m) remains as the original square.
* Volumetric family: parametric envelopes (L, W, H) with the A4 element pattern scaled into the box.
  Intermediate envelope (1.00, 0.85, 0.75 m) reproduces A4 exactly. Compact (0.45 m class),
  distributed (4 m class) and distributed-shallow (4 m class with 0.25 m vertical extent, a
  draft-limited mounting assumption) envelopes are assumptions, not host surveys.

## Consequences
Equal-footprint comparisons separate the effect of element count from aperture. No candidate is
eliminated in SIM-02A (D06).
