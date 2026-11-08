> **Evidence file (SIM-02B.1, reviewer decision D01).** Desk research carried out on 2026-11-08 by a Claude Code research agent under this program's instructions. Every number in the table carries a verbatim quote and URL; the agent checked all 64 table quotes and 38 narrative quotes by script against text extracted from the downloaded documents. The downloaded documents themselves are not redistributed here. Paths below that point to a local scratch folder refer to the agent's working copies. Requires review like the rest of this work.

# Research D01: published sources for ambient-noise, sensor and calibration inputs

Access date for every URL below: 2026-11-08. Prepared by an AI research agent for PCK-SIM-001; it needs
review by a qualified person before any value is adopted.

## How to read this file

* Every quote was copied from a document opened in this session. The documents were downloaded through the
  environment proxy, PDFs were converted with `pdftotext`, and HTML pages were stripped to text.
* `scripts/verify.py` and `scripts/verify_prose.py` (both under the scratchpad folder that holds this file)
  checked every quote in the table and the narrative against the extracted source text: 64 table rows and
  32 narrative quotes, with 0 missing. Matching ignores whitespace, ligatures (fi/fl/ff), the Unicode
  minus and micro signs, and line-break hyphenation. `[...]` separates fragments that are not contiguous
  in the source. Superscripts that were lost in extraction are kept as extracted: `µPa 2 /Hz` means
  µPa²/Hz and `m s 1` means m s⁻¹. A separate check confirmed the KCDB record-to-uncertainty pairings.
* Local copies of the sources are in `dl/` and their text extractions are in `txt/` (same scratchpad folder).
* "Primary" means the document that made the measurement or published the specification. "Secondary"
  means a document that repeats another document's number; the original is named.
* Numbers marked **derived** were computed by this agent from a quoted equation. They are not source
  numbers. Recompute them in study code before you quote them.

## Status summary

| # | Source (as named by the reviewer) | Status | What it gives the program |
|---|---|---|---|
| 1 | Wenz (1962) JASA 34(12) | Bibliographic data verified; **full text not opened** (publisher returned HTTP 403) | Citation only. Wenz-type equations come from Coates (1989), as printed by Stojanovic (2007): **secondary**, opened |
| 2 | NRC (2003) Ocean Noise and Marine Mammals | **Opened, primary** (NAP read-online, Ch. 2) | Review statements with levels and trends, mostly citing other work; Wenz curves only as a graphic (Plate 1) |
| 3 | NOAA NCEI Passive Acoustic Data Archive and NRS (Haver et al. 2018) | **Opened, primary** | Product forms and formats, NRS hydrophone and sampling data, variability statistics. Absolute NRS levels appear only in figures |
| 4 | Teledyne RESON TC4032, TC4033, TC4014, TC4013, TC4040 (+ TC4034, TC4038) | **Opened, primary** (manufacturer PDFs and web table) | Sensitivity, preamplifier yes/no, band, capacitance (bare elements), gain, power, depth, size. Self-noise is a graph only, except TC4038 |
| 5 | "Aquarian Scientific A5" | **Opened, primary** (manufacturer web pages). The A5 exists and its vendor field reads "Aquarian Scientific" | A5 sensitivity, band, power, size and depth. S1n/AS-1 bare-element sensitivity and capacitance. No self-noise anywhere |
| 6 | IMR CRIMAC cruise report "2026" | **Opened, primary**: it is the *CRIMAC cruise report 2025*, report series Toktrapport 2026-13 | No numerical vessel-noise levels in text or tables; PSD only in Fig. 30 |
| 7 | PNNL "Oil Filled Flow Shield Performance Evaluation" (2026) | **Opened, primary** (PNNL-39138, March 2026), plus Cotter et al. 2024 (JASA EL) | Flow-noise reductions and differences, flow speeds, shield insertion loss. No absolute levels in text; **no correlation-length data** |
| 8 | NPL GPG 133 and NPL calibration services | **Opened, primary**, plus BIPM KCDB CMC records for NPL | Calibration uncertainties: 0.5 to 0.9 dB (k = 2) by band (CMC); guidance values of 0.5 dB and about 1 dB |
| + | Multi-sensor flow-noise coherence | **Partly found**: one primary thesis (opened) and the abstract of the related IEEE JOE paper (full paper not opened) | Spatial-coherence evidence at 17 cm spacing; **no correlation length is reported** |

---

## 1. Wenz (1962) and Wenz-derived parametric envelopes

**Primary article (not opened).** Wenz, G. M. (1962). "Acoustic Ambient Noise in the Ocean: Spectra and
Sources." *J. Acoust. Soc. Am.* **34**(12), 1936–1956. DOI: https://doi.org/10.1121/1.1909155.

* Verified through the Crossref API (`api.crossref.org/works?query.bibliographic=...`), which returned
  volume 34, issue 12, pages 1936-1956, published in print on 1962-12-01, author Wenz. The same data appear
  in the reference list of Cotter et al. (2024): "G. M. Wenz, “Acoustic ambient noise in the ocean: Spectra
  and sources,” J. Acoust. Soc. Am. 34(12), 1936–1956 (1962)."
* Attempt: `https://doi.org/10.1121/1.1909155` redirects to
  `https://pubs.aip.org/jasa/article/34/12/1936/684933/...`, which returned **HTTP 403** (a "Just a
  moment..." bot challenge). The article is paywalled. No equation or number from Wenz itself is used here.

### 1a. Coates empirical formulas, as printed by Stojanovic (opened; secondary)

* **Document read:** Stojanovic, M. "On the Relationship Between Capacity and Distance in an Underwater
  Acoustic Communication Channel." *ACM SIGMOBILE Mobile Computing and Communications Review* **11**(4),
  34–43 (Oct. 2007), DOI 10.1145/1347364.1347373. The DOI, volume, issue and pages come from Crossref.
  The copy I opened is the author's paper hosted by a third party:
  https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf
  (10 pages). It states: "This is a revision of the work published in the Proceedings of the First ACM
  International Workshop on Underwater Networks (WUWNet) 2006" (WUWNet'06 DOI 10.1145/1161039.1161049,
  p. 41, per Crossref).
* **Provenance chain:** Stojanovic attributes the formulas to reference [7], printed as "R.Coates,
  Underwater Acoustic Systems, New York: Wiley, 1989." The reviewer's brief says Coates (1990); the
  year and publisher in Stojanovic's reference differ, and I could not open Coates to settle this. These
  are Coates' empirical approximations to Wenz-type spectra. Neither Stojanovic nor this agent compared
  them with Wenz's published curves. Treat them as **secondary, published** values with **no stated
  uncertainty**.
* **Equations, verbatim** (PDF p. 3, Section II.B, Eq. (6); extraction spacing kept):

  ```
  10 log Nt(f ) = 17 − 30 log f
  10 log Ns (f ) = 40 + 20(s − 0.5) + 26 log f − 60 log(f + 0.03)
  10 log Nw (f ) = 50 + 7.5w 1/2 + 20 log f − 40 log(f + 0.4)
  10 log Nth(f ) = −15 + 20 log f                                  (6)
  N (f ) = Nt(f ) + Ns (f ) + Nw (f ) + Nth (f )                   (sum of linear p.s.d.)
  10 log N (f ) ≈ N1 − η log f                                     (7)  with N 1 = 50 dB re μ Pa and η=18 dB/decade
  ```

  Variables and units as printed: "the p.s.d. of the four noise components in dB re μ Pa per Hz as a
  function of frequency in kHz"; `s` is the "shipping activity factor s, whose value ranges between 0
  and 1 for low and high activity, respectively"; "w is the wind speed in m/s". `log` is base 10, which
  the paper implies but does not state. The unit label "dB re μ Pa per Hz" is as printed. Reading it as
  dB re 1 μPa²/Hz is an interpretation that the program's reviewer should confirm.
* **Validity as printed:** no formal validity range is given. Only the dominance regions are stated:
  turbulence "f < 10 Hz", shipping "10 Hz -100 Hz", wind "100 Hz - 100 kHz", thermal "f > 100 kHz". The
  paper does not give a wind-speed range or a water depth (deep or shallow).
* **Cross-check copies (both opened):**
  * Lucani, D. E., Stojanovic, M., Médard, M. "On the Relationship between Transmission Power and Capacity
    of an Underwater Acoustic Communication Channel," arXiv:0801.0426v1 (2 Jan 2008),
    https://arxiv.org/pdf/0801.0426; Crossref lists it as OCEANS 2008 Kobe, DOI
    10.1109/oceanskobe.2008.4531073. It prints the same four equations in "Bel" form (`log Nt (f ) = 1.7 − 3
    log f`, and so on), "in dB re µ Pa per Hz as a function of frequency in kHz", citing Stojanovic
    WUWNet'06. The text layer loses the "1/2" in its shipping equation (5).
  * Stojanovic, M., Preisig, J. "Underwater Acoustic Communication Channels: Propagation Models and
    Statistical Characterization," *IEEE Communications Magazine*, January 2009 (article starts p. 84).
    Author copy: https://stuff.mit.edu/people/millitsa/resources/pdfs/chmj-print.pdf. It gives no
    equations, only the figure and "approximately 18 dB/decade" (it cites Brekhovskikh and Lysanov).

