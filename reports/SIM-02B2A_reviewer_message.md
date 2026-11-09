Subject: PCK-SIM-001: SIM-02B.2-A adaptive noise estimation results for review

[Name],

Your SIM-02B.1 review made adaptive noise estimation the first SIM-02B.2 activity and set a gate: show false-alarm control with estimated backgrounds and quantify the detection loss against A0 and the oracle before stage B begins. SIM-02B.2-A is complete and ready for that review. Stages B and C have not started.

Attachments:
1. SIM-02B2A_transmittal.pdf (@TP@ pages). Start here. It maps each deliverable and additional requirement to evidence, records the D01 to D07 dispositions, and lists the defects found this cycle and the decisions needed for stage B.
2. SIM-02B2A_engineering_report.pdf (@RP@ pages). Methods, findings, robustness by scenario, verification, limitations and recommendations.
3. @ZIP@ (@ZS@ MB). The documents above plus figures, run tables, summary tables, the supplement and regression tables, the D02 collection plan with its design tables, both source baselines with embedded run-of-record tables, and the test and snapshot-check logs. SHA256SUMS.txt verifies every file.

Scope and assumptions. The noise is stationary circular Gaussian inside every window. Spectra follow the published Wenz-type equations with assumed shipping and wind values; coherence, scenario parameters and estimator settings are assumed (4 published records, 27 assumed, none measured). Thresholds are fixed at design time under the nominal model, and every Pfa is per decision window. Results are input-SNR ratios at one element, and none of them supports an operational conclusion.

Principal findings:
1. False-alarm control with estimated backgrounds holds under the nominal design. Across 1,170 evaluation rows, 4.3 % of the exact-test p-values fall below 0.05 and none falls below 0.001.
2. Estimating the background costs tonal detection 2.10 dB on A0 and 2.51 to 2.63 dB with beam search, and broadband detection 0.11 to 0.47 dB, at Pfa 1e-3 and Pd 0.5 from 200 Hz to 2 kHz. The A0 loss matches the exact CFAR law within 0.13 dB.
3. The array advantage over A0 survives estimation. P8-C beam search keeps 2.83 to 3.05 dB of its 3.42 dB tonal gain. Below 200 Hz no compact candidate beats A0 (-0.26 to 0.72 dB).
4. Time references and frequency references fail in opposite conditions. A 1 dB level step multiplies the tonal false alarms of time references by 3.50 to 11.25, and a persistent target masks itself so that Pd never reaches 0.5. Frequency references hold in both cases but cannot serve broadband detectors.
5. No level estimator repairs a coherence mismatch. Under flow-like coherence, 121 of 132 incoherent rows give no false alarm at Pfa 1e-2, and beam search runs up to 2.93 times its target. The D02 collection plan addresses this input.
6. Pfa 1e-3 on 1 s windows equals 3.6 false alerts per hour for each detector.

Gap. D01 also asked for robust multichannel covariance estimation. This run does not include it, and the transmittal asks whether to close it as a stage A supplement or within stage B.

Defects. The run tables carry a status column that uses a Wilson interval and over-flags small false-alarm counts, the same defect class we recorded for SIM-02B.1. No result value changes. The report uses the exact test, the errata file records the problem, and the code now writes the exact status. The claims checker caught three errors in the draft report before delivery, including the coherence-mismatch maximum, which the draft quoted as 2.40 times target instead of 2.93.

Decisions requested before stage B (transmittal Section 7):
1. Acceptance of the stage A exit requirement within the model scope, and authorization of stage B.
2. Timing of the robust multichannel covariance comparison.
3. The normalizer set for stage B.
4. Treatment of the multichannel threshold law under coherence uncertainty.
5. Funding for array thresholds at Pfa 1e-4, at 2.5 to 3.0 core-hours per array in the 200 Hz to 2 kHz cell, or acceptance of 1e-3 as the array floor.
6. Target-aware reference censoring as a stage B item.
7. In-principle approval of the D02 collection plan, with candidate sites and host access.
8. Approval to request quotes for the loaned-sensor bench evaluation (D05).

Claude Code produced this increment under your authorization, and a qualified acoustic engineer needs to review it before it informs requirements. All @NT@ verification tests pass at the packaging baseline and @NC@ at the run's code commit. "make sim02b2a" reproduces the study in about 2.3 hours on four cores. The package builder unpacked the source snapshot without git and ran "make sim02b2a-claims", which rechecks every number quoted in the report, the transmittal and this message, and "make sim02b2a-repro-check", which recomputes five work units of the run and matches every table row. The repository is keithatulmo/picket-sim, branch claude/beautiful-darwin-vbeoue.

Please send comments and decisions by [date].

[Your name]
