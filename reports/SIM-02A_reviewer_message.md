Subject: PCK-SIM-001: SIM-01 closure (Rev A) and SIM-02A results for review

[Name],

Your SIM-01 review required five documentation corrections before closure and authorized SIM-02A. Both are complete. The attached package closes SIM-01 and submits the SIM-02A numerical results for your review. SIM-02B has not started and waits on the decisions listed below.

Attachments:
1. SIM-02A_transmittal.pdf (3 pages). Start here. It maps every SIM-01 correction and SIM-02A deliverable to evidence and lists the decisions needed for SIM-02B.
2. SIM-02A_engineering_report.pdf (8 pages). Models, results, traceability to D01 through D06, limitations and SIM-02B recommendations.
3. SIM-01_engineering_report.pdf (Rev A, 15 pages). The corrected SIM-01 report with its revision history.
4. PCK-SIM-001_SIM-02A_Review_Package_20261107T214846Z_c56c0048_31da01b.zip (10.7 MB). The documents above plus figures, tables, the run record and errata, the test log at the code commit, the model documentation, the acoustic vector sensor feasibility assessment and a source snapshot. SHA256SUMS.txt in the package verifies every file.

SIM-01 closure. All five corrections are made without changing any experimental result and are recorded in ADR-0008. The band definition correction has the largest effect. Over the horizon steering set, the band guaranteed for every steering direction has a ratio of 1.77 for the line arrays, 1.28 for the 2x2 square and 1.06 for A4. The corresponding median-direction ratios are 3.54, 1.54 and 1.36. The Rev 0 figures mixed the two conventions.

SIM-02A results. Every sensor, ambient, host and calibration-error level in this increment is an assumed scenario: 72 parameters are assumed, one is a published physical constant, and none is measured. Results are expressed as ratios wherever possible so they remain valid when measured values replace the assumptions. The principal findings:

1. Realized gain over A0 depends mainly on the spatial coherence of the dominant noise. In diffuse, ambient-limited noise every array up to 1.07 m gains at most 0.07 dB between 20 and 200 Hz. When sensor self-noise or short-correlation, flow-like noise dominates, the same arrays approach 10 log10 N at every frequency.
2. At an equal 0.45 m footprint, six- and eight-element circles widen the guaranteed -3 dB band ratio from 1.28 for the square to 2.53 and 3.78. Under a -10 dB criterion they fall to 1.28 and 1.32, because ring arrays carry sidelobes near -8 dB.
3. Calibration and synchronization errors degrade bearing well before they degrade signal level. A 10 us timing error at 15 kHz costs the eight-element compact circle 4.4 dB of signal and produces a wrong-lobe bearing in 65 percent of trials.
4. Line arrays remain unable to resolve left from right under any channel error.
5. Pareto dominance shifts with the provisional tolerances. No candidate is eliminated.

Defects. The transmittal records the defects found and corrected during the work: an assumed sensor scenario that was physically inconsistent, corrected before any run, and two errors in the Monte Carlo bearing statistics that required two additional runs. The earlier runs are retained with errata entries, and every table outside the bearing statistics is identical across all three runs.

Decisions requested before SIM-02B (transmittal Section 6):
1. Published or measured sources for sensor, ambient, host and flow noise. SIM-02B results cannot inform requirements without them.
2. The candidate subset and priorities for SIM-02B.
3. Detection experiment settings: false-alarm probabilities, integration times and signal classes.
4. A synchronization model for distributed modules.
5. Whether to fund acoustic vector sensor data collection.
6. Whether to keep the -1 dB structural-ambiguity level and the four-azimuth Monte Carlo steering set.

Claude Code produced this increment under your authorization. The work needs review by a qualified acoustic engineer before it informs requirements. All 166 verification tests pass at the code commit, and "make sim02a" reproduces the study in about six minutes. The repository is keithatulmo/picket-sim, branch claude/beautiful-darwin-vbeoue.

Please send comments and decisions by [date].

[Your name]
