"""Command-line interface: ``python -m picket_sim run <config.yaml>``."""

from __future__ import annotations

import argparse
import sys

from .records import DirtyTreeError


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(prog="picket-sim", description="Picket acoustic array simulation (experimental)")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run an experiment configuration into a new, immutable run directory")
    r.add_argument("config", help="path to the experiment YAML (e.g. configs/sim01/sim01_baseline.yaml)")
    r.add_argument("--output-root", default=None, help="override output.root from the configuration")
    r.add_argument("--allow-dirty", action="store_true",
                   help="run even if tracked files have uncommitted changes (recorded in record.json)")
    r.add_argument("--no-figures", action="store_true", help="skip figure generation")
    v = sub.add_parser("validate", help="validate a configuration without running it")
    v.add_argument("config")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        from .config import config_sha256, load_config

        cfg = load_config(args.config)
        print(f"OK {args.config} sha256={config_sha256(cfg)}")
        return 0
    from .config import load_config

    exp = load_config(args.config)["experiment"]["id"]
    if exp != "SIM-01":
        print(f"no runner registered for experiment id {exp!r}", file=sys.stderr)
        return 2
    from .experiments import sim01

    try:
        sim01.run(args.config, args.output_root, args.allow_dirty, not args.no_figures,
                  argv=["picket-sim", *argv])
    except DirtyTreeError as exc:
        print(f"refusing to run: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