**Derived evaluation (this agent; NOT source numbers; recompute in study code before use).** These are
the A1 to A4 equations summed linearly, with f in kHz and the output read as dB re 1 μPa²/Hz:

| f (kHz) | s=0, w=0 m/s | s=0.5, w=0 m/s | s=0.5, w=5 m/s | s=1, w=10 m/s |
|---|---|---|---|---|
| 0.02 | 69.40 | 74.88 | 74.89 | 84.00 |
| 0.1 | 57.68 | 67.22 | 67.79 | 77.47 |
| 1 | 44.30 | 45.37 | 60.95 | 67.93 |
| 10 | 29.34 | 29.35 | 46.09 | 53.04 |
| 20 | 23.87 | 23.87 | 40.41 | 47.35 |

Slopes of the summed model (derived): from 1 to 10 kHz, -14.96 dB/decade (s=0, w=0); -16.02 dB/decade (s=0.5, w=0); -14.86 dB/decade (s=0.5, w=5); -14.89 dB/decade (s=1, w=10). From 10 to 20 kHz, -18.17 dB/decade (s=0, w=0); -18.21 dB/decade (s=0.5, w=0); -18.86 dB/decade (s=0.5, w=5); -18.88 dB/decade (s=1, w=10). The wind term alone tends to 20 - 40 = -20 dB/decade only for f much greater than 0.4 kHz. The program assumes -17 dB/decade. At 1 kHz the s=0.5, w=0 case evaluates to 45.37 dB (derived), close to the program's assumed 'quiet' 45 dB; w=5 m/s gives 60.95 dB.

### 1b. Other Wenz-type sources sought

* **Knudsen sea-state spectra.** Citation (from the NPL GPG 133 reference list, opened): "Knudsen V.O.,
  Alford R.S., Emling J.W. Journal of Marine Research 7: 410-429, 1948." **Not opened**; I found no open
  copy. The only Knudsen number in an opened document is NRC's "5-6 dB/octave" slope (row N5).
* **Hildebrand, Frasier, Baumann-Pickering, Wiggins (2021)**, "An empirical model for wind-generated ocean
  noise," *J. Acoust. Soc. Am.* 149(6), 4516–4533, doi 10.1121/10.0005430 (citation from the Cotter 2024
  and Rogers et al. arXiv reference lists). This is the most relevant modern empirical wind-noise model
  for 10 Hz to 20 kHz. **Not opened:** `https://www.cetus.ucsd.edu/docs/publications/HildebrandJASA2021.pdf`
  failed TLS verification ("certificate has expired"; I did not bypass it), WebFetch returned HTTP 503,
  and eScholarship (`escholarship.org/uc/item/6fc3m4w5`) returned an empty response. **Recommended
  next acquisition.**
* **APL-UW TR 9407** (High-Frequency Ocean Environmental Acoustic Models Handbook, DTIC ADB199453), which
  holds the ambient-noise section. **Not opened:** DTIC returned "Service unavailable / The request is blocked."
* **"Limits of prevailing noise" (Wenz).** Found only as a graphic: NRC Plate 1 reproduces the Wenz curves.
  I found no published table or equation of the limits in any opened document.

## 2. National Research Council (2003), *Ocean Noise and Marine Mammals*

* **Citation:** National Research Council (2003). *Ocean Noise and Marine Mammals.* Washington, DC: The
  National Academies Press. https://doi.org/10.17226/10564 (paperback ISBN 0-309-08536-5, from the NAP
  catalog page https://nap.nationalacademies.org/catalog/10564/ocean-noise-and-marine-mammals).
* **Read:** Chapter 2, "Sources of Sound in the Ocean and Long-Term Trends in Ocean Noise", NAP read-online
  https://nap.nationalacademies.org/read/10564/chapter/4 (the page heading reads "Ocean Noise and Marine
  Mammals (2003) Chapter: 2. Sources of Sound in the Ocean and Long-Term Trends in Ocean Noise"). Page
  numbers in the table are the NAP read-online page markers. Anomaly: the page's "Get this book" box points
  to "NAP.edu/10766", which I did not resolve.
* **Content relevant to 20 Hz to 20 kHz:** Plate 1 is the Wenz curves, as a graphic only. The text refers
  to "broad spectral peaks labeled “usual traffic noise” in the Wenz curves (see Plate 1)". Table 2-1a/b
  characterizes anthropogenic sources. The numerical statements are in rows N1 to N9. Most are NRC
  summaries of other studies (Cato 2001, Andrew et al. 2002, Wales and Heitmeyer, Ross, Mazzuca 2001), so
  they are **secondary**. The chapter has no tabulated ambient spectrum levels across 20 Hz to 20 kHz.

## 3. NOAA NCEI Passive Acoustic Data Archive and the NOAA/NPS Ocean Noise Reference Stations

* **Archive page (opened):** https://www.ncei.noaa.gov/products/passive-acoustic-data. Archive citation
  as given on the page: "NOAA National Centers for Environmental Information. 2017. Passive Acoustic Data
  Collection. NOAA National Centers for Environmental Information. https://doi.org/10.25921/PF0H-SQ72".
* **What exists and in what form** (from the page): "The archive currently hosts free,
  globally-accessible, raw audio files and data products."
  * Raw audio in standard formats (wav, aif, mp3, flac).
  * Derived sound-level metrics. The SoundCoop standard is daily netCDF files of 1-min hybrid millidecade
    (HMD) bands (row H5); the page links an NRS example, `nrs/products/sound_level_metrics/11/.../
    NRS11_H5R6.1.5000_20191107_DAILY_MILLIDEC_MinRes_v3_v3.nc`. For SanctSound, "the SanctSound project
    established hourly decidecade bands created from 1-s observations". Its metadata records list
    broadband, octave, one-third-octave and 1 Hz PSD products at 1 h resolution.
  * Detections, propagation-model outputs and sound clips.
  * Access: Google Cloud bucket `noaa-passive-bioacoustic`, an interactive map, and the SanctSound and
    SoundCoop portals.
  * Calibration requirement: "At a minimum, manufacturer specifications for the hydrophone must be
    provided."
* **Haver et al. (2018), opened (primary):** Haver, S. M., Gedamke, J., Hatch, L. T., et al. "Monitoring
  long-term soundscape trends in U.S. Waters: The NOAA/NPS Ocean Noise Reference Station Network."
  *Marine Policy* 90 (2018) 6–13, https://doi.org/10.1016/j.marpol.2018.01.023. I opened the NOAA
  Institutional Repository copy, https://repository.library.noaa.gov/view/noaa/49062/noaa_49062_DS1.pdf
  (8 pp., journal layout). The network provides "multi-year, continuous observations of low-frequency
  underwater sound between 10 Hz and 2000 Hz". Hydrophone, sampling and processing are in rows H1 and H2.
  Monthly L50, L10 and L90 spectrum levels (dB re 1 µPa²/Hz) are shown **only in Figs. 6 and 7**; the
  text gives variability statistics only (rows H3 and H4). For Fig. 6: "The dashed line in each plot
  indicates the system noise floor." That floor is also given only graphically.
* **Implication:** calibrated NRS spectral levels exist as public data products (HMD netCDF), but I found
  no published table of summary levels. To get numbers with provenance, the program would download the
  products and compute percentiles itself; the result would be "derived from published data". I did not
  do that here.

## 4. Teledyne Marine (RESON) hydrophones

Documents opened (manufacturer, primary). PDF-metadata or copyright year is in brackets:

* TC4032 leaflet [© 2022]: https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4032%20product%20leaflet.pdf
* TC4033 leaflet [© 2026]: https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4033%20%20product%20leaflet.pdf
  (note the double space in the file name)
* TC4014 leaflet [© 2020]: `.../RESON/TC4014%20product%20leaflet.pdf`
* TC4013 leaflet [© 2020]: `.../RESON/TC4013%20product%20leaflet.pdf`
* TC4040 leaflet [PDF 2020]: `.../RESON/TC4040%20product%20leaflet.pdf`
* TC4034 leaflet [PDF 2025]: `.../RESON/TC4034%20product%20leaflet.pdf`
* TC4038 leaflet [© 2020]: `.../RESON/TC4038%20product%20leaflet.pdf`
* Product guide (catalog) [PDF 2022]: `.../RESON/Teledyne%20RESON%20Hydrophone%20catalog%20web.pdf`
* Web comparison table: https://www.teledynemarine.com/hydrophones
* Tank uncertainty sheet [PDF 2017]: https://www.teledynemarine.com/en-us/brands/SiteAssets/RESONtanktest.pdf
* Hydrophone FAQ [PDF 2020]: https://www.teledynemarine.com/en-us/products/SiteAssets/RESON/Hydrophone%20FAQ%20v1-1.pdf

