# Deliverables

| Package | Contents | SHA-256 of zip |
|---|---|---|
| `PCK-SIM-001_SIM-01_Review_Package_20261107T203522Z_d64d297c_8043684.zip` | SIM-01 review package for the PCK-SIM-001 handoff author: transmittal (compliance matrix, review guide, decisions requested), engineering report (PDF and Markdown), figures, tables, run record, verification log at the code commit, documentation, source archive, manifest, checksums | `1a32d68540978e962a66f0f1dd04d545f6017679853cd108d436111478d14669` |

Built with `python tools/build_review_package.py --run results/sim01/20261107T203522Z_d64d297c_8043684`
from a clean tree. Unpack and run `sha256sum -c SHA256SUMS.txt` inside the package folder to verify
every file. Start with `00_TRANSMITTAL.pdf`.
