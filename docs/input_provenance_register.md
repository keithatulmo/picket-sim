# SIM-02B input provenance register (reviewer decision D01, ADR-0017)

Status as of SIM-02B.1. Every entry was located in a document that was opened and quoted; the evidence,
with verbatim quotes, URLs and page or table references, is in
[`docs/research/D01_input_sources.md`](research/D01_input_sources.md) (IDs in the first column). Values
that enter a simulation are also recorded, with all D01 fields, in each run's
`tables/parameters_by_provenance.csv`.

"Secondary" means the document opened is not the original source of the number. No value below was
measured by this program.

## 1. Inputs used in the SIM-02B.1 run of record

| ID | Quantity | Value | Units | Frequency range | Applicability | Uncertainty | Provenance |
|---|---|---|---|---|---|---|---|
| A1 to A6 | Ambient noise PSD, sum of turbulence, shipping, wind and thermal terms (Coates 1989, printed by Stojanovic 2007, Eq. 6) | 10 log Nt = 17 - 30 log f; 10 log Ns = 40 + 20(s - 0.5) + 26 log f - 60 log(f + 0.03); 10 log Nw = 50 + 7.5 w^(1/2) + 20 log f - 40 log(f + 0.4); 10 log Nth = -15 + 20 log f; f in kHz | printed "dB re uPa per Hz", used as dB re 1 uPa^2/Hz | used 20 Hz to 10 kHz; source states dominance regions only | Wenz-type deep-water envelope; no depth or wind range stated | not stated | published, secondary (Coates not opened; Wenz 1962 not opened, HTTP 403) |
| (scenario) | Shipping activity s | 0.5 | 1 (0 to 1) | all | moderate shipping | n/a | assumed |
| (scenario) | Wind speed w | 5 | m/s | all | moderate wind | n/a | assumed |
| H3 | Spread of monthly ambient levels (L10 minus L90), mode | 14 (Alaskan Arctic); 9.2, 7.7, 9.3 (Olympic Coast, Channel Islands, Gulf of Mexico) | dB | 10 Hz to 2 kHz | NOAA/NPS Ocean Noise Reference Stations, Nov 2014 to Jun 2015 | variability statistic | published, primary (Haver et al. 2018). Used as the stated uncertainty context of the ambient envelope and to motivate the +1 and +3 dB level-mismatch tests |
| X1 to X3 | Flow noise spatially incoherent at 17 cm element spacing; coherence upper limit 100 to 125 Hz at 0.1 to 2.6 m/s | qualitative | n/a | below 500 Hz analysed | Minas Passage tidal channel, towed array | none stated | published, primary (honours thesis) and abstract of the related journal paper. Used only as qualitative support for treating flow-like noise as short-correlation; the 0.1 m correlation length remains assumed |

Everything else in the SIM-02B.1 noise model is assumed and labeled so: the S1 acquisition chain (SIM-02A),
the sensor-limited condition (self-noise 20 dB above ambient), all spatial coherence models, and the
mismatch offsets.

## 2. Inputs recorded for later increments (not used in SIM-02B.1)