Key points:

* **Integrated preamplifier:**
  * **TC4032** (10 dB) and **TC4014** (26 dB) have one, so their quoted sensitivities **include the
    preamplifier**. They must not be combined with bare-element thermal noise; the program's
    `sensor_noise_error_models.md` already warns about this.
  * **TC4013, TC4033, TC4034, TC4038 and TC4040** are bare elements (web table: "No").
* **Sensitivity convention:** the web table footnote reads "*Sensitivity stated for differential output
  and for shortest cable length". Its TC4014 row is "-180 dB" (differential); the TC4014 leaflet gives
  -186 dB single-ended and -180 dB differential.
* **Capacitance:** TC4013 3.4 nF; TC4033 7.8 nF including 10 m of cable (the prose says 7nF); TC4034 3 nF;
  TC4040 8.3 nF; TC4038 0.5 nF with 2 m of cable. RESON publishes **no loss tangent**. TC4040 gives a
  leakage resistance of >2 GΩ.
* **Self-noise:**
  * TC4032 and TC4014 show a "Typical equivalent noise pressure" **graph** with no tabulated values. The
    TC4032 graph axis is labelled "dB re 1uPa / sqr.Hz", 0 to 80, over 10 Hz to 100 kHz, with "Seastate
    zero", "Venz´s minimum" and "Thermal noise" reference curves.
  * The only numeric value is for TC4038: "Equivalent noise: 80dB re 1µPa (with VP1000 Pre-amp √Hz at
    1 kHz)". The VP1000 is an external preamplifier, and 1 kHz is outside the TC4038's stated usable range
    of 10 kHz to 800 kHz.
* **Calibration notes:**
  * The FAQ says receive sensitivity below 5 kHz is measured "in air at 250Hz using calibrated
    pistonphone".
  * The tank sheet gives "source level" (transmit) uncertainties: ±1.83 dB at 2-5 kHz, ±0.76 at 5-20 kHz,
    ±0.70 at 20-70 kHz. These apply to projector source level, not to receive sensitivity, and the sheet
    states no confidence level.
* **Inconsistencies:** the web table lists the TC4038 at "50 kHz" minimum, while its leaflet says
  "Usable frequency range: 10kHz - 800kHz".

## 5. "Aquarian Scientific A5"

* **Exists.** Product page https://www.aquarianaudio.com/products/a5-hydrophone. The store's product JSON
  (`/products/a5-hydrophone.json`) carries `"vendor":"Aquarian Scientific"`; "Aquarian Audio" is the
  older brand on the same site. No PDF datasheet is linked. The receive-sensitivity plot on the page is an
  image and I did not extract it.
* **A5:** integrated signal conditioning for plug-in-power microphone inputs, so the sensitivity includes
  the electronics. Values are in rows Q1 and Q2. The page states a uniform band of only 20 Hz to 10 kHz
  (±4 dB), which **does not cover 10 to 20 kHz** of the program band. The page gives **no self-noise, no
  capacitance and no preamplifier gain**.
* **Bare-element alternatives from the same maker:**
  * **S1n** (passive): https://www.aquarianaudio.com/products/s1-hydrophone, row Q3. The page says: "The
    receive voltage sensitivity and directional response charts are derived from calibration data provided
    by the U.S. Navy Underwater Sound Reference Division calibration labs at Newport."
  * **AS-1** (deprecated, "practically identical" to the S1n): row Q5. Its note reads: "Data obtained from
    US Navy, Underwater Sound Reference Division, Newport, June 2013, measurements taken at end of 9-meter
    cable."
  * The S1e, S1f and S1i variants with electronics are in row Q4.
  * No loss tangent and no self-noise are published for any Aquarian product.

## 6. IMR CRIMAC cruise report (vessel noise)

* **Citation:** Tenningen, M. (ed.), Allken, V. S. D., Kamrla, J., Korneliussen, R., Kubilius, R.,
  Ladroit, Y., Malde, K., Pedersen, G., Rose, C., Saltskår, J., Sørhagen, R. *CRIMAC cruise report 2025.
  GO Sars 2025001018.* Toktrapport 2026-13, Institute of Marine Research, published 30.04.2026, ISSN
  1503-6294. Section 6 (passive acoustic monitoring) is by G. Pedersen (IMR) and R. Sørhagen (Kongsberg
  Discovery). Landing page https://www.hi.no/hi/nettrapporter/toktrapport-en-2026-13; PDF
  https://www.hi.no/templates/reporteditor/report-pdf?id=114079&nc=53325687892 (64 pp.).
* **Name mismatch:** the reviewer's "2026 cruise report" is the 2025 cruise ("The cruise was conducted
  between November 14th and 20th in the Fjords in Troms") published in the 2026 report series.
* **What it contains:**
  * A temporary Kongsberg Discovery hydrophone in the drop keel of RV G.O. Sars: "The hydrophone module was
    installed in the vessel's drop keel to enable near-field measurements of vessel noise". So these are
    **near-field self-noise** data, not radiated-noise source levels.
  * Speeds of 3, 7 and 11 knots, drop keel at 0, 1.25 and 2.5 m (Table 6), drifting periods, and "Data was
    collected at sampling frequency 768 kHz."
  * Results are **only graphical**. Fig. 30 shows PSD percentiles, RMS and median at 11, 7 and 3 knots on
    an axis labelled dB re 1 µPa² Hz⁻¹ (read from the rendered figure), roughly 10 Hz to 20 kHz.
  * The text gives no levels, distances or calibration details. Rows K1 to K3 hold the only numbers.
* Not digitized. Values read off Fig. 30 would have to be labelled as "digitized from figure" and
  re-reviewed.

## 7. PNNL oil-filled flow shield (flow noise)

* **Citation:** Cotter, E., Nelson, S., Haxel, J. (PNNL), Strom, B., Brownstein, I. (XFlow Energy
  Company). *Oil Filled Flow Shield Performance Evaluation.* PNNL-39138, Pacific Northwest National
  Laboratory, March 2026. URL:
  https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-39138.pdf
* **Access:** direct `curl` returned an HTML "Request Rejected" page. I obtained the PDF through the
  WebFetch tool, which saved the binary, and extracted it locally. PNNL-39139 (the CRADA final report)
  was rejected the same way and **was not opened**.
* **Companion paper, opened, CC BY:** Cotter, E., McVey, J., Weicht, L., Haxel, J. "Performance of three
  hydrophone flow shields in a tidal channel." *JASA Express Lett.* 4(1), 016001 (2024),
  https://doi.org/10.1121/10.0024333; copy at
  https://tethys-engineering.pnnl.gov/sites/default/files/publications/Cotter_et_al_2024.pdf
* **Content:** rows P1 to P5 and C1 to C3.
  * Shield geometry: PNNL-39138 says "The wavelength of sound in seawater at 32 kHz is approximately 47 mm,
    equivalent to the inner diameter of the flow shield". In Cotter 2024, "The enclosure had a diameter of
    7 cm (4.5 times larger than the diameter of the hydrophone)".
  * Absolute flow-noise spectral levels against speed are given **only in figures** (PNNL-39138 Figs. 4 to
    6; Cotter 2024 Figs. 2 and 3).
* **Spatial correlation and coherence:** **none**. Neither document computes cross-hydrophone coherence or
  a correlation length. Both deployments placed the sensors in a row perpendicular to the flow in order to
  avoid wake interaction. The only statement about length scales is qualitative (Cotter 2024): the shield
  "effectively increases the size of the hydrophone, which increases the length scales of turbulent
  fluctuations that will partially cancel out over the body of the flow shield".
* **Internal inconsistencies in PNNL-39138, as printed:**
  * Peak flow is given as 0.75 m/s in Sec. 3.2, 0.67 m/s in the Fig. 6 caption, ">.65 m/s" in the text,
    and "< 0.7 m/s" in Sec. 3.2.
  * The list-of-figures caption for Fig. 3 says results come from "the hydrophones on the right hand side
    of the lander"; the body caption says "left hand side".
  * The report mentions "a tone at 160 kHz" while analysing 20 to 1,000 Hz spectra; this may be a typo
    for Hz.

## 8. NPL hydrophone calibration guidance and uncertainties

* **NPL GPG 133, opened (primary):** Robinson, S. P., Lepper, P. A., Hazelwood, R. A. *Good Practice
  Guide for Underwater Noise Measurement.* NPL Good Practice Guide No. 133, ISSN 1368-6550, © Crown
  Copyright 2014 (National Measurement Office, Marine Scotland, The Crown Estate). PDF:
  https://eprintspublications.npl.co.uk/6121/1/mgpg133.pdf (97 pp.). Values are in rows G1 to G4; these
  are guidance figures, not a service CMC.
