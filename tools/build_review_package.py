"""Assemble the SIM-01 review package from a completed run directory.

Usage (from the repository root, clean working tree):

    python tools/build_review_package.py --run results/sim01/<run_id> [--out deliverables]

Produces ``<out>/PCK-SIM-001_SIM-01_Review_Package_<run_id>/`` and a zip of it:

    00_TRANSMITTAL.pdf / .md       cover memo, compliance matrix, review guide, open decisions
    01_SIM-01_Engineering_Report.pdf / .md
    02_figures/                    all run figures (PNG)
    03_tables/                     all run tables (CSV, Markdown)
    04_run_record/                 record.json, summary.md, configuration, RUN_INDEX, ERRATA
    05_verification/               pytest log, JUnit XML, test inventory (run at the code commit)
    06_documentation/              plan, conventions, metrics, assumptions, ADRs
    07_source/                     two source archives and SOURCE.md:
                                   * picket-sim_<code>.tar.gz: git archive of the code commit that produced the run
                                   * picket-sim_<head>_baseline.tar.gz: git archive of the packaging HEAD (the final
                                     source baseline, including later report-generation tools) plus the record and
                                     tables of each --include-results run, so documented commands work from it
    MANIFEST.md, SHA256SUMS.txt

Options added for the SIM-02A review closeout: ``--include-results RUN ...`` embeds run-of-record tables in the
baseline archive; ``--snapshot-check CMD`` (repeatable) runs CMD inside an unpacked copy of the baseline archive and
logs the result to 05_verification/snapshot_checks.txt (the build fails if any command fails); the verification
suite runs at both the code commit and the packaging HEAD.

Requires: ``markdown`` and ``pypdf`` (Python), Node with Playwright/Chromium for PDF printing.
The package is assembled only from committed files and the immutable run directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import io
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import markdown
from pypdf import PdfReader, PdfWriter

REPO = Path(__file__).resolve().parents[1]

CSS = """
@page { size: Letter; }
body { font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; font-size: 9.6pt; line-height: 1.42;
       color: #0b0b0b; max-width: 100%; }
h1 { font-size: 17pt; margin: 0 0 4pt 0; }
h2 { font-size: 12.5pt; margin: 16pt 0 5pt 0; padding-bottom: 2pt; border-bottom: 1px solid #d9d8d4;
     break-after: avoid; }
h3 { font-size: 10.5pt; margin: 11pt 0 3pt 0; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; margin: 6pt 0 8pt 0; font-size: 7.6pt; width: 100%;
        break-inside: auto; }
th, td { border: 1px solid #d9d8d4; padding: 2.5pt 4pt; vertical-align: top; text-align: left; }
th { background: #f3f2ef; font-weight: 600; }
tr { break-inside: avoid; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.4pt; background: #f3f2ef; padding: 0 2px;
       border-radius: 2px; }
blockquote { border-left: 3px solid #eb6834; margin: 6pt 0; padding: 2pt 8pt; color: #52514e; }
img { max-width: 100%; display: block; margin: 6pt auto 2pt auto; break-inside: avoid; }
figure { margin: 8pt 0 10pt 0; break-inside: avoid; }
figcaption { font-size: 8pt; color: #52514e; text-align: center; }
hr { border: 0; border-top: 1px solid #d9d8d4; margin: 12pt 0; }
"""


def sh(cmd, cwd=REPO, **kw) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, **kw).stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md_to_pdf(md_text: str, html_path: Path, pdf_path: Path, title: str, footer: str, image_map=None):
    """Render Markdown to HTML (images resolved through ``image_map``) and print to PDF."""
    html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    for src, dst in (image_map or {}).items():
        html_body = html_body.replace(f'src="{src}"', f'src="{dst}"')
    html = (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>"
            f"<style>{CSS}</style></head><body>{html_body}</body></html>")
    html_path.write_text(html, encoding="utf-8")
    subprocess.run(["node", str(REPO / "tools" / "print_pdf.mjs"), str(html_path), str(pdf_path), footer],
                   check=True, cwd=REPO)
    # set document metadata
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({"/Title": title, "/Subject": f"Ulmo Picket PCK-SIM-001 {footer.split('/')[-1].split('|')[0].strip()}",
                         "/Creator": "picket-sim tools/build_review_package.py",
                         "/Author": "Generated with Claude Code; requires human engineering review"})
    with open(pdf_path, "wb") as fh:
        writer.write(fh)
    return len(reader.pages)


def _tar_add_bytes(tar: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644):
    info = tarfile.TarInfo(name)
    info.size, info.mtime, info.mode = len(data), 1767225600, mode  # 2026-01-01T00:00:00Z
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    tar.addfile(info, io.BytesIO(data))


def build_baseline_archive(head: str, out: Path, include_results: list[str]) -> list[str]:
    """git archive of HEAD (without results/ and deliverables/) plus selected run records and tables.

    Deterministic: sorted members, fixed timestamps and ownership. Returns the included result paths.
    """
    prefix = f"picket-sim-{head[:7]}/"
    raw = subprocess.run(["git", "archive", "--format=tar", head, "--", ".", ":(exclude)results",
                          ":(exclude)deliverables"], cwd=REPO, check=True, capture_output=True).stdout
    members: dict[str, tuple[bytes, int]] = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        for m in t.getmembers():
            if m.isfile():
                members[m.name] = (t.extractfile(m).read(), 0o755 if m.mode & 0o111 else 0o644)
    included = []
    for rd in include_results:
        run = (REPO / rd).resolve()
        rel = run.relative_to(REPO).as_posix()
        tracked = sh(["git", "ls-files", "--error-unmatch", f"{rel}/record.json"]).strip()
        if not tracked:
            raise SystemExit(f"{rel} is not a committed run directory")
        files = [run / "record.json", run / "summary.md", *sorted((run / "tables").rglob("*"))]
        files += [run.parent / f for f in ("ERRATA.md", "RUN_INDEX.csv")]
        for f in files:
            if f.is_file():
                members[f.relative_to(REPO).as_posix()] = (f.read_bytes(), 0o644)
        included.append(rel)
    with open(out, "wb") as fh:
        with tarfile.open(fileobj=fh, mode="w:gz", format=tarfile.PAX_FORMAT) as tar:
            for name in sorted(members):
                data, mode = members[name]
                _tar_add_bytes(tar, prefix + name, data, mode)
    return included


def source_md(code_commit: str, head: str, code_archive: str, baseline_archive: str, included: list[str]) -> str:
    log = sh(["git", "log", "--format=%h %ad %s", "--date=short", f"{code_commit}..{head}"]).strip()
    stat = sh(["git", "diff", "--stat", f"{code_commit}..{head}", "--", "src", "configs", "tests", "tools",
               "Makefile", "pyproject.toml", "requirements.lock"]).strip()
    src_changed = sh(["git", "diff", "--name-only", f"{code_commit}..{head}", "--", "src"]).strip()
    lines = [
        "# Source snapshots and baselines",
        "",
        "| Baseline | Commit | Archive | Use |",
        "|---|---|---|---|",
        f"| Code commit of the run of record | `{code_commit}` | `{code_archive}` | The exact code that produced the "
        "run of record (recorded in `04_run_record/record.json`). Verification log: `05_verification/pytest_log.txt`. |",
        f"| Final source baseline (packaging HEAD) | `{head}` | `{baseline_archive}` | Everything committed when this "
        "package was built, including report-generation and checking tools added after the code commit, plus the "
        "run-of-record tables listed below so that documented commands run from the snapshot. Verification log: "
        "`05_verification/pytest_log_baseline.txt`; snapshot command log: `05_verification/snapshot_checks.txt`. |",
        "",
        "Run-of-record directories embedded in the baseline archive (record.json, summary.md, tables/, and the "
        "study's ERRATA.md and RUN_INDEX.csv; figures are in `02_figures`):",
        "",
        *[f"* `{r}`" for r in included],
        "",
        "## Changes between the code commit and the final baseline",
        "",
        "Library code under `src/` changed: " + ("yes, see the file list below." if src_changed else
                                                 "no. The run of record reproduces from either baseline."),
        "",
        *([f"* `{x}`" for x in src_changed.splitlines()] + [""] if src_changed else []),
        "Commits:",
        "",
        "```",
        log or "(none)",
        "```",
        "",
        "Changed code, configuration, test and tool files (`git diff --stat`):",
        "",
        "```",
        stat or "(none)",
        "```",
        "",
        "## Reproduce",
        "",
        "```",
        f"tar xzf {baseline_archive} && cd {baseline_archive.split('_baseline')[0].replace('_', '-')}",
        "python -m venv .venv && . .venv/bin/activate",
        "pip install -r requirements.lock && pip install -e . --no-deps",
        "make test",
        "```",
        "",
        "Rendering PDFs with `tools/build_review_package.py` additionally needs `requirements-tools.lock` and Node "
        "with Playwright/Chromium.",
        "",
    ]
    return "\n".join(lines)


def run_suite(commit: str, ver: Path, suffix: str):
    """Run the verification suite in a git worktree at ``commit``; write logs; fail the build on failure."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "worktree", "add", "--detach", td, commit], cwd=REPO, check=True, capture_output=True)
        try:
            env = dict(os.environ, PYTHONPATH=str(Path(td) / "src"))
            inv = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
                                 cwd=td, env=env, capture_output=True, text=True)
            (ver / f"test_inventory{suffix}.txt").write_text(inv.stdout, encoding="utf-8")
            res = subprocess.run([sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider",
                                  f"--junitxml={ver / f'pytest_junit{suffix}.xml'}"],
                                 cwd=td, env=env, capture_output=True, text=True)
            (ver / f"pytest_log{suffix}.txt").write_text(
                f"# pytest at commit {commit} (git worktree), Python {sys.version.split()[0]}\n"
                f"# exit status {res.returncode}\n\n{res.stdout}\n{res.stderr}", encoding="utf-8")
            if res.returncode != 0:
                raise SystemExit(f"verification suite failed at {commit}; package not built")
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", td], cwd=REPO, capture_output=True)


def run_snapshot_checks(baseline: Path, head: str, commands: list[str], log_path: Path):
    """Unpack the baseline archive (no git metadata) and run each command there; log; fail on any failure."""
    out = [f"# Commands run inside an unpacked copy of {baseline.name} (no .git directory), "
           f"Python {sys.version.split()[0]} at {sys.executable}", ""]
    failed = []
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(baseline) as t:
            t.extractall(td, filter="data")
        root = Path(td) / f"picket-sim-{head[:7]}"
        env = dict(os.environ, PYTHONPATH=str(root / "src"), PY=sys.executable)
        for cmd in commands:
            res = subprocess.run(cmd, shell=True, cwd=root, env=env, capture_output=True, text=True)
            out += [f"$ {cmd}", f"# exit status {res.returncode}", res.stdout.rstrip(), res.stderr.rstrip(), ""]
            if res.returncode != 0:
                failed.append(cmd)
    log_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit(f"snapshot checks failed: {failed}; see {log_path}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="run directory, e.g. results/sim01/<run_id>")
    ap.add_argument("--out", default="deliverables")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--skip-tests", action="store_true", help="do not re-run the verification suite")
    ap.add_argument("--report", default="reports/SIM-01_engineering_report.md")
    ap.add_argument("--transmittal", default="reports/SIM-01_transmittal.md")
    ap.add_argument("--label", default="SIM-01", help="increment label used in names and footers")
    ap.add_argument("--extra", nargs="*", default=[], help="additional repository files for 01_extra/")
    ap.add_argument("--include-results", nargs="*", default=[],
                    help="run directories whose record.json, summary.md and tables/ go into the baseline archive")
    ap.add_argument("--snapshot-check", action="append", default=[],
                    help="shell command run inside an unpacked baseline archive (repeatable)")
    args = ap.parse_args(argv)

    run = (REPO / args.run).resolve()
    record = json.loads((run / "record.json").read_text())
    if record.get("status") != "complete":
        raise SystemExit("run is not complete")
    run_id = record["run_id"]
    code_commit = record["software"]["git_commit"]
    if record["software"].get("git_dirty"):
        raise SystemExit("run of record was produced from a dirty tree; refusing to package it")
    status = sh(["git", "status", "--porcelain", "--untracked-files=no"])
    if status.strip() and not args.allow_dirty:
        raise SystemExit("working tree has uncommitted changes; commit before packaging")
    head = sh(["git", "rev-parse", "HEAD"]).strip()

    name = f"PCK-SIM-001_{args.label}_Review_Package_{run_id}"
    out_root = (REPO / args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    final = out_root / name
    if final.exists():
        raise SystemExit(f"package already exists, refusing to overwrite: {final}")
    stage = Path(tempfile.mkdtemp(prefix=".pkg.", dir=out_root)) / name
    stage.mkdir()

    # ---------------------------------------------------------------- files from the run
    shutil.copytree(run / "figures", stage / "02_figures")
    shutil.copytree(run / "tables", stage / "03_tables")
    rec = stage / "04_run_record"
    rec.mkdir()
    for f in ("record.json", "summary.md"):
        shutil.copy2(run / f, rec / f)
    shutil.copy2(REPO / record["config_path"], rec / Path(record["config_path"]).name)
    for f in ("RUN_INDEX.csv", "ERRATA.md"):
        if (run.parent / f).exists():
            shutil.copy2(run.parent / f, rec / f)

    # ---------------------------------------------------------------- documentation
    doc = stage / "06_documentation"
    shutil.copytree(REPO / "docs", doc)
    shutil.copy2(REPO / "README.md", doc / "README.md")

    # ---------------------------------------------------------------- source snapshots
    src = stage / "07_source"
    src.mkdir()
    archive = src / f"picket-sim_{code_commit[:7]}.tar.gz"
    with open(archive, "wb") as fh:
        # code, configuration, documentation and tests only: run outputs are in 04_run_record and the
        # historical results and deliverables are not part of the source snapshot
        subprocess.run(["git", "archive", "--format=tar.gz", f"--prefix=picket-sim-{code_commit[:7]}/", code_commit,
                        "--", ".", ":(exclude)results", ":(exclude)deliverables"],
                       cwd=REPO, check=True, stdout=fh)
    baseline = src / f"picket-sim_{head[:7]}_baseline.tar.gz"
    included = build_baseline_archive(head, baseline, args.include_results)
    shutil.copy2(REPO / "requirements.lock", src / "requirements.lock")
    if (REPO / "requirements-tools.lock").exists():
        shutil.copy2(REPO / "requirements-tools.lock", src / "requirements-tools.lock")
    (src / "SOURCE.md").write_text(source_md(code_commit, head, archive.name, baseline.name, included),
                                   encoding="utf-8")

    # ---------------------------------------------------------------- verification evidence
    ver = stage / "05_verification"
    ver.mkdir()
    if not args.skip_tests:
        run_suite(code_commit, ver, "")
        if head != code_commit:
            run_suite(head, ver, "_baseline")
    if args.snapshot_check:
        run_snapshot_checks(baseline, head, args.snapshot_check, ver / "snapshot_checks.txt")
    (ver / "self_checks.json").write_text(json.dumps(record["self_checks"], indent=2) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- report and transmittal PDFs
    footer = f"Ulmo Picket PCK-SIM-001 / {args.label}  |  run {run_id}"
    rel_fig = "../" + run.relative_to(REPO).as_posix() + "/figures/"
    report_md = (REPO / args.report).read_text(encoding="utf-8")
    rep_name = f"01_{args.label}_Engineering_Report"
    shutil.copy2(REPO / args.report, stage / f"{rep_name}.md")
    figs = sorted((stage / "02_figures").glob("*.png"))
    image_map = {rel_fig + f.name: f"02_figures/{f.name}" for f in figs}
    n_rep = md_to_pdf(report_md, stage / ".report.html", stage / f"{rep_name}.pdf",
                      f"{args.label} Engineering Report", footer, image_map)
    tr_md = (REPO / args.transmittal).read_text(encoding="utf-8")
    shutil.copy2(REPO / args.transmittal, stage / "00_TRANSMITTAL.md")
    n_tr = md_to_pdf(tr_md, stage / ".transmittal.html", stage / "00_TRANSMITTAL.pdf",
                     f"{args.label} Review Transmittal", footer)
    if args.extra:
        ex = stage / "01_extra"
        ex.mkdir()
        for e in args.extra:
            src_path = REPO / e
            shutil.copy2(src_path, ex / src_path.name)  # .pdf files are included as already rendered
            if src_path.suffix == ".md":
                md_to_pdf(src_path.read_text(encoding="utf-8"), stage / ".extra.html", ex / (src_path.stem + ".pdf"),
                          src_path.stem, footer)
    for h in stage.glob(".*.html"):
        h.unlink()

    # ---------------------------------------------------------------- manifest and checksums
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    lines = [f"# {name}", "", f"* Run of record: `{run_id}`", f"* Code commit: `{code_commit}`",
             f"* Packaged from repository HEAD `{head}`",
             f"* Transmittal: {n_tr} pages; engineering report: {n_rep} pages", "",
             "| File | Bytes |", "|---|---|"]
    lines += [f"| `{p.relative_to(stage)}` | {p.stat().st_size:,} |" for p in files]
    (stage / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    (stage / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(p)}  {p.relative_to(stage)}\n" for p in files), encoding="utf-8")

    # ---------------------------------------------------------------- move into place and zip (fixed timestamps)
    os.replace(stage, final)
    shutil.rmtree(stage.parent, ignore_errors=True)
    zpath = out_root / f"{name}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(final.rglob("*")):
            if p.is_file():
                info = zipfile.ZipInfo(str(Path(name) / p.relative_to(final)), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, p.read_bytes())
    print(f"package: {final}\nzip: {zpath} ({zpath.stat().st_size:,} bytes)\n"
          f"transmittal {n_tr} pages, report {n_rep} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
