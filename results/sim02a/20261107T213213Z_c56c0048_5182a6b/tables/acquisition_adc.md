## Converter noise versus analog noise

| Sensor | Band | Acquirable | Analog minus ADC noise (dB) | Clip level (dB re 1 uPa peak) | Clips first |
|---|---|---|---|---|---|
| S1-ASSUMED-lownoise | B1 | True | +44.4 | 173.0 | adc |
| S1-ASSUMED-lownoise | B2 | True | +35.3 | 173.0 | adc |
| S1-ASSUMED-lownoise | B3 | True | +30.1 | 173.0 | adc |
| S1-ASSUMED-lownoise | B4 | True | +28.9 | 173.0 | adc |
| S2-ASSUMED-mid | B1 | True | +8.8 | 173.0 | adc |
| S2-ASSUMED-mid | B2 | True | +0.5 | 173.0 | adc |
| S2-ASSUMED-mid | B3 | True | -2.7 | 173.0 | adc |
| S2-ASSUMED-mid | B4 | True | -3.2 | 173.0 | adc |
| S3-ASSUMED-lowcost | B1 | True | +38.3 | 165.0 | adc |
| S3-ASSUMED-lowcost | B2 | True | +28.6 | 165.0 | adc |
| S3-ASSUMED-lowcost | B3 | True | +24.4 | 165.0 | adc |
| S3-ASSUMED-lowcost | B4 | False | +23.6 | 165.0 | adc |

* Positive: analog (sensor + preamplifier) noise dominates the ADC.