* **BIPM KCDB calibration and measurement capabilities (CMCs) for NPL, opened (primary):** queried by POST
  to `https://www.bipm.org/api/kcdb/cmc/searchData/physics` with `{"metrologyAreaLabel":"AUV",
  "countries":["GB"],"keywords":"hydrophone"}`. It returned 10 records. The 5 records relevant to the
  program's band are rows M1 to M3: expanded uncertainty, k = 2, 95 %, status "Published", dated
  2004-09-29, method references IEC 565:1977. The other 5 cover 1 MHz to 20 MHz and are not relevant.
* **NPL service pages, opened:**
  * https://www.npl.co.uk/products-services/underwater-acoustics/hydrophone-calibration lists current
    ranges (row M4) but **states no uncertainties**.
  * https://www.npl.co.uk/underwater-acoustics/sensor-calibration says "The existing primary standard for
    the free-field calibration of hydrophones is based on the three-transducer reciprocity method for
    frequencies from 250 Hz to 500 kHz."
* **Caveats:**
  * The KCDB ranges (from 1 kHz) are from 2004 and do not match today's service ranges (reciprocity from
    315 Hz, pressure 5 to 315 Hz). The CMCs are the NMI's best capability, not the uncertainty of a typical
    commercial calibration.
  * The IOA paper "Standards for hydrophone calibration in the UK" (Robinson, Preston, Doré) returned HTML
    instead of a PDF and **was not opened**.

## 9. Multi-sensor flow-noise coherence (explicit measurements only)

* **Opened (primary, not peer reviewed):** Auvinen, E. M. F. *Performance of a Low-Frequency High-Flow
  Acoustic Sensing Array for Turbulent Ocean Conditions.* BSc honours thesis, Dalhousie University, April
  2017. https://noise.phys.ocean.dal.ca/docs/matthew_auvinen_honours_thesis.pdf
  * A 4-element horizontal array (GeoSpectrum) at 15 m depth, towed from an anchored vessel in Minas
    Passage, Bay of Fundy, in October 2016. Element spacing is 17 cm (row X1).
  * Magnitude coherence was computed for every pair, with a 0.7 to 0.9 threshold (row X3). The thesis
    states: "Flow noise is inherently stochastic and propagating ambient noise is highly correlated at low
    frequencies (relative to hydrophone spacing)."
* **Peer-reviewed version (abstract only):** Auvinen, M., Barclay, D., Coffin, M. "Performance of a passive
  acoustic linear array in a tidal channel." *IEEE J. Oceanic Eng.*, publication date October 1, 2020,
  https://doi.org/10.1109/JOE.2019.2944444. I opened only the abstract, on the Tethys record
  https://tethys.pnnl.gov/publications/performance-passive-acoustic-linear-array-tidal-channel (row X2).
  The full paper is on IEEE Xplore and was not opened.
* **What this does and does not support:**
  * It supports two things: flow noise was **spatially incoherent at 17 cm spacing** in the flow-noise
    band, and the band edge found from coherence (100 to 125 Hz) differs from the edge found from spectral
    slope (180 to 275 Hz) at 0.1 to 2.6 m/s.
  * Neither document reports a **correlation length** or a fitted coherence model. Turning "incoherent at
    17 cm" into a value of L for the program's exp(−r/L) field would require an assumed model, so the
    0.1 m value stays **assumed**.
* **Not pursued:** the Corcos (1963/64) turbulent-boundary-layer wall-pressure coherence model. Its
  constants (α ≈ 0.11 streamwise, 0.7 spanwise) appeared only in a search-result summary of a secondary
  arXiv paper and were not opened. That model is for flush-mounted wall sensors, not free hydrophones in
  ambient flow.

---

## Table of numerical inputs

Columns: ID | quantity | value (as printed, condensed) | units | frequency range | conditions and
applicability | stated uncertainty | verbatim quote (fragments separated by [...]) | URL | location |
primary or secondary.

