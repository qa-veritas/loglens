"""Write path for the index loader (example source for loglens).

This module exists so the example log's `writer.py:88` token resolves to
a real line of code. Line 88 is the flood-stage guard — a capacity
guard that surfaces as a FORBIDDEN error, which is exactly why a
code-aware brief is more useful than the raw error string.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


class WriteRejected(Exception):
    """Raised when the index refuses writes (read-only / flood-stage)."""


class WriteTimeout(Exception):
    """Raised when a write does not complete within the deadline."""


@dataclass
class WriteResult:
    written: int
    rejected: int


class Writer:
    """Writes documents to an index with backoff and a deadline."""

    def __init__(self, client, batch_size: int = 500, deadline_s: float = 30.0):
        self.client = client
        self.batch_size = batch_size
        self.deadline_s = deadline_s

    def write_load(self, docs, checkpoint_every: int = 4200) -> WriteResult:
        """Write a stream of docs, checkpointing progress.

        Args:
            docs: An iterable of documents to write.
            checkpoint_every: Emit a progress checkpoint at this cadence.

        Returns:
            A WriteResult with counts.

        Raises:
            WriteRejected: If the index has flipped to read-only.
            WriteTimeout: If the deadline is exceeded.
        """
        written = 0
        rejected = 0
        started = time.monotonic()

        batch = []
        for doc in docs:
            batch.append(doc)
            if len(batch) < self.batch_size:
                continue

            written += self._flush(batch)
            batch = []

            if written and written % checkpoint_every == 0:
                self._checkpoint(written)

            if time.monotonic() - started > self.deadline_s:
                raise WriteTimeout("write deadline exceeded")

        if batch:
            written += self._flush(batch)

        return WriteResult(written=written, rejected=rejected)

    def _checkpoint(self, written: int) -> None:
        """Log a progress checkpoint (the 'last progress' line)."""
        # progress checkpoint: <written> docs written
        self.client.note(f"progress checkpoint: {written} docs written")

    def _flush(self, batch) -> int:
        """Flush a batch; translate a read-only index into WriteRejected."""
        resp = self.client.bulk_write(batch)
        if resp.status == 403:
            # The index flipped to read-only because a data node crossed
            # the storage flood-stage watermark. This is a CAPACITY guard,
            # not a permissions problem — that distinction is the whole
            # point of correlating the log line back to this code.
            raise WriteRejected("index is read-only (flood-stage guard)")
        return len(batch)
