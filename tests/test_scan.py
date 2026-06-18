from pathlib import Path

from loglens.scan import scan

LOG = Path(__file__).resolve().parents[1] / "examples" / "run.log"


def test_first_error_is_the_rejection_not_the_cascade():
    result = scan(LOG)
    assert result.first_error is not None
    assert "rejected" in result.first_error.text.lower()
    assert result.first_error.lineno == 3


def test_first_error_carries_emitting_token():
    result = scan(LOG)
    assert "writer.py:88" in result.first_error.tokens


def test_last_progress_recorded():
    result = scan(LOG)
    assert result.last_progress is not None
    assert "checkpoint" in result.last_progress[1].lower()


def test_timeout_cascade_clusters_together():
    result = scan(LOG)
    # The four "context deadline exceeded" lines collapse to one cluster.
    deadline_clusters = [count for sig, count in result.clusters.items() if "deadline" in sig.lower()]
    assert deadline_clusters and deadline_clusters[0] == 4


def test_byte_offsets_are_monotonic():
    result = scan(LOG)
    offsets = [h.byte_offset for h in result.hits]
    assert offsets == sorted(offsets)
