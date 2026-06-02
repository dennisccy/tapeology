# Goal Session i_will_be_rich — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-1 — 2026-06-02T20:50:21Z

**Verdict:** CONTINUE
**Lesson:** A corrupted Next.js dev `.next` cache made the managed frontend dev server return HTTP 500, so browser-qa-agent SKIPPED all 18 UI tests — yet the iteration still reached `status: complete` / QA PASS on the strength of backend tests + a clean production build. That combination is a trap: "backend PASS + build clean" is NOT evidence that the UI journeys (J-01/J-02/J-08) work, and they were left entirely browser-unverified. A full vertical-slice iteration whose target journeys are user-visible MUST get at least one real browser pass with screenshots before it counts as delivering them; an all-skipped browser run is a hard signal to do a verification-closure iteration, not to advance to the next feature.
**Applies to:** Any iteration with `Frontend Present: yes` where browser QA reports SKIPPED (frontend HTTP 500 / not serving). Precondition for browser QA on Next.js: `rm -rf apps/frontend/.next` and restart the dev server with `NEXT_PUBLIC_API_URL` set before driving the browser. Do not let a backend-PASS stand in for browser verification of UI journeys.
