# SIM-01 conventional-band definitions (derived)

Derived by `tools/sim01_band_definitions.py` from `results/sim01/20261107T203522Z_d64d297c_8043684/tables/thresholds_summary.csv`.
No experimental result was recomputed or altered. Frequencies in Hz; ambiguity level -3 dB.

* **Median band**: from the median f_SL to the median f_amb over the steering set (a typical direction).
* **As reported (Rev 0)**: median f_SL to the earliest f_amb. This mixed convention was used in the
  SIM-01 Rev 0 report and is neither typical nor guaranteed.
* **Guaranteed band**: from the latest f_SL to the earliest f_amb, so that every steering direction in
  the set has a closed mainlobe and no -3 dB ambiguity lobe. Empty when latest f_SL >= earliest f_amb.

| ID | Steering set | Median band | Ratio | As reported (Rev 0) | Ratio | Guaranteed band | Ratio |
|---|---|---|---|---|---|---|---|
| A0 | horizon | none (no pattern) | n/a | none | n/a | none | n/a |
| A1 | horizon | 1,465 to 5,192 | 3.54 | 1,465 to 4,432 | 3.03 | 2,501 to 4,432 | 1.77 |
| A2 | horizon | 733 to 2,596 | 3.54 | 733 to 2,216 | 3.03 | 1,251 to 2,216 | 1.77 |
| A3 | horizon | 1,306 to 2,010 | 1.54 | 1,306 to 1,877 | 1.44 | 1,465 to 1,877 | 1.28 |
| A4 | horizon | 527 to 717 | 1.36 | 527 to 623 | 1.18 | 586 to 623 | 1.06 |
| A0 | depressed30 | none (no pattern) | n/a | none | n/a | none | n/a |
| A1 | depressed30 | 1,551 to 5,500 | 3.55 | 1,551 to 4,751 | 3.06 | 2,501 to 4,751 | 1.90 |
| A2 | depressed30 | 776 to 2,750 | 3.55 | 776 to 2,376 | 3.06 | 1,251 to 2,376 | 1.90 |
| A3 | depressed30 | 1,395 to 2,138 | 1.53 | 1,395 to 2,011 | 1.44 | 1,551 to 2,011 | 1.30 |
| A4 | depressed30 | 526 to 731 | 1.39 | 526 to 608 | 1.16 | empty | n/a |

Steering sets: horizon ring (el = 0 deg) and depressed ring (el = -30 deg), 24 azimuths each at 15 deg spacing. 'Guaranteed' applies only to these sampled directions and to the idealized model.
