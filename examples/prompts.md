# Example prompts

How an agent uses loglens instead of `grep | tail` on a huge log.

## Triage from a brief, not the raw log

> Build a loglens brief for this run log against the source tree. Tell
> me the FIRST error (not the most frequent), what code emitted it, and
> whether that code is an assertion, a capacity guard, or a product
> path. Don't read the whole log.

## Decide cause vs cascade

> The brief shows one rejected write followed by four "context deadline
> exceeded" lines. Decide which is the cause and which is the cascade,
> using the timeline and the emitting code at `writer.py:88`.

## Drill down only where needed

> The first error is at line 3. Slice ±4 lines around it for context. If
> you need more, use the byte offset from the scan to read a raw window —
> don't load the whole file.

## Correlate an arbitrary token

> Resolve `client.py:140` against the source tree and show me the code.
> If it's ambiguous, list the candidates instead of guessing.
