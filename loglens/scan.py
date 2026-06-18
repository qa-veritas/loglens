"""Stream a log once and extract a bounded summary.

Constant memory: the whole file is never held in RAM. We keep the first
error, the last progress checkpoint, a capped list of error hits with
their byte offsets (for drill-down), and clustered error counts by a
normalized signature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_ERROR = re.compile(
    r"\b(error|exception|failed|fatal|rejected|forbidden|refused|timeout|traceback|assert)\b",
    re.IGNORECASE,
)
_PROGRESS = re.compile(r"\b(progress|checkpoint|completed|written|processed|step)\b", re.IGNORECASE)
_FILELINE = re.compile(r"([\w./-]+\.\w+):(\d+)")
_LEADING_TS = re.compile(r"^\s*[\d:.\-T ]{4,}\s+")
_LEVEL = re.compile(r"^(INFO|WARN|WARNING|ERROR|DEBUG|FATAL|TRACE)\b", re.IGNORECASE)
_DIGITS = re.compile(r"\d+")


def _signature(text: str) -> str:
    """Normalize a log line into a stable cluster key.

    Strips a leading timestamp and level, then replaces digit runs with
    ``#`` so "4200 docs" and "8800 docs" cluster together.
    """
    stripped = _LEADING_TS.sub("", text).strip()
    stripped = _LEVEL.sub("", stripped).strip()
    stripped = _FILELINE.sub("", stripped).strip()
    return _DIGITS.sub("#", stripped)[:120]


@dataclass
class ErrorHit:
    """One error line with enough metadata to find it again."""

    lineno: int
    byte_offset: int
    text: str
    tokens: list[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """A bounded summary of a streamed log."""

    total_lines: int = 0
    total_bytes: int = 0
    first_error: ErrorHit | None = None
    last_progress: tuple[int, str] | None = None
    hits: list[ErrorHit] = field(default_factory=list)
    clusters: dict[str, int] = field(default_factory=dict)

    @property
    def emitting_tokens(self) -> list[str]:
        return self.first_error.tokens if self.first_error else []


def scan(log_path: str | Path, max_hits: int = 200) -> ScanResult:
    """Stream a log and return a bounded :class:`ScanResult`.

    Args:
        log_path: The log file.
        max_hits: Cap on retained error hits (clusters keep full counts).
    """
    log_path = Path(log_path)
    result = ScanResult()
    offset = 0

    with log_path.open("rb") as handle:
        for raw in handle:
            line = raw.decode("utf-8", errors="replace")
            result.total_lines += 1
            text = line.rstrip("\n")

            if _ERROR.search(text):
                tokens = [f"{m.group(1)}:{m.group(2)}" for m in _FILELINE.finditer(text)]
                hit = ErrorHit(lineno=result.total_lines, byte_offset=offset, text=text, tokens=tokens)
                if result.first_error is None:
                    result.first_error = hit
                if len(result.hits) < max_hits:
                    result.hits.append(hit)
                sig = _signature(text)
                result.clusters[sig] = result.clusters.get(sig, 0) + 1
            elif _PROGRESS.search(text):
                result.last_progress = (result.total_lines, text)

            offset += len(raw)

    result.total_bytes = offset
    return result
