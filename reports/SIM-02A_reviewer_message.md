Subject: PCK-SIM-001: SIM-01 closure (Rev A) and SIM-02A results (Rev A) for review

[Name],

Your SIM-01 review required five documentation corrections before closure and authorized SIM-02A. Both are complete. The attached package closes SIM-01 and submits the SIM-02A numerical results for your review. SIM-02B has not started and waits on the decisions listed below.

Attachments:
1. SIM-02A_transmittal.pdf (Rev A, {TR_PAGES} pages). Start here. It maps every SIM-01 correction and SIM-02A deliverable to evidence, records the defects found and corrected, and lists the decisions needed for SIM-02B.
2. SIM-02A_engineering_report.pdf (Rev A, {REP_PAGES} pages). Models, results, traceability to D01 through D06, limitations and SIM-02B recommendations.
3. SIM-01_engineering_report.pdf (Rev A, 15 pages). The corrected SIM-01 report with its revision history.
4. {ZIP_NAME} ({ZIP_MB} MB). The documents above plus figures, tables, the run record and errata, the criterion-margin supplement, the claims check, the test log at the code commit, the model documentation, the acoustic vector sensor feasibility assessment and a source snapshot. SHA256SUMS.txt in the package verifies every file.

SIM-01 closure. All five corrections are made without changing any experimental result and are recorded in ADR-0008. The band definition correction has the largest effect. Over the horizon steering set, the band guaranteed for every steering direction has a ratio of 1.77 for the line arrays, 1.28 for the 2x2 square and 1.06 for A4. The corresponding median-direction ratios are 3.54, 1.54 and 1.36. The Rev 0 figures mixed the two conventions.

SIM-02A results. Every sensor, ambient, host and calibration-error level in this increment is an assumed scenario: 72 parameters are assumed, one is a published physical constant, and none is measured. Results are expressed as ratios wherever possible so they remain valid when measured values replace the assumptions. The principal findings:

1. Realized gain over A0 depends mainly on the spatial coherence of the dominant noise. In diffuse, ambient-limited noise, arrays up to 1.07 m gain at most 0.07 dB as a 20 to 200 Hz band median and at most 0.73 dB at 200 Hz. With sensor self-noise 20 dB above ambient, the same arrays come within 0.29 dB of 10 log10 N in every band. In short-correlation, flow-like noise they come within 0.5 dB, except A1, P6-C and P8-C, which fall 0.9 to 1.7 dB short below 2 kHz.
2. At an equal 0.45 m footprint, six- and eight-element circles widen the guaranteed -3 dB band ratio from 1.28 for the square to 2.53 and 3.78. Under a -10 dB criterion the ratios fall to 1.28 and 1.32, because the circles' sidelobe plateaus sit at {P6_PSL} and {P8_PSL} dB. The six-element circle's -6 dB result is knife-edge: its plateau lies 0.02 dB below the criterion, and its guaranteed ratio drops from 2.37 to {P6_61} at -6.1 dB.
3. Calibration and synchronization errors degrade bearing well before they degrade signal level. Under the loose error scenario E3 (1 dB gain, 10 deg phase, 1 cm position, 10 us timing) at 15 kHz, the eight-element compact circle loses 4.3 to 4.4 dB of signal and locks onto a wrong lobe in 65 to 81 percent of trials across four target azimuths. Timing supplies about two thirds of that phase error.
4. Line arrays cannot resolve left from right under any channel error, except at exact endfire where target and mirror coincide.
5. Pareto dominance shifts with the provisional tolerances. No candidate is eliminated.

Defects. The transmittal records the defects found and corrected during the work. Before any run, one assumed sensor scenario proved physically inconsistent and was corrected. Two errors in the Monte Carlo bearing statistics required two additional runs; the earlier runs are retained with errata entries, and every table outside the bearing statistics is identical across all three runs. Before this package went out, a programmatic check of every quoted number against the run tables found four prose errors in the first issue of the report and transmittal. The most significant put both circles' sidelobes near -8 dB, which hid the knife-edge in finding 2; another quoted a low-band median as a maximum. Revision A corrects all four. No run, table or figure changed, and the first issue is retained with an errata entry.

Decisions requested before SIM-02B (transmittal Section 6):
1. Published or measured sources for sensor, ambient, host and flow noise. SIM-02B results cannot inform requirements without them.
2. The candidate subset and priorities for SIM-02B.
3. Detection experiment settings: false-alarm probabilities, integration times and signal classes.
4. A synchronization model for distributed modules.
5. Whether to fund acoustic vector sensor data collection.
6. Criterion conventions: whether to keep the -1 dB structural-ambiguity level and the four-azimuth Monte Carlo steering set, and whether the -6 dB criterion means -6.00 dB in power or half amplitude (-6.02 dB). P6-C's -6 dB band depends on that choice.

Claude Code produced this increment under your authorization. The work needs review by a qualified acoustic engineer before it informs requirements. All 166 verification tests pass at the code commit, "make sim02a" reproduces the study in about six minutes, and "make sim02a-claims" rechecks every number quoted in the report findings, the transmittal and this message. The repository is keithatulmo/picket-sim, branch claude/beautiful-darwin-vbeoue.

Please send comments and decisions by [date].

[Your name]
