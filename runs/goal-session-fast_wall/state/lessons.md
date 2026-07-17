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

## iter-1 — 2026-07-17T04:59:39Z

**Verdict:** CONTINUE
**Lesson:** The QA report marked the browser tests TC-11/TC-12 as SKIP ("Chrome session timed out")
and `status.json` said `browser_checks_run: false`, yet the merged
`reports/phase-goal-fast_wall-iter-1-ui-test-results.md` recorded 7/7 PASS with real screenshots
(UT-02/UT-03) that the auditor and I both opened and confirmed. A QA "SKIP due to browser timeout"
is a superseded *attempt*, not the absence of browser evidence — trust the merged ui-test-results.md
+ evidence PNGs over a QA SKIP. Separately, `test_edge_report_tool_byte_identical_to_rest`
(`test_mcp_server.py`) was made order-coupled this iteration (fails in isolation on `assert 0 >= 1`,
passes in the canonical module run) — flagged loud, not a false-green, but a known future-cleanup.
**Applies to:** any iter reconciling a QA SKIP against merged browser results; any J-02+ iter that
next touches `test_mcp_server.py` (self-seed TC-6's own dataset).

## iter-2 — 2026-07-17T08:14:57Z

**Verdict:** CONTINUE
**Lesson:** iter-2 was the first `Frontend Present: no` iteration whose Required-still-passing set
(J-01, J-07) is entirely UI journeys — so the browser-qa step, and with it the golden-replay lane
that normally re-verifies that set, was SKIPPED (`ui-test-results.md` = SKIPPED,
`status.json` `browser_checks_run: false`). Those journeys' non-regression then rested ENTIRELY on
the byte-identity tests (TC-8 datasets REST+MCP, TC-14 edge-report integrity-500) plus the
zero-frontend git diff — i.e. the byte-identity test literally stands in for the skipped UI replay.
Takeaway: on any backend-only iter that touches an endpoint a passing UI journey reads, treat a
mechanically-proven byte-identity assertion as a *required* gate, not a nicety — it is the only
guardrail left for those UI journeys when replay does not run.
**Applies to:** any future `Frontend Present: no` iter that touches an endpoint or shared value a
`passing` browser journey depends on (J-03, J-05, J-06 all qualify — each accelerates a value the
`/structure` surfaces read).

## iter-3 — 2026-07-17T11:15:22Z

**Verdict:** CONTINUE
**Lesson:** For a byte-identical accelerator, "the equivalence test passes" is NOT by itself sufficient evidence of the critical "No divergent accelerator output" anti-goal — the auditor closed the gap by *mutation-probing* the memo (poisoning it to serve a stale level/tradability state), which flips the run from 1 trade to 0, proving TC-5..TC-8 genuinely bite rather than being vacuously satisfiable. An accelerator whose "byte-identity" test would still pass against a deliberately-broken accelerator is a false guardrail.
**Applies to:** any future accelerator iter under "No divergent accelerator output" — specifically J-05 (resumable/parallel sweep: cross-process/resumed byte-identity is the veto-class risk) and J-06 (durable setups scan cache); demand the determinism/equivalence test be shown non-vacuous (a deliberately-broken accelerator must fail it), not merely present-and-green.
