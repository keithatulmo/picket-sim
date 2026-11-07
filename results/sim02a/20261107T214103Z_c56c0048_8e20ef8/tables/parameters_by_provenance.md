## Parameters by provenance (ADR-0010)

| Provenance | Context | Parameter | Value | Unit | Source / rationale |
|---|---|---|---|---|---|
| published | constants | boltzmann_constant | 1.381e-23 | J/K | SI Brochure, 9th edition (BIPM, 2019): exact defining constant k = 1.380649e-23 J/K |
| assumed | S1-ASSUMED-lownoise.hydrophone | sensitivity_db_re_1v_per_upa | -185 | dB re 1 V/uPa | illustrative bare-element (open-circuit) sensitivity, larger element; used to refer element thermal noise |
| assumed | S1-ASSUMED-lownoise.hydrophone | capacitance_f | 1e-08 | F | illustrative piezoceramic capacitance |
| assumed | S1-ASSUMED-lownoise.hydrophone | loss_tangent | 0.01 | 1 | illustrative dielectric loss tangent |
| assumed | S1-ASSUMED-lownoise.hydrophone | temperature_k | 283 | K | 10 degC water temperature assumed |
| assumed | S1-ASSUMED-lownoise.preamp | gain_db | 20 | dB | illustrative preamplifier gain |
| assumed | S1-ASSUMED-lownoise.preamp | voltage_noise_v_per_rthz | 1e-09 | V/sqrt(Hz) | illustrative low-noise input stage |
| assumed | S1-ASSUMED-lownoise.preamp | current_noise_a_per_rthz | 1e-15 | A/sqrt(Hz) | illustrative input current noise |
| assumed | S1-ASSUMED-lownoise.preamp | flicker_corner_hz | 50 | Hz | illustrative 1/f corner |
| assumed | S1-ASSUMED-lownoise.preamp | max_output_v_peak | 5 | V | illustrative preamplifier swing |
| assumed | S1-ASSUMED-lownoise.adc | bits | 24 | bit | illustrative 24-bit converter (ideal quantization; no ENOB loss modeled) |
| assumed | S1-ASSUMED-lownoise.adc | full_scale_v_peak | 2.5 | V | illustrative converter full scale |
| assumed | S1-ASSUMED-lownoise.adc | sample_rate_hz | 9.6e+04 | Hz | illustrative sample rate covering B4 |
| assumed | S1-ASSUMED-lownoise.bandwidth | bandwidth_low_hz | 10 | Hz | declared usable band of the scenario |
| assumed | S1-ASSUMED-lownoise.bandwidth | bandwidth_high_hz | 4e+04 | Hz | declared usable band of the scenario |
| assumed | S2-ASSUMED-mid.hydrophone | sensitivity_db_re_1v_per_upa | -195 | dB re 1 V/uPa | illustrative bare-element (open-circuit) sensitivity, mid-size element |
| assumed | S2-ASSUMED-mid.hydrophone | capacitance_f | 5e-09 | F | illustrative piezoceramic capacitance |
| assumed | S2-ASSUMED-mid.hydrophone | loss_tangent | 0.015 | 1 | illustrative dielectric loss tangent |
| assumed | S2-ASSUMED-mid.hydrophone | temperature_k | 283 | K | 10 degC water temperature assumed |
| assumed | S2-ASSUMED-mid.preamp | gain_db | 30 | dB | illustrative preamplifier gain |
| assumed | S2-ASSUMED-mid.preamp | voltage_noise_v_per_rthz | 3e-09 | V/sqrt(Hz) | illustrative input stage |
| assumed | S2-ASSUMED-mid.preamp | current_noise_a_per_rthz | 5e-15 | A/sqrt(Hz) | illustrative input current noise |
| assumed | S2-ASSUMED-mid.preamp | flicker_corner_hz | 100 | Hz | illustrative 1/f corner |
| assumed | S2-ASSUMED-mid.preamp | max_output_v_peak | 5 | V | illustrative preamplifier swing |
| assumed | S2-ASSUMED-mid.adc | bits | 16 | bit | illustrative 16-bit converter (ideal quantization) |
| assumed | S2-ASSUMED-mid.adc | full_scale_v_peak | 2.5 | V | illustrative converter full scale |
| assumed | S2-ASSUMED-mid.adc | sample_rate_hz | 4.8e+04 | Hz | illustrative sample rate |
| assumed | S2-ASSUMED-mid.bandwidth | bandwidth_low_hz | 10 | Hz | declared usable band of the scenario |
| assumed | S2-ASSUMED-mid.bandwidth | bandwidth_high_hz | 2e+04 | Hz | declared usable band of the scenario |
| assumed | S3-ASSUMED-lowcost.hydrophone | sensitivity_db_re_1v_per_upa | -205 | dB re 1 V/uPa | illustrative bare-element (open-circuit) sensitivity, small element |
| assumed | S3-ASSUMED-lowcost.hydrophone | capacitance_f | 1e-09 | F | illustrative small-element capacitance |
| assumed | S3-ASSUMED-lowcost.hydrophone | loss_tangent | 0.02 | 1 | illustrative dielectric loss tangent |
| assumed | S3-ASSUMED-lowcost.hydrophone | temperature_k | 283 | K | 10 degC water temperature assumed |
| assumed | S3-ASSUMED-lowcost.preamp | gain_db | 40 | dB | illustrative preamplifier gain |
| assumed | S3-ASSUMED-lowcost.preamp | voltage_noise_v_per_rthz | 1e-08 | V/sqrt(Hz) | illustrative general-purpose input stage |
| assumed | S3-ASSUMED-lowcost.preamp | current_noise_a_per_rthz | 1e-14 | A/sqrt(Hz) | illustrative input current noise |
| assumed | S3-ASSUMED-lowcost.preamp | flicker_corner_hz | 1000 | Hz | illustrative 1/f corner |
| assumed | S3-ASSUMED-lowcost.preamp | max_output_v_peak | 5 | V | illustrative preamplifier swing |
| assumed | S3-ASSUMED-lowcost.adc | bits | 16 | bit | illustrative 16-bit converter (ideal quantization) |
| assumed | S3-ASSUMED-lowcost.adc | full_scale_v_peak | 1 | V | illustrative converter full scale |
| assumed | S3-ASSUMED-lowcost.adc | sample_rate_hz | 3.2e+04 | Hz | illustrative sample rate (does not cover B4) |
| assumed | S3-ASSUMED-lowcost.bandwidth | bandwidth_low_hz | 20 | Hz | declared usable band of the scenario |
| assumed | S3-ASSUMED-lowcost.bandwidth | bandwidth_high_hz | 1.2e+04 | Hz | declared usable band of the scenario |
| assumed | AMB-ASSUMED-quiet | level_db_re_1upa2_per_hz | 45 | dB re 1 uPa^2/Hz | illustrative low ambient level at 1 kHz |
| assumed | AMB-ASSUMED-quiet | reference_frequency_hz | 1000 | Hz | reference frequency of the power law |
| assumed | AMB-ASSUMED-quiet | slope_db_per_decade | -17 | dB/decade | illustrative spectral slope, not fitted to data |
| assumed | AMB-ASSUMED-moderate | level_db_re_1upa2_per_hz | 60 | dB re 1 uPa^2/Hz | illustrative moderate ambient level at 1 kHz |
| assumed | AMB-ASSUMED-moderate | reference_frequency_hz | 1000 | Hz | reference frequency of the power law |
| assumed | AMB-ASSUMED-moderate | slope_db_per_decade | -17 | dB/decade | illustrative spectral slope, not fitted to data |
| assumed | AMB-ASSUMED-loud | level_db_re_1upa2_per_hz | 75 | dB re 1 uPa^2/Hz | illustrative high ambient level at 1 kHz |
| assumed | AMB-ASSUMED-loud | reference_frequency_hz | 1000 | Hz | reference frequency of the power law |
| assumed | AMB-ASSUMED-loud | slope_db_per_decade | -17 | dB/decade | illustrative spectral slope, not fitted to data |
| assumed | broadband | crest_factor_db | 12.04 | dB | 4-sigma peak criterion for Gaussian noise (P(|x|>4 sigma) = 6.3e-5) |
| assumed | transient | crest_factor_db | 25 | dB | illustrative impulsive crest factor for headroom sizing |
| assumed | noise_field_parameters | noise_field_parameters | n/a | - | Field shapes and the 0.1 m correlation length are assumed for sensitivity analysis; not fitted to data. |
| assumed | host_scenarios | host_scenarios | n/a | - | Generic host-noise source placements and levels for sensitivity analysis; no vessel geometry implied. |
| assumed | E1-ASSUMED-tight | sigma_gain_db | 0.25 | dB | illustrative tight calibration |
| assumed | E1-ASSUMED-tight | sigma_phase_deg | 1 | deg | illustrative tight calibration |
| assumed | E1-ASSUMED-tight | sigma_position_m | 0.001 | m | illustrative tight position knowledge |
| assumed | E1-ASSUMED-tight | sigma_timing_s | 1e-07 | s | illustrative tight synchronization |
| assumed | E2-ASSUMED-moderate | sigma_gain_db | 0.5 | dB | illustrative moderate calibration |
| assumed | E2-ASSUMED-moderate | sigma_phase_deg | 3 | deg | illustrative moderate calibration |
| assumed | E2-ASSUMED-moderate | sigma_position_m | 0.003 | m | illustrative moderate position knowledge |
| assumed | E2-ASSUMED-moderate | sigma_timing_s | 1e-06 | s | illustrative moderate synchronization |
| assumed | E3-ASSUMED-loose | sigma_gain_db | 1 | dB | illustrative loose calibration |
| assumed | E3-ASSUMED-loose | sigma_phase_deg | 10 | deg | illustrative loose calibration |
| assumed | E3-ASSUMED-loose | sigma_position_m | 0.01 | m | illustrative loose position knowledge |
| assumed | E3-ASSUMED-loose | sigma_timing_s | 1e-05 | s | illustrative loose synchronization |
| assumed | E4-ASSUMED-unsynchronized | sigma_gain_db | 1 | dB | illustrative distributed modules without tight calibration |
| assumed | E4-ASSUMED-unsynchronized | sigma_phase_deg | 10 | deg | illustrative distributed modules |
| assumed | E4-ASSUMED-unsynchronized | sigma_position_m | 0.03 | m | illustrative distributed-installation position knowledge |
| assumed | E4-ASSUMED-unsynchronized | sigma_timing_s | 0.0001 | s | illustrative unsynchronized module clocks |
| assumed | error_sweeps | error_sweeps | n/a | - | Sweep levels chosen to span tight to loose; not requirements. |

* No measured values exist in SIM-02A.
* Block entries (value n/a) carry provenance for a whole block.