| ID | Quantity | Value | Units | Frequency range | Conditions / applicability | Stated uncertainty | Verbatim quote | URL | Page / table / figure | Primary or secondary |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Turbulence noise PSD | 10 log Nt(f) = 17 - 30 log f | dB 're μ Pa per Hz' as printed (conventionally dB re 1 μPa^2/Hz); f in kHz | stated dominant f < 10 Hz | generic deep-ocean empirical model | none stated | "10 log Nt(f ) = 17 − 30 log f [...] Turbulence noise influences only the very low frequency region, f < 10 Hz" | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Sec. II.B, Eq. (6) | secondary: Stojanovic cites R. Coates, Underwater Acoustic Systems (Wiley, 1989) as [7]; Coates not opened |
| A2 | Distant-shipping noise PSD | 10 log Ns(f) = 40 + 20(s - 0.5) + 26 log f - 60 log(f + 0.03) | as A1; s dimensionless 0..1 | stated dominant 10 Hz to 100 Hz | s = shipping activity factor, 0 low, 1 high | none stated | "10 log Ns (f ) = 40 + 20(s − 0.5) + 26 log f − [...] 60 log(f + 0.03) [...] Noise caused by distant shipping is dominant in the frequency region 10 Hz -100 Hz, and it is modeled through the shipping activity factor s, whose value ranges between 0 and 1 for low and high activity, respectively" | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Sec. II.B, Eq. (6) | secondary: Stojanovic cites R. Coates, Underwater Acoustic Systems (Wiley, 1989) as [7]; Coates not opened |
| A3 | Wind (surface-wave) noise PSD | 10 log Nw(f) = 50 + 7.5 w^(1/2) + 20 log f - 40 log(f + 0.4) | as A1; w in m/s | stated major contributor 100 Hz to 100 kHz | w = wind speed (m/s) | none stated | "10 log Nw (f ) = 50 + 7.5w 1/2 + 20 log f − [...] 40 log(f + 0.4) [...] (w is the wind speed in m/s) is the major factor contributing to the noise in the frequency region 100 Hz - 100 kHz" | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Sec. II.B, Eq. (6) | secondary: Stojanovic cites R. Coates, Underwater Acoustic Systems (Wiley, 1989) as [7]; Coates not opened |
| A4 | Thermal noise PSD | 10 log Nth(f) = -15 + 20 log f | as A1 | stated dominant f > 100 kHz |  | none stated | "10 log Nth(f ) = −15 + 20 log f [...] thermal noise becomes dominant for f > 100 kHz" | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Sec. II.B, Eq. (6) | secondary: Stojanovic cites R. Coates, Underwater Acoustic Systems (Wiley, 1989) as [7]; Coates not opened |
| A5 | Units/frequency convention of A1-A4 | dB re μ Pa per Hz; f in kHz | as printed | n/a | applies to A1-A4 | n/a | "The following empirical formulae give the p.s.d. of the four noise components in dB re μ Pa per Hz as a function of frequency in kHz [7]" | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Sec. II.B | secondary: Stojanovic cites R. Coates, Underwater Acoustic Systems (Wiley, 1989) as [7]; Coates not opened |
| A6 | Total ambient PSD (linear sum) | N(f) = Nt + Ns + Nw + Nth | linear PSD | n/a | sum in linear units | n/a | "The overall p.s.d. of the ambient noise, N (f ) = Nt(f ) + Ns (f ) + Nw (f ) + Nth (f )" | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Sec. II.B | secondary (as A1) |
| A7 | Single-slope approximation of N(f) | N1 = 50; eta = 18 | N1 'dB re μ Pa'; eta dB/decade; f in kHz | 'in a certain frequency region' (not specified) | approximation to Fig. 2 curves | none stated | "10 log N (f ) ≈ N1 − η log f [...] with N 1 = 50 dB re μ Pa and η=18 dB/decade." | https://typeset.io/pdf/on-the-relationship-between-capacity-and-distance-in-an-1m9kacxwgf.pdf | PDF p.3, Eq. (7) | secondary (Stojanovic's own fit to the Coates-model curves) |
| A8 | Same Coates equations, Bel form (cross-check copy) | log Nw(f) = 5 + 0.75w1/2 + 2 log f - 4 log(f + 0.4) (others analogous) | 'dB re µ Pa per Hz' as printed; f in kHz | not stated | s 0..1, w m/s | none stated | "log Nt (f ) = 1.7 − 3 log f [...] log Nw (f ) = 5 + 0.75w1/2 + 2 log f − 4 log(f + 0.4) (6) [...] log Nth (f ) = −1.5 + 2 log f [...] in dB re µ Pa per Hz as a function of frequency in kHz" | https://arxiv.org/pdf/0801.0426 | p.2, Eqs. (4)-(7); text extraction drops the '1/2' in Eq. (5) | secondary (cites Stojanovic WUWNet'06 as [2]) |
| A9 | Ambient PSD decay rate | approximately 18 | dB/decade | not stated | generic | none stated | "The power spectral density of ambient noise decays at a rate of approximately 18 dB/decade" | https://stuff.mit.edu/people/millitsa/resources/pdfs/chmj-print.pdf | IEEE Commun. Mag. Jan 2009, p.85 | secondary (cites Brekhovskikh and Lysanov as [1]) |
| N1 | Ship-traffic noise spectrum level, Tasman Sea | as high as 80 | dB re 1 µPa^2/Hz | 20 Hz | Tasman Sea (Cato 2001) | none stated | "the ship traffic noise data indicate values as high as 80 dB re 1 µPa 2 /Hz at 20 Hz in the Tasman Sea" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 75 | secondary (NRC review; underlying measurement cited in quote) |
| N2 | Ship-traffic noise spectrum level, Timor and Arafura seas | 50 to 58 | dB re 1 µPa^2 per Hz | 20-200 Hz | Timor and Arafura seas (Cato 2001) | none stated | "in the Timor and Arafura seas, the ship noise levels vary from 50 to 58 dB re 1 µPa 2 per Hz in the band 20-200 Hz" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 75 | secondary (NRC review; underlying measurement cited in quote) |
| N3 | Long-term increase, Point Sur | approximately 10 dB over 33 years (about 0.3 dB per year) | dB | 20 to 80 Hz | continental slope off Point Sur, 1963-65 vs 1994-2001 (Andrew et al. 2002) | none stated | "The results of their analysis indicated an increase of approximately 10 dB over 33 years (about 0.3 dB per year) from 20 to 80 Hz" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 77, Fig. 2-8 | secondary (NRC review; underlying measurement cited in quote) |
| N4 | Merchant-ship spectrum variability (individual ship vs mean) | up to 5.3 below 400 Hz; about 3.1 above | dB (standard deviation) | below / above 400 Hz | Wales and Heitmeyer analysis | these are the variability values | "variations are significantly greater below 400 Hz (up to 5.3 dB standard deviation) than above (a standard deviation of about 3.1 dB)" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 55 | secondary (NRC review; underlying measurement cited in quote) |
| N5 | High-frequency slope of ship spectra and Knudsen wind curves | 5-6 | dB/octave | above 400 Hz | Knudsen curves (Plate 1) | none stated | "the decrease in ship spectral density levels with frequency above 400 Hz has the 5-6 dB/octave dependence as seen in the Knudsen curves for wind-generated noise" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 55 | secondary (NRC review; underlying measurement cited in quote) |
| N6 | Natural short-term variability | 20-30 | dB | not stated | natural processes, short periods | n/a | "naturally occurring processes can change noise levels by 20-30 dB over short periods" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 80 | secondary (NRC review; underlying measurement cited in quote) |
| N7 | Drizzle spectral peak | 10-20 dB above background | dB | near 15 kHz | drizzle in light winds | none stated | "For drizzle in light winds, a broad spectral peak 10-20 dB above the background occurs near 15 kHz" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 38 | secondary (NRC review; underlying measurement cited in quote) |
| N8 | Wind dependence band | below 1 Hz to at least 50 kHz | Hz | as value | absent man-made, biological, transient sounds | n/a | "In the absence of man-made, biological, and transient sounds, ambient noise is wind dependent over the band from below 1 Hz to at least 50 kHz" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 29 | secondary (NRC review; underlying measurement cited in quote) |
| N9 | Low-frequency shipping-noise increase | about 10-15 | dB over a 25-50-year period | 20-80 Hz | synthesis (Ross; Mazzuca 2001; Andrew et al. 2002) | none stated | "shipping noise at low frequencies (20-80 Hz) has increased by about 10-15 dB over a 25-50-year period" | https://nap.nationalacademies.org/read/10564/chapter/4 | Ch. 2, NAP page marker 80 | secondary (NRC review; underlying measurement cited in quote) |
| H1 | NRS hydrophone (ITC-1032) nominal sensitivity | -192 (flat +/-1 dB 10-2000 Hz) | dB re 1 V/μPa | 10 Hz to 2000 Hz | AUH with pre-amplifier and pre-whitening filter; 16-bit logger | flatness -/+ 1 dB | "The hydrophones are model ITC1032 (International Transducer Corp., Santa Barbara, CA) with a nominal sensitivity of −192 dB re 1 V/μ Pa and a flat frequency response (-/+ 1 dB) between 10 Hz and 2000 Hz" | https://repository.library.noaa.gov/view/noaa/49062/noaa_49062_DS1.pdf | Marine Policy 90, Sec. 2 | primary |
| H2 | NRS sampling | 5 kHz sample rate, 2 kHz low-pass; 16-bit | Hz, bits | up to 2 kHz | all NRS AUH | n/a | "record acoustic data continuously at a sample rate of 5 kHz (2 kHz low-pass cutoff) [...] maximize the dynamic range of the 16-bit acoustic data logging system" | https://repository.library.noaa.gov/view/noaa/49062/noaa_49062_DS1.pdf | Sec. 2 | primary |
| H3 | Spread of monthly levels (L10 minus L90), mode | 9.2 (Olympic Coast), 7.7 (Channel Islands), 9.3 (Gulf of Mexico); 14 (Alaskan Arctic) | dB | 10-2000 Hz (1 Hz bins) | Nov 2014 to Jun 2015 | n/a (these are variability statistics) | "with modes of 9.2 dB, 7.7 dB, and 9.3 dB, respectively [...] The frequent occurrence of a Δ dB of 14 in the Alaskan Arctic" | https://repository.library.noaa.gov/view/noaa/49062/noaa_49062_DS1.pdf | Sec. 3-4, Fig. 8 caption | primary |
| H4 | Seasonal change, Alaskan Arctic monthly L50 | ~12 dB higher (Jan 2015 vs Jun 2015) | dB | most frequencies (10-2000 Hz) | NRS01, sea-ice seasonality | n/a | "maximum monthly L50 values were recorded in January 2015 and were ~12 dB higher across most frequencies than the monthly L50 recorded in June 2015" | https://repository.library.noaa.gov/view/noaa/49062/noaa_49062_DS1.pdf | Sec. 4 | primary |
| H5 | NCEI standard soundscape product resolution | 1-min hybrid millidecade (HMD) bands, daily netCDF | time, band | product-dependent (e.g. NRS 10-2000 Hz) | SoundCoop standard | n/a | "established standardized daily netCDF files containing 1-min hybrid millidecade (HMD) bands" | https://www.ncei.noaa.gov/products/passive-acoustic-data | About / Archive Resources tab | primary (archive documentation) |
| R1 | TC4032 receiving sensitivity (includes integral preamp) | -170 single-ended; -164 differential | dB re 1V/μPa | linear 15 Hz-40 kHz +/-2 dB; 10 Hz-80 kHz +/-2.5 dB; usable 5 Hz-120 kHz | integral 10 dB preamplifier; differential output by default | band flatness only; no sensitivity tolerance stated | "connected to an integral low- [...] noise 10dB preamplifier [...] Usable frequency range: 5Hz to120kHz [...] Linear frequency range: 15Hz to 40kHz ±2dB [...] 10Hz to 80kHz ±2.5dB [...] Receiving sensitivity: -170dB re 1V/ μPa (-164dB with differential output)" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4032%20product%20leaflet.pdf | leaflet p.1/4 | primary (manufacturer) |
| R2 | TC4032 preamp, power, depth | gain 10 dB; 12-24 VDC; <=19 mA at 12 VDC; HPF 7 Hz; depth 600 m; max out >=3.5 Vrms | dB, V, mA, Hz, m | n/a |  | none stated | "Preamplifier gain: 10dB [...] Supply voltage: 12 to 24VDC [...] High pass filter: 7Hz -3dB [...] Quiescent supply current: ≤19mA at 12VDC [...] Operating depth: 600m [...] Max. output voltage: ≥3.5Vrms (at 12VDC)" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4032%20product%20leaflet.pdf | leaflet p.1/4 | primary (manufacturer) |
| R3 | TC4032 self-noise | curve only (axis 0-80 dB re 1uPa / sqr.Hz, 10 Hz-100 kHz); no tabulated value | dB re 1uPa/sqrt(Hz) | 10 Hz-100 kHz (plot axis) | 'Valid for all versions of TC4032' | none | "Typical equivalent noise pressure [...] Valid for all versions of TC4032" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4032%20product%20leaflet.pdf | leaflet p.2/4 (graph) | primary (manufacturer), graphical only |
| R4 | TC4014 receiving sensitivity (includes integral preamp) | -186 +/-3 single-ended; -180 +/-3 differential | dB re 1V/μPa | usable 15 Hz-480 kHz; linear 30 Hz-100 kHz +/-2 dB, 25 Hz-250 kHz +/-3 dB | 26 dB preamp; HPF 15 Hz | +/-3 dB | "Usable frequency range: 15Hz to 480kHz [...] Linear frequency range: 30Hz to 100kHz ±2dB 25Hz to 250kHz ±3dB [...] Receiving sensitivity: Single ended: -186dB ±3dB re 1V/μPa [...] Diff. out: -180dB ±3dB re 1V/μPa)" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4014%20product%20leaflet.pdf | leaflet p.1/4 | primary (manufacturer) |
| R5 | TC4014 preamp, power, depth | gain 26 dB; <28 mA at 12 VDC, <34 mA at 24 VDC; depth 900 m | dB, mA, m | n/a |  | none stated | "Preamplifier gain: 26dB [...] Current consumption: <28mA at 12VDC <34 mA at 24VDC [...] Operating depth: 900m [...] High pass filter: 15Hz -3dB" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4014%20product%20leaflet.pdf | leaflet p.1/4 | primary (manufacturer) |
| R6 | TC4013 (no preamp): sensitivity, capacitance | -211 +/-3; 3.4 nF | dB re 1V/µPa; nF | usable 1 Hz-170 kHz | 6 m standard cable; depth 700 m | +/-3 dB | "Usable frequency range: 1Hz to 170kHz [...] Receiving sensitivity: -211dB ±3dB re 1V/µPa [...] Nominal capacitance: 3.4nF [...] Operating depth: 700m [...] Cable length: Standard length 6m" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4013%20product%20leaflet.pdf | leaflet p.1/3 | primary (manufacturer) |
| R7 | TC4033 (no preamp): sensitivity, capacitance | -203 +/-2 at 250 Hz; 7.8 nF incl. 10 m cable (prose: 7nF) | dB re 1V/μPa; nF | usable 1 Hz-140 kHz; linear 1 Hz-80 kHz | depth 900 m | +/-2 dB | "The typical sensitivity of -203dB re 1V/µPa and the capacitance of 7nF [...] Usable frequency range: 1Hz to 140kHz [...] Linear frequency range: 1Hz to 80kHz [...] Receiving sensitivity: -203dB ±2dB re 1V/μPa at 250Hz [...] Nominal capacitance: 7.8 nF (incl.10m cable) [...] Operating depth: 900m" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4033%20%20product%20leaflet.pdf | leaflet p.1/3 | primary (manufacturer) |
| R8 | TC4040 (no preamp): sensitivity, capacitance, leakage | -206 (+/-3), 56 µV/Pa; 0.42 pC/Pa; 8.3 nF; >2 Gohm | dB re 1V/µPa; pC/Pa; nF; ohm | usable 1 Hz-120 kHz +3/-10 dB; linear 1 Hz-80 kHz +/-2.5 dB | 10 m cable; depth 400 m | +/-3 dB | "Usable frequency range: 1Hz to 120kHz +3/–10dB [...] Linear frequency range: 1Hz to 80kHz ±2.5dB [...] Receiving voltage sensitivity: -206dB re 1V/µPa (±3dB) 56µV/Pa (nominal) [...] Charge sensitivity: 0.42pC/Pa (nominal) [...] Capacitance: 8.3nF (nominal) [...] Leakage resistance: >2Gohm [...] Operating depth: 400m" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4040%20product%20leaflet.pdf | leaflet p.1/3 | primary (manufacturer) |
| R9 | TC4034 (no preamp): sensitivity, capacitance | -218 +/-3 at 250 Hz; 3 nF | dB re 1V/μPa; nF | usable 1 Hz-470 kHz (+5/-13 dB); linear 1 Hz-250 kHz (+2,-4 dB) | depth 900 m | +/-3 dB | "Usable frequency range: 1Hz to 470kHz (typical +5/-13dB) [...] Linear frequency range: 1Hz to 250kHz (+2, -4dB) [...] Receiving sensitivity: (re 1V/μPa) -218dB ±3dB (at 250Hz) [...] Nominal capacitance: 3nF [...] Operating depth: 900m" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4034%20product%20leaflet.pdf | leaflet p.1/3 | primary (manufacturer) |
| R10 | TC4038 equivalent noise (with external VP1000 preamp) | 80 at 1 kHz | dB re 1µPa per sqrt(Hz) (as printed) | 1 kHz (device usable 10 kHz-800 kHz) | with VP1000 pre-amp; 0.5 nF (2 m cable) | none stated | "Usable frequency range: 10kHz - 800kHz [...] Nominal capacitance: 0.5nF (TC4038-1 w 2m of cable) [...] Equivalent noise: 80dB re 1µPa (with VP1000 Pre-amp √Hz at 1 kHz)" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/TC4038%20product%20leaflet.pdf | leaflet p.1/3 | primary (manufacturer) |
| R11 | RESON web comparison table convention | TC4033: 1 Hz-140 kHz, -203 dB, no preamp, 900 m; sensitivities differential, shortest cable | dB rel. 1Vrms/µPa | per row | table footnote | none | "TC4033 1 Hz 140 kHz -203 dB No 900 m [...] *Sensitivity stated for differential output and for shortest cable length" | https://www.teledynemarine.com/hydrophones | hydrophone comparison table | primary (manufacturer web page) |
| R12 | Housing size (catalog) | TC4013 OD 10 mm x L 63 mm; TC4033 OD 25 x 138; TC4032 OD 38 x 285 | mm | n/a | Product guide (2022 PDF) | none | "TC4013 1 Hz to 170 kHz [...] OD 10mm [...] Length 63mm [...] TC4033 1 Hz to 140 kHz [...] OD 25mm [...] Length 138mm [...] TC4032 5 Hz to 120 kHz -164dB differential [...] Length 285mm" | https://teledynemarine.com/en-us/products/SiteAssets/RESON/Teledyne%20RESON%20Hydrophone%20catalog%20web.pdf | catalog pp.4/8 (layout-extracted; row assignment by layout) | primary (manufacturer) |
| R13 | RESON tank calibration uncertainty, single-channel | 1.83 (2-5 kHz); 0.76 (5-20 kHz); 0.70 (20-70 kHz) | +/- dB | 2-70 kHz shown (more bands in source) | stated as SOURCE LEVEL uncertainty (transmit), not receive sensitivity | as value; confidence level not stated | "For single channel units such as hydrophones and transducers the source level uncertainties are as follows [...] 2-5kHz [...] 5-20kHz [...] 20-70kHz [...] 1.83 [...] 0.76 [...] 0.70" | https://www.teledynemarine.com/en-us/brands/SiteAssets/RESONtanktest.pdf | 1-page sheet | primary (manufacturer) |
| R14 | RESON low-frequency sensitivity method; depth effect | in-air 250 Hz pistonphone; about 0.03 dB/bar | dB/bar | 250 Hz; below 5 kHz not water-calibrated | manufacturer FAQ | none stated | "As a standard RESON does not calibrate hydrophones in water below 5kHz [...] receive sensitivity measurements are performed in air at 250Hz using calibrated pistonphone and pistonphone coupler [...] About 0.03dB/Bar (1bar=10m)" | https://www.teledynemarine.com/en-us/products/SiteAssets/RESON/Hydrophone%20FAQ%20v1-1.pdf | FAQ pp.2-3 | primary (manufacturer) |
| Q1 | A5 receive sensitivity (integrated signal conditioning) | -173 | dBV re: 1uPa | uniform 20 Hz-10 kHz (+/-4 dB); omni <20 kHz | plug-in power 2.4 V/400 uA min to 48 V/10 mA max | +/-4 dB band flatness; no sensitivity tolerance | "The A5 includes integrated signal conditioning designed for direct compatibility with Plug-In Power (PIP) microphone input circuits. [...] Minimum power consumption: 2.4V, 400uA [...] Maximum power consumption: 48V, 10mA [...] Sensitivity: -173dBV re: 1uPa [...] Uniform bandwidth 20Hz - 10KHz (+/-4dB) [...] Directivity: Omnidirectional (<20KHz)" | https://www.aquarianaudio.com/products/a5-hydrophone | Specifications tab | primary (manufacturer web page; vendor field 'Aquarian Scientific') |
| Q2 | A5 size and depth | 17.5 mm dia x 35 mm; max depth 100 m | mm, m | n/a |  | none | "17.5mm diameter by 35mm overall length [...] Max depth: 100 meters" | https://www.aquarianaudio.com/products/a5-hydrophone | Specifications tab | primary (manufacturer) |
| Q3 | S1n passive element: sensitivity, capacitance | -206 dBV re 1 µPa; 6.5 nF; 1 Hz-110 kHz | dBV re 1µPa; nF | 1 Hz-110 kHz (+1.2/-3.0 dBV) | sensitivity affected by cable length; depth 200 m; 12 x 43 mm | +/-3.0 dBV QC; unit-to-unit <2 dBV typical | "S1n - Passive [...] Uniform Range (+1.2/-3.0 dBV) [...] 1 Hz–110 kHz [...] -206 dBV re: 1µPa [...] Nominal Capacitance [...] 6.5nF [...] S1n sensitivity affected by cable length. +/-3.0 dBV passed in QC. Typical variation between units of the same build is less than 2 dBV. [...] Operating Depth Maximum [...] 200 meters [...] Ø12mm x 43mm" | https://www.aquarianaudio.com/products/s1-hydrophone | Specifications tab | primary (manufacturer) |
| Q4 | S1 with integrated conditioning: sensitivity | S1e -180; S1f -180; S1i -187 | dBV re 1µPa | S1e 4 Hz-110 kHz; S1f 4 Hz-108 kHz; S1i 19 Hz-108 kHz (+1.2/-3.0 dBV) | phantom / IEPE / plug-in power | not stated per variant | "S1e - Phantom Power [...] 4 Hz–110 kHz [...] -180 dBV re: 1µPa [...] S1f - IEPE Power [...] 4 Hz–108 kHz [...] S1i - Plug-In Power [...] 19 Hz–108 kHz [...] -187 dBV re: 1µPa" | https://www.aquarianaudio.com/products/s1-hydrophone | Specifications tab | primary (manufacturer) |
| Q5 | AS-1 passive element (deprecated): sensitivity, capacitance | -208 dBV re 1 µPa (40 µV/Pa); 5 nF +/-15% plus 118 pF/m cable | dBV re 1 µPa; nF | linear 1 Hz-100 kHz (+/-2 dB) | measured at end of 9 m cable; average of limited sample; not individually calibrated | +/-3 dB QC deviation 'plus measurement error' | "The following specifications were obtained from the average of a limited sample group and were measured at the end of 9-meter cable lengths. [...] 1 Hz to 100 kHz (±2 dB) [...] -208 dBV re: 1 µPa (40 µV / Pascal) [...] 5 nF ±15% (plus cable @ 118 pF/m) [...] Standard quality control allows for a ±3 dB deviation of nominal sensitivity plus measurement error with compensation for cable attenuation." | https://www.aquarianaudio.com/products/as-1-hydrophone | Specifications tab | primary (manufacturer) |
| P1 | Flow-shield flow-noise reduction (oil-filled, icListen HF) | >20 | dB | below 50 Hz | flow > 0.5 m/s; Sequim Bay tidal channel near pier; 26-day deployment | none stated | "reduce flow noise by over 20 dB below 50 Hz at flow speeds greater than 0.5 m/s" | https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-39138.pdf | Abstract p.ii; Sec. 1 p.8 | primary |
| P2 | Flow-shield insertion loss on propagating sound | <=2 below 30 kHz; up to 6 above 30 kHz | dB | 2-130 kHz calibrated | icListen HF RB9 s/n 6661, ONC HydroCal; 3 shields | shield-to-shield within 2.5 dB (shields 1, 3) | "Below 30 kHz, the calibration curves with all three flow shields agree with the baseline calibration curve within 2 dB [...] Above 30 kHz, attenuation up to 6 dB is observed at some frequencies." | https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-39138.pdf | Sec. 2, p.9 | primary |
| P3 | Flow speeds in PNNL-39138 field test | peak 0.75 (Fig. 6 period 0.67; analysis states < 0.7) | m/s | n/a | ADV sampled 5 min every 30 min | ADV SNR degraded below ~0.25 m/s | "Peak horizontal flow speeds reached 0.75 m/s [...] peak flow speeds (0.67 m/s) [...] (flow speeds < 0.7 m/s)" | https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-39138.pdf | Sec. 3.2 pp.12-15 | primary (note internal inconsistency) |
| P4 | Unshielded excess noise at slack flow | over 10 | dB | lowest frequencies measured (from 20 Hz) | flow 0-0.2 m/s; unshielded vs shielded | none stated | "Even in data collected when flow speeds were between 0 and 0.2 m/s, noise levels measured by the baseline hydrophone are elevated over 10 dB above the shielded hydrophone at the lowest frequencies measured." | https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-39138.pdf | Sec. 3.2 p.12 | primary |
| P5 | Upper frequency of flow-noise contamination | approximately 300 | Hz | n/a | icListen HF unshielded, flows to ~0.75 m/s | none stated | "Below 200 Hz, noise levels measured by the baseline hydrophone increase with flow speed [...] Above approximately 300 Hz, noise levels measured by the baseline and" | https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-39138.pdf | Sec. 3.2 pp.12-13 | primary |
| C1 | Flow noise above slack, unshielded SoundTrap ST600 HF | 59 | dB above slack | 40 Hz | flow 1.2-1.4 m/s; Sequim Bay inlet, Jan-Feb 2023 | none stated | "At peak recorded flow velocities (1.2–1.4 m s 1), baseline sound levels were elevated 59 dB above slack conditions at 40 Hz." | https://tethys-engineering.pnnl.gov/sites/default/files/publications/Cotter_et_al_2024.pdf | JASA EL 4, 016001-4 (Sec. 3) | primary |
| C2 | Flow-noise reduction by shield (oil / nylon / ballistic nylon) | 31, 19, 25 at 40 Hz; 23, 11, 21 at 100 Hz | dB | 40 Hz; 100 Hz | flow 1.2-1.4 m/s; oil shield 7 cm dia on 1.5 cm hydrophone | none stated | "the oil-filled, nylon, and ballistic nylon flow shields reduced mean flow noise contamination by 31, 19, and 25 dB, respectively [...] reduced mean flow noise contamination by 23, 11, and 21 dB at 100 Hz, respectively" | https://tethys-engineering.pnnl.gov/sites/default/files/publications/Cotter_et_al_2024.pdf | 016001-4 (Sec. 3) | primary |
| C3 | Flow noise vs ambient in tidal channels (Bassett et al. 2014) | over 50 dB above ambient at 20 Hz; affected up to 500 Hz | dB; Hz | 20-500 Hz | peak current 3 m/s | none stated | "found that flow noise effects exceeded ambient levels by over 50 dB at the lowest frequencies measured (20 Hz) and impacted measurements at frequencies up to 500 Hz at peak current speeds of 3 m s 1" | https://tethys-engineering.pnnl.gov/sites/default/files/publications/Cotter_et_al_2024.pdf | 016001-1 (Introduction) | secondary (Cotter citing Bassett et al. 2014, JASA 135(4)) |
| K1 | GO Sars hull (drop-keel) hydrophone: vessel-noise dominance | below ~100 Hz; biological signals visible above ~3000 Hz | Hz | as value | 3, 7, 11 knots; drop keel 0/1.25/2.5 m; Troms fjords Nov 2025 | none; levels only in Fig. 30 (dB re 1µPa^2 Hz^-1 axis) | "Passive acoustic monitoring with hull (drop keel) mounted hydrophone showed that vessel noise dominates below ~100 Hz [...] vocalization above ~3000 Hz (e.g. by killer whales) is clearly" | https://www.hi.no/templates/reporteditor/report-pdf?id=114079&nc=53325687892 | Summary p.3; Sec. 6.3 pp.35-37 | primary |
| K2 | GO Sars: flow noise at speed | saturation and flow-related noise at 11 knots | knots | not stated | hull-mounted, near field | none | "At 11 knots saturation and additional noise related to flow is observed which is not found at lower cruising speeds." | https://www.hi.no/templates/reporteditor/report-pdf?id=114079&nc=53325687892 | Sec. 6.3 p.35 | primary |
| K3 | 333 kHz echosounder noise change (out of band) | 4.5 times (6.5 dB) 2025 vs 2023 | dB | 280-380 kHz | EK80 FM mode, ~10 knots | none | "noise averaged over the whole bandwidth in FM-mode was 4.5 times (6.5 dB) stronger in 2025 than in 2023" | https://www.hi.no/templates/reporteditor/report-pdf?id=114079&nc=53325687892 | Sec. 3 p.23, Fig. 19 | primary |
| G1 | Hydrophone lab calibration uncertainty (guidance) | 0.5 (hydrophone); order of 1 (system) | dB | not stated | laboratory conditions | as value | "It is possible to calibrate a hydrophone in laboratory conditions with an uncertainty of 0.5 dB, and the overall uncertainty of the recording system can be of the order of 1 dB." | https://eprintspublications.npl.co.uk/6121/1/mgpg133.pdf | Sec. 8.2 p.77 | primary (guidance, not a service CMC) |
| G2 | System calibration uncertainty (guidance) | better than 1 (95 % confidence) | dB | not stated | hydrophone and recording system | as value | "It is possible to calibrate a hydrophone and recording system with an overall uncertainty of better than 1 dB (expressed at a 95% confidence level)." | https://eprintspublications.npl.co.uk/6121/1/mgpg133.pdf | Sec. 3.2.1 p.29 | primary |
| G3 | Self-noise margin rule | at least 6 below lowest level to be measured | dB | frequency range of interest | guidance | n/a | "the self-noise equivalent sound pressure level should ideally be at least 6 dB below the lowest noise level to be measured in the frequency range of interest" | https://eprintspublications.npl.co.uk/6121/1/mgpg133.pdf | Sec. 3.1.4 p.25 | primary |
| G4 | Flow noise band (guidance) | typically <100 | Hz | n/a | depends on hydrophone diameter and current speed | n/a | "It gives rise to low frequency signals (typically <100 Hz), with the frequency being dependent upon the hydrophone diameter and the speed of the current" | https://eprintspublications.npl.co.uk/6121/1/mgpg133.pdf | Sec. 4.3.1 pp.39-40 | primary |
| M1 | NPL CMC free-field sensitivity, reciprocity | 0.7 (1-2 kHz); 0.5 (2-500 kHz) | dB, k = 2, 95 % | 1 kHz to 500 kHz | three-transducer reciprocity, IEC 565:1977; published 2004-09-29 | as value | ""kcdbCode":"EURAMET-AUV-GB-000007W8-1" [...] "cmcUncertainty":{"lowerLimit":0.7,"upperLimit":0.7,"unit":"dB"} [...] "parameterValue":"1 kHz to 2 kHz" [...] "kcdbCode":"EURAMET-AUV-GB-000007W9-1" [...] "cmcUncertainty":{"lowerLimit":0.5,"upperLimit":0.5,"unit":"dB"} [...] "parameterValue":"2 kHz to 500 kHz"" | https://www.bipm.org/api/kcdb/cmc/searchData/physics (POST, NPL, AUV, keyword hydrophone) | KCDB records W8-1, W9-1 | primary (BIPM KCDB) |
| M2 | NPL CMC free-field sensitivity, comparison | 0.9 (1-2 kHz); 0.7 (2 kHz-1 MHz) | dB, k = 2, 95 % | 1 kHz to 1 MHz | comparison with reference hydrophone | as value | ""kcdbCode":"EURAMET-AUV-GB-000007WA-1" [...] "cmcUncertainty":{"lowerLimit":0.9,"upperLimit":0.9,"unit":"dB"} [...] "kcdbCode":"EURAMET-AUV-GB-000007WB-1" [...] "parameterValue":"2 kHz to 1 MHz"" | https://www.bipm.org/api/kcdb/cmc/searchData/physics (POST, NPL, AUV, keyword hydrophone) | KCDB records WA-1, WB-1 | primary (BIPM KCDB) |
| M3 | NPL CMC pressure sensitivity (low frequency) | 0.5 | dB, k = 2, 95 % | 25 Hz to 400 Hz | comparison with a calibrated reference microphone | as value | ""kcdbCode":"EURAMET-AUV-GB-000007WC-1" [...] "quantityValue":"Pressure sensitivity level" [...] "parameterValue":"25 Hz to 400 Hz"" | https://www.bipm.org/api/kcdb/cmc/searchData/physics (POST, NPL, AUV, keyword hydrophone) | KCDB record WC-1 | primary (BIPM KCDB) |
| M4 | NPL current service ranges (no uncertainties on page) | reciprocity 315 Hz-500 kHz; comparison 1 kHz-1 MHz; pressure 5-315 Hz | Hz | as value | NPL web page | not stated on page | "Free-field calibration of hydrophones by the reciprocity method in the NPL tank facilities in the frequency range from 315 Hz to 500 kHz. [...] Pressure calibration of hydrophones by comparison method from 5 Hz to 315 Hz" | https://www.npl.co.uk/products-services/underwater-acoustics/hydrophone-calibration | service list | primary |
| X1 | Array geometry for flow-noise coherence measurement | 17 cm element spacing; 51 cm max | cm | n/a | 4-element horizontal array, 15 m depth, towed from anchored vessel in Minas Passage, Oct 2016 | n/a | "Each hydrophone pair is separated by 17 centimeters such that the maximum spacing is 51 centimeters." | https://noise.phys.ocean.dal.ca/docs/matthew_auvinen_honours_thesis.pdf | Sec. 3.2.2 p.14 | primary (BSc honours thesis, not peer reviewed) |
| X2 | Max frequency of (incoherent) flow noise from spatial coherence | 100 to 125 Hz; spectral equal-level 180 to 275 Hz | Hz | < 500 Hz analysed | currents 0.1 to 2.6 m/s | none stated in abstract | "Spectral slope analysis is used to identify the frequencies at which the flow noise and ambient noise contributions to the recorded signal are equal, between 180 and 275 Hz for current speeds of 0.1 to 2.6 m/s, respectively. The maximum frequencies at which flow noise is observed, between 100 and 125 Hz over the same current speed range, are determined using analysis of the spatial coherence." | https://tethys.pnnl.gov/publications/performance-passive-acoustic-linear-array-tidal-channel | IEEE JOE abstract (doi 10.1109/JOE.2019.2944444); full paper not opened | primary abstract only |
| X3 | Coherence threshold used | 0.7 - 0.9 | magnitude coherence | f < 500 Hz | choice by author | n/a | "Record length, hydrophone spacing, and other physical details suggest a reasonable spatial coherence threshold range of 0.7 - 0.9." | https://noise.phys.ocean.dal.ca/docs/matthew_auvinen_honours_thesis.pdf | Sec. 3.3.4 p.21 | primary (thesis) |

