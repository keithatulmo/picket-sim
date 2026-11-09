# D02 synchronized multihydrophone coherence collection plan

Status: plan only; no collection has been performed or authorized beyond planning (ADR-0018, D02). Every design
number below is computed by `tools/d02_collection_design.py` with the study code and tabulated in
`reports/SIM-02B2A_d02_design.md`. Published coherence measurements remain interim references and are never labeled
as Picket measurements. Coherence-sensitive simulation predictions may not set hardware requirements until this
collection (or an equivalent) supplies empirical evidence.

## 1. Questions the collection must answer

1. **Ambient coherence.** Does the ambient field at Picket-relevant sites follow the spherically or horizontally
   isotropic coherence used as the nominal model (SIM-02A/B, N-AMB), at the pair spacings that occur in the
   candidates (0.150 to 1.070 m across A1, P8-C and A4) and over B1 to B3 (20 Hz to 10 kHz)?
2. **Structure-related interference.** How much of the received field near a representative host mount is coherent
   with the host's own vibration, and at which frequencies?
3. **Flow-associated effects.** At what spacing does flow-associated pressure noise decorrelate, as a function of
   frequency and current speed? The simulation's 0.1 m exponential correlation length (N-FLOW) is assumed; the only
   published evidence found (D01, register rows X1 to X3) is qualitative: incoherent at 17 cm spacing below roughly
   100 to 125 Hz in a tidal channel, with no correlation length reported.
4. **Background stationarity (new with SIM-02B.2-A).** The adaptive-normalizer results depend on how quickly the
   background changes between reference and test windows and how often reference windows are disturbed. The STEP
   (+1 and +3 dB) and INTERF (probability 0.25, +10 dB) scenarios are assumed. The collection should measure the
   distribution of level changes between a 1 s test window and its 16 preceding windows, and the fraction of windows
   with band power well above the running median, so that those scenarios can be replaced by measured ones.

## 2. Separation principle

The three components differ in how their coherence depends on spacing and on controllable conditions:

* Acoustic (ambient) noise is coherent over spacings that are small against half a wavelength. At 100 Hz and
  0.08 m the spherically isotropic model gives a coherence of 1.000, and at 200 Hz and 0.16 m it gives 0.997.
* Flow-associated noise decorrelates over a convective length that does not scale with the acoustic wavelength.
  Under the assumed 0.1 m exponential model the same two pairs would show 0.449 and 0.202. A short-spacing pair at
  low frequency therefore separates the two: a coherence well below the acoustic prediction, rising and falling
  with current speed, is the flow signature. The contrast disappears at high frequency (at 10 kHz and 0.08 m the
  spherical model already gives -0.062), so flow separation is a low-frequency measurement.
* Structure-related interference is coherent with vibration of the mount. Reference accelerometers on the mount,
  recorded on the same clock, allow partial and multiple coherence analysis (Bendat and Piersol, *Random Data*, 4th
  ed., Wiley, 2010, chapter on multiple-input systems): the part of each hydrophone spectrum that is linearly
  predictable from the accelerometers is attributed to the structure, and the residual is analysed as ambient plus
  flow.

Controlled contrasts make the attribution testable rather than inferred: host machinery on and off, array on the
mount and on a stand-off frame, flow shield on and off at matched current, and current speed over a tidal cycle.

## 3. Sensor layout and acquisition

* **Line of seven hydrophones** at marks 0, 1, 4, 10, 18, 23 and 25 times 0.08 m (a Golomb ruler: every pair
  spacing occurs once). Aperture 2 m; 21 distinct pair spacings from 0.08 to 2 m, covering every candidate spacing
  with margin. One deployment measures coherence against spacing without moving sensors.
* **Optional close pair:** an eighth hydrophone 0.04 m from the first, for flow decorrelation at the shortest scale
  and for the 5 to 10 kHz end of B3, where the line's shortest spacing (0.08 m) exceeds half a wavelength at 10 kHz
  (0.075 m).
* **Vibration references:** at least one triaxial accelerometer on the host mount, and one on the array frame, on
  the same acquisition clock.
