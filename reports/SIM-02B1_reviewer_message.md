Subject: PCK-SIM-001: SIM-02A closeout and SIM-02B.1 results for review

[Name],

Your SIM-02A review set five reproducibility actions and authorized SIM-02B in stages. The closeout actions are complete, and SIM-02B.1, the signal and detection-model foundation, is ready for your review. SIM-02B.2 has not started and waits on the decisions below.

Attachments:
1. SIM-02B1_transmittal.pdf ({TR_PAGES} pages). Start here. It maps each closeout action, deliverable and verification requirement to evidence, records the D01 to D06 dispositions and lists the decisions needed for SIM-02B.2.
2. SIM-02B1_engineering_report.pdf ({REP_PAGES} pages). Methods, results by band and signal class, false-alarm calibration, limitations and recommendations.
3. {ZIP_NAME} ({ZIP_MB} MB). The documents above plus figures, run tables, example waveforms, the input provenance register with its evidence files, the AVS assessment, the D06 criterion table and two source archives. SHA256SUMS.txt verifies every file.

SIM-02A closeout. The package now ships the run's code commit and the final source baseline as separate archives, and the baseline archive carries the run-of-record tables. The package builder unpacked that archive without git and ran the documented commands: the 59 claims checks pass, the criterion-margin supplement regenerates byte for byte, and a full SIM-02A rerun reproduces every run table byte for byte. Fifteen new tests cover the supplementary tools, including a check that the claims tool still fails on the Revision 0 documents. On D06, the six-element circles' -6 dB band ratio is 2.37 at exactly -6.00 dB and 1.73 at -6.0206 dB; every other candidate is stable.

SIM-02B.1 results. Ambient noise follows the published Wenz-type formulas printed by Stojanovic (2007) with assumed shipping and wind values. Spatial coherence, sensor self-noise, signal classes and detector settings are assumed: 2 records are published, 23 assumed and none measured. Gains are reductions in input SNR per element relative to a single hydrophone, at Pd 0.5 and Pfa 1e-3 per window, with calibration, synchronization and host noise not yet modeled. The principal findings:

1. Below 200 Hz in ambient-limited, isotropic noise, no candidate up to 1.07 m beats A0. Gains run from -0.2 to 0.8 dB and 119 of 120 intervals contain zero. Only the 4 m envelopes gain there.
2. Above 200 Hz the arrays gain measurably with beam search: 1.5 to 5.0 dB from 200 Hz to 2 kHz, and 3.5 to 7.4 dB from 2 to 10 kHz in 0.1 s windows.
3. When sensor self-noise or flow-like noise dominates, the arrays gain in every band, 4.3 to 9.0 dB below 200 Hz. The low-band case for an array therefore rests on measured noise coherence, which we do not have.
4. False-alarm control needs the noise level to well under 1 dB. A 1 dB error turns a 0.01 target into 0.075 to 0.332, and into 1.0 for the energy detector, for A0 and arrays alike. A wrong coherence assumption breaks the arrays while leaving A0 untouched.
5. Thresholds are calibrated on independent evaluation sets, and the gains translate into equivalent A0 integration time. With beam search and 1 s windows, P8-C's gain from 200 Hz to 2 kHz equals integrating 2.06 times longer on A0 for tones and 5.36 times for broadband signals.

Defects. The run's own false-alarm self-check used an interval that ignores threshold estimation error and overstated the scatter. An exact test on the same rows shows the thresholds are calibrated, no result changes, and the errata file records it. Before the run, the fail-visibly check rejected a low-band chirp that leaked energy outside its band, and the configuration was corrected. The run took 98 minutes against a 75-minute estimate, so 10 s windows and the 2 to 10 kHz band rely on conservative bounds at Pfa 1e-3; the report flags those cells.

Decisions requested before SIM-02B.2 (transmittal Section 7):
1. Approval to make adaptive noise estimation the first SIM-02B.2 item, with gains reported net of estimation loss.
2. Whether to obtain measured multi-sensor coherence data, or to designate a published source.
3. Confirmation of the ambient inputs: the Coates formulas read as dB re 1 uPa^2/Hz, shipping 0.5 and wind 5 m/s.
4. Synchronization model ranges for shared and distributed clocks, or approval to use assumption-labeled ranges.
5. Go or no-go on the conditional AVS bench-test recommendation.
6. The trial budget at Pfa 1e-3 for 10 s windows and the 2 to 10 kHz band.
7. The SIM-02B.2 beam search definition, including spacing tied to beamwidth and the worst-case directions.

Claude Code produced this increment under your authorization. A qualified acoustic engineer needs to review it before it informs requirements. All 214 verification tests pass at the packaging baseline. "make sim02b1" reproduces the study in about 100 minutes on four cores, and "make sim02b1-claims" rechecks every number quoted in the report findings, the transmittal and this message. The repository is keithatulmo/picket-sim, branch claude/beautiful-darwin-vbeoue.

Please send comments and decisions by [date].

[Your name]
