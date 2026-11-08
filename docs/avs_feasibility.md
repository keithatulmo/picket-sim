# Acoustic vector sensors: feasibility assessment for Picket (D05)

Status: SIM-02A deliverable. Assessment only; no vector-sensor model is implemented beyond the ideal
first-order directivity calculation in `src/picket_sim/avs.py`. No vendor, product or measured value
is used. Statements carry confidence levels.

## 1. Why consider them

The SIM-01 and SIM-02A results show that compact pressure arrays gain almost nothing against diffuse
noise at low frequency, and reach -3 dB conventional discrimination only once the aperture is a
substantial fraction of a wavelength. An acoustic vector sensor (AVS) measures pressure and particle
motion (velocity, acceleration or a pressure gradient) at one point. Its directivity comes from the
vector nature of particle motion, not from aperture, so in the ideal it does not degrade as frequency
falls. That directly addresses the regime where the pressure-array candidates are weakest.

## 2. Expected capability (ideal theory)

An ideal AVS with pressure and three orthogonal velocity channels can form any first-order pattern
b(theta) = alpha + (1 - alpha) cos(theta), steered electronically to any direction. Against
spherically isotropic noise its directivity factor is D = 1 / (alpha^2 + (1 - alpha)^2 / 3)
(derived and verified by quadrature in `avs.py` and `tests/test_sim02a_models.py`):

| Pattern | alpha | D | DI (dB) |
|---|---|---|---|
| Omnidirectional (pressure only) | 1 | 1 | 0.00 |
| Dipole (one velocity axis) | 0 | 3 | 4.77 |
| Cardioid | 1/2 | 3 | 4.77 |
| Hypercardioid (first-order maximum) | 1/4 | 4 | 6.02 |

Confidence: high, for ideal noise-free, perfectly calibrated channels.

Consequences relative to the SIM-02A pressure-array results:

* A single ideal AVS would provide 4.8 to 6.0 dB of directivity against isotropic noise at every
  frequency. The compact 4-hydrophone candidates provide band-median values under 0.3 dB from 100 Hz to
  1 kHz in the same noise model (SIM-01 Rev A). Moderate confidence that a practical advantage exists
  at low frequency; its size depends on the non-ideal effects in Section 3.
* A cardioid (pressure plus velocity) has a single null, so a horizontal two-axis AVS resolves
  left/right ambiguity at one point. That provides full-circle azimuth observability (D02) without an
  extended aperture. High confidence in the ideal; practical accuracy depends on calibration and
  heading knowledge.
* First-order patterns are broad (cardioid half-power width of about 131 deg), so an AVS offers bearing
  estimation and moderate noise rejection, not high resolution. Resolving several simultaneous sources
  requires arrays of AVSs or subspace methods. High confidence.

Standard reference for vector-sensor array processing: A. Nehorai and E. Paldi, "Acoustic
vector-sensor array processing," IEEE Transactions on Signal Processing, vol. 42, no. 9, 1994.

## 3. Factors that limit practical performance

| Factor | Effect | Confidence |
|---|---|---|
| Particle-motion channel self-noise | The motion signal of ambient noise is small; at low frequency inertial sensors need very low acceleration noise to stay ambient-limited. If channel noise dominates, the realized directivity falls toward that of the pressure channel alone. | High (qualitative); magnitude unknown without device data |
| Mechanical vibration and flow | Motion sensors respond to housing motion. On a moving or vibrating host, vibration and flow-induced motion can dominate the acoustic particle motion. Compliant suspension and flow shielding are normally required. | High (qualitative) |
| Proximity to the host structure | Near a rigid surface the normal particle velocity is forced toward zero and the pressure field is modified. A hull-mounted AVS without standoff sees a distorted field. | High (boundary-condition physics) |
| Orientation | Directions are measured in the sensor frame; bearing needs heading and attitude (compass or IMU). Their errors add directly to the bearing error. | High |
| Calibration | Relative gain and phase between the pressure and motion channels set the null depth and the achieved DI. This is the same mathematics as the SIM-02A channel-error model applied to p-v channels. | High |
| Channel count and acquisition | 3 to 4 channels per sensor: similar acquisition load to a 4-hydrophone array, at a single mounting point. | High |
| Power, cost, integration | Depend on the sensing technology (inertial or pressure-gradient) and on suspension and packaging. Not assessed: no published or measured data have been collected. | Unknown |

## 4. Fit with Picket objectives

* Primary objective (observation and detection, D02): the AVS pressure channel provides the A0
  capability, so an AVS-based node is no worse than A0 for omnidirectional detection.
* Secondary objective (incremental value of directional sensing): an AVS offers directional
  information below the frequencies where compact pressure arrays reach -3 dB discrimination, and
  removes left/right ambiguity at a single point. The value depends on the motion-channel noise and
  the platform vibration environment, which SIM-02A does not model.

