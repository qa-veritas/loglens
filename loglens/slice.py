"""Pull a bounded window out of a log for drill-down.

Two modes: a line window around a center line, and a raw byte range
(the byte offsets come from the scan, so you can seek straight to an
error in a multi-GB file without reading the whole thing).
"""

from __future__ import annotations

from pathlib import Path


def slice_lines(log_path: str | Path, center_line: int, context: int = 5) -> str:
    """Return ``context`` lines either side of ``center_line``.

    Reads only up to the end of the window, not the whole file.
    """
    log_path = Path(log_path)
    lo = max(1, center_line - context)
    hi = center_line + context
    out: list[str] = []
    with log_path.open(errors="replace") as handle:
        for lineno, line in enumerate(handle, start=1):
            if lineno < lo:
                continue
            if lineno > hi:
                break
            marker = ">" if lineno == center_line else " "
            out.append(f"{marker} {lineno:>6}  {line.rstrip()}")
    return "\n".join(out)


def byte_range(log_path: str | Path, start: int, length: int = 4096) -> str:
    """Read ``length`` bytes starting at ``start`` (seek, no full read)."""
    log_path = Path(log_path)
    with log_path.open("rb") as handle:
        handle.seek(start)
        return handle.read(length).decode("utf-8", errors="replace")
