> **Evidence file (SIM-02B.1, reviewer decision D05).** Desk research and supplier-data collection carried out on 2026-11-08 by a Claude Code research agent under this program's instructions (no purchases, no experiments). Quotes were checked by script against downloaded text (159 of 187 exact; 25 transcribed from image-only datasheet pages are marked (img); 3 differ by extraction artifacts, noted). Downloaded documents are not redistributed. Requires review like the rest of this work.

# D05 follow-up: acoustic vector sensor (AVS) supplier and measurement evidence

Desk research only (no purchases, no experiments, no supplier contact). Compiled 2026-11-08 for the
go/no-go decision on a future AVS bench test. It adds to `docs/avs_feasibility.md` and does not repeat
its directivity theory. AI-generated; needs review by a qualified person before anyone relies on it.

## 0. Method and provenance conventions

* Every number in Sections 1 and 2 comes from a document that was downloaded and read in this session.
  Each one points to a quote ID (`[Qn]`). Sections 1.2 and 2 give each quote verbatim with its URL.
* Provenance tags (in the spirit of ADR-0010):
  * **[V]**: the vendor publishes it (datasheet, product page, vendor technical note).
  * **[T]**: a third-party report compiled it from vendor information (the TNO 2019 survey table).
  * **[M]**: a third party measured it (TNO, Georgia Tech, Thode et al., Mantouka et al., Raghukumar
    et al.).
  * **[D]**: I derived it by arithmetic from a quoted value. The formula is given each time. These
    values are not sourced facts.
* Transcription notes:
  * Page 1 of each Geospectrum spec sheet and the TNO Table 2.1 page are raster images with no text
    layer. I rendered them with `pdftoppm` and transcribed them from the image. Those quotes are
    marked *(img)*.
  * All other quotes are copied from `pdftotext` or HTML text extraction. The extraction occasionally
    drops symbols (degree signs, µ, minus signs). Each case is flagged where it occurs.
* Prices: none of the suppliers publishes a price list. The only prices found are in the TNO survey
  table (kEUR; the purchase-survey vintage is about 2017 to 2019 and the quote basis is not stated).
  They are reported only as TNO printed them.
* About 48 web fetches and 20 searches. Every source that was blocked or unavailable is listed in
  Section 3.

## 1. Supplier table

### 1.1 Table

Abbreviations: acc = accelerometer channel; hyd = pressure (hydrophone) channel; PM = particle motion;
n.p. = not published in any document opened; "—" = the source table printed a dash.

