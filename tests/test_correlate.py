from pathlib import Path

import pytest

from loglens.correlate import CorrelationError, code_context, find_source

SRC = Path(__file__).resolve().parents[1] / "examples" / "src"


def test_token_resolves_to_source():
    matches = find_source("writer.py:88", SRC)
    assert len(matches) == 1
    assert matches[0].name == "writer.py"


def test_code_context_targets_the_right_line():
    ctx = code_context("writer.py:88", SRC, context=1)
    assert ctx is not None
    assert ctx.line == 88
    target = [text for _, text, is_target in ctx.snippet if is_target]
    assert target and "WriteRejected" in target[0]


def test_unknown_token_returns_none():
    assert code_context("nope.py:5", SRC) is None


def test_bad_token_raises():
    with pytest.raises(CorrelationError):
        find_source("not-a-token", SRC)
