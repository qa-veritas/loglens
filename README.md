# loglens

**Code-aware log intelligence: slice a huge log, find the first error,
and correlate every `file:line` token back to the source that emitted
it.**

A multi-gigabyte run log is too big to read and too important to skip.
The instinct — `grep -i error | tail` — fails twice: it surfaces the
*loudest* error instead of the *first* one, and it tells you a line was
emitted at `writer.py:88` without telling you what `writer.py:88`
actually does. `loglens` fixes both.

It streams the log once (constant memory, never the whole file in RAM),
finds the first error and the last progress checkpoint, clusters the
repeated noise, and — the part that matters — resolves each `file:line`
token against your source tree so you read the *code that emitted the
line*, not just the line.

The output is a small tiered brief (a few KB) with byte offsets back
into the raw log for drill-down. You read the brief; you only open the
raw log at the exact offset when you need to.

## Install

```bash
pip install -e .
python -m loglens --help
```

Python 3.10+, no third-party runtime dependencies.

## Use

```bash
# The headline: a tiered brief that correlates errors to source
python -m loglens brief --log examples/run.log --source examples/src

# Resolve one file:line token to its code
python -m loglens correlate --token writer.py:88 --source examples/src

# Pull a window around a line for drill-down
python -m loglens slice --log examples/run.log --around 3 --context 4

# Raw scan summary (first error, last progress, clusters)
python -m loglens scan --log examples/run.log
```

### Example brief

```
# Log brief  (examples/run.log — 9 lines, 612 bytes)

class: INFRA (first error is an environment rejection, not an assertion)

timeline:
  last progress  L2   progress checkpoint: 4200 docs written
  first error    L3   write rejected (FORBIDDEN/8/index read-only ...)
  cascade        L5+  context deadline exceeded  x4

emitting code:
  writer.py:88  ->  examples/src/writer.py:88
      87  if resp.status == 403:
   >  88      raise WriteRejected("index is read-only (flood-stage guard)")
      89  # this is a capacity guard, not a permissions error

error clusters:
  write rejected (FORBIDDEN/#/index read-only ...)   x1   (first)
  context deadline exceeded on write                 x4
```

That last block is the difference between "an error happened at line 88"
and "line 88 is a capacity guard, so this is INFRA, not a permissions
bug."

## How the correlation works

Every `path:line` token in the log is matched against the source tree by
path suffix (so `writer.py:88` resolves whether the tree has
`writer.py` or `app/io/writer.py`). The matched line plus a few lines of
context are extracted. Ambiguous matches are reported, not guessed.

## Layout

```
loglens/
  loglens/
    __init__.py
    scan.py        # stream a log: first error, last progress, clusters, tokens
    correlate.py   # file:line token -> source file + code context
    slice.py       # line/byte windows for drill-down
    brief.py       # assemble the tiered brief
    cli.py         # brief / correlate / slice / scan
  examples/
    run.log
    src/writer.py
    src/client.py
  tests/
  LICENSE
  pyproject.toml
```

## Roadmap

- HTTP range-request backend so the same brief works against a remote
  multi-GB log without downloading it.
- A `--since`/`--window` time filter to bound the scan to a phase.
- Pluggable signature normalizers per log format.
- Cross-reference the emitting commit (git blame) so a brief points at
  the change that introduced the line.

## License

MIT. See [LICENSE](LICENSE).