| ID | Supplier / model | Axes, sensing principle | Motion-channel sensitivity | Pressure-channel sensitivity | Frequency range | Self-noise (motion channels) | Size | Mass / buoyancy | Power, supply | Depth rating | Output | Orientation sensing | Price | Status / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | GeoSpectrum Technologies (Canada) M20-105 | 3 orthogonal accelerometer-based PM sensors plus omni pressure sensor [Q1][V] | Graph only, axis in "dB re 1V/m/s"; no tabulated value [Q2][V] | Graph only, axis in "dB re1 V/µPa" [Q2][V] | 2.0 Hz to 3.0 kHz [Q1][V] | Not on the datasheet. Vendor technical note gives one value for the M20 family: "70 dB at 5 Hz in a 1 Hz band" (SPL-referred) [Q8][V] | 127 mm diam., 231 mm length [Q3][V] | 3.4 kg; apparent mass in water 1.0 kg [Q1][V]. M20 family SG "typically 1.5" [Q8][V]. TNO measured a different M20: 4 kg, SG 1.9 [Q30][M] | 5-15 VDC, 37.5 mA [Q1][V] (0.19 to 0.56 W [D]) | 1000 m [Q1][V] | Differential, 8.5 Vpp max; compass on RS422 [Q1][V] | 3D orientation sensor/compass [Q1][V] | n.p. by vendor. TNO table: M20 "10" kEUR [Q28][T] | Current product. The negatively buoyant single-point suspension is part of the vendor's noise-rejection design [Q9][V] |
| S2 | GeoSpectrum M20-040 | 3 accelerometer-based PM sensors plus omni [Q4][V] | Graph only [Q2b][V] | Graph only [Q2b][V] | 10 Hz to 3 kHz [Q4][V] | n.p. (see S1 family note) | 64 mm diam., 176 mm length [Q4][V] | 1.12 kg; in-water mass n.p. [Q4][V] | 12 VDC, 50 mA [Q4][V] (0.6 W [D]) | 300 m [Q4][V] | Current loop [Q4][V] | None (product page: digital compass "N") [Q3][V] | n.p. | Current product. Used in the NoiseSpotter tidal trial [Q40][M] |
| S3 | GeoSpectrum M20-600 | 2 orthogonal horizontal dipole sensors resolved to North/East plus omni [Q5][V] | Graph only [Q5][V] | Graph only [Q5][V] | 1.0 Hz to 3.0 kHz [Q5][V] | n.p. | 107 mm diam., 120 mm length [Q3][V] | 1.2 kg; apparent mass in water 0.6 kg [Q5][V] | 5-15 VDC, <300 mW @5VDC [Q5][V] | 1000 m [Q5][V] | Differential voltage [Q5][V] | Compass; outputs resolved N/E [Q5][Q3][V] | n.p. | Current product |
| S4 | GeoSpectrum M35-300 | 2D directional plus omni [Q3][V] | n.p. | n.p. | 100 Hz - 15 kHz [Q3][V] | n.p. | 127 mm diam., 157 mm length [Q3][V] | n.p. | n.p. | 1000 m [Q3][V] | n.p. | Digital compass "Y" [Q3][V] | n.p. | Product-page row only; spec sheet not opened. Its band is above the low-frequency interest |
| S5 | Wilcoxon Sensing Technologies (Amphenol, USA) VS-101 | 3 orthogonal accelerometers plus 1 omni hydrophone (inertial) [Q12][V] | 6.0 V/g [Q12][V] (0.612 V/(m/s²) [D]) | -162 dB re 1.0 V/µPa [Q12][V] | acc 3.0 Hz - 2.0 kHz; hyd 8.0 Hz - 2.0 kHz (±3 dB) [Q12][V] | n.p. | 3.00 in. diam., 7.41 in. length [Q12][V] (76.2 x 188.2 mm [D]) | 700 g without cables; buoyancy in water -2% [Q12][V] | 6.5 - 12.0 VDC, 40 mA nominal [Q12][V] (TNO table prints "3-9 VDC 30 mA" [Q28][T]) | 1,000 psi operational, 1,500 psi absolute [Q12][V] (about 685 m operational [D]) | Differential, 2.1 - 2.6 V bias; RS-485 digital [Q12][V] | Pitch, roll, heading [Q12][V] | n.p.; TNO table "-" [Q28][T] | Near-neutral buoyancy. ITAR-controlled per TNO [Q29][T] |
| S6 | Wilcoxon VS-209 (mid-frequency) | 3 orthogonal accelerometers plus omni hydrophone [Q10][V] | 1.5 V/g [Q10][V] (0.153 V/(m/s²) [D]) | -164 dB re 1.0 V/µPa [Q10][V] | acc 3.0 Hz - 7.0 kHz; hyd 8.0 Hz - 7.0 kHz (±3 dB) [Q10][V] | n.p. | 1.62 in. diam., 2.80 in. length [Q10][V] (41.1 x 71.1 mm [D]) | 95 g without cables; buoyancy in water -65% [Q10][V] | 6.5 - 12.0 VDC, 40 mA [Q10][V] (0.26 to 0.48 W [D]) | 1,500 psi operational, 2,500 psi absolute [Q10][V] (about 1028 m operational [D]) | Differential, 2.1 - 2.6 V bias; RS-485 [Q10][V] | Pitch, roll, heading [Q10][V] | n.p. by vendor; TNO table "10" kEUR [Q28][T] | Max transverse sensitivity 5% [Q10][V]. ITAR per TNO [Q29][T] |
| S7 | Wilcoxon VS-301 (low-frequency) | 3 orthogonal accelerometers plus omni hydrophone [Q11][V] | 10 V/g [Q11][V] (1.020 V/(m/s²) [D]). Measured in-water X/Y about 8 V/g on one unit [Q35][M] | -162 dB re 1.0 V/µPa [Q11][V] | acc 3.0 Hz - 2.0 kHz; hyd 8.0 Hz - 2.0 kHz [Q11][V] | n.p. Georgia Tech found unequal X/Z noise floors that affected bearings [Q37][M] | 0.80 in. diam., 3.37 in. length [Q11][V] (20.3 x 85.6 mm [D]) | 43 g without cables; buoyancy in water -68% [Q11][V] | 6.5 - 12.0 VDC, 40 mA [Q11][V] (TNO table prints "6.5-9 VDC 40 mA" [Q28][T]) | 800 psi operational, 1,200 psi absolute [Q11][V] (about 548 m [D]) | Differential, 2.1 - 2.6 V bias; RS-485 [Q11][V] | Pitch, roll, heading [Q11][V] | TNO table "10" kEUR [Q28][T] | Has "Power management capability" [Q11][V]. Tested at Georgia Tech (S-lit L4) |
| S8 | Wilcoxon VS-403 | Accelerometer plus pressure (TNO table) [Q28][T] | 3 mV/m/s2 [Q28][T] | -202 dB re 1uPa (as printed) [Q28][T] | 1 Hz - 20 kHz [Q28][T] | n.p. | Ø1.5 cm; H3.6 cm [Q28][T] | 0.011 kg [Q28][T] | 6.5-9 VDC 15 mA [Q28][T] | n.p. | n.p. | "yes" [Q28][T] | "-" [Q28][T] | Vendor datasheet not found or opened. Low sensitivity; high-level use |
| S9 | Wilcoxon DVS-100 (deep vector sensor, preliminary) | Not verified | Not verified | Not verified | Not verified | n.p. | n.p. | n.p. | Not verified | Not verified | n.p. | n.p. | n.p. | Datasheet URL exists but returned HTTP 403 to curl and WebFetch (Section 3). No values are used |
| S10 | Ocean Applied Acoustics (China; per TNO table flag) VHS-100 | 3 pairs of accelerometers in an epoxy sphere plus a separate pressure channel; elastic-band cage suspension [Q31][M] | 250 mV/m/s2 (-12 dB re 1V/m/s2) [Q31][T] | -178 dB re 1 V/µPa in TNO text [Q31]; -180 in TNO table [Q28][T] | 20 Hz - 4 kHz [Q28][T]. Usable from about 20 Hz because of the 10 Hz suspension resonance [Q32][M] | Measured in the TNO basin: at higher frequencies 10 dB below sea-state-1 acceleration; extrapolated close to sea state 1 at 25 Hz; pressure channel about 20 dB noisier than B&K 8106 [Q33][M] | Sphere radius 0.045 m [Q32][M]; Ø9 cm [Q28][T]; suspension cage 17 cm diameter [Q34][M] | 0.465 kg in air, 82 g in water; SG 1.2 [Q32][M] | 18-28 V DC, 2-10 mA [Q28][T]; pre-amps on a 24V battery [Q31][T] | n.p. | n.p. (external pre-amps) | None ("no") [Q28][T] | TNO table "12" kEUR [Q28][T] | TNO purchased and calibrated it (calibration done at HAARI, China) [Q32][M]. Not ITAR [Q28][T]. No English datasheet found |
| S11 | Ocean Applied Acoustics VHS-58 | Accelerometer plus pressure [Q28][T] | 80 mV/m/s2 [Q28][T] | -190 dB re 1uPa (as printed) [Q28][T] | 100 Hz - 7 kHz [Q28][T] | n.p. | Ø5.8 cm [Q28][T] | 0.1 kg [Q28][T] | 24 V [Q28][T] | n.p. | n.p. | "no" [Q28][T] | "15" kEUR [Q28][T] | TNO table only. Above the low-frequency band of interest |
| S12 | Micro-Fine (Singapore; per TNO table flag) AVS120 | Accelerometer plus pressure (sphere) [Q28][T] | 12 mV/m/s2 [Q28][T] | -194 dB re 1uPa (as printed) [Q28][T] | 100 Hz - 3 kHz [Q28][T] | n.p. | Ø6.5 cm [Q28][T] | blank [Q28][T] | blank [Q28][T] | n.p. | n.p. | "no" [Q28][T] | "9" kEUR [Q28][T] | Existence is not confirmed beyond the TNO table; one web search found nothing |
| S13 | Integral Consulting NoiseSpotter (system) | Array of 3 vector sensors (pressure plus 3D PM) on a bottom platform with optional flow shields [Q42][V][Q39][M] | Not stated (sensors in the 2019 trial were GeoSpectrum M20-040 x2 plus "M020-100" [Q40][M]) | — | 10 Hz to 3 kHz [Q42][V] | n.p. | Sensor spacing typically 25/50/75 cm above seabed; 1.25 m horizontal [Q42][V] | n.p. | 78 days continuous recording at 10 kHz [Q42][V] | 200 m standard, 1000 m option [Q42][V] | Logged on board, 9.6 kHz sampling; telemetry [Q42][V] | Yes (one sensor "also measures sensor orientation") [Q40][M] | Lease only, "daily fee" [Q42][V] | Turnkey service, not a component |
| S14 | Greeneridge Sciences DASAR (research recorder) | Omni pressure sensor plus 2 horizontal particle-velocity sensors [Q45][M] | n.p. | −149 dB re V/1 µPa (glyphs decoded; see note under Q46) [Q45][M] | Sampled at 1 kHz; maximum usable 450 Hz [Q45][M] | n.p. | n.p. | n.p. | n.p. | Not a rating. In this study the deepest unit at each site sat at 23 to 53 m [Q45b][M] | Autonomous recording | Orientation from a calibration playback, not a compass [Q46][M] | n.p. | No product page found (one search). Long-running Beaufort Sea use |
| S15 | Research prototype DAVS (Mantouka et al. 2017; not commercial) | 2 PCB 356A17 accelerometers plus PZT hydrophone, moulded; built for AUV use [Q47][M] | 50 mV/m/s2 nominal in air; 24 mV/m/s2 measured at 2 kHz [Q47][Q49][M] | -195 dB re V/μPa nominal [Q47][M] | 120 Hz–4 kHz [Q47][M] | n.p. | n.p. | n.p. | Battery: 20 h with 20 V–3100 mAh [Q47][M] | n.p. | 24-bit internal logging [Q47][M] | AUV navigation data | n.p. | A low-cost off-the-shelf build. It is the closest analogue to a Picket-style DIY sensor |

