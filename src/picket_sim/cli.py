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
    r.add_argument("--workers", type=int, default=None, help="parallel worker processes (SIM-02B.1; default: CPUs)")
    v = sub.add_parser("validate", help="validate a configuration without running it")
    v.add_argument("config")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        import yaml

        from .config import config_sha256, load_config

        with open(args.config, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        if raw.get("experiment", {}).get("id") == "SIM-02A":
            from .experiments.sim02a import load_sim02a_config

            cfg = load_sim02a_config(args.config)
        elif raw.get("experiment", {}).get("id") == "SIM-02B.1":
            from .experiments.sim02b1 import load_sim02b1_config

            cfg = load_sim02b1_config(args.config)
        elif raw.get("experiment", {}).get("id") == "SIM-02B.2-A":
            from .experiments.sim02b2a import load_sim02b2a_config

            cfg = load_sim02b2a_config(args.config)
        else:
            cfg = load_config(args.config)
        print(f"OK {args.config} sha256={config_sha256(cfg)}")
        return 0
    from .config import load_config

    import yaml

    with open(args.config, "r", encoding="utf-8") as fh:
        exp = (yaml.safe_load(fh) or {}).get("experiment", {}).get("id")
    if exp == "SIM-01":
        load_config(args.config)
        from .experiments import sim01 as runner
    elif exp == "SIM-02A":
        from .experiments import sim02a as runner
    elif exp in ("SIM-02B.1", "SIM-02B.2-A"):
        from .experiments import sim02b1, sim02b2a

        runner = sim02b1 if exp == "SIM-02B.1" else sim02b2a

        try:
            runner.run(args.config, args.output_root, args.allow_dirty, not args.no_figures,
                       argv=["picket-sim", *argv], workers=args.workers)
        except DirtyTreeError as exc:
            print(f"refusing to run: {exc}", file=sys.stderr)
            return 3
        return 0
    else:
        print(f"no runner registered for experiment id {exp!r}", file=sys.stderr)
        return 2
    try:
        runner.run(args.config, args.output_root, args.allow_dirty, not args.no_figures,
                   argv=["picket-sim", *argv])
    except DirtyTreeError as exc:
        print(f"refusing to run: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
