# SIM-02B.2-A ORACLE regression against SIM-02B.1

SIM-02B.2-A run `20261109T003718Z_27abcd69_73fbe35`; SIM-02B.1 run `20261108T125126Z_1c70e065_8dbe019`. STAT, ORACLE normalizer, all cells, candidates, modes, classes, Pfa and Pd present in both runs.

Estimate against estimate: 348 rows; consistent (within the combined 95 % half-width): 343; marginal (within 1.5 x): 5; inconsistent: 0. Censored in either run: 0.

Against SIM-02B.1 union-bound thresholds: 48 rows; bound holds: 48; bound violated: 0. The bound's excess SNR requirement (SIM-02B.1 minus SIM-02B.2-A) ranges from -0.19 to 3.53 dB, median 0.65 dB.

Absolute difference: median 0.11 dB, maximum 0.61 dB.

Largest difference relative to its uncertainty: A0 single tone C3 Pfa 0.001 Pd 0.5: +0.47 dB against a combined half-width of 0.36 dB.

With about 95 % intervals, roughly 5 % of rows are expected outside 1.0 x by chance (the intervals are approximate and the comparisons are not independent: rows share trials across Pd targets and Pfa).

| Cell | Candidate | Mode | Class | Pfa | Pd | B.2-A (dB) | B.1 (dB) | Difference (dB) | Half-width (dB) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | A0 | single | broadband | 0.0001 | 0.5 | -11.15 | -11.18 | +0.03 | 0.20 | consistent |
| C1 | A0 | single | broadband | 0.0001 | 0.9 | -9.19 | -9.21 | +0.02 | 0.39 | consistent |
| C1 | A0 | single | broadband | 0.001 | 0.5 | -11.84 | -12.04 | +0.20 | 0.30 | consistent |
| C1 | A0 | single | broadband | 0.001 | 0.9 | -10.18 | -10.21 | +0.03 | 0.16 | consistent |
| C1 | A0 | single | broadband | 0.01 | 0.5 | -13.22 | -13.29 | +0.07 | 0.32 | consistent |
| C1 | A0 | single | broadband | 0.01 | 0.9 | -10.78 | -10.76 | -0.02 | 0.26 | consistent |
| C1 | A0 | single | chirp | 0.0001 | 0.5 | 12.33 | 12.30 | +0.03 | 0.31 | bound holds |
| C1 | A0 | single | chirp | 0.0001 | 0.9 | 14.33 | 14.40 | -0.06 | 0.61 | bound holds |
| C1 | A0 | single | chirp | 0.001 | 0.5 | 11.64 | 11.51 | +0.13 | 0.64 | consistent |
| C1 | A0 | single | chirp | 0.001 | 0.9 | 13.56 | 13.59 | -0.03 | 0.55 | consistent |
| C1 | A0 | single | chirp | 0.01 | 0.5 | 10.76 | 10.59 | +0.17 | 0.38 | consistent |
| C1 | A0 | single | chirp | 0.01 | 0.9 | 13.17 | 13.12 | +0.05 | 0.33 | consistent |
| C1 | A0 | single | harmonic | 0.0001 | 0.5 | 8.29 | 8.46 | -0.17 | 0.34 | bound holds |
| C1 | A0 | single | harmonic | 0.0001 | 0.9 | 10.63 | 10.71 | -0.09 | 0.31 | bound holds |
| C1 | A0 | single | harmonic | 0.001 | 0.5 | 7.72 | 8.02 | -0.31 | 0.43 | consistent |
| C1 | A0 | single | harmonic | 0.001 | 0.9 | 10.08 | 10.23 | -0.14 | 0.69 | consistent |
| C1 | A0 | single | harmonic | 0.01 | 0.5 | 6.91 | 6.95 | -0.04 | 0.44 | consistent |
| C1 | A0 | single | harmonic | 0.01 | 0.9 | 9.13 | 9.16 | -0.03 | 0.24 | consistent |
| C1 | A0 | single | tone | 0.0001 | 0.5 | 13.30 | 13.24 | +0.06 | 0.31 | consistent |
| C1 | A0 | single | tone | 0.0001 | 0.9 | 15.86 | 15.88 | -0.01 | 0.37 | consistent |
| C1 | A0 | single | tone | 0.001 | 0.5 | 12.53 | 12.49 | +0.04 | 0.40 | consistent |
| C1 | A0 | single | tone | 0.001 | 0.9 | 15.24 | 15.38 | -0.14 | 0.56 | consistent |
| C1 | A0 | single | tone | 0.01 | 0.5 | 11.65 | 11.60 | +0.05 | 0.34 | consistent |
| C1 | A0 | single | tone | 0.01 | 0.9 | 14.32 | 14.38 | -0.06 | 0.35 | consistent |
| C1 | A1 | beam_search | broadband | 0.001 | 0.5 | -14.46 | -14.51 | +0.06 | 0.63 | consistent |
| C1 | A1 | beam_search | broadband | 0.001 | 0.9 | -12.33 | -12.27 | -0.06 | 0.43 | consistent |
| C1 | A1 | beam_search | broadband | 0.01 | 0.5 | -15.47 | -15.52 | +0.05 | 0.38 | consistent |
| C1 | A1 | beam_search | broadband | 0.01 | 0.9 | -12.96 | -12.96 | +0.00 | 0.46 | consistent |
| C1 | A1 | beam_search | chirp | 0.001 | 0.5 | 9.45 | 9.41 | +0.04 | 0.54 | consistent |
| C1 | A1 | beam_search | chirp | 0.001 | 0.9 | 11.65 | 11.69 | -0.04 | 0.57 | consistent |
| C1 | A1 | beam_search | chirp | 0.01 | 0.5 | 8.86 | 8.66 | +0.20 | 0.37 | consistent |
| C1 | A1 | beam_search | chirp | 0.01 | 0.9 | 11.33 | 11.32 | +0.01 | 0.33 | consistent |
| C1 | A1 | beam_search | harmonic | 0.001 | 0.5 | 6.17 | 6.17 | +0.01 | 0.52 | consistent |
| C1 | A1 | beam_search | harmonic | 0.001 | 0.9 | 8.53 | 8.66 | -0.12 | 0.56 | consistent |
| C1 | A1 | beam_search | harmonic | 0.01 | 0.5 | 5.45 | 5.43 | +0.02 | 0.43 | consistent |
| C1 | A1 | beam_search | harmonic | 0.01 | 0.9 | 7.48 | 7.89 | -0.42 | 0.62 | consistent |
| C1 | A1 | beam_search | tone | 0.0001 | 0.5 | 10.91 | 11.75 | -0.83 | 0.44 | bound holds |
| C1 | A1 | beam_search | tone | 0.0001 | 0.9 | 14.11 | 14.78 | -0.67 | 0.53 | bound holds |
| C1 | A1 | beam_search | tone | 0.001 | 0.5 | 10.18 | 10.78 | -0.59 | 0.64 | consistent |
| C1 | A1 | beam_search | tone | 0.001 | 0.9 | 13.52 | 13.90 | -0.38 | 0.58 | consistent |
| C1 | A1 | beam_search | tone | 0.01 | 0.5 | 9.38 | 9.69 | -0.30 | 0.52 | consistent |
| C1 | A1 | beam_search | tone | 0.01 | 0.9 | 12.56 | 13.10 | -0.53 | 0.71 | consistent |
| C1 | A1 | incoherent | broadband | 0.001 | 0.5 | -12.93 | -12.94 | +0.01 | 0.48 | consistent |
| C1 | A1 | incoherent | broadband | 0.001 | 0.9 | -10.74 | -10.77 | +0.03 | 0.36 | consistent |
| C1 | A1 | incoherent | broadband | 0.01 | 0.5 | -13.94 | -13.89 | -0.05 | 0.52 | consistent |
| C1 | A1 | incoherent | broadband | 0.01 | 0.9 | -11.73 | -12.05 | +0.32 | 0.63 | consistent |
| C1 | A1 | incoherent | chirp | 0.001 | 0.5 | 10.74 | 10.71 | +0.02 | 0.39 | consistent |
| C1 | A1 | incoherent | chirp | 0.001 | 0.9 | 12.94 | 12.94 | +0.01 | 0.46 | consistent |
| C1 | A1 | incoherent | chirp | 0.01 | 0.5 | 10.03 | 10.01 | +0.02 | 0.39 | consistent |
| C1 | A1 | incoherent | chirp | 0.01 | 0.9 | 12.01 | 12.16 | -0.15 | 0.61 | consistent |
| C1 | A1 | incoherent | harmonic | 0.001 | 0.5 | 7.13 | 7.45 | -0.32 | 0.65 | consistent |
| C1 | A1 | incoherent | harmonic | 0.001 | 0.9 | 9.14 | 9.24 | -0.10 | 0.56 | consistent |
| C1 | A1 | incoherent | harmonic | 0.01 | 0.5 | 6.36 | 6.39 | -0.03 | 0.36 | consistent |
| C1 | A1 | incoherent | harmonic | 0.01 | 0.9 | 8.75 | 8.83 | -0.08 | 0.27 | consistent |
| C1 | A1 | incoherent | tone | 0.0001 | 0.5 | 12.36 | 14.63 | -2.28 | 0.34 | bound holds |
| C1 | A1 | incoherent | tone | 0.0001 | 0.9 | 14.90 | 16.54 | -1.64 | 0.52 | bound holds |
| C1 | A1 | incoherent | tone | 0.001 | 0.5 | 11.63 | 11.82 | -0.19 | 0.66 | consistent |
| C1 | A1 | incoherent | tone | 0.001 | 0.9 | 14.26 | 14.25 | +0.01 | 0.44 | consistent |
| C1 | A1 | incoherent | tone | 0.01 | 0.5 | 10.69 | 11.23 | -0.55 | 0.43 | marginal |
| C1 | A1 | incoherent | tone | 0.01 | 0.9 | 13.62 | 13.78 | -0.16 | 0.58 | consistent |
| C1 | A4 | beam_search | broadband | 0.001 | 0.5 | -16.60 | -16.80 | +0.21 | 0.67 | consistent |
| C1 | A4 | beam_search | broadband | 0.001 | 0.9 | -14.58 | -14.66 | +0.08 | 0.39 | consistent |
| C1 | A4 | beam_search | broadband | 0.01 | 0.5 | -17.56 | -17.54 | -0.02 | 0.33 | consistent |
| C1 | A4 | beam_search | broadband | 0.01 | 0.9 | -15.39 | -15.51 | +0.13 | 0.61 | consistent |
| C1 | A4 | beam_search | chirp | 0.001 | 0.5 | 6.70 | 6.57 | +0.13 | 0.49 | consistent |
| C1 | A4 | beam_search | chirp | 0.001 | 0.9 | 9.02 | 8.81 | +0.21 | 0.53 | consistent |
| C1 | A4 | beam_search | chirp | 0.01 | 0.5 | 6.04 | 5.76 | +0.28 | 0.41 | consistent |
| C1 | A4 | beam_search | chirp | 0.01 | 0.9 | 8.34 | 7.76 | +0.58 | 0.54 | marginal |
| C1 | A4 | beam_search | harmonic | 0.001 | 0.5 | 3.52 | 3.56 | -0.04 | 0.55 | consistent |
| C1 | A4 | beam_search | harmonic | 0.001 | 0.9 | 5.57 | 5.40 | +0.17 | 0.72 | consistent |
| C1 | A4 | beam_search | harmonic | 0.01 | 0.5 | 2.83 | 2.86 | -0.03 | 0.40 | consistent |
| C1 | A4 | beam_search | harmonic | 0.01 | 0.9 | 5.14 | 5.19 | -0.05 | 0.23 | consistent |
| C1 | A4 | beam_search | tone | 0.0001 | 0.5 | 8.42 | 8.47 | -0.05 | 0.39 | bound holds |
| C1 | A4 | beam_search | tone | 0.0001 | 0.9 | 11.50 | 11.92 | -0.42 | 0.72 | bound holds |
| C1 | A4 | beam_search | tone | 0.001 | 0.5 | 7.64 | 7.84 | -0.20 | 0.60 | consistent |
| C1 | A4 | beam_search | tone | 0.001 | 0.9 | 10.92 | 11.17 | -0.25 | 1.08 | consistent |
| C1 | A4 | beam_search | tone | 0.01 | 0.5 | 6.95 | 7.20 | -0.24 | 0.42 | consistent |
| C1 | A4 | beam_search | tone | 0.01 | 0.9 | 10.48 | 10.55 | -0.07 | 0.82 | consistent |
| C1 | A4 | incoherent | broadband | 0.001 | 0.5 | -14.62 | -14.48 | -0.14 | 0.56 | consistent |
| C1 | A4 | incoherent | broadband | 0.001 | 0.9 | -12.50 | -12.44 | -0.05 | 0.25 | consistent |
| C1 | A4 | incoherent | broadband | 0.01 | 0.5 | -15.74 | -15.68 | -0.06 | 0.49 | consistent |
| C1 | A4 | incoherent | broadband | 0.01 | 0.9 | -13.30 | -13.13 | -0.17 | 0.52 | consistent |
| C1 | A4 | incoherent | chirp | 0.001 | 0.5 | 7.38 | 7.42 | -0.04 | 0.52 | consistent |
| C1 | A4 | incoherent | chirp | 0.001 | 0.9 | 9.49 | 9.38 | +0.11 | 0.25 | consistent |
| C1 | A4 | incoherent | chirp | 0.01 | 0.5 | 6.83 | 6.69 | +0.15 | 0.33 | consistent |
| C1 | A4 | incoherent | chirp | 0.01 | 0.9 | 9.17 | 8.99 | +0.18 | 0.29 | consistent |
| C1 | A4 | incoherent | harmonic | 0.001 | 0.5 | 5.83 | 5.86 | -0.02 | 0.49 | consistent |
| C1 | A4 | incoherent | harmonic | 0.001 | 0.9 | 7.40 | 7.56 | -0.17 | 0.74 | consistent |
| C1 | A4 | incoherent | harmonic | 0.01 | 0.5 | 4.90 | 5.00 | -0.10 | 0.39 | consistent |
| C1 | A4 | incoherent | harmonic | 0.01 | 0.9 | 7.01 | 7.14 | -0.13 | 0.21 | consistent |
| C1 | A4 | incoherent | tone | 0.0001 | 0.5 | 11.68 | 13.82 | -2.14 | 0.24 | bound holds |
| C1 | A4 | incoherent | tone | 0.0001 | 0.9 | 14.03 | 15.98 | -1.95 | 0.26 | bound holds |
| C1 | A4 | incoherent | tone | 0.001 | 0.5 | 10.93 | 10.98 | -0.05 | 0.45 | consistent |
| C1 | A4 | incoherent | tone | 0.001 | 0.9 | 13.34 | 12.99 | +0.35 | 0.68 | consistent |
| C1 | A4 | incoherent | tone | 0.01 | 0.5 | 9.83 | 9.92 | -0.09 | 0.36 | consistent |
| C1 | A4 | incoherent | tone | 0.01 | 0.9 | 12.27 | 12.34 | -0.07 | 0.35 | consistent |
| C1 | P8-C | beam_search | broadband | 0.001 | 0.5 | -16.14 | -15.62 | -0.52 | 0.63 | consistent |
| C1 | P8-C | beam_search | broadband | 0.001 | 0.9 | -14.34 | -14.21 | -0.14 | 0.51 | consistent |
| C1 | P8-C | beam_search | broadband | 0.01 | 0.5 | -17.03 | -17.04 | +0.01 | 0.35 | consistent |
| C1 | P8-C | beam_search | broadband | 0.01 | 0.9 | -14.69 | -14.75 | +0.06 | 0.27 | consistent |
| C1 | P8-C | beam_search | chirp | 0.001 | 0.5 | 8.57 | 8.31 | +0.26 | 0.45 | consistent |
| C1 | P8-C | beam_search | chirp | 0.001 | 0.9 | 10.94 | 10.59 | +0.35 | 0.59 | consistent |
| C1 | P8-C | beam_search | chirp | 0.01 | 0.5 | 7.73 | 7.67 | +0.06 | 0.46 | consistent |
| C1 | P8-C | beam_search | chirp | 0.01 | 0.9 | 9.94 | 9.76 | +0.17 | 0.52 | consistent |
| C1 | P8-C | beam_search | harmonic | 0.001 | 0.5 | 5.16 | 5.31 | -0.15 | 0.51 | consistent |
| C1 | P8-C | beam_search | harmonic | 0.001 | 0.9 | 7.64 | 7.88 | -0.24 | 0.76 | consistent |
| C1 | P8-C | beam_search | harmonic | 0.01 | 0.5 | 4.40 | 4.65 | -0.25 | 0.41 | consistent |
| C1 | P8-C | beam_search | harmonic | 0.01 | 0.9 | 7.18 | 7.35 | -0.17 | 0.47 | consistent |
| C1 | P8-C | beam_search | tone | 0.0001 | 0.5 | 9.80 | 10.54 | -0.74 | 0.59 | bound holds |
| C1 | P8-C | beam_search | tone | 0.0001 | 0.9 | 13.73 | 14.22 | -0.49 | 0.50 | bound holds |
| C1 | P8-C | beam_search | tone | 0.001 | 0.5 | 9.11 | 9.61 | -0.49 | 0.86 | consistent |
| C1 | P8-C | beam_search | tone | 0.001 | 0.9 | 12.87 | 13.48 | -0.61 | 0.80 | consistent |
| C1 | P8-C | beam_search | tone | 0.01 | 0.5 | 8.41 | 8.79 | -0.38 | 0.68 | consistent |
| C1 | P8-C | beam_search | tone | 0.01 | 0.9 | 12.34 | 12.77 | -0.43 | 0.65 | consistent |
| C1 | P8-C | incoherent | broadband | 0.001 | 0.5 | -13.29 | -13.17 | -0.12 | 0.52 | consistent |
| C1 | P8-C | incoherent | broadband | 0.001 | 0.9 | -11.22 | -11.02 | -0.21 | 0.62 | consistent |
| C1 | P8-C | incoherent | broadband | 0.01 | 0.5 | -14.62 | -14.48 | -0.14 | 0.53 | consistent |
| C1 | P8-C | incoherent | broadband | 0.01 | 0.9 | -12.38 | -12.31 | -0.08 | 0.23 | consistent |
| C1 | P8-C | incoherent | chirp | 0.001 | 0.5 | 10.30 | 10.09 | +0.22 | 0.40 | consistent |
| C1 | P8-C | incoherent | chirp | 0.001 | 0.9 | 12.09 | 11.67 | +0.42 | 0.62 | consistent |
| C1 | P8-C | incoherent | chirp | 0.01 | 0.5 | 9.31 | 9.17 | +0.14 | 0.34 | consistent |
| C1 | P8-C | incoherent | chirp | 0.01 | 0.9 | 11.36 | 11.35 | +0.01 | 0.21 | consistent |
| C1 | P8-C | incoherent | harmonic | 0.001 | 0.5 | 6.91 | 7.19 | -0.28 | 0.50 | consistent |
| C1 | P8-C | incoherent | harmonic | 0.001 | 0.9 | 9.09 | 9.12 | -0.03 | 0.26 | consistent |
| C1 | P8-C | incoherent | harmonic | 0.01 | 0.5 | 6.12 | 6.37 | -0.25 | 0.37 | consistent |
| C1 | P8-C | incoherent | harmonic | 0.01 | 0.9 | 8.44 | 8.76 | -0.32 | 0.39 | consistent |
| C1 | P8-C | incoherent | tone | 0.0001 | 0.5 | 12.36 | 15.85 | -3.49 | 0.27 | bound holds |
| C1 | P8-C | incoherent | tone | 0.0001 | 0.9 | 14.53 | 18.06 | -3.53 | 0.36 | bound holds |
| C1 | P8-C | incoherent | tone | 0.001 | 0.5 | 11.68 | 11.79 | -0.11 | 0.53 | consistent |
| C1 | P8-C | incoherent | tone | 0.001 | 0.9 | 14.11 | 14.10 | +0.01 | 0.40 | consistent |
| C1 | P8-C | incoherent | tone | 0.01 | 0.5 | 10.79 | 11.02 | -0.23 | 0.40 | consistent |
| C1 | P8-C | incoherent | tone | 0.01 | 0.9 | 13.20 | 13.38 | -0.17 | 0.64 | consistent |
| C2 | A0 | single | broadband | 0.0001 | 0.5 | -7.72 | -7.63 | -0.09 | 0.22 | consistent |
| C2 | A0 | single | broadband | 0.0001 | 0.9 | -5.62 | -5.47 | -0.15 | 0.33 | consistent |
| C2 | A0 | single | broadband | 0.001 | 0.5 | -8.53 | -8.52 | -0.01 | 0.34 | consistent |
| C2 | A0 | single | broadband | 0.001 | 0.9 | -6.70 | -6.67 | -0.03 | 0.21 | consistent |
| C2 | A0 | single | broadband | 0.01 | 0.5 | -9.84 | -9.85 | +0.00 | 0.35 | consistent |
| C2 | A0 | single | broadband | 0.01 | 0.9 | -7.29 | -7.22 | -0.08 | 0.27 | consistent |
| C2 | A0 | single | chirp | 0.0001 | 0.5 | 11.36 | 11.73 | -0.37 | 0.38 | bound holds |
| C2 | A0 | single | chirp | 0.0001 | 0.9 | 13.30 | 13.97 | -0.67 | 0.66 | bound holds |
| C2 | A0 | single | chirp | 0.001 | 0.5 | 10.48 | 10.62 | -0.15 | 0.53 | consistent |
| C2 | A0 | single | chirp | 0.001 | 0.9 | 12.74 | 12.90 | -0.16 | 0.35 | consistent |
| C2 | A0 | single | chirp | 0.01 | 0.5 | 9.48 | 9.76 | -0.27 | 0.40 | consistent |
| C2 | A0 | single | chirp | 0.01 | 0.9 | 12.13 | 12.42 | -0.29 | 0.42 | consistent |
| C2 | A0 | single | harmonic | 0.0001 | 0.5 | 7.80 | 7.76 | +0.04 | 0.31 | bound holds |
| C2 | A0 | single | harmonic | 0.0001 | 0.9 | 10.19 | 10.14 | +0.05 | 0.26 | bound holds |
| C2 | A0 | single | harmonic | 0.001 | 0.5 | 7.14 | 6.97 | +0.16 | 0.52 | consistent |
| C2 | A0 | single | harmonic | 0.001 | 0.9 | 9.61 | 9.64 | -0.03 | 0.48 | consistent |
| C2 | A0 | single | harmonic | 0.01 | 0.5 | 6.02 | 5.92 | +0.10 | 0.47 | consistent |
| C2 | A0 | single | harmonic | 0.01 | 0.9 | 8.56 | 8.57 | -0.01 | 0.46 | consistent |
| C2 | A0 | single | tone | 0.0001 | 0.5 | 12.53 | 12.51 | +0.02 | 0.34 | consistent |
| C2 | A0 | single | tone | 0.0001 | 0.9 | 15.15 | 15.17 | -0.02 | 0.31 | consistent |
| C2 | A0 | single | tone | 0.001 | 0.5 | 11.72 | 11.70 | +0.02 | 0.41 | consistent |
| C2 | A0 | single | tone | 0.001 | 0.9 | 14.58 | 14.43 | +0.15 | 0.57 | consistent |
| C2 | A0 | single | tone | 0.01 | 0.5 | 10.62 | 10.68 | -0.06 | 0.41 | consistent |
| C2 | A0 | single | tone | 0.01 | 0.9 | 13.43 | 13.49 | -0.05 | 0.29 | consistent |
| C2 | A1 | beam_search | broadband | 0.001 | 0.5 | -8.64 | -8.86 | +0.22 | 0.63 | consistent |
| C2 | A1 | beam_search | broadband | 0.001 | 0.9 | -6.68 | -6.70 | +0.01 | 0.46 | consistent |
| C2 | A1 | beam_search | broadband | 0.01 | 0.5 | -10.01 | -10.03 | +0.02 | 0.45 | consistent |
| C2 | A1 | beam_search | broadband | 0.01 | 0.9 | -7.34 | -7.33 | -0.00 | 0.42 | consistent |
| C2 | A1 | beam_search | chirp | 0.001 | 0.5 | 10.36 | 10.37 | -0.01 | 0.57 | consistent |
| C2 | A1 | beam_search | chirp | 0.001 | 0.9 | 12.67 | 12.74 | -0.07 | 0.46 | consistent |
| C2 | A1 | beam_search | chirp | 0.01 | 0.5 | 9.42 | 9.24 | +0.19 | 0.47 | consistent |
| C2 | A1 | beam_search | chirp | 0.01 | 0.9 | 11.96 | 12.13 | -0.17 | 0.53 | consistent |
| C2 | A1 | beam_search | harmonic | 0.001 | 0.5 | 6.96 | 7.16 | -0.21 | 0.49 | consistent |
| C2 | A1 | beam_search | harmonic | 0.001 | 0.9 | 9.15 | 9.47 | -0.32 | 0.74 | consistent |
| C2 | A1 | beam_search | harmonic | 0.01 | 0.5 | 6.03 | 6.14 | -0.11 | 0.47 | consistent |
| C2 | A1 | beam_search | harmonic | 0.01 | 0.9 | 8.44 | 8.50 | -0.06 | 0.26 | consistent |
| C2 | A1 | beam_search | tone | 0.0001 | 0.5 | 12.67 | 13.32 | -0.65 | 0.32 | bound holds |
| C2 | A1 | beam_search | tone | 0.0001 | 0.9 | 15.21 | 15.80 | -0.59 | 0.42 | bound holds |
| C2 | A1 | beam_search | tone | 0.001 | 0.5 | 11.90 | 11.57 | +0.33 | 0.83 | consistent |
| C2 | A1 | beam_search | tone | 0.001 | 0.9 | 14.57 | 14.23 | +0.34 | 0.90 | consistent |
| C2 | A1 | beam_search | tone | 0.01 | 0.5 | 10.87 | 10.58 | +0.29 | 0.42 | consistent |
| C2 | A1 | beam_search | tone | 0.01 | 0.9 | 13.49 | 13.45 | +0.05 | 0.49 | consistent |
| C2 | A1 | incoherent | broadband | 0.001 | 0.5 | -8.61 | -8.82 | +0.21 | 0.65 | consistent |
| C2 | A1 | incoherent | broadband | 0.001 | 0.9 | -6.68 | -6.68 | +0.00 | 0.49 | consistent |
| C2 | A1 | incoherent | broadband | 0.01 | 0.5 | -9.97 | -10.00 | +0.03 | 0.46 | consistent |
| C2 | A1 | incoherent | broadband | 0.01 | 0.9 | -7.31 | -7.31 | +0.01 | 0.40 | consistent |
| C2 | A1 | incoherent | chirp | 0.001 | 0.5 | 10.36 | 10.38 | -0.03 | 0.58 | consistent |
| C2 | A1 | incoherent | chirp | 0.001 | 0.9 | 12.67 | 12.76 | -0.09 | 0.45 | consistent |
| C2 | A1 | incoherent | chirp | 0.01 | 0.5 | 9.44 | 9.24 | +0.20 | 0.47 | consistent |
| C2 | A1 | incoherent | chirp | 0.01 | 0.9 | 11.96 | 12.16 | -0.19 | 0.53 | consistent |
| C2 | A1 | incoherent | harmonic | 0.001 | 0.5 | 6.97 | 7.17 | -0.21 | 0.49 | consistent |
| C2 | A1 | incoherent | harmonic | 0.001 | 0.9 | 9.15 | 9.47 | -0.32 | 0.74 | consistent |
| C2 | A1 | incoherent | harmonic | 0.01 | 0.5 | 6.06 | 6.13 | -0.07 | 0.47 | consistent |
| C2 | A1 | incoherent | harmonic | 0.01 | 0.9 | 8.45 | 8.50 | -0.05 | 0.26 | consistent |
| C2 | A1 | incoherent | tone | 0.0001 | 0.5 | 12.70 | 14.46 | -1.76 | 0.29 | bound holds |
| C2 | A1 | incoherent | tone | 0.0001 | 0.9 | 15.23 | 16.86 | -1.63 | 0.38 | bound holds |
| C2 | A1 | incoherent | tone | 0.001 | 0.5 | 11.93 | 11.59 | +0.34 | 0.83 | consistent |
| C2 | A1 | incoherent | tone | 0.001 | 0.9 | 14.59 | 14.23 | +0.36 | 0.89 | consistent |
| C2 | A1 | incoherent | tone | 0.01 | 0.5 | 10.87 | 10.58 | +0.29 | 0.44 | consistent |
| C2 | A1 | incoherent | tone | 0.01 | 0.9 | 13.52 | 13.47 | +0.05 | 0.53 | consistent |
| C2 | A4 | beam_search | broadband | 0.001 | 0.5 | -8.93 | -9.23 | +0.30 | 0.68 | consistent |
| C2 | A4 | beam_search | broadband | 0.001 | 0.9 | -6.81 | -7.01 | +0.19 | 0.30 | consistent |
| C2 | A4 | beam_search | broadband | 0.01 | 0.5 | -10.13 | -10.10 | -0.03 | 0.40 | consistent |
| C2 | A4 | beam_search | broadband | 0.01 | 0.9 | -7.62 | -7.64 | +0.02 | 0.52 | consistent |
| C2 | A4 | beam_search | chirp | 0.001 | 0.5 | 10.34 | 10.24 | +0.10 | 0.47 | consistent |
| C2 | A4 | beam_search | chirp | 0.001 | 0.9 | 12.75 | 12.61 | +0.13 | 0.34 | consistent |
| C2 | A4 | beam_search | chirp | 0.01 | 0.5 | 9.52 | 9.19 | +0.32 | 0.48 | consistent |
| C2 | A4 | beam_search | chirp | 0.01 | 0.9 | 12.24 | 12.07 | +0.17 | 0.43 | consistent |
| C2 | A4 | beam_search | harmonic | 0.001 | 0.5 | 7.00 | 7.08 | -0.08 | 0.61 | consistent |
| C2 | A4 | beam_search | harmonic | 0.001 | 0.9 | 9.26 | 9.30 | -0.04 | 0.85 | consistent |
| C2 | A4 | beam_search | harmonic | 0.01 | 0.5 | 6.04 | 5.99 | +0.05 | 0.46 | consistent |
| C2 | A4 | beam_search | harmonic | 0.01 | 0.9 | 8.39 | 8.36 | +0.03 | 0.28 | consistent |
| C2 | A4 | beam_search | tone | 0.0001 | 0.5 | 12.36 | 12.88 | -0.52 | 0.35 | bound holds |
| C2 | A4 | beam_search | tone | 0.0001 | 0.9 | 15.02 | 15.52 | -0.49 | 0.33 | bound holds |
| C2 | A4 | beam_search | tone | 0.001 | 0.5 | 11.44 | 11.28 | +0.16 | 0.79 | consistent |
| C2 | A4 | beam_search | tone | 0.001 | 0.9 | 14.19 | 13.94 | +0.25 | 0.93 | consistent |
| C2 | A4 | beam_search | tone | 0.01 | 0.5 | 10.49 | 10.08 | +0.41 | 0.52 | consistent |
| C2 | A4 | beam_search | tone | 0.01 | 0.9 | 13.32 | 13.15 | +0.16 | 0.45 | consistent |
| C2 | A4 | incoherent | broadband | 0.001 | 0.5 | -8.66 | -8.96 | +0.30 | 0.70 | consistent |
| C2 | A4 | incoherent | broadband | 0.001 | 0.9 | -6.72 | -6.88 | +0.16 | 0.29 | consistent |
| C2 | A4 | incoherent | broadband | 0.01 | 0.5 | -9.99 | -9.92 | -0.07 | 0.40 | consistent |
| C2 | A4 | incoherent | broadband | 0.01 | 0.9 | -7.47 | -7.43 | -0.05 | 0.45 | consistent |
| C2 | A4 | incoherent | chirp | 0.001 | 0.5 | 10.39 | 10.25 | +0.14 | 0.50 | consistent |
| C2 | A4 | incoherent | chirp | 0.001 | 0.9 | 12.76 | 12.62 | +0.14 | 0.33 | consistent |
| C2 | A4 | incoherent | chirp | 0.01 | 0.5 | 9.60 | 9.24 | +0.36 | 0.47 | consistent |
| C2 | A4 | incoherent | chirp | 0.01 | 0.9 | 12.29 | 12.09 | +0.21 | 0.37 | consistent |
| C2 | A4 | incoherent | harmonic | 0.001 | 0.5 | 7.10 | 7.09 | +0.01 | 0.62 | consistent |
| C2 | A4 | incoherent | harmonic | 0.001 | 0.9 | 9.34 | 9.22 | +0.12 | 0.85 | consistent |
| C2 | A4 | incoherent | harmonic | 0.01 | 0.5 | 6.08 | 6.02 | +0.05 | 0.47 | consistent |
| C2 | A4 | incoherent | harmonic | 0.01 | 0.9 | 8.42 | 8.39 | +0.04 | 0.27 | consistent |
| C2 | A4 | incoherent | tone | 0.0001 | 0.5 | 12.49 | 14.09 | -1.60 | 0.34 | bound holds |
| C2 | A4 | incoherent | tone | 0.0001 | 0.9 | 15.06 | 16.81 | -1.75 | 0.41 | bound holds |
| C2 | A4 | incoherent | tone | 0.001 | 0.5 | 11.50 | 11.37 | +0.13 | 0.72 | consistent |
| C2 | A4 | incoherent | tone | 0.001 | 0.9 | 14.27 | 14.16 | +0.11 | 0.90 | consistent |
| C2 | A4 | incoherent | tone | 0.01 | 0.5 | 10.60 | 10.19 | +0.41 | 0.53 | consistent |
| C2 | A4 | incoherent | tone | 0.01 | 0.9 | 13.36 | 13.23 | +0.13 | 0.43 | consistent |
| C2 | P8-C | beam_search | broadband | 0.001 | 0.5 | -8.74 | -8.96 | +0.22 | 0.65 | consistent |
| C2 | P8-C | beam_search | broadband | 0.001 | 0.9 | -6.77 | -6.82 | +0.05 | 0.34 | consistent |
| C2 | P8-C | beam_search | broadband | 0.01 | 0.5 | -9.87 | -9.89 | +0.02 | 0.41 | consistent |
| C2 | P8-C | beam_search | broadband | 0.01 | 0.9 | -7.30 | -7.26 | -0.04 | 0.34 | consistent |
| C2 | P8-C | beam_search | chirp | 0.001 | 0.5 | 10.35 | 10.31 | +0.04 | 0.70 | consistent |
| C2 | P8-C | beam_search | chirp | 0.001 | 0.9 | 12.74 | 12.73 | +0.02 | 0.51 | consistent |
| C2 | P8-C | beam_search | chirp | 0.01 | 0.5 | 9.30 | 9.49 | -0.19 | 0.48 | consistent |
| C2 | P8-C | beam_search | chirp | 0.01 | 0.9 | 12.15 | 12.21 | -0.07 | 0.45 | consistent |
| C2 | P8-C | beam_search | harmonic | 0.001 | 0.5 | 7.06 | 6.85 | +0.21 | 0.59 | consistent |
| C2 | P8-C | beam_search | harmonic | 0.001 | 0.9 | 9.18 | 9.05 | +0.13 | 0.88 | consistent |
| C2 | P8-C | beam_search | harmonic | 0.01 | 0.5 | 6.07 | 5.80 | +0.27 | 0.48 | consistent |
| C2 | P8-C | beam_search | harmonic | 0.01 | 0.9 | 8.52 | 8.34 | +0.18 | 0.30 | consistent |
| C2 | P8-C | beam_search | tone | 0.0001 | 0.5 | 12.60 | 13.49 | -0.89 | 0.34 | bound holds |
| C2 | P8-C | beam_search | tone | 0.0001 | 0.9 | 15.26 | 15.98 | -0.71 | 0.46 | bound holds |
| C2 | P8-C | beam_search | tone | 0.001 | 0.5 | 11.87 | 11.87 | -0.00 | 0.61 | consistent |
| C2 | P8-C | beam_search | tone | 0.001 | 0.9 | 14.57 | 14.72 | -0.15 | 0.62 | consistent |
| C2 | P8-C | beam_search | tone | 0.01 | 0.5 | 10.85 | 10.80 | +0.06 | 0.53 | consistent |
| C2 | P8-C | beam_search | tone | 0.01 | 0.9 | 13.65 | 13.70 | -0.05 | 0.48 | consistent |
| C2 | P8-C | incoherent | broadband | 0.001 | 0.5 | -8.65 | -8.88 | +0.23 | 0.66 | consistent |
| C2 | P8-C | incoherent | broadband | 0.001 | 0.9 | -6.71 | -6.79 | +0.09 | 0.41 | consistent |
| C2 | P8-C | incoherent | broadband | 0.01 | 0.5 | -9.86 | -9.86 | -0.00 | 0.41 | consistent |
| C2 | P8-C | incoherent | broadband | 0.01 | 0.9 | -7.27 | -7.22 | -0.04 | 0.34 | consistent |
| C2 | P8-C | incoherent | chirp | 0.001 | 0.5 | 10.36 | 10.37 | -0.01 | 0.71 | consistent |
| C2 | P8-C | incoherent | chirp | 0.001 | 0.9 | 12.75 | 12.76 | -0.01 | 0.52 | consistent |
| C2 | P8-C | incoherent | chirp | 0.01 | 0.5 | 9.31 | 9.52 | -0.20 | 0.47 | consistent |
| C2 | P8-C | incoherent | chirp | 0.01 | 0.9 | 12.15 | 12.23 | -0.08 | 0.45 | consistent |
| C2 | P8-C | incoherent | harmonic | 0.001 | 0.5 | 7.06 | 6.88 | +0.18 | 0.59 | consistent |
| C2 | P8-C | incoherent | harmonic | 0.001 | 0.9 | 9.15 | 9.12 | +0.03 | 0.88 | consistent |
| C2 | P8-C | incoherent | harmonic | 0.01 | 0.5 | 6.10 | 5.81 | +0.29 | 0.49 | consistent |
| C2 | P8-C | incoherent | harmonic | 0.01 | 0.9 | 8.52 | 8.34 | +0.18 | 0.30 | consistent |
| C2 | P8-C | incoherent | tone | 0.0001 | 0.5 | 12.63 | 15.88 | -3.26 | 0.34 | bound holds |
| C2 | P8-C | incoherent | tone | 0.0001 | 0.9 | 15.27 | 18.31 | -3.04 | 0.50 | bound holds |
| C2 | P8-C | incoherent | tone | 0.001 | 0.5 | 11.90 | 11.93 | -0.03 | 0.60 | consistent |
| C2 | P8-C | incoherent | tone | 0.001 | 0.9 | 14.57 | 14.74 | -0.17 | 0.63 | consistent |
| C2 | P8-C | incoherent | tone | 0.01 | 0.5 | 10.87 | 10.80 | +0.08 | 0.51 | consistent |
| C2 | P8-C | incoherent | tone | 0.01 | 0.9 | 13.65 | 13.66 | -0.02 | 0.48 | consistent |
| C3 | A0 | single | broadband | 0.0001 | 0.5 | -10.98 | -10.87 | -0.11 | 0.20 | consistent |
| C3 | A0 | single | broadband | 0.0001 | 0.9 | -9.37 | -8.85 | -0.52 | 0.48 | marginal |
| C3 | A0 | single | broadband | 0.001 | 0.5 | -11.66 | -11.61 | -0.06 | 0.31 | consistent |
| C3 | A0 | single | broadband | 0.001 | 0.9 | -9.98 | -9.88 | -0.10 | 0.15 | consistent |
| C3 | A0 | single | broadband | 0.01 | 0.5 | -13.02 | -12.97 | -0.05 | 0.30 | consistent |
| C3 | A0 | single | broadband | 0.01 | 0.9 | -10.57 | -10.50 | -0.07 | 0.28 | consistent |
| C3 | A0 | single | chirp | 0.0001 | 0.5 | 12.09 | 11.94 | +0.16 | 0.32 | bound holds |
| C3 | A0 | single | chirp | 0.0001 | 0.9 | 14.29 | 14.17 | +0.12 | 0.53 | bound holds |
| C3 | A0 | single | chirp | 0.001 | 0.5 | 11.21 | 11.27 | -0.06 | 0.60 | consistent |
| C3 | A0 | single | chirp | 0.001 | 0.9 | 13.37 | 13.43 | -0.06 | 0.53 | consistent |
| C3 | A0 | single | chirp | 0.01 | 0.5 | 10.39 | 10.30 | +0.09 | 0.40 | consistent |
| C3 | A0 | single | chirp | 0.01 | 0.9 | 12.83 | 12.88 | -0.06 | 0.33 | consistent |
| C3 | A0 | single | harmonic | 0.0001 | 0.5 | 18.06 | 17.87 | +0.19 | 0.31 | bound holds |
| C3 | A0 | single | harmonic | 0.0001 | 0.9 | 20.34 | 20.21 | +0.14 | 0.26 | bound holds |
| C3 | A0 | single | harmonic | 0.001 | 0.5 | 17.44 | 17.17 | +0.26 | 0.48 | consistent |
| C3 | A0 | single | harmonic | 0.001 | 0.9 | 19.74 | 19.47 | +0.27 | 0.70 | consistent |
| C3 | A0 | single | harmonic | 0.01 | 0.5 | 16.43 | 16.35 | +0.07 | 0.44 | consistent |
| C3 | A0 | single | harmonic | 0.01 | 0.9 | 18.68 | 18.60 | +0.08 | 0.25 | consistent |
| C3 | A0 | single | tone | 0.0001 | 0.5 | 23.22 | 23.01 | +0.21 | 0.31 | consistent |
| C3 | A0 | single | tone | 0.0001 | 0.9 | 25.62 | 25.62 | +0.00 | 0.31 | consistent |
| C3 | A0 | single | tone | 0.001 | 0.5 | 22.56 | 22.08 | +0.47 | 0.36 | marginal |
| C3 | A0 | single | tone | 0.001 | 0.9 | 24.96 | 24.72 | +0.25 | 0.59 | consistent |
| C3 | A0 | single | tone | 0.01 | 0.5 | 21.55 | 21.36 | +0.19 | 0.35 | consistent |
| C3 | A0 | single | tone | 0.01 | 0.9 | 24.03 | 24.04 | -0.01 | 0.28 | consistent |
| C3 | A1 | beam_search | broadband | 0.001 | 0.5 | -16.67 | -16.23 | -0.43 | 0.59 | consistent |
| C3 | A1 | beam_search | broadband | 0.001 | 0.9 | -14.49 | -14.18 | -0.31 | 0.34 | consistent |
| C3 | A1 | beam_search | broadband | 0.01 | 0.5 | -17.50 | -17.12 | -0.37 | 0.33 | marginal |
| C3 | A1 | beam_search | broadband | 0.01 | 0.9 | -15.75 | -15.17 | -0.58 | 0.60 | consistent |
| C3 | A1 | beam_search | chirp | 0.001 | 0.5 | 6.17 | 6.21 | -0.03 | 0.57 | consistent |
| C3 | A1 | beam_search | chirp | 0.001 | 0.9 | 8.66 | 8.44 | +0.22 | 0.62 | consistent |
| C3 | A1 | beam_search | chirp | 0.01 | 0.5 | 5.45 | 5.53 | -0.09 | 0.46 | consistent |
| C3 | A1 | beam_search | chirp | 0.01 | 0.9 | 7.70 | 7.51 | +0.18 | 0.57 | consistent |
| C3 | A1 | beam_search | harmonic | 0.001 | 0.5 | 12.39 | 12.31 | +0.08 | 0.55 | consistent |
| C3 | A1 | beam_search | harmonic | 0.001 | 0.9 | 14.71 | 14.66 | +0.05 | 0.43 | consistent |
| C3 | A1 | beam_search | harmonic | 0.01 | 0.5 | 11.70 | 11.54 | +0.16 | 0.35 | consistent |
| C3 | A1 | beam_search | harmonic | 0.01 | 0.9 | 14.32 | 14.17 | +0.15 | 0.38 | consistent |
| C3 | A1 | beam_search | tone | 0.0001 | 0.5 | 17.96 | 17.99 | -0.03 | 0.36 | bound holds |
| C3 | A1 | beam_search | tone | 0.0001 | 0.9 | 21.01 | 21.01 | -0.00 | 0.58 | bound holds |
| C3 | A1 | beam_search | tone | 0.001 | 0.5 | 17.42 | 17.17 | +0.24 | 0.50 | consistent |
| C3 | A1 | beam_search | tone | 0.001 | 0.9 | 20.14 | 20.04 | +0.09 | 0.51 | consistent |
| C3 | A1 | beam_search | tone | 0.01 | 0.5 | 16.58 | 16.46 | +0.12 | 0.49 | consistent |
| C3 | A1 | beam_search | tone | 0.01 | 0.9 | 19.62 | 19.52 | +0.10 | 0.46 | consistent |
| C3 | A1 | incoherent | broadband | 0.001 | 0.5 | -14.75 | -14.61 | -0.14 | 0.60 | consistent |
| C3 | A1 | incoherent | broadband | 0.001 | 0.9 | -12.52 | -12.44 | -0.08 | 0.37 | consistent |
| C3 | A1 | incoherent | broadband | 0.01 | 0.5 | -15.86 | -15.64 | -0.22 | 0.45 | consistent |
| C3 | A1 | incoherent | broadband | 0.01 | 0.9 | -13.78 | -13.74 | -0.04 | 0.58 | consistent |
| C3 | A1 | incoherent | chirp | 0.001 | 0.5 | 7.60 | 7.28 | +0.32 | 0.64 | consistent |
| C3 | A1 | incoherent | chirp | 0.001 | 0.9 | 9.55 | 9.53 | +0.01 | 0.79 | consistent |
| C3 | A1 | incoherent | chirp | 0.01 | 0.5 | 6.66 | 6.59 | +0.07 | 0.38 | consistent |
| C3 | A1 | incoherent | chirp | 0.01 | 0.9 | 9.09 | 9.03 | +0.06 | 0.29 | consistent |
| C3 | A1 | incoherent | harmonic | 0.001 | 0.5 | 14.01 | 13.93 | +0.08 | 0.45 | consistent |
| C3 | A1 | incoherent | harmonic | 0.001 | 0.9 | 16.28 | 16.20 | +0.08 | 0.38 | consistent |
| C3 | A1 | incoherent | harmonic | 0.01 | 0.5 | 13.12 | 13.14 | -0.02 | 0.42 | consistent |
| C3 | A1 | incoherent | harmonic | 0.01 | 0.9 | 15.49 | 15.59 | -0.10 | 0.59 | consistent |
| C3 | A1 | incoherent | tone | 0.0001 | 0.5 | 19.92 | 21.42 | -1.50 | 0.28 | bound holds |
| C3 | A1 | incoherent | tone | 0.0001 | 0.9 | 22.16 | 23.80 | -1.64 | 0.26 | bound holds |
| C3 | A1 | incoherent | tone | 0.001 | 0.5 | 19.14 | 18.94 | +0.20 | 0.49 | consistent |
| C3 | A1 | incoherent | tone | 0.001 | 0.9 | 21.59 | 21.58 | +0.01 | 0.48 | consistent |
| C3 | A1 | incoherent | tone | 0.01 | 0.5 | 18.07 | 17.78 | +0.29 | 0.42 | consistent |
| C3 | A1 | incoherent | tone | 0.01 | 0.9 | 20.59 | 20.17 | +0.43 | 0.52 | consistent |
| C3 | A4 | beam_search | broadband | 0.001 | 0.5 | -14.91 | -15.11 | +0.20 | 0.72 | consistent |
| C3 | A4 | beam_search | broadband | 0.001 | 0.9 | -12.47 | -12.69 | +0.22 | 0.64 | consistent |
| C3 | A4 | beam_search | broadband | 0.01 | 0.5 | -16.28 | -16.12 | -0.16 | 0.53 | consistent |
| C3 | A4 | beam_search | broadband | 0.01 | 0.9 | -13.79 | -13.80 | +0.01 | 0.55 | consistent |
| C3 | A4 | beam_search | chirp | 0.001 | 0.5 | 7.65 | 7.78 | -0.13 | 0.61 | consistent |
| C3 | A4 | beam_search | chirp | 0.001 | 0.9 | 10.60 | 10.59 | +0.01 | 0.59 | consistent |
| C3 | A4 | beam_search | chirp | 0.01 | 0.5 | 6.86 | 6.98 | -0.11 | 0.43 | consistent |
| C3 | A4 | beam_search | chirp | 0.01 | 0.9 | 9.87 | 9.74 | +0.14 | 0.65 | consistent |
| C3 | A4 | beam_search | harmonic | 0.001 | 0.5 | 13.36 | 13.24 | +0.12 | 0.54 | consistent |
| C3 | A4 | beam_search | harmonic | 0.001 | 0.9 | 15.66 | 16.01 | -0.36 | 0.63 | consistent |
| C3 | A4 | beam_search | harmonic | 0.01 | 0.5 | 12.53 | 12.35 | +0.18 | 0.47 | consistent |
| C3 | A4 | beam_search | harmonic | 0.01 | 0.9 | 14.73 | 14.82 | -0.09 | 0.46 | consistent |
| C3 | A4 | beam_search | tone | 0.0001 | 0.5 | 18.37 | 18.36 | +0.01 | 0.36 | bound holds |
| C3 | A4 | beam_search | tone | 0.0001 | 0.9 | 20.75 | 20.73 | +0.02 | 0.66 | bound holds |
| C3 | A4 | beam_search | tone | 0.001 | 0.5 | 17.67 | 17.58 | +0.08 | 0.61 | consistent |
| C3 | A4 | beam_search | tone | 0.001 | 0.9 | 20.11 | 20.03 | +0.08 | 0.60 | consistent |
| C3 | A4 | beam_search | tone | 0.01 | 0.5 | 16.93 | 16.88 | +0.05 | 0.37 | consistent |
| C3 | A4 | beam_search | tone | 0.01 | 0.9 | 19.54 | 19.55 | -0.00 | 0.43 | consistent |
| C3 | A4 | incoherent | broadband | 0.001 | 0.5 | -14.84 | -15.04 | +0.20 | 0.58 | consistent |
| C3 | A4 | incoherent | broadband | 0.001 | 0.9 | -12.68 | -12.75 | +0.07 | 0.67 | consistent |
| C3 | A4 | incoherent | broadband | 0.01 | 0.5 | -16.20 | -16.31 | +0.11 | 0.52 | consistent |
| C3 | A4 | incoherent | broadband | 0.01 | 0.9 | -13.96 | -13.95 | -0.01 | 0.30 | consistent |
| C3 | A4 | incoherent | chirp | 0.001 | 0.5 | 9.10 | 8.94 | +0.17 | 0.54 | consistent |
| C3 | A4 | incoherent | chirp | 0.001 | 0.9 | 11.19 | 11.12 | +0.07 | 0.29 | consistent |
| C3 | A4 | incoherent | chirp | 0.01 | 0.5 | 8.33 | 8.17 | +0.16 | 0.35 | consistent |
| C3 | A4 | incoherent | chirp | 0.01 | 0.9 | 10.70 | 10.66 | +0.04 | 0.36 | consistent |
| C3 | A4 | incoherent | harmonic | 0.001 | 0.5 | 13.20 | 13.06 | +0.14 | 0.45 | consistent |
| C3 | A4 | incoherent | harmonic | 0.001 | 0.9 | 14.97 | 15.14 | -0.17 | 0.70 | consistent |
| C3 | A4 | incoherent | harmonic | 0.01 | 0.5 | 12.35 | 12.44 | -0.09 | 0.42 | consistent |
| C3 | A4 | incoherent | harmonic | 0.01 | 0.9 | 14.54 | 14.60 | -0.06 | 0.21 | consistent |
| C3 | A4 | incoherent | tone | 0.0001 | 0.5 | 18.41 | 18.75 | -0.35 | 0.33 | bound holds |
| C3 | A4 | incoherent | tone | 0.0001 | 0.9 | 20.43 | 21.21 | -0.77 | 0.50 | bound holds |
| C3 | A4 | incoherent | tone | 0.001 | 0.5 | 17.67 | 17.43 | +0.25 | 0.43 | consistent |
| C3 | A4 | incoherent | tone | 0.001 | 0.9 | 20.05 | 19.95 | +0.09 | 0.34 | consistent |
| C3 | A4 | incoherent | tone | 0.01 | 0.5 | 16.95 | 16.94 | +0.01 | 0.36 | consistent |
| C3 | A4 | incoherent | tone | 0.01 | 0.9 | 19.51 | 19.55 | -0.05 | 0.44 | consistent |
| C3 | P8-C | beam_search | broadband | 0.001 | 0.5 | -18.76 | -18.68 | -0.08 | 0.33 | consistent |
| C3 | P8-C | beam_search | broadband | 0.001 | 0.9 | -16.69 | -16.58 | -0.11 | 0.45 | consistent |
| C3 | P8-C | beam_search | broadband | 0.01 | 0.5 | -19.57 | -19.51 | -0.06 | 0.37 | consistent |
| C3 | P8-C | beam_search | broadband | 0.01 | 0.9 | -17.82 | -17.88 | +0.06 | 0.25 | consistent |
| C3 | P8-C | beam_search | chirp | 0.001 | 0.5 | 4.02 | 3.90 | +0.12 | 0.47 | consistent |
| C3 | P8-C | beam_search | chirp | 0.001 | 0.9 | 5.78 | 5.48 | +0.30 | 0.63 | consistent |
| C3 | P8-C | beam_search | chirp | 0.01 | 0.5 | 3.22 | 3.04 | +0.17 | 0.39 | consistent |
| C3 | P8-C | beam_search | chirp | 0.01 | 0.9 | 5.27 | 5.19 | +0.08 | 0.19 | consistent |
| C3 | P8-C | beam_search | harmonic | 0.001 | 0.5 | 10.27 | 10.27 | -0.00 | 0.48 | consistent |
| C3 | P8-C | beam_search | harmonic | 0.001 | 0.9 | 12.48 | 12.57 | -0.08 | 0.29 | consistent |
| C3 | P8-C | beam_search | harmonic | 0.01 | 0.5 | 9.69 | 9.69 | -0.00 | 0.35 | consistent |
| C3 | P8-C | beam_search | harmonic | 0.01 | 0.9 | 12.13 | 12.15 | -0.02 | 0.34 | consistent |
| C3 | P8-C | beam_search | tone | 0.0001 | 0.5 | 15.64 | 15.55 | +0.08 | 0.32 | bound holds |
| C3 | P8-C | beam_search | tone | 0.0001 | 0.9 | 18.21 | 18.24 | -0.03 | 0.48 | bound holds |
| C3 | P8-C | beam_search | tone | 0.001 | 0.5 | 15.10 | 14.92 | +0.18 | 0.48 | consistent |
| C3 | P8-C | beam_search | tone | 0.001 | 0.9 | 17.76 | 17.91 | -0.15 | 0.43 | consistent |
| C3 | P8-C | beam_search | tone | 0.01 | 0.5 | 14.36 | 14.07 | +0.29 | 0.44 | consistent |
| C3 | P8-C | beam_search | tone | 0.01 | 0.9 | 17.04 | 17.29 | -0.25 | 0.72 | consistent |
| C3 | P8-C | incoherent | broadband | 0.001 | 0.5 | -16.19 | -15.97 | -0.22 | 0.64 | consistent |
| C3 | P8-C | incoherent | broadband | 0.001 | 0.9 | -14.14 | -14.09 | -0.05 | 0.25 | consistent |
| C3 | P8-C | incoherent | broadband | 0.01 | 0.5 | -17.27 | -17.22 | -0.05 | 0.40 | consistent |
| C3 | P8-C | incoherent | broadband | 0.01 | 0.9 | -14.74 | -14.87 | +0.13 | 0.44 | consistent |
| C3 | P8-C | incoherent | chirp | 0.001 | 0.5 | 6.30 | 6.38 | -0.08 | 0.35 | consistent |
| C3 | P8-C | incoherent | chirp | 0.001 | 0.9 | 8.39 | 8.41 | -0.02 | 0.58 | consistent |
| C3 | P8-C | incoherent | chirp | 0.01 | 0.5 | 5.54 | 5.61 | -0.08 | 0.38 | consistent |
| C3 | P8-C | incoherent | chirp | 0.01 | 0.9 | 7.37 | 7.32 | +0.04 | 0.18 | consistent |
| C3 | P8-C | incoherent | harmonic | 0.001 | 0.5 | 12.26 | 12.42 | -0.16 | 0.61 | consistent |
| C3 | P8-C | incoherent | harmonic | 0.001 | 0.9 | 14.42 | 14.48 | -0.05 | 0.32 | consistent |
| C3 | P8-C | incoherent | harmonic | 0.01 | 0.5 | 11.49 | 11.68 | -0.19 | 0.31 | consistent |
| C3 | P8-C | incoherent | harmonic | 0.01 | 0.9 | 13.78 | 13.94 | -0.16 | 0.40 | consistent |
| C3 | P8-C | incoherent | tone | 0.0001 | 0.5 | 17.71 | 19.67 | -1.96 | 0.25 | bound holds |
| C3 | P8-C | incoherent | tone | 0.0001 | 0.9 | 19.99 | 21.96 | -1.97 | 0.25 | bound holds |
| C3 | P8-C | incoherent | tone | 0.001 | 0.5 | 16.96 | 16.74 | +0.22 | 0.54 | consistent |
| C3 | P8-C | incoherent | tone | 0.001 | 0.9 | 19.33 | 19.36 | -0.03 | 0.61 | consistent |
| C3 | P8-C | incoherent | tone | 0.01 | 0.5 | 15.96 | 15.81 | +0.14 | 0.40 | consistent |
| C3 | P8-C | incoherent | tone | 0.01 | 0.9 | 18.20 | 18.28 | -0.08 | 0.48 | consistent |