---

## Gaps: inputs that cannot be sourced now and must stay labeled "assumed"

1. **Element dielectric loss tangent (tan δ).** No manufacturer publishes one: RESON TC4013, TC4033,
   TC4034, TC4038 and TC4040; Aquarian S1n and AS-1. Only TC4040 states a leakage resistance (>2 GΩ).
   Capacitance **is** published, so the bare-element thermal noise can use published C and sensitivity
   with an assumed tan δ.
2. **Preamplifier e_n, i_n and 1/f corner.** Not published for the TC4032 or TC4014 integral preamps, the
   A5 or S1 electronics, or the RESON EC6081. Equivalent self-noise exists only as graphs (TC4032, TC4014)
   or as one off-band point (TC4038 with VP1000, 80 dB re 1 µPa/√Hz at 1 kHz). To source these, measure
   them, or digitize the curves and label them "digitized".
3. **Self-noise of low-cost hydrophones (A5, S1).** Not published.
4. **Ambient spectrum levels.**
   * The only equation-form source opened is Coates via Stojanovic (secondary). It has no stated
     uncertainty and no validity range beyond dominance bands, and its unit label is ambiguous.
   * Wenz (1962), Knudsen (1948), Hildebrand et al. (2021) and APL-UW TR 9407 were not opened.
   * The NRS and other NCEI data are public, but published summary levels appear only in figures.
   * Site percentiles would have to be computed from the HMD netCDF products and labelled "derived from
     published data".