Suppliers checked with no AVS product found: Microflown/Hydroflown, Applied Physical Sciences,
Ocean Sonics, JASCO, Benthowave, Harbin Engineering University spin-offs and other Chinese makers (apart
from Ocean Applied Acoustics), and Sercel (a marketing page only). Section 3 gives details.

### 1.2 Supplier quotes (verbatim) and URLs

**GeoSpectrum**

* [Q1] M20-105 spec sheet, SP-M20-105 R2, page 1 *(img)*.
  https://geospectrum.ca/wp-content/uploads/2022/05/SP-M20-105-R2.pdf
  > "-Three Orthogonal Accelerometer-Based Particle Motion Sensors / -Omnidirectional Acoustic Pressure Sensor / -3D Orientation Sensor/Compass"
  > "Maximum Operating Depth 1000 Meters" · "Mass 3.4 Kg" · "Apparent Mass in Water 1.0 Kg" · "Operating Temperatures 0°C to +35°C"
  > "Operational Frequency Range 2.0 Hz to 3.0 kHz" · "Power Requirements 5-15 VDC 37.5 mA" · "Acoustic Output Type Differential, 8.5 Vpp Max" · "Orientation/Compass Output RS422" · "Receive Sensitivity Refer to Graph Below"
* [Q2] Same PDF, page 2 (text layer). The sensitivity is shown only as a graph.
  > "Acoustic Pressure Sensitivity (dB re1 V/µPa)" · "Particle Motion Sensitivity (dB re 1V/m/s)" · "Figure 1: Receive Sensitivity Response for M20-105"
* [Q2b] M20-040 spec sheet, page 2.
  https://geospectrum.ca/wp-content/uploads/2022/05/SP-M20-040-R3.pdf
  > "Particle Motion Sensitivity (dB re 1V/m/s)" · "Figure 1: Receive Sensitivity Response for M20-040"
* [Q3] Product page, specifications table, rows as extracted. The columns are: Sensor | Directional
  Particle Motion Sensors | Compass-Resolved Particle Motion Outputs | Omnidirectional Hydrophone |
  Digital Compass | *Usable Frequency Range | Depth Rating | Size.
  https://geospectrum.ca/product/particle-motion-sensor/
  > "M20-105 3D - X, Y, Z Optional Y Y 2 Hz - 3 kHz 1000 m 127 mm diam., 231 mm length"
  > "M20-040 3D - X, Y, Z N Y N 10 Hz - 3 kHz 300 m 64 mm diam., 176 mm length"
  > "M20-600 2D Y Y Y 1 Hz - 3000 Hz 1000 m 107 mm diam., 120 mm length"
  > "M35-300 2D Y Y Y 100 Hz - 15 kHz 1000 m 127 mm diam., 157 mm length"
* [Q4] M20-040 spec sheet, SP-M20-040 R3, page 1 *(img)*. Same URL as Q2b.
  > "-Three Orthogonal Accelerometer-Based Particle Motion Sensors / -Omnidirectional Acoustic Pressure Sensor"
  > "Maximum Operating Depth 300 Meters" · "Mass 1.12 Kg" · "Diameter 64 mm" · "Length 176 mm"
  > "Operational Frequency Range 10Hz to 3 kHz" · "Power Requirements 12 VDC, 50 mA" · "Output Type Current loop (Can be converted to single ended voltage with external line receiver)"
* [Q5] M20-600 spec sheet, SP-M20-600 R0, page 1 *(img)* and page 2.
  https://geospectrum.ca/wp-content/uploads/2022/05/SP-M20-600-R0.pdf
  > "-Two Orthogonal Compass Orientation Dipole Sensors, Resolved in their North and East Components. -Omnidirectional Acoustic Pressure Sensor."
  > "Maximum Operating Depth 1000 Meters" · "Mass 1.2 Kg" · "Apparent Mass in Water 0.6 Kg" · "Operational Frequency Range 1.0 Hz to 3.0 kHz" · "Power Requirements 5-15 VDC <300 mW @5VDC" · "Acoustic Output Type Differential Voltage"
  > (page 2) "Figure 1: Receive Sensitivity Response for M20-600 with 20Hz Roll-off Frequency and 25dB Pre-Amp Gain"
* GeoSpectrum vector hydrophone technical note, document 2022-1195-R0, by B. Armstrong (VP Technology
  Advancement). The note is dated by its own text "as of December 2022".
  https://geospectrum.ca/wp-content/uploads/2023/02/2022-1195-R0-Vector-Hydrophone-Technical-Note.pdf
  * [Q6] > "Vector hydrophones are susceptible to mechanically-induced noise and expensive so they should only be used when necessary."
  * [Q7] > "GeoSpectrum designed accelerometers within the pressure vessel have a well-damped resonance near 450 Hz" · "At a frequency between 2.5 to 3 kHz, the amplitude tracking, phase tracking, and beam patterns begin to differ from optimal because of unwanted resonance." · "As an example, the sensitivity of the X channel is -175 dBV re 1 µPa at 100 Hz." (sensitivity referenced to plane-wave pressure) · "When done properly, the compact vector sensor can make meaningful measurements from about 3 Hz and up."
  * [Q8] > "The specific gravity of a M20 is typically 1.5 so the velocity of a M20 (if it were spherical) would be 3/4 that of the particle velocity of the water. This corresponds to a loss of sensitivity of 20 log(3/4) = 2.5 dBV." · "Even with this loss, the SPL referred electrical noise of the M20 is 70 dB at 5 Hz in a 1 Hz band."
  * [Q9] > "GeoSpectrum's M20 is negatively buoyant and axially symmetric with one suspension point top dead center." · "Hydrophones that employ this noise-reducing technique are 20+ dBV quieter at 5 Hz compared to hydrophones that do not employ it." · "In this test, the vector hydrophones were bottom mounted on a frame with a flow shield in tidal currents of about 1 knot. The M20 was about 20 dBV quieter than the competition under these conditions." · "Hydrophones that are neutrally buoyant cannot employ the noise-reducing technique. Such hydrophones must be suspended in all three directions."
  * [Q9b] > "If you deployed the vector hydrophone from a boat or a floating buoy, do not expect good results at very low frequencies; the mechanical inputs will mask quiet acoustic signals. In situations where there is a surface expression to the suspension, Geospectrum puts passive acoustic filters at about 30 Hz in order to avoid having the preamps saturate." · "You can achieve good results from a vector hydrophone mounted in a glider so long as the glider is drifting in the current and all pumps and motors are turned off during the acoustic measurement." · "This system has been deployed but there are no measured results as of December 2022." · "If you decide that you are going to use a vector hydrophone, expect a learning curve that will last a few months."
  * [Q9c] > "A vector hydrophone is calibrated the same way that a pressure hydrophone is calibrated." · "At high frequencies where k is large, the correction is small, but at low frequencies, the near field pressure gradient dominates."

**Wilcoxon Sensing Technologies (Amphenol)**

