"""Compare the tables of two run directories byte for byte (reproduction check).

    python tools/compare_run_tables.py results/sim02a/<run_of_record> build/sim02a_check/<new_run>

Exit status 0 if every table file in the first run exists in the second with identical bytes; 1 otherwise.
Gzip-compressed tables are compared after decompression (gzip headers carry timestamps).
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path


def _content(p: Path) -> bytes:
    data = p.read_bytes()
    return gzip.decompress(data) if p.suffix == ".gz" else data


def compare(a: Path, b: Path) -> list[str]:
    problems = []
    ta, tb = a / "tables", b / "tables"
    for f in sorted(ta.iterdir()):
        g = tb / f.name
        if not g.exists():
            problems.append(f"missing in second run: {f.name}")
        elif _content(f) != _content(g):
            problems.append(f"differs: {f.name}")
    for g in sorted(tb.iterdir()):
        if not (ta / g.name).exists():
            problems.append(f"extra in second run: {g.name}")
    return problems


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 2
    a, b = Path(args[0]), Path(args[1])
    problems = compare(a, b)
    n = len(list((a / "tables").iterdir()))
    for p in problems:
        print(p)
    print(f"{n - len([p for p in problems if not p.startswith('extra')])} of {n} tables identical")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
