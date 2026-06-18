# LinkedIn announcement — loglens

`grep -i error | tail` on a multi-gigabyte run log fails you twice. It
surfaces the *loudest* error instead of the *first* one — and one
rejected write becomes 200 timeout lines, so you debug the timeouts. And
it tells you a line came from `writer.py:88` without telling you what
`writer.py:88` does.

`loglens` is code-aware log intelligence. It streams the log once
(constant memory, never the whole file in RAM), finds the first error
and the last progress checkpoint, clusters the repeated noise, and — the
part that earns its keep — resolves every `file:line` token against your
source tree so you read the *code that emitted the line*.

That last step changes the diagnosis. The raw error is "FORBIDDEN —
index read-only," which reads like a permissions bug. Correlate it to
the source and line 88 is a flood-stage capacity guard. It's not a
permissions bug; it's a full disk. Same log line, opposite root cause —
and the only way to know is to look at the code.

The output is a few-KB tiered brief with byte offsets back into the raw
log. You read the brief; you only seek into the raw bytes at the exact
offset when you actually need to.

The principle: logs are emitted by code, so log analysis should be
code-aware. Treat `file:line` as a join key between the log and the
repository.

Python, no runtime deps, MIT.

Repo: github.com/qa-veritas/loglens

#observability #sre #debugging #aiengineering
