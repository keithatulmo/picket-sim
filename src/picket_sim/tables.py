"""Deterministic CSV / Markdown table writers."""

from __future__ import annotations

import csv
import gzip
import io
import math
from pathlib import Path

import numpy as np

__all__ = ["write_csv", "write_markdown", "fmt_value"]


def fmt_value(v, digits: int = 10) -> str:
    if v is None:
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "true" if v else "false"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        v = float(v)
        if math.isnan(v):
            return ""
        if math.isinf(v):
            return "inf" if v > 0 else "-inf"
        return format(v, f".{digits}g")
    return str(v)


def _columns(rows, columns):
    if columns:
        return list(columns)
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    return cols


def write_csv(path, rows: list[dict], columns=None, gz: bool = False) -> Path:
    path = Path(path)
    cols = _columns(rows, columns)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in rows:
        w.writerow([fmt_value(r.get(c)) for c in cols])
    data = buf.getvalue().encode("utf-8")
    if gz:
        with open(path, "wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:  # mtime=0: reproducible bytes
                fh.write(data)
    else:
        path.write_bytes(data)
    return path


def write_markdown(path, rows: list[dict], columns: list[tuple[str, str, str]], title: str = "", notes=()) -> Path:
    """``columns``: list of (key, header, format spec or '' for str)."""
    lines = []
    if title:
        lines += [f"## {title}", ""]
    lines.append("| " + " | ".join(h for _, h, _ in columns) + " |")
    lines.append("|" + "|".join("---" for _ in columns) + "|")
    for r in rows:
        cells = []
        for key, _, spec in columns:
            v = r.get(key)
            if isinstance(v, (float, np.floating)) and spec:
                v = float(v)
                cells.append("n/a" if math.isnan(v) else ("inf" if math.isinf(v) else format(v, spec)))
            else:
                cells.append("n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    if notes:
        lines.append("")
        lines += [f"* {n}" for n in notes]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return Path(path)
