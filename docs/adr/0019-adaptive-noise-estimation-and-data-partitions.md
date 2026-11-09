# ADR-0019: Adaptive noise estimation, data partitions and ground-truth isolation

Status: Accepted (SIM-02B.2-A, reviewer decision D01)

## Decision

**Streams.** Every detector input is a stream of DFT bins: the A0 element, a DAS beam (24-beam regression search
set), or one element (incoherent mode). A normalizer supplies a background estimate G_hat(f_k) for each stream and
bin; the detector statistics of SIM-02B.1 are computed on |y_k|^2 / G_hat_k.

**Normalizers.**

| Name | Data used | Estimate per stream and bin |
|---|---|---|
| ORACLE | true covariance (simulation only) | w^H C_true w; upper-bound baseline, never a performance claim |
| NOMINAL | nominal design model (Wenz nominal, isotropic, S1) | w^H C_nom w; the SIM-02B.1 clairvoyant normalizer |
| TREF-CA | M reference windows before the test window, after a guard of g windows | mean of the M reference powers; in the beam domain equal to w^H S_hat w with S_hat the sample covariance (SCM) |
| TREF-OS | same reference windows | r-th smallest of the M reference powers (ordered statistic; robust to intermittent interference) |
| FREF-CA | the test window itself | mean of |y_j|^2 over 2L reference bins j, with G guard bins on each side of k (one-sided at band edges) |
| FREF-OS | the test window itself | r-th smallest of the same 2L reference bins (median-type; robust to tones in the reference bins) |

**Partitions.** Reference (training) windows, calibration trials and evaluation trials are independent draws with
separate seed streams. Reference windows belong to the trial they normalize and are never reused across trials.
A guard of g windows separates the newest reference window from the test window; in frequency, G guard bins
separate reference bins from the cell under test.

**Ground-truth isolation.** Adaptive normalizers receive only stream data arrays (reference-window powers or the
test window's own bins); they have no access to C_true, scenario labels, signal presence, signal parameters or
truth flags. The code separates the oracle path explicitly (tests enforce it). Thresholds are fixed at design time
from the nominal model (ADR-0020) and are not re-tuned per scenario.

**Signal contamination.** Positive (target) evaluation trials may contaminate their own reference windows only
through the physically defined contamination scenario: a target with onset r windows before the test window is
present in every reference window inside that interval. Calibration and noise-only evaluation trials never contain
signal.

## Consequences
CFAR loss, contamination loss and nonstationarity effects appear explicitly. The A0, ORACLE and NOMINAL results
reproduce SIM-02B.1 behavior and serve as baselines.