wilcoxon.com returned HTTP 403 (Akamai "Access Denied") to curl and WebFetch. The datasheets below
are the vendor's own PDFs as hosted by distributors: Bestech (Australia) and PCB Piezotronics Germany.
The PCB copy of the VS-301 sheet was diffed against the Bestech copy and the extracted text is
identical.

* [Q10] VS-209 datasheet, "99080NC Rev.B.2 10/19".
  https://cdn.bestech.com.au/wp-content/uploads/2023/08/VS-209-Mid-Frequency-Vector-Sensor-ID-9203.pdf
  > "Mid-frequency vector sensor VS-209" · "Output sensitivity, nominal1: Accelerometer 1.5 V/g Hydrophone –164 dB re 1.0 V/µPa" · "Full scale input range: Accelerometer 1.0 g peak Hydrophone 200 Pa peak" · "Frequency response, ± 3 dB: Accelerometer 3.0 Hz - 7.0 kHz Hydrophone 8.0 Hz - 7.0 kHz" · "Transverse sensitivity, max 5%" · "Voltage 6.5 - 12.0 VDC" · "Current, nominal 40 mA" · "Output type, differential 2.1 - 2.6 V bias" · "Operational, max 1,500 psi" · "Absolute max 2,500 psi" · "Diameter 1.62 in." · "Length 2.80 in." · "Buoyancy in water –65%" · "Weight, without cables 95 grams" · "• Three orthogonal axis accelerometers and one omni-directional hydrophone" (wrapped over three lines in the right-hand column) · "• Four channel combination provides an approximately 4.8 dB improvement in signal to noise ratio" · "• Pitch and roll, heading" · "• Micro-controller with RS-485 link" · "Notes: Actual values of X, Y, Z, and H are recorded on calibration sheet." · "This document is cleared for public release."
