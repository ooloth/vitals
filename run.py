#!/usr/bin/env python3
"""
Autonomous agent loops for scanning projects and fixing issues.

Usage:
  python run.py scan <project-id> [--type logs|codebase|...]
  python run.py fix [--issue <number>] [--project <id>]

Secrets:
  op run --env-file=secrets.env -- python run.py scan pilots
"""
import argparse

from loops.fix import run_fix
from loops.scan import run_scan


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("project")
    scan_p.add_argument("--type", default="logs")
    scan_p.add_argument("--dry-run", action="store_true")

    fix_p = sub.add_parser("fix")
    fix_p.add_argument("--issue", type=int, default=None)
    fix_p.add_argument("--project", default=None)

    args = parser.parse_args()

    if args.command == "scan":
        run_scan(args.project, args.type, dry_run=args.dry_run)
    elif args.command == "fix":
        run_fix(args.issue, args.project)


if __name__ == "__main__":
    main()
