## Pareto dominance (only attributes evaluated in SIM-01)

| Attribute set | Tie tolerance | ID | Dominated | Dominated by | Undefined attributes |
|---|---|---|---|---|---|
| all_candidates | numerical ties | A0 | False |  |  |
| all_candidates | numerical ties | A1 | True | A3 |  |
| all_candidates | numerical ties | A2 | False |  |  |
| all_candidates | numerical ties | A3 | False |  |  |
| all_candidates | numerical ties | A4 | False |  |  |
| all_candidates | engineering tolerances | A0 | False |  |  |
| all_candidates | engineering tolerances | A1 | True | A3 |  |
| all_candidates | engineering tolerances | A2 | False |  |  |
| all_candidates | engineering tolerances | A3 | False |  |  |
| all_candidates | engineering tolerances | A4 | False |  |  |
| multichannel | numerical ties | A1 | False |  |  |
| multichannel | numerical ties | A2 | False |  |  |
| multichannel | numerical ties | A3 | False |  |  |
| multichannel | numerical ties | A4 | False |  |  |
| multichannel | engineering tolerances | A1 | False |  |  |
| multichannel | engineering tolerances | A2 | False |  |  |
| multichannel | engineering tolerances | A3 | False |  |  |
| multichannel | engineering tolerances | A4 | False |  |  |

* A candidate is dominated if another is at least as good on every listed attribute and strictly better on one. Attribute lists are in the configuration (pareto.sets).
* Numerical ties: differences below 1e-9 (relative) are ties. Engineering tolerances: differences below the per-attribute tol / rel_tol declared in the configuration are ties (smaller differences are not meaningful given model fidelity, sound-speed uncertainty and grid resolution).
* Cost is NOT evaluated; channel count and maximum dimension are proxies only.
