"""Assemble a small tiered brief from a scan + source correlation.

Tier 1 is this brief (a few KB): classification hint, timeline, emitting
code, error clusters. Tier 2/3 are the byte offsets in the scan, used to
pull raw windows on demand.
"""

from __future__ import annotations

import re
from pathlib import Path

from loglens.correlate import code_context
from loglens.scan import ScanResult, scan

# A light classification hint for the brief header. The dedicated
# classifier lives in state-triage; here we just nudge the reader.
_INFRA = re.compile(r"no space|disk.*full|flood.?stage|read-only|FORBIDDEN|refused|deadline|timeout", re.I)
_TESTBUG = re.compile(r"assert|expected .* but got|keyerror|indexerror", re.I)


def _class_hint(result: ScanResult) -> str:
    if result.first_error is None:
        return "HANG (no error found; check the last progress line)"
    text = result.first_error.text
    if _TESTBUG.search(text):
        return "TEST-BUG (first error is an assertion)"
    if _INFRA.search(text):
        return "INFRA (first error is an environment rejection, not an assertion)"
    return "PRODUCT or FRAMEWORK (no infra/test signature; check the emitting code)"


def build_brief(log_path: str | Path, source_root: str | Path | None = None, max_clusters: int = 8) -> str:
    """Build a Tier-1 brief for a log, correlating to source if given."""
    log_path = Path(log_path)
    result = scan(log_path)

    lines = [f"# Log brief  ({log_path} — {result.total_lines} lines, {result.total_bytes} bytes)", ""]
    lines += [f"class: {_class_hint(result)}", ""]

    lines.append("timeline:")
    if result.last_progress:
        ln, txt = result.last_progress
        lines.append(f"  last progress  L{ln}   {txt.strip()[:80]}")
    if result.first_error:
        fe = result.first_error
        lines.append(f"  first error    L{fe.lineno}   {fe.text.strip()[:80]}")
        cascade = [h for h in result.hits if h.lineno > fe.lineno]
        if cascade:
            lines.append(f"  cascade        L{cascade[0].lineno}+  {len(cascade)} more error line(s)")
    lines.append("")

    if source_root and result.emitting_tokens:
        lines.append("emitting code:")
        for token in result.emitting_tokens:
            ctx = code_context(token, source_root, context=2)
            if ctx is None:
                lines.append(f"  {token}  ->  (no source match under {source_root})")
            else:
                for rendered in ctx.render().splitlines():
                    lines.append("  " + rendered)
        lines.append("")

    if result.clusters:
        lines.append("error clusters:")
        first_sig = None
        if result.first_error:
            from loglens.scan import _signature  # local import; internal helper
            first_sig = _signature(result.first_error.text)
        ranked = sorted(result.clusters.items(), key=lambda kv: kv[1], reverse=True)[:max_clusters]
        for sig, count in ranked:
            tag = "  (first)" if sig == first_sig else ""
            lines.append(f"  {sig[:60]:60} x{count}{tag}")

    return "\n".join(lines).rstrip() + "\n"
