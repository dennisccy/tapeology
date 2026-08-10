# Goal Session playbook — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-10T07:12:37Z

**Verdict:** CONTINUE
**Lesson:** The four "route not found" screenshots (`J-01/J-02/J-07/J-08-route-404.png`) are the
same file byte-for-byte (md5 `a11b5066…`): a raw JSON body capture contains no address bar, so it
cannot prove WHICH endpoint was probed — fine for recording an absence, useless once these routes
ship and the acceptance becomes "the endpoint serves the honest empty payload". Capture the URL in
frame (or a body that names its own route) from J-01 onward. Separately: J-10's acceptance text
spans the whole era ("MCP = exactly 20 tools"), so it stays `partial` until J-09 lands — and a
`partial` sentinel does not auto-trip the regression halt, so a kept-screen break must be halted on
manually.
**Applies to:** any iteration capturing browser evidence for a `/research/desk/playbook*` endpoint,
and any iteration reading J-10's status to decide whether the kept product is safe.