| ID | Quantity | Value | Units | Range / conditions | Uncertainty as published | Provenance | Why not used now |
|---|---|---|---|---|---|---|---|
| R6 | TC4013 bare element: sensitivity, capacitance | -211; 3.4 nF | dB re 1 V/uPa | usable 1 Hz to 170 kHz | +/-3 dB | published, primary (manufacturer) | candidate element data for a published-element chain; loss tangent and preamplifier noise are not published, so the chain would remain mostly assumed |
| R7 | TC4033 bare element | -203 at 250 Hz; 7.8 nF incl. 10 m cable | dB re 1 V/uPa | usable 1 Hz to 140 kHz | +/-2 dB | published, primary | as R6 |
| R8 | TC4040 bare element | -206; 8.3 nF; > 2 Gohm | dB re 1 V/uPa | usable 1 Hz to 120 kHz | +/-3 dB | published, primary | as R6 |
| R9 | TC4034 bare element | -218 at 250 Hz; 3 nF | dB re 1 V/uPa | usable 1 Hz to 470 kHz | +/-3 dB | published, primary | as R6 |
| R1, R3 | TC4032 integrated hydrophone: sensitivity incl. 10 dB preamplifier; self-noise | -170 single-ended, -164 differential; self-noise graph only | dB re 1 V/uPa | linear 15 Hz to 40 kHz +/-2 dB | flatness only | published, primary | integrated sensor: needs a published self-noise spectrum (ADR-0017); only a graph is published |
| R4 | TC4014 integrated hydrophone | -186 +/-3 single-ended | dB re 1 V/uPa | linear 30 Hz to 100 kHz +/-2 dB | +/-3 dB | published, primary | as R1 |
| R10 | TC4038 equivalent noise with VP1000 preamplifier | 80 at 1 kHz | dB re 1 uPa/sqrt(Hz) | single frequency | none | published, primary | one frequency, outside the device's usable band; not a spectrum |
| Q1 | Aquarian A5 integrated hydrophone | -173 | dBV re 1 uPa | uniform 20 Hz to 10 kHz (+/-4 dB); does not reach 20 kHz | flatness only | published, primary | no self-noise published |
| Q3 | Aquarian S1n passive element | -206; 6.5 nF | dBV re 1 uPa | 1 Hz to 110 kHz | QC +/-3.0 dBV | published, primary | as R6 |
| G1, G2 | Hydrophone and system calibration uncertainty (NPL Good Practice Guide 133) | 0.5 (hydrophone, laboratory); better than 1 (system, 95 %) | dB | not stated | as value | published, primary | SIM-02B.2 calibration-error scenarios |
| M1 to M3 | NPL calibration capabilities (BIPM KCDB, 2004, k = 2) | reciprocity 0.7 (1-2 kHz), 0.5 (2-500 kHz); comparison 0.9, 0.7; pressure 0.5 (25-400 Hz) | dB | as listed | as value | published, primary | SIM-02B.2 calibration-error scenarios |
| P1, P2 | PNNL oil-filled flow shield: flow-noise reduction; insertion loss | > 20 below 50 Hz at > 0.5 m/s; <= 2 below 30 kHz | dB | as listed | none stated | published, primary | relative values only; no absolute flow-noise levels or correlation lengths |
| C1, C2 | Flow noise above slack; shield reductions (Cotter et al. 2024) | 59 at 40 Hz (1.2-1.4 m/s); 31/19/25 at 40 Hz | dB | 40 and 100 Hz | none stated | published, primary | relative values only |
| K1, K2 | CRIMAC cruise report 2025 (published 2026): vessel noise dominates below ~100 Hz; flow noise and saturation at 11 knots | qualitative; levels only in a figure | n/a | hull-mounted | none | published, primary | no numerical levels in text; host-noise levels remain assumed |
| N1 to N9 | National Academies (2003) ambient-noise summaries (e.g. 80 dB re 1 uPa^2/Hz at 20 Hz, Tasman Sea) | various | various | various | none | published, secondary | site-specific levels; Wenz curves only as a graphic |
| H1, H2 | NRS hydrophone ITC-1032: -192 dB re 1 V/uPa, flat +/-1 dB 10 Hz to 2 kHz; 5 kHz sampling, 16 bit | as listed | as listed | 10 Hz to 2 kHz | +/-1 dB flatness | published, primary | reference for a future calibrated-dataset comparison (NCEI archive) |

## 3. Gaps that remain assumed

Element loss tangent; preamplifier voltage and current noise and 1/f corner; self-noise spectra of
integrated hydrophones; ambient-level uncertainty as an envelope parameter; absolute vessel and flow-noise
levels; flow-noise correlation length; channel-to-channel gain and phase mismatch; ambient directionality;
synchronization characteristics. See `docs/research/D01_input_sources.md`, "Gaps".

## 4. Open interpretation for the reviewer

Stojanovic prints the Coates formulas "in dB re uPa per Hz". This program reads that as dB re 1 uPa^2/Hz
(spectral density of squared pressure), the usual convention for these curves. Please confirm.
