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

## iter-2 — 2026-06-02T22:06:18Z

**Verdict:** CONTINUE
**Lesson:** A color-semantics defect can be invisible to a "looks green" visual QA pass yet hard-confirmed by computed-style measurement — and the two disagreed here. The `qa.md` report PASSed claiming "emerald=buy confirmed" (it saw the working static `text-emerald-300` Bid and the green Live dot), while `browser-qa-agent` correctly FAILed: `.text-emerald-400` and `.bg-emerald-500` are absent from the served Tailwind bundle because they appear ONLY as dynamic return strings in `lib/format.ts` (`stateColor`/`sideColor`/`impactColor`/`stateBarColor`), so Tailwind's content scanner never emits them — the headline state color, confidence-bar fill, BUY rows, and positive impacts render slate/transparent. The trap is general: any Tailwind class produced only by runtime string-building (never a static `className`) is silently dropped from the build. Verify color/style assertions with `getComputedStyle` + a stylesheet-rule probe, not a screenshot glance; and crucially the FIRST state browser-verified (buyer→emerald) does NOT prove the others — `bg-rose-500` (J-03 bar) and `text-amber-400`/`bg-amber-500` (J-04/J-05 absorption, J-06 unclear) share the same dynamic-only pattern and are latent-broken until safelisted.
**Applies to:** Any iteration touching `apps/frontend` color/state styling, especially when a class is chosen at runtime (`lib/format.ts` and any dynamic `className`). Before building J-03/J-04/J-05/J-06, ensure the Tailwind safelist (or static references) covers every dynamically-returned color class. When an evaluator sees a QA `PASS` and a browser-qa `FAIL` disagree on a visual property, trust the computed-style/stylesheet evidence over the visual claim.

## iter-3 — 2026-06-02T22:52:33Z

**Verdict:** CONTINUE
**Lesson:** Sharpening of the iter-2 "measure color, don't eyeball" lesson: a Tailwind color probe MUST match the BASE selector (`.text-emerald-400{` / `.bg-emerald-500{`) and explicitly EXCLUDE variant forms (`.hover\:bg-emerald-500:hover{`, `focus:`, etc.). In iter-3 `bg-emerald-500` existed in the OLD bundle only as its `hover:` variant — a naive `grep bg-emerald-500` would have returned the exact false PASS that the iter-2 screenshot glance gave; the base-selector probe correctly reported MISSING. So presence-of-substring is not presence-of-base-utility. Root-cause fix that worked: add `./lib/**/*.{ts,tsx}` to the tailwind `content` globs (the dynamic color strings live in `lib/format.ts`, which was unscanned) — preferred over a safelist because it is self-documenting and robust to incidental static usage elsewhere.
**Applies to:** any iter verifying dynamic/runtime-built Tailwind classes — immediately J-03 (rose `bg-rose-500` confidence bar, first on-screen render), J-04/J-05/J-06 (amber `text-amber-400`/`bg-amber-500` absorption/unclear). The base utilities are now in the bundle (latent-class guard passed), but each new state's first on-screen render must still be confirmed with the base-selector + getComputedStyle probe, never a `grep`-substring or visual glance.

## iter-4 — 2026-06-03T00:27:11Z

**Verdict:** CONTINUE
**Lesson:** A journey-history "notes" claim that a path is "already built + unit-proven" can be flat wrong and propagate forward. The iter-3 evaluator (this agent) wrote that J-03's seller backend was already wired in `simulated.py` and covered by tests, and recommended **lean**; the iter-4 decomposer's direct code inspection found the opposite — `classifier.py` had only buyer_control+unclear, `simulated.py` had only `_buyer_control_stream()`, and SIM-SELLER emitted zero events — so it correctly overrode to **full** for net-new, safety-critical (price-impact-guard) classifier work. A lean browser-verify of a non-existent backend would have produced an all-honest-unclear SIM-SELLER and a confusing "why won't it resolve" loop.
**Applies to:** Any iteration whose depth/effort decision rests on a prior evaluator's or journey-history's assertion that code "already exists" — the decomposer (and evaluator) MUST grep/read the actual engine/provider/config files to confirm the claimed branch, scenario stream, and thresholds are present before sizing the iteration as a thin verify pass. Do not trust forward-carried "already built" notes for classifier/provider state paths.
