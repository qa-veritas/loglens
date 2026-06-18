"""Index client (example source for loglens).

The example log's `client.py:140` token resolves into the write path
here, where a deadline turns into the "context deadline exceeded"
cascade that follows the first error.
"""

from __future__ import annotations


class Response:
    def __init__(self, status: int):
        self.status = status


class Client:
    """A thin client over the index transport."""

    def __init__(self, transport, deadline_s: float = 5.0):
        self.transport = transport
        self.deadline_s = deadline_s

    def note(self, message: str) -> None:
        """Emit an informational note (progress, etc.)."""
        self.transport.log(message)

    def bulk_write(self, batch) -> Response:
        """Issue a bulk write and return the transport response."""
        return self.transport.bulk(batch)
