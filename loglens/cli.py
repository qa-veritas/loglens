"""Command-line entrypoint for loglens.

Subcommands:
    brief      tiered brief: timeline + emitting code + clusters
    correlate  resolve a file:line token to its source
    slice      pull a line window for drill-down
    scan       raw scan summary
"""

from __future__ import annotations

import argparse
import sys

from loglens.brief import build_brief
from loglens.correlate import CorrelationError, code_context, find_source
from loglens.scan import scan
from loglens.slice import slice_lines


def cmd_brief(args: argparse.Namespace) -> int:
    print(build_brief(args.log, args.source))
    return 0


def cmd_correlate(args: argparse.Namespace) -> int:
    matches = find_source(args.token, args.source)
    if len(matches) > 1:
        print(f"ambiguous: {args.token} matches {len(matches)} files:", file=sys.stderr)
        for match in matches:
            print(f"  {match}", file=sys.stderr)
    ctx = code_context(args.token, args.source, context=args.context)
    if ctx is None:
        print(f"no source match for {args.token} under {args.source}", file=sys.stderr)
        return 1
    print(ctx.render())
    return 0


def cmd_slice(args: argparse.Namespace) -> int:
    print(slice_lines(args.log, args.around, context=args.context))
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    result = scan(args.log)
    print(f"lines: {result.total_lines}  bytes: {result.total_bytes}")
    if result.last_progress:
        print(f"last progress: L{result.last_progress[0]}  {result.last_progress[1].strip()[:80]}")
    if result.first_error:
        print(f"first error:   L{result.first_error.lineno}  {result.first_error.text.strip()[:80]}")
        if result.first_error.tokens:
            print(f"  tokens: {', '.join(result.first_error.tokens)}")
    print(f"error lines:   {sum(result.clusters.values())}  clusters: {len(result.clusters)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loglens", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_brief = sub.add_parser("brief", help="tiered brief")
    p_brief.add_argument("--log", required=True)
    p_brief.add_argument("--source", help="source tree root for code correlation")
    p_brief.set_defaults(func=cmd_brief)

    p_corr = sub.add_parser("correlate", help="resolve a file:line token")
    p_corr.add_argument("--token", required=True)
    p_corr.add_argument("--source", required=True)
    p_corr.add_argument("--context", type=int, default=2)
    p_corr.set_defaults(func=cmd_correlate)

    p_slice = sub.add_parser("slice", help="line window for drill-down")
    p_slice.add_argument("--log", required=True)
    p_slice.add_argument("--around", type=int, required=True)
    p_slice.add_argument("--context", type=int, default=5)
    p_slice.set_defaults(func=cmd_slice)

    p_scan = sub.add_parser("scan", help="raw scan summary")
    p_scan.add_argument("--log", required=True)
    p_scan.set_defaults(func=cmd_scan)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except CorrelationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
