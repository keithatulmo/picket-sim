# ADR-0017: Published-reference inputs and integrated hydrophone transfer functions

Status: Accepted (SIM-02B.1, reviewer decision D01)

## Decision
* Every SIM-02B numerical input is a provenance record with **value, units, provenance, source** (as in
  ADR-0010) and, for published or measured values, **frequency range, applicability and uncertainty**.
  The loader rejects a published or measured record without these fields. A source is cited only after the
  document has been opened and the number located; the citation names the table, figure or page.
  `tables/parameters_by_provenance.csv` of SIM-02B runs lists all fields.
* **Ambient noise**: published Wenz-derived envelopes are encoded as the equations or values printed in the
  cited document, over the printed frequency range only; evaluating outside that range fails visibly.
  Where published data are insufficient, the SIM-02A assumed envelopes remain and stay labeled assumed.
* **Integrated active hydrophones** (element and preamplifier sold as one unit) are modeled as a separate
  sensor type with a documented equivalent transfer function: output voltage = M(f) p(f) + n_out(f), with
  M(f) the published receiving sensitivity including the internal preamplifier, valid over the published
  frequency range, and the input-referred self-noise equal to the published equivalent noise spectrum.
  They are never decomposed into the bare-element thermal-noise model. If a product publishes no
  self-noise spectrum, it is not used as a noise source in the study.
* **Spatial coherence** is never inferred from single-channel spectra. Coherence models remain
  assumption-labeled (spherically isotropic, horizontally isotropic, exponential flow-like, white) unless a
  published multi-sensor coherence measurement is available for the relevant geometry and frequency.

## Consequences
Published spectra set levels and shapes; they do not validate coherence, host-noise geometry or
synchronization models, which the reports continue to identify as unvalidated.
