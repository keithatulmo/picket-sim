# ADR-0007: Extension points for noise, propagation and platform effects

Status: Accepted (SIM-01)

## Decision
* All downstream code consumes array manifold vectors through `PlaneWaveManifold.vectors(...)`
  (shape `(..., N)`). Element directivity, per-channel gain/phase errors, near-field (spherical
  wave) or multipath models are added as alternative manifold classes with the same interface.
* Array gain is computed from a noise coherence matrix (`noise.py`). New noise fields
  (cylindrically isotropic, surface-generated, directional shipping, sensor self-noise, flow
  noise) are new coherence-matrix functions; DAS, MVDR or other weights consume them unchanged.
* Beamformer weights are explicit arrays, so tapering, adaptive or superdirective weights can be
  evaluated with the same metric code (`normalized_power` normalizes by `|w^H a0|^2`).
* Geometry supports arbitrary coordinates and rigid transforms for host-specific layouts.

## Consequences
SIM-02+ can add sensor noise, propagation and host-platform effects without rewriting the core
numerical framework.