* [Q11] VS-301 datasheet, "98935NC Rev.B.4 01/20".
  https://cdn.bestech.com.au/wp-content/uploads/2023/08/VS-301_Low-Frequency-Vector-Sensor-ID-9202.pdf
  (identical copy: https://pcbpiezotronics.de/produkte_skript/downloads/specs/vs-301_specs.pdf)
  > "Low-frequency vector sensor VS-301" · "Accelerometer 10 V/g Hydrophone –162 dB re 1.0 V/µPa" · "Accelerometer 0.5 g peak Hydrophone 200 Pa peak" · "Accelerometer 3.0 Hz - 2.0 kHz Hydrophone 8.0 Hz - 2.0 kHz" · "Transverse sensitivity, max <5%" · "Voltage 6.5 - 12.0 VDC" · "Current, nominal 40 mA" · "Operational, max 800 psi" · "Absolute max 1,200 psi" · "Diameter 0.80 in." · "Length 3.37 in." · "Buoyancy in water –68%" · "Weight, without cables 43 grams" · "• Power management capability"
* [Q12] VS-101 datasheet, "98933NC Rev.B.1 10/19".
  https://cdn.bestech.com.au/wp-content/uploads/2023/08/VS-101_Low-Frequency-Vector-Sensor-ID-9201.pdf
  > "Low-frequency vector sensor VS-101" · "Accelerometer 6.0 V/g Hydrophone –162 dB re 1.0 V/µPa" · "Accelerometer 0.5 g peak" · "Accelerometer 3.0 Hz - 2.0 kHz Hydrophone 8.0 Hz - 2.0 kHz" · "Transverse sensitivity, max 2%" · "Voltage 6.5 - 12.0 VDC" · "Current, nominal 40 mA" · "Operational, max 1,000 psi" · "Absolute max 1,500 psi" · "Diameter 3.00 in." · "Length 7.41 in." · "Buoyancy in water –2%" · "Weight, without cables 700 grams"
* [Q13] Wilcoxon brochure (Thermo Fisher ANZ host).
  https://assets.thermofisher.com/TFS-Assets/ANZ/brochures/wilcoxon-advanced-extreme-environments.pdf
  > "When combined, the four channels of the vector sensor produce a cardioid directivity pattern which provides approximately 4.8 dB improvement in the signal to noise ratio over a traditional omni-directional pressure sensor."

**TNO survey and calibration report (third party; Dutch national applied-research organisation)**

TNO 2017 R11589, "Vector sensors and acoustic calibration procedures", H.W. Jansen, E. Brouns,
M.K. Prior. Report date: "December 2019".
https://publications.tno.nl/publication/34637270/uzshRr/TNO-2017-R11589.pdf

* [Q28] Table 2.1, page 10 *(img; the table is rotated; transcribed cell by cell)*. Caption: "Table 2.1 Overview of commercially available vector sensors with properties and specifications."
  Columns: Supplier | Type | Peak Acceleration | Peak pressure/acc. | Band width | Sensitivity | Power supply | Dimensions | Orientation sensor | Weight [kg in air] | Price kEUR | Delivery tim[e] months | ITAR.
  * Geospectrum M20: "gain depending" | (blank) | "10 Hz - 3 kHz" | "gain depending" | "12-V" | "Ø12.7cm; H16.5cm" | "yes" | "3.4" | "10" | "2.5" | "no"
  * Wilcoxon VS-301: "5 m/s2 (134 dB re 1 um/s2)" | "175 dB re 1uPa" | "3 Hz - 2 kHz" | "pressure: -162 dB re 1uPa acc. 1 V/m/s2" | "6.5-9 VDC 40 mA" | "Ø2cm; H8cm" | "yes" | "0.04" | "10" | "2" | "yes"
  * Wilcoxon VS-209: "10 m/s2 (140 dB re 1 um/s2)" | "166 dB re 1uPa" | "3 Hz - 7 kHz" | "pressure: -164 dB re 1uPa acc. 0.15 V/m/s2" | "6.5-12 VDC 40 mA" | "Ø4cm; H7cm" | "yes" | "0.1" | "10" | "2" | "yes"
  * Wilcoxon VS-101: "5 m/s2 (134 dB re 1 um/s2)" | "166 dB re 1uPa" | "3 Hz - 2 kHz" | "pressure: -162 dB re 1uPa acc. 0.6 V/m/s2" | "3-9 VDC 30 mA" | "Ø7.6cm; H19cm" | "yes" | "0.7" | "-" | (blank) | "yes"
  * Wilcoxon VS-403: "150 m/s2 (134 dB re 1 um/s2)" | "190 dB re 1uPa" | "1 Hz - 20 kHz" | "pressure: -202 dB re 1uPa acc. 3 mV/m/s2" | "6.5-9 VDC 15 mA" | "Ø1.5 cm; H3.6 cm" | "yes" | "0.011" | "-" | (blank) | "yes"
  * Ocean applied acoustics VHS-100: "1.5 kPa (184 dB re 1µPa). 8 m/s² (138 dB re 1µ m/s2)" | "-" | "20 Hz - 4 kHz" | "pressure: -180 dB re 1uPa acc. 0.25 V/m/s2" | "18-28 V DC 2-10 mA" | "Ø9 cm" | "no" | "0.4" | "12" | "1.5" | "no"
  * Ocean applied acoustics VHS-58: "4.8 kPa (194 dB re 1µPa). 25 m/s² (148 dB re 1µ m/s2)" | (shared "-") | "100 Hz - 7 kHz" | "pressure: -190 dB re 1uPa acc. 80 mV/m/s2" | "24 V" | "Ø5.8 cm" | "no" | "0.1" | "15" | "3" | "no"
  * Micro-Fine Acoustic Vector Sensor AVS120: "unknown" | "-" | "100 Hz - 3 kHz" | "pressure: -194 dB re 1uPa acc. 12 mV/m/s2" | (blank) | "Ø6.5 cm" | "no" | (blank) | "9" | "2-3" | "no"
  * Note: the table prints pressure sensitivities as "dB re 1uPa" with no "V/". The VS-301 VDC range
    differs from the vendor datasheet ([Q11]: 6.5 - 12.0 VDC), and so do the VS-101 power values
    ([Q12]: 6.5 - 12.0 VDC, 40 mA).
* [Q29] > "The US sensors of Wilcoxon are considered as military goods by the US government and require special US permits (ITAR) to export the vector sensor for measurements campaigns, but also to share technical specifications and measurement data and results."
* [Q30] > "The M20 sensor of Geospectrum is found frequently in the bio-acoustic literature. The sensor is relatively large and heavy (mass 4 kg in air, 17 cm length, 13 cm diameter) and has a specific gravity of 1.9."
* [Q31] > "TNO decided to purchase the VHS-100 sensor of Ocean Applied Acoustics." · "The spherical vector sensor VHS-100 is made of three pairs of accelerometers set in three orthogonal directions." · "The external pre-amps of the accelerometers are powered by a 24V battery. The sensitivity of the accelerometers is 250 mV/m/s2 (-12 dB re 1V/m/s2). The separate acoustic pressure channel (-178 dB re 1 V/µPa) measures the underwater sound pressure."
* [Q32] > "The weight of the sensor equals 0.465 kg in air and 82 g in water. The radius of the sphere is 0.045 m. This results in a density of 1218 kg/m3, and a specific gravity [...] = 1.2." · "The natural frequency of the mass-spring system (the ball in the elastic suspension) is 10 Hz in air. [...] This makes the sensor usable from about 20 Hz, which is according to specification." · "The calibration of the sensor was performed at the facilities of Hangzhou Applied Acoustics Research Institute (HAARI) in China by the comparison method"

### 1.3 Other product quotes

* [Q42] Integral Consulting NoiseSpotter product page. https://www.integral-corp.com/services/noisespotter/
  > "Frequency range 10 Hz to 3 kHz" · "Number of sensors 3" · "Typically 25 cm, 50 cm, and 75 cm above seabed" · "Typically 1.25 m" · "Sampling rate 9.6 kHz" · "Operating duration 78 days continuous recording at 10 KHz" · "Depth rating 200 m standard, can be extended to 1000 m" · "NoiseSpotter® is available for lease for a daily fee." · feature list includes "Flow Noise Suppression"
* [Q47] Mantouka et al. 2017 DAVS (full citation in Section 2), table and text.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5492495/
  > "The DAVS device was built predominantly with off-the-self components, with the intention of being a low-cost sensor independently deployable from different platforms." · "20 h operation with 20 V–3100 mAh battery" · "Bandwidth 120 Hz–4 kHz" · "2 PCB 356A17 accelerometers, nominal sensitivity 50 mV/m/s2 in air" · "cylindrical PZT element, nominal sensitivity −195 dB re V/μ Pa" · "24 bit Sigma Delta, simultaneous sampling at 10,547 Hz or 52,734 Hz"
* [Q45], [Q46]: DASAR (Section 2, L3).

## 2. Measurement literature (third-party measurements)

### L1. TNO 2019 (government-affiliated lab): calibration, self-noise vs ambient, mounting, field use
Jansen, Brouns, Prior, *Vector sensors and acoustic calibration procedures*, TNO report TNO 2017
R11589 (dated December 2019).
https://publications.tno.nl/publication/34637270/uzshRr/TNO-2017-R11589.pdf

* Self-noise vs ambient (basin):
  * [Q33] VHS-100: > "It shows that for higher frequencies the self-noise level is 10 dB below the acceleration levels at sea-state 1." · "The background noise level at lower frequencies is governed by external sources and do therefore not represent the sensor's self-noise floor. When the high-frequency line for the self-noise floor is extrapolated towards lower frequencies it is expected close to sea-state 1 at 25 Hz." · "The noise floor of the sensor is about 20 dB higher than for a B&K 8106 hydrophone with comparable sensitivity."
  * [Q36] M20: > "Figure 4.21 shows that the self-noise levels on the acceleration channels are below the levels for sea state 1." · "The studied version of the M20 was much more sensitive to particle motion (10-15 dB) then the VHS-100. This in combination with a low self-noise levels on the accelerometer channels, makes the M20 suitable to monitor ambient levels. Due its sensitivity the tested M20 tends to clip at relatively low levels."
* Calibration, with the discrepancies found:
  * [Q34] > "• Shaker method in air (dry calibration) for lower frequencies (20 Hz - 1 kHz); • Comparison method in water (wet calibration) for higher frequencies (500 Hz – 4 kHz)." · "At the start of the project no standardized calibration methods for vector sensors existed." · "The negatively buoyant M20 is 4 dB less sensitive to acceleration in water than in air." · "The phase mismatch is frequency dependent and is large, over 153 degrees at 3 kHz. This implies that a phase correction is required on the acceleration channels if the M20 is to be used for directional estimation using acoustic pressure." · "The phase characteristics of the VHS-100 are good and require no correction." · "However, the suspension cage of the VHS-100 is also 17 cm in diameter, so effectively the same amount of space is required." · (VHS-100 shaker) "The measurement results match the specifications well up to a frequency of 1 kHz. For higher frequencies the calculated sensitivities of the accelerometers drop-off."
* Mounting, platform motion and vibration:
  * [Q38] > "Since the mass of the submerged sensor and the suspension stiffness becomes a resonating system, its resonant frequency should be designed outside the measurement frequency range of interest." · (North Sea, sensor at 20 m depth, 750 m from a pile driver) "Due to the movement of the surface buoy and the connected vector sensor suspension cage induced by the surface waves, the self-noise floor was very high for frequencies below 50 Hz;" · "This is a result of the soft suspension system resulting in high wave induced oscillations in the low frequency range." · "Deployment of a vector sensor by a surface-buoy at sea is not advisable if particle acceleration measurements below 100 Hz are to be made. The self-noise due to the movement of the surface buoy is too high. Deployment on the seabed in a cage structure is preferred in this case."
* Bearing in practice (qualitative only):
  * [Q38b] > "In Figure 6.2 the location of the RHIB can be reasonably tracked with a single vector sensor. The orientation of the coordinate system of the sensor is crucial." (No numeric bearing error is reported.)

### L2. Raghukumar et al. 2019: flow noise and flow shield, energetic tidal channel (GeoSpectrum M20)
K. Raghukumar, G. Chang, F. Spada, C. Jones, J. Spence, S. Griffin, J. Roberts, "Performance
characteristics of a vector sensor array in an energetic tidal channel", Sandia report SAND2019-10105C
(OSTI). https://www.osti.gov/servlets/purl/1891335 (another version:
https://www.osti.gov/servlets/purl/1641799)

* [Q39] > "A flow noise removal shield is shown to improve the detectability of low intensity sound such as those that are expected to be emitted by marine renewable energy devices."
* [Q40] > "This location is an energetic tidal channel, where the tidal excursion during the deployment was 2.5 m. Sensors on the VSA consisted of two Geospectrum M20-040 vector sensors and one Geospectrum M020-100 vector sensor that also measures sensor orientation." · "The flow noise shields were constructed of 1050 ballistic nylon wrapped around a baffled PVC tube in which a vector sensor was suspended."
* [Q41] > "Improvements in flow noise reduction are seen in the primary flow noise frequency band of 0-500 Hz on the pressure, x-, and z-particle velocity channels. Little to no change is observed for the y-particle velocity channel, attributed to the flow being orthogonal to the y-axis." · "A visibly higher noise floor is seen in the absence of the flow shield, indicating significant degradation of signal detectability in the absence of the flow shield." · "Use of the flow shield on vector sensor arrays in energetic ocean environments is critical to improving acoustic measurements"
* No current speed and no dB value for the shield's noise reduction appear in the text that was
  extracted.

### L3. Thode et al. 2012 (JASA): realized low-frequency bearing precision of an operational vector-sensor network (DASAR)
A. M. Thode, K. H. Kim, S. B. Blackwell, C. R. Greene Jr., et al., "Automated detection and localization
of bowhead whale sounds in the presence of seismic airgun surveys", J. Acoust. Soc. Am. 131(5), 2012.
https://escholarship.org/content/qt8dc3t33d/qt8dc3t33d.pdf

* [Q45] > "The acoustic data were recorded on DASARs (Greene et al., 2004), autonomous acoustic recording packages equipped with an omnidirectional acoustic pressure sensor (−149 dB re V/1 µPa) and two horizontal directional sensors capable of measuring the north-south and east-west components of acoustic particle velocity" · "All time series are sampled at 1 kHz and have a maximum usable acoustic frequency of 450 Hz."
* [Q45b] > "For example, the deepest DASAR at sites 1–5 sat at 23, 32, 41, 41, and 53 m depth, respectively."
* [Q46] > "shortly after the deployment and before the recovery of every DASAR, a calibrated frequency-modulated signal is sequentially broadcast at roughly 4 km range from three to six positions around each DASAR." · "The bearing uncertainty of the DASARs, derived by comparing the acoustic intensity measured along orthogonal directions, is around 15°–20° for signals with signal-to-noise ratios (SNR) of 5 dB or less, and 1°–2° for signals with SNR greater than 10 dB."
  * Extraction note: the PDF stores the minus sign, the µ and the degree sign as symbol-font glyphs.
    In the raw extraction they appear as "(\x02149 dB re V/1 lPa)" and "15\x03 –20\x03", where
    \x02 = U+0002 and \x03 = U+0003. I mapped \x02 to "−", "l" to "µ" and \x03 to "°" from context.
    Check against the journal PDF before relying on these characters.

### L4. Lawrence 2023 (Georgia Tech MS thesis): VS-301 calibration (shaker vs standing-wave tube) and tank bearing accuracy
A. J. Lawrence, *Calibration and Deployment of an Inertial Acoustic Vector Sensor for Autonomous Underwater
Vehicles*, M.S. thesis, Georgia Institute of Technology, December 2023.
https://repository.gatech.edu/server/api/core/bitstreams/f56f663d-1665-4f41-ba90-b74e5684b376/content
(landing page: https://repository.gatech.edu/entities/publication/23f0f85d-5dd0-4a37-8a7e-9177548f75a7)

* [Q35] > "The X and Y axes seem to be closer to 8 V/g compared to their given calibrations, whereas the Z axis is much closer to 10 V/g." · "the difference between the experimental values and theoretical constant is around 20% for the X and Y axes and closer to 8% for the Z axis." · "In the shaker experiment, the VS-301 performed within 1% of the provided calibrations from the manufacturer, whereas the Standing Wave Tube experiment showcased a larger difference of around 4%." · "The difference between the manufacturer's calibrations for the 350-1300 Hz range for SN:0242 is roughly 8% compared to the 4% seen from SN:0240. These results show that VS-301s differ from each other significantly"
* [Q36b] > "The vector sensor is sensitive to vibrations from movement and needs extensive calibration to ensure accuracy" · "The plots in Figure 2 omit data below 200 Hz, as that section of data is largely contaminated by non-acoustic noise sources." · "directionality measurements were taken in a large water tank to ensure that an acoustic source could be located accurately within 5 degrees within a frequency band of 350-1300 Hz."
* [Q37] Table 3, "Maximum angle error for each beamforming estimate". Rows as printed: > "0 2 2 ± .1 2.1" · "45 46.4 1.4 ± 1.4 2.8" · "90 84.4 -5.6 ± .28 5.88". Text: > "The noise floors of the X and Z axis accelerometers on VS-301 SN:0240 appear to not be equal, as Table 3 shows that the beamforming estimate for 90 degrees has a difference of more than 5 degrees from the true angle, while the estimate for 0 degrees is only 2 degrees away from the true angle."
* Caveat: this is a tank result for a single source at high SNR in a band 350-1300 Hz. It is not an
  ambient-limited sea result.

### L5. Mantouka et al. 2017 (Sensors): low-cost AVS on an AUV, 1-2 kHz
A. Mantouka, P. Felisberto, P. Santos, F. Zabel, M. Saleiro, S. M. Jesus, L. Sebastião, "Development and
Testing of a Dual Accelerometer Vector Sensor for AUV Acoustic Surveys", Sensors 17(6):1328, 2017,
doi:10.3390/s17061328. https://pmc.ncbi.nlm.nih.gov/articles/PMC5492495/

* [Q48] > "The frequency range of interest for the in situ experiments that are discussed in this paper is 1 kHz–2 kHz." · "there is a 6 dB gain pre-amplifier with one pole high pass filter at 120 Hz for attenuation of low frequency vibrations originating from device motion."
* [Q49] > "numerically, an average of 20∘ difference is observed." · "The curves shown here were not corrected for the roll and pitch AUV motion" · "It was shown that for the Medusa class AUVs, there is no interference between vehicle motion and noise on the DAVS measurements." · "The accelerometer sensitivity is 24 mV/m/s2 at 2 kHz"

### L6. Best-practice guide and NPL review: self-noise of commercial accelerometers, calibration methods and facilities
(a) Nedelec, Ainslie, Andersson, Cheong, Halvorsen, Linné, Martin, Nöjd, Robinson, Simpson, Wang, Ward,
*Best Practice Guide for Underwater Particle Motion Measurement for Biological Applications*, Exeter /
JASCO / FOI / NPL et al., October 2021.
https://tethys.pnnl.gov/sites/default/files/publications/Nedelec_et_al_2021.pdf

* [Q50] > "Table 5 presents examples of self-noise spectral density values that can be found for high end commercial accelerometers available at the time of writing this guide." Table 5, rows as extracted: > "Self-noise 1 Hz 10 Hz 100 Hz 1,000 Hz" · "square root of system self-noise spectral density / ((µm s-2) Hz-1/2) 112 39 12 4.4" · "system self-noise spectral density level (re 1 (µm s-2)2 Hz-1) / dB 41 32 22 13" (the superscripts in the dB row's unit are split across lines in the extraction)
* [Q51] > "The downside with most accelerometers at the time of writing is the relatively high self-noise amplitude limiting their use to high sound amplitude measurements." · "PM sensors must be sufficiently sensitive to PM that the electrical noise floor is at least 10 dB below the signal levels of interest." · "There is a trade-off between buoyancy of the sensor, electrical noise, and mechanical noise affected by the suspension system."
* [Q52] (Hydroflown) > "Preliminary data show that the sensor is usable in the frequency range of 5 Hz to 1 kHz with low self-noise characteristics. There is no commercial underwater sensor of this type yet."
* [Q53] (calibration) > "free-field methods implemented for frequencies from about 500 Hz to tens of kilohertz" · (standing-wave tube) "The method can be applied for the frequency range of 5 Hz to around 400 Hz." · "Such a comparison calibration is less accurate than a primary absolute method because of the uncertainty introduced by the reference device."
* [Q54] (platform noise) > "Noise caused by the action of current on the taut cable." (cable strum) · "Low frequency noise caused by the turbulent flow around the hydrophone." (flow noise) · "Drifting autonomous recorders, or drifting recorders with radio transmitters such as sonobuoys, have been developed to move with the fluid flow, minimising the relative motion between hydrophone and the medium, thereby reducing flow noise."

(b) P. Theobald and T. Pangerc, *Review of methods for the calibration of vector sensors for the
measurement of underwater acoustic fields*, NPL Report AC 17, 2016.
https://eprintspublications.npl.co.uk/7088/1/AC17.pdf

* [Q55] > "at NPL in the UK down to 1 kHz in a 5 m tank (smallest dimension); and at USRD (NAVSEA Underwater Sound Reference Division) down to 1 kHz in a ~4.6 m tank (smallest dimension)." · "The NPL open water facility supports measurements down to tens of Hz, and the USRD open water facility enables measurements down to 5 Hz." · "USRD, have a number of standing wave facilities which provide hydrophone calibration from 1 Hz to 50 Hz. This approach is also being used by the Hangzhou Applied Acoustic Research Institute (HAARI) to calibrate vector sensors at low frequencies"
* [Q56] > "The use of a reference hydrophone for comparison methods will ultimately limit the achievable calibration uncertainty due to the uncertainty of the reference hydrophone calibration, the comparison method, and the calculation of the sound particle velocity from the sound pressure." · "Whilst methods for the calibration of underwater acoustic vector sensors already exist, and are in some laboratories carried out routinely, no standardisation exists."

## 3. Gaps and unknowns

1. **Motion-channel self-noise is almost never published.** None of the eight datasheets opened (three
   Wilcoxon, three GeoSpectrum, the GeoSpectrum product page, the NoiseSpotter page) gives a noise spectrum
   or noise-equivalent acceleration. The only numbers are:
   * one vendor point for the M20 family [Q8];
   * TNO basin comparisons, read against Wenz curves in figures and reported in the text only
     relative to sea state [Q33][Q36];
   * generic "high end commercial accelerometers" [Q50].

   Below roughly 25 to 50 Hz, no low-frequency self-noise measurement exists that is free of facility
   or platform noise. TNO says its basin cannot resolve it [Q33].
2. **Vibration sensitivity is not specified numerically by any supplier.** The only related vendor
   specification is Wilcoxon's transverse sensitivity (2% to 5%) [Q10][Q11][Q12]. Evidence about mounting
   is qualitative or relative ("20+ dBV quieter", "about 20 dBV quieter" [Q9]; "very high for frequencies
   below 50 Hz" from a surface buoy [Q38]). No dB-per-g rejection figure was found for cable strum or
   platform motion.
3. **Flow noise is not quantified** in the open text of Raghukumar et al. [Q39]-[Q41]. The text gives
   no current speed and no dB reduction. The JASCO/OERA Minas Passage PA/PV evaluation report was
   blocked: netzeroatlantic.ca returned a Cloudflare challenge to curl and HTTP 403 to WebFetch, at
   `https://netzeroatlantic.ca/sites/default/files/2019-05/Real-Time%20Particle%20Acceleration-Particle%20Velocity%20%28PA-PV%29%20Measurement%20System%20Evaluation%20in%20a%20Tidal%20Environment%20%E2%80%93%20Final%20Report.pdf`.
4. **No numeric vector-sensor calibration uncertainty was found in open documents.**
   * Search results indicate that IEC 63305 (calibration of acoustic wave vector receivers, 5 Hz to
     10 kHz, published as EN IEC 63305:2024) contains an uncertainty annex. It is paywalled and was
     not opened, so it is only a lead.
   * Practical discrepancies measured by third parties: 1% (shaker) vs about 4% (standing-wave tube)
     vs about 8% between units vs about 20% for X/Y from the theoretical constant [Q35]; 4 dB
     buoyancy correction and over 153 degrees of phase mismatch at 3 kHz for an M20 [Q34].
5. **No public prices.** The only prices are the TNO table's 9 to 15 kEUR (survey about 2017 to 2019;
   VS-101 and VS-403 "-") [Q28]. NoiseSpotter is lease-only [Q42]. Wilcoxon export and data sharing are
   ITAR-restricted per TNO [Q29].
6. **Datasheets not obtained.**
   * Wilcoxon DVS-100: `https://wilcoxon.com/wp-content/uploads/2023/02/DVS-100-preliminary-non-controlled-spec-99397NCA.pdf`
     returned 403 to both curl and WebFetch. No value is used.
   * Wilcoxon VSM-302B mounting spec: same 403.
   * Wilcoxon VS-403: no vendor sheet found.
   * GeoSpectrum M35-300 sheet: not opened.
   * The GeoSpectrum "M020-100" used in [Q40] is not on the current product page [Q3].
7. **Suppliers checked with no AVS product evidence:**
   * Microflown/Hydroflown: Nedelec 2021 states there is no commercial underwater sensor [Q52]. A
     search limited to microflown.com found no current underwater product page. The 2015
     navyrecognition.com article URL now serves unrelated gambling content, so it was discarded.
     Status in 2026 is unverified.
   * Applied Physical Sciences: searches returned only patents (US 9,016,129 and others) and Navy SBIR
     topic pages. No product or datasheet was found.
   * Ocean Sonics: one search found no vector or particle-motion product.
   * JASCO: the fetched AMAR page (https://www.jasco.com/amar) has no mention of vector or particle
     motion. JASCO staff co-authored [Q50] and led the Minas evaluation (item 3).
   * Benthowave: one search found nothing.
   * Harbin Engineering University spin-offs and other Chinese makers: English and Chinese-language
     searches found research prototypes only and no English datasheet. The only Chinese supplier found
     is "Ocean applied acoustics" (VHS-100, VHS-58), and only via TNO [Q28]. That makes it a
     secondary source, and the company's own site was not found.
   * Micro-Fine AVS120: TNO table only; one search found nothing.
   * Greeneridge DASAR: no product page found in one search; specifications come from [Q45].
   * Sercel: "What is an acoustic vector sensor?" (https://www.sercel.com/fr/node/485) is marketing
     text with no specifications.
8. **Internal inconsistencies in the sources** (none resolved):

   | Item | Value A | Value B |
   |---|---|---|
   | M20 specific gravity | "typically 1.5" (vendor) [Q8] | 1.9 (TNO) [Q30] |
   | M20 mass and size | 3.4 kg, 231 mm (M20-105) [Q1][Q3] | 4 kg, 17 cm (TNO) [Q30] |
   | VS-301 supply | 6.5 - 12.0 VDC (datasheet) [Q11] | 6.5-9 VDC (TNO table) [Q28] |
   | VS-101 supply | 6.5 - 12.0 VDC, 40 mA (datasheet) [Q12] | 3-9 VDC, 30 mA (TNO table) [Q28] |
   | VHS-100 pressure sensitivity | -178 (TNO text) [Q31] | -180 (TNO table) [Q28] |
   | VS-301 X/Y sensitivity | 10 V/g nominal [Q11] | about 8 V/g measured in water [Q35] |

9. **Realized low-frequency bearing performance at sea below about 100 Hz on a non-bottom-mounted
   platform was not found.**
   * DASAR (bottom-mounted, 450 Hz maximum) is the only quantified sea-trial bearing precision [Q46].
   * The Georgia Tech result is from a tank [Q37].
   * The AUV result is at 1-2 kHz [Q48][Q49].

## 4. Assessment against the go/no-go criteria (my interpretation, not sourced fact)

Everything in this section is interpretation. Numbers marked [D] are my arithmetic on quoted values,
with ρ = 1026 kg/m³ and c = 1491 m/s (the values the GeoSpectrum note uses [Q7]). Where I compare with
ambient noise, I use only the program's own AS-12 scenarios. AS-12 is explicitly *assumed* and
illustrative (`docs/assumptions.md`: "power laws 45/60/75 dB re 1 uPa^2/Hz at 1 kHz, -17 dB/decade").
I quote no ambient levels from memory. Nothing here selects an architecture or sets a hardware
requirement.

**Derived comparison [D].** I converted the Nedelec Table 5 accelerometer self-noise [Q50] to
plane-wave-equivalent pressure using p = ρc·a/(2πf):

| Frequency | Equivalent pressure, dB re 1 µPa²/Hz | Relative to AS-12 45 / 60 / 75 scenarios |
|---|---|---|
| 1 Hz | 148.7 | -52.7 / -37.7 / -22.7 dB |
| 10 Hz | 119.6 | -40.6 / -25.6 / -10.6 dB |
| 100 Hz | 89.3 | -27.3 / -12.3 / +2.7 dB |
| 1 kHz | 60.6 | -15.6 / -0.6 / +14.4 dB |

Positive values in the last column mean ambient exceeds sensor noise. For comparison, the GeoSpectrum
claim of 70 dB at 5 Hz [Q8] sits +14.1 / +29.1 / +44.1 dB below the AS-12 scenarios at 5 Hz (84.1 /
99.1 / 114.1 dB). The two sources therefore differ by several tens of dB at low frequency. The likely
reason is that "generic high-end accelerometers" and purpose-built resonant AVS designs are different
things [Q7], but nobody has checked this independently at low frequency.

| Criterion | What the evidence shows | Neutral reading |
|---|---|---|
| Plausible low-frequency benefit | Realized bearing performance exists: DASAR 1°–2° at SNR > 10 dB and 15°–20° at SNR ≤ 5 dB, below 450 Hz, bottom-mounted [Q46]; VS-301 tank error ≤ 5.88 degrees at 350-1300 Hz [Q37]; uncorrected AUV about 20 degrees at 1-2 kHz [Q49]. Ambient-limited operation is supported only above about 25 Hz for VHS-100 (extrapolated) [Q33] and qualitatively for M20 in a basin [Q36]. Generic accelerometer noise [Q50] would not be ambient-limited at low frequency in the quieter AS-12 scenarios [D]. | Plausible for purpose-built sensors on quiet, decoupled mounts. Unproven below about 25-50 Hz. Doubtful for a build from generic accelerometers in quiet conditions. The size of the benefit depends on self-noise data that do not exist publicly. |
| Size | Sensor bodies range from Ø1.5 cm / 0.011 kg (VS-403 [Q28]) and 43 g (VS-301 [Q11]) to 3.4 kg (M20-105 [Q1]). Suspensions and cages add volume (VHS-100 cage 17 cm [Q34]); flow shields add more [Q40]. | Favourable compared with a pressure array of equal low-frequency directivity. The effective footprint is set by the suspension and flow shield, not the sensor. |
| Power | Vendor figures: 37.5 mA at 5-15 VDC (0.19-0.56 W [D]) [Q1]; < 300 mW at 5 VDC [Q5]; 12 VDC 50 mA (0.6 W [D]) [Q4]; 40 mA at 6.5-12 VDC (0.26-0.48 W [D]) [Q10]-[Q12]. | Sub-watt per 4-channel sensor. Not a discriminator for a bench test. |
| Cost | No public prices. The TNO survey shows 9-15 kEUR per sensor [Q28]; NoiseSpotter is lease only [Q42]; Wilcoxon carries ITAR constraints [Q29]. A DIY build from off-the-shelf parts is possible [Q47] but carries the self-noise penalty above. | Unfavourable relative to a low-cost program if commercial units are needed. Current quotes would require supplier contact, which is outside this authorization. |
| Calibration | Methods exist and their bands are documented: shaker in air 20 Hz-1 kHz; water comparison ≥ 500 Hz [Q34]; standing-wave tube 5 to about 400 Hz [Q53]; facilities at NPL, USRD and HAARI [Q55]. There is no open numeric uncertainty for vector sensors [Q56]. Measured discrepancies are 1-20% in amplitude, 4 dB from buoyancy, and over 153 degrees of phase [Q34][Q35]. | A bench test is feasible (shaker plus reference accelerometer; a tank comparison above about 500 Hz). Traceable low-frequency in-water calibration and phase matching are the main difficulty. Vendor nominal sensitivities cannot be relied on without per-unit calibration. |
| Vibration sensitivity and mounting | Every source treats this as the dominant practical problem: surface-buoy deployment unusable below 50-100 Hz [Q38]; boat or floating-buoy deployments poor at very low frequency [Q9b]; seabed cage preferred [Q38]; non-acoustic contamination below 200 Hz on a shaker [Q36b]; suspension resonance must sit below the band [Q38][Q32]. No numeric rejection specification exists. | Unfavourable for hosts with surface expression or vibration. Neutral for bottom-mounted or freely drifting configurations. This is the main unknown a bench test would need to characterize. |
| Flow noise | A shield is described as "critical" in a tidal channel, acting over 0-500 Hz [Q41]; the M20 field trial used a flow shield at about 1 knot [Q9]; drifting reduces flow noise [Q54]. | Unfavourable in current unless shielded or drifting. There is no quantitative open data for sizing a shield. |

Overall neutral reading:

* The supplier and measurement evidence confirms that commercial AVS exist with sub-watt power and
  compact sensing heads.
* It confirms that bearings can be estimated in practice (bottom-mounted, below 450 Hz, with
  SNR-dependent precision).
* Its main gaps are exactly the factors that `docs/avs_feasibility.md` marked as unknown:
  * low-frequency motion-channel self-noise;
  * numeric vibration and flow sensitivity;
  * calibration uncertainty;
  * cost.

The open literature cannot close these gaps, and a bench test would address them directly. Whether
that justifies a "go" is a decision for the reviewer.
