# ADR-0009: SIM-02 authorization and reviewer decisions D01 to D06

Status: Accepted (SIM-01 technical review and SIM-02 authorization)

## Decisions recorded

| ID | Decision | Implementation consequence |
|---|---|---|
| D01 | No single mission band. Provisional study bands: 20-200 Hz, 200 Hz-2 kHz, 2-10 kHz, and 10-20 kHz (exploratory, contingent on sensor and acquisition assumptions). Signal classes: tonal, harmonic, broadband, transient where appropriate. Bearing is not assumed necessary for every class. | SIM-02A analyses 20 Hz to 20 kHz with per-band summaries; the 10-20 kHz band is flagged as contingent; acquisition validity (Nyquist, bandwidth) is checked; signal classes enter the acquisition/dynamic-range analysis; task-level signal processing is SIM-02B. |
| D02 | Primary objective: observation and detection. Secondary: incremental value of directional sensing. Full-circle horizontal azimuth observability for bearing-capable configurations, with unresolved ambiguities identified. 3-D bearing not required. No maneuver-assisted disambiguation by default. No architecture selection from narrowband beampatterns. | A0 is the comparison baseline for gain; bearing metrics are horizontal-azimuth; geometric and narrowband ambiguities are reported, not resolved by assumption. |
| D03 | Keep -3 dB for continuity; add -6 and -10 dB sensitivity; task-level ambiguity where broadband processing exists; no single threshold becomes a requirement. | Thresholds computed at -3, -6 and -10 dB; SIM-01 -3 dB values reproduced as regression checks. |
| D04 | A4 stays notional; no fabricated vessel geometry; parameterized envelopes (compact, intermediate, distributed) reported against actual dimensions and mounting assumptions; original A4 kept as a regression case. | Envelope-parameterized volumetric family; original A4 regression test. |
| D05 | Keep A0 to A4; add 6- and 8-element planar arrays and compact and extended aperture variants under consistent footprints; treat A1/A2 as one linear family; investigate broadband/TDOA (SIM-02B); separate feasibility assessment of acoustic vector sensors (no implementation required in SIM-02A). | Footprint-matched candidate set; linear family parameterized by spacing; AVS feasibility document. |
| D06 | Keep numerical and engineering tolerances for continuity; treat engineering tolerances as provisional; analyze tolerance sensitivity; eliminate no candidate before cost, installation, calibration burden and other attributes are included. | Tolerance-sensitivity analysis; no elimination language in reports. |

## Gating
SIM-02 proceeds incrementally. SIM-02A covers sensor, noise and error modeling. SIM-02B (broadband
and task-level performance) does not begin until the SIM-02A numerical results have been reviewed.
No Fathom inference during SIM-02. SIM-02 is not authorized to select a production architecture,
establish operational detection ranges, or convert unvalidated environmental assumptions into
hardware performance requirements.