* **Acquisition:** one simultaneous-sampling multichannel recorder (all channels on one sample clock), with sample
  rate high enough for B3 (above 20 kHz; 10 kHz is the B3 upper edge). Inter-channel skew sets a phase error of
  360 f dt degrees: 1 degree at 10 kHz corresponds to 0.278 us and 5 degrees at 2 kHz to 6.94 us, so a single
  simultaneous-sampling recorder is preferred over separately clocked units. Residual skew is measured (Section 5)
  rather than assumed.
* **Ancillary data:** current speed and direction at array depth (current meter or ADCP), wind speed, sea state,
  vessel traffic (AIS where available), host machinery state log, water depth, temperature and salinity (sound
  speed), and the array depth and orientation.

This is measurement equipment for the collection. It is not a Picket sensor, array or hardware recommendation.

## 4. Configurations and run matrix

| ID | Array position | Host machinery | Flow shield | Current | Purpose |
|---|---|---|---|---|---|
| K1 | stand-off frame, away from host | off or absent | on | low (slack water) | reference ambient coherence |
| K2a | representative host mount | off | on | low | mount effect without machinery |
| K2b | representative host mount | on | on | low | structure-related interference (partial coherence against accelerometers) |
| K3a | stand-off frame | off or absent | on | swept over a tidal cycle | flow dependence with shielding |
| K3b | stand-off frame | off or absent | off | matched to K3a | shield effect, flow decorrelation length |

Each condition is recorded for at least 30 minutes so that several independent coherence estimates can be formed
and their stability checked (Section 6). Two sites would show whether the ambient result transfers (for example an
open-water site and a current-dominated site); the site choice is the program's.

## 5. Calibration and synchronization records

* Per-channel sensitivity and phase at the start and end of the collection by a comparison method, with stated
  uncertainty; recorded with the data as `measured` per ADR-0010.
* Electrical common-signal injection into every channel to measure inter-channel delay and gain of the acquisition
  path; repeated each deployment.
* Co-located check: all hydrophones within a small cluster in the same field for a short record, to confirm that
  measured coherence at negligible spacing is near one after calibration.

## 6. Analysis and statistical sizing

* **Estimates:** per-channel PSD, cross-spectral density and magnitude-squared coherence (MSC) for every pair, with
  1 Hz resolution in B1 and B2 (1 s segments) and coarser resolution in B3; the same windows as the simulation where
  possible.
* **Estimator statistics** (checked by Monte Carlo in the design tables): with n independent segments, the MSC
  estimate of truly incoherent channels exceeds 1 - alpha^(1/(n - 1)) with probability alpha; for n = 256 and
  alpha = 0.05 that threshold is 0.0117, and the mean bias of the null estimate is 1/n (0.0039). For a true MSC of
  0.6 the standard deviation at n = 256 is 0.027. With 1 s segments, 256 segments take 256 s, so a 30 minute record
  gives several independent estimates per condition for a stationarity check.
* **Model fits:** for each frequency, fit measured coherence against spacing with the spherical and horizontal
  isotropic models plus a short-correlation term whose length is estimated (replacing the assumed 0.1 m), with
  confidence intervals; report goodness of fit rather than forcing a model.
* **Structure-related fraction:** multiple coherence of each hydrophone with the accelerometers, per frequency, for
  K2a and K2b.
* **Stationarity statistics for SIM-02B.2-A:** distribution of 10 log10 of the ratio of each 1 s window's band power
  to the mean of its 16 preceding windows (two-window guard), and the fraction of windows exceeding the running
  median by 10 dB, per condition. These map directly onto the STEP and INTERF scenarios.

## 7. Products and labeling

* Raw multichannel records with calibration, ancillary and configuration metadata; processed tables of PSD, MSC
  and the fitted parameters with uncertainties; a short report.
* Values entering simulation configurations are labeled `measured` with site, date, configuration ID and instrument
  (ADR-0010). Published coherence measurements stay `published` interim references.
* No Picket hardware requirement is derived from the collection without a separate review.

## 8. Decisions requested from the program

Site selection; access to a representative host mount and machinery; whether the optional close pair and a second
site are included; the acceptance criteria for the fitted correlation length and stationarity statistics. A cost
estimate requires the site and equipment decisions and is not given here.
