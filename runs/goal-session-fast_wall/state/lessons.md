# Goal Session fast_wall — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-17T00:51:29Z

**Verdict:** CONTINUE
**Lesson:** Browser-QA of `/structure` against the DEFAULT (real-corpus) backend is an active
hazard until J-01 ships: `structure/page.tsx:1228-1255` fires a mount-time `GET /research/edge-report`
that, on a cold cache, synchronously runs the never-completing sweep and pins the uvicorn process at
~98% CPU for hours (single process, no `--workers`), GIL-freezing every other endpoint and breaking
concurrent goal-mode work. The dev + browser-QA agents correctly substituted grep/SSR code-citations
(spec-sanctioned) rather than trigger it, leaving J-07's `/structure` live-interactive leg an honest
gap.
**Applies to:** any iter whose browser-QA loads `/structure` before J-01's not-computed short-circuit
lands — run the frontend against a SCOPED/keyless dataset dir (or a warmed cache), never the default
882MB `.data/datasets`; and re-run J-07's deferred `/structure` era-5/5B spot-check once J-01 makes the
cold GET safe.
