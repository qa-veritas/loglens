"""loglens: code-aware log intelligence.

Stream a log once, find the first error and last progress checkpoint,
cluster the noise, and correlate every file:line token back to the
source that emitted it.
"""

from loglens.correlate import CodeContext, code_context, find_source
from loglens.scan import ErrorHit, ScanResult, scan
from loglens.slice import slice_lines

__all__ = [
    "CodeContext",
    "ErrorHit",
    "ScanResult",
    "code_context",
    "find_source",
    "scan",
    "slice_lines",
]

__version__ = "0.1.0"
