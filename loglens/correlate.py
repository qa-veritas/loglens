"""Resolve a ``file:line`` token to its source and extract code context.

This is what makes the log *code-aware*: instead of "an error happened
at writer.py:88," you see the three lines of code around line 88, so you
know whether 88 is an assertion (test bug), a capacity guard (infra), or
a product code path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class CorrelationError(ValueError):
    """Raised when a token cannot be parsed."""


@dataclass
class CodeContext:
    """A resolved code location and the lines around it."""

    token: str
    source_file: Path
    line: int
    snippet: list[tuple[int, str, bool]]  # (lineno, text, is_target)

    def render(self) -> str:
        out = [f"{self.token}  ->  {self.source_file}:{self.line}"]
        for lineno, text, is_target in self.snippet:
            marker = ">" if is_target else " "
            out.append(f"  {marker} {lineno:>4}  {text}")
        return "\n".join(out)


def _parse_token(token: str) -> tuple[str, int]:
    if ":" not in token:
        raise CorrelationError(f"not a file:line token: {token!r}")
    path, _, line = token.rpartition(":")
    if not line.isdigit():
        raise CorrelationError(f"line part is not a number: {token!r}")
    return path, int(line)


def find_source(token: str, source_root: str | Path) -> list[Path]:
    """Find source files whose path ends with the token's path.

    Returns all matches (zero, one, or — for ambiguous basenames — many),
    so the caller can decide rather than the matcher guessing.
    """
    path, _ = _parse_token(token)
    source_root = Path(source_root)
    wanted = Path(path)
    basename = wanted.name

    matches: list[Path] = []
    for candidate in source_root.rglob(basename):
        if not candidate.is_file():
            continue
        # Match by path suffix so "io/writer.py" and "writer.py" both work.
        if str(candidate).endswith(str(wanted)) or candidate.name == basename:
            matches.append(candidate)
    return sorted(set(matches))


def code_context(token: str, source_root: str | Path, context: int = 2) -> CodeContext | None:
    """Resolve a token and extract ``context`` lines around the target.

    Returns None when the token resolves to no source file. When it
    resolves ambiguously, the first match is used and the ambiguity is
    discoverable via :func:`find_source`.
    """
    _, line = _parse_token(token)
    matches = find_source(token, source_root)
    if not matches:
        return None

    source_file = matches[0]
    lines = source_file.read_text(errors="replace").splitlines()
    lo = max(1, line - context)
    hi = min(len(lines), line + context)
    snippet = [(n, lines[n - 1], n == line) for n in range(lo, hi + 1)]
    return CodeContext(token=token, source_file=source_file, line=line, snippet=snippet)
