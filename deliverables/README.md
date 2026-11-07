# Deliverables

| Package | Contents | SHA-256 of zip |
|---|---|---|
| `PCK-SIM-001_SIM-02A_Review_Package_20261107T214846Z_c56c0048_31da01b.zip` | SIM-01 closure (Rev A documents) and SIM-02A review package: transmittal (SIM-01 corrections, SIM-02A deliverables, verification requirements, errata, decisions for SIM-02B), SIM-02A engineering report, figures, tables, run record and errata, test log at the code commit, plan and model documentation, AVS feasibility, source snapshot, checksums | `33fd747d4e284ef8f45c125112e595c670f5cff2e1f2b1ea953c13dc77754502` |
| `PCK-SIM-001_SIM-01_Review_Package_20261107T203522Z_d64d297c_8043684.zip` | SIM-01 review package for the PCK-SIM-001 handoff author: transmittal (compliance matrix, review guide, decisions requested), engineering report (PDF and Markdown), figures, tables, run record, verification log at the code commit, documentation, source archive, manifest, checksums | `1a32d68540978e962a66f0f1dd04d545f6017679853cd108d436111478d14669` |

SIM-01 (Rev 0, reviewed baseline) built with `python tools/build_review_package.py --run results/sim01/20261107T203522Z_d64d297c_8043684`; SIM-02A built with `--label SIM-02A --report reports/SIM-02A_engineering_report.md --transmittal reports/SIM-02A_transmittal.md --extra ...`
from a clean tree. Unpack and run `sha256sum -c SHA256SUMS.txt` inside the package folder to verify
every file. Start with `00_TRANSMITTAL.pdf`.