5. **Ambient level uncertainty and variability.**
   * Haver et al. give L10 minus L90 spreads with modes of 7.7 to 14 dB at four NRS sites (10 to 2000 Hz).
   * NRC states that natural processes change levels by 20 to 30 dB over short periods.
   * Neither is an uncertainty on a model curve.
6. **Vessel radiated and self-noise levels (CRIMAC).** Figures only. The report gives no source levels,
   ranges or calibration description in its text.
7. **Absolute flow-noise levels against speed.** PNNL and Cotter give these only in figures. The text
   gives relative values (for example 59 dB above slack at 40 Hz, 1.2 to 1.4 m/s, unshielded SoundTrap)
   that are site-, turbulence- and geometry-specific.
8. **Flow-noise spatial correlation length.** No published value was found. Coherence evidence exists
   (17 cm spacing, incoherent below roughly 100 to 125 Hz), but no length or model, so the program's
   0.1 m must stay assumed.
9. **Channel-to-channel gain and phase mismatch.** These are not absolute calibration uncertainty.
   * Published absolute-calibration figures: 0.5 to 0.9 dB (NPL CMC, k = 2); "0.5 dB" hydrophone and
     "of the order of 1 dB" system (GPG 133).
   * Manufacturer sensitivity tolerances: ±2 to ±3 dB (RESON); ±3 dB QC with typical unit-to-unit
     variation under 2 dB (Aquarian).
   * None of these is a measured inter-channel mismatch for an array, so the program's σ_g and σ_φ sweeps
     stay assumed. The figures can bound them.
10. **Ambient-noise directionality and spatial structure.** Not addressed by any source in this task, so
    the field shapes stay assumed.

## Attempts that failed (for the record)

* pubs.aip.org (Wenz 1962): HTTP 403 bot challenge.
* cetus.ucsd.edu (Hildebrand 2021): expired TLS certificate, and HTTP 503 via WebFetch. eScholarship:
  empty response.
* apps.dtic.mil (APL-UW TR 9407): "The request is blocked".
* pnnl.gov direct download: "Request Rejected" (PNNL-39138 was obtained via WebFetch; PNNL-39139 was not
  opened).
* ioa.org.uk (Robinson, Preston, Doré): an HTML page instead of a PDF.
* peerj.com/articles/20382.pdf (2025 NRS retrospective): an HTML page instead of a PDF; not opened.
* A first attempt to fetch a pnnl.gov PDF with a browser user-agent string was blocked by this session's
  permission policy and was not repeated.