## 5. Recommended next steps (not authorized work; for the reviewer's decision)

1. Collect published and measured data for candidate AVS technologies (self-noise spectra of the
   motion channels, vibration sensitivity, size, power, cost), with provenance per ADR-0010.
2. Extend the framework: the `element_response` hook of `PlaneWaveManifold` (ADR-0007) can represent
   dipole channels (cosine response), and the SIM-02A noise and error machinery applies unchanged to
   p-v channels. Add motion-channel self-noise and a vibration-noise scenario model.
3. Compare A0, a single AVS, and the compact pressure arrays at equal channel count in SIM-02B's
   task-level experiments (detection at fixed false-alarm rate, bearing error statistics).

Overall feasibility for further study: favorable for low-frequency directional sensing in the ideal
(high confidence). Practical feasibility on Picket hosts is unknown until motion-channel noise and
platform vibration are characterized.

## 6. D05 desk research and bench-test recommendation (SIM-02B.1)

Authorized scope: desk research and documented supplier data only (ADR-0014). Evidence, with verbatim quotes
and URLs, is in [`docs/research/D05_avs_supplier_data.md`](research/D05_avs_supplier_data.md): 15 product rows
from GeoSpectrum, Wilcoxon, Ocean Applied Acoustics, Micro-Fine, Integral Consulting and Greeneridge, plus six
measurement sources (TNO 2019 tank and field tests, Raghukumar et al. 2019, Thode et al. 2012, Lawrence 2023,
Mantouka et al. 2017, and a best-practice guide with the NPL calibration review).

| Criterion | Evidence (sourced) | Reading |
|---|---|---|
| Low-frequency benefit | Realized bearing precision exists: 1 to 2 deg at SNR above 10 dB and 15 to 20 deg at 5 dB or less, below 450 Hz, bottom-mounted (Thode et al.); tank error at most 5.88 deg at 350 to 1300 Hz (Lawrence). Ambient-limited operation is shown only above about 25 Hz (TNO, extrapolated). Generic accelerometer self-noise would not be ambient-limited at low frequency in quiet conditions (derived in the evidence file). | Plausible for purpose-built sensors on decoupled mounts; unproven below about 25 to 50 Hz. SIM-02B.1 shows compact pressure arrays gain essentially nothing over A0 in diffuse low-band noise, so a single-point directional sensor is the only compact route to low-frequency direction. |
| Size | Sensing heads from 0.011 kg (VS-403) and 43 g (VS-301) to 3.4 kg (M20-105); suspensions, cages and flow shields set the real envelope. | Favorable relative to a pressure array of equal low-frequency directivity. |
| Power | Sub-watt per sensor in every vendor figure found (for example 40 mA at 6.5 to 12 VDC, VS-301). | Not a discriminator. |
| Cost | No public prices; one survey table gives 9 to 15 kEUR per sensor; one system is lease-only; Wilcoxon units are reported as ITAR-controlled. | Unfavorable for a proliferated low-cost system if commercial units are required. |
| Calibration | Shaker, standing-wave tube and water comparison methods are documented; no open numeric uncertainty for vector sensors; measured discrepancies of 1 to 20 % in amplitude, 4 dB in water versus air, and over 153 deg of phase. | A bench test is feasible; traceable low-frequency in-water calibration and channel phase matching are the hard part. |
| Vibration and mounting | Every source names it the dominant practical problem: surface-buoy use poor below 50 to 100 Hz; seabed cages preferred; no numeric rejection specification published. | The main unknown for Picket hosts. |
| Flow noise | A flow shield is described as critical in a tidal channel (0 to 500 Hz); no quantitative open data for sizing one. | Unfavorable in current unless shielded or drifting. |

**Recommendation: conditional go for a limited bench test (moderate confidence).** The open literature
cannot close the four gaps that decide feasibility: low-frequency motion-channel self-noise, vibration
transfer from a representative host mount, flow-noise susceptibility, and achievable calibration and phase
matching. A bench test is the cheapest way to measure them, and nothing else in the program can supply a
compact low-frequency directional option. The test should measure, with stated uncertainty: (1)
motion-channel self-noise from 20 Hz to 2 kHz on a decoupled mount, compared with the published-reference
ambient envelope of SIM-02B.1; (2) noise added by a representative host mount under representative
vibration; (3) per-unit sensitivity and inter-channel phase repeatability by shaker and tube calibration;
(4) the bearing error against a known source in a tank above about 500 Hz. Pass/fail values for these
quantities are a program decision and are not proposed here. A "no-go" is the better choice if Picket
hosts cannot offer a decoupled, low-vibration mount, because then the vibration evidence above predicts
the sensor would not be ambient-limited where its benefit lies. Unit cost remains unfavorable for
proliferation unless a lower-cost design proves adequate in the same test.
