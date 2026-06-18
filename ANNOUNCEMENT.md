# LinkedIn announcement — LogLens

---

`grep -i error | tail` on a multi-gigabyte log fails twice. It surfaces the loudest error — the one repeated 400 times downstream — instead of the first one. And it tells you a line came from `writer.py:88` without telling you what `writer.py:88` actually does. You end up triaging a string, blind to the code that produced it.

Logs are emitted by code, so evidence should point back at code. LogLens streams the log once in constant memory, finds the first error and last progress checkpoint, clusters the noise, and resolves every `file:line` token against the source tree — so you read the line *and* the function that raised it. Output is a few-KB brief with byte offsets, so you open the giant file only at the exact spot you need.

That's the difference between "an error at line 88" and "line 88 is a capacity guard, so this is infra, not a permissions bug."

This is the evidence half of the **Reasoning** layer in QA Veritas — a platform exploring how AI agents reason about, verify, and operate complex systems. It hands a model evidence it can actually reason over, instead of a gigabyte it can't.

Repo + write-up in the comments.

---
*First comment:* Repo: github.com/qa-veritas/loglens · Platform: github.com/qa-veritas
