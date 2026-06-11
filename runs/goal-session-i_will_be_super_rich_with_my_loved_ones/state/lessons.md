# Goal Session i_will_be_super_rich_with_my_loved_ones — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-10T14:56:28Z

**Verdict:** CONTINUE
**Lesson:** The "absence proof" screenshot `UT-J-38-J68-no-research-surfaces.png` is actually an ERR_CONNECTION_REFUSED page (dev server was down at capture) — absence claims must be evidenced by REST 404 probes with the server demonstrably up, or by file-tree inspection. Also: the QA report's summary counts (22 PASS/13 PARTIAL) contradicted its own table (23/12) — always recount from the table; and the `next dev` reloader child survives `pkill -f "next dev"`, so harness cleanup must kill by port (`fuser -k`).
**Applies to:** any iter recording journeys failing-by-absence (J-38–J-68 block); any browser-QA run that starts/stops the frontend dev server.

## iter-1 — 2026-06-10T15:54:30Z

**Verdict:** CONTINUE
**Lesson:** Screenshots of TRANSIENT scenario phases can miss the phase: `UT-J-68-sim-shift-buyer-control.png` was captured just after SIM-SHIFT's regime shift, so the state panel already reads Unclear even though the filename/claim is the buyer_control phase. The evidence still held because the event log (append-only transition messages), the chart's state markers, and the deterministic phase-sequence unit tests carry the sequence — capture those, or screenshot within the phase window. Related timing fact from the dev handoff: the feeder fast-forwards only warm-up, then paces by logical gaps, so phase 2 of SIM-SHIFT/SIM-REVERSAL takes ~real time (~60s logical) to appear live — browser QA must budget for it.
**Applies to:** any iter browser-verifying multi-phase scenarios (J-40, J-41, J-43, J-44, J-46, J-53 verdict-transition legs all replay SIM-SHIFT/SIM-REVERSAL); prefer event-log/timeline assertions over single state-panel screenshots for sequence claims.

## iter-2 — 2026-06-10T17:17:06Z

**Verdict:** CONTINUE
**Lesson:** A green QA verdict can silently hide total browser-verification failure: the QA agent ran `npm run build` against the live dev server's shared `.next` mid-pipeline, the dev frontend then 500'd ("Cannot find module './833.js'"), and ALL 17 browser tests + the demo became SKIPs while the QA report still read PASS (its own skip-tolerance rule) — so the iteration shipped a major new UI surface (ThesisStrip) with zero rendered-pixel evidence. Treat an all-SKIP browser report as "frontend unverified" (target journeys cannot flip to passing on it), and isolate QA builds from the dev server's dist dir (NEXT_DIST_DIR=.next-qa) or defer builds until after browser tests.
**Applies to:** every full/lean iteration with a frontend leg — the QA step must precondition-check the dev server AFTER any build it runs, and browser-qa-agent must hard-flag (not soft-skip) a dead frontend when the iteration's target journeys are UI journeys.

## iter-3 — 2026-06-10T18:18:14Z

**Verdict:** ESCALATE
**Lesson:** A non-empty evidence directory can still prove nothing about the target surface: iter-3's browser run was real (harness healthy, 0 skips, REST cross-checks pass) yet every thesis-strip screenshot was a viewport-top capture showing only the price chart — the strip sits BELOW the chart and was below the fold in all five strip-named PNGs, so the target surface has zero rendered-pixel proof after two consecutive iterations. Screenshot framing is a distinct failure mode from a dead harness: browser-qa must scroll the asserted element into view (or take a full-page capture) before every screenshot, and the evaluator must open the pixels, not trust the filename. Also: the report summary said "14/15 passed" while its table held 16 all-PASS rows, and the demo step skipped itself on a false "Frontend Present: no" — recount from tables and distrust step self-reports of frontend presence.
**Applies to:** every iteration asserting below-the-fold UI (thesis strip, panel grid, event log, future /journal and /studies pages) — require captures that visibly contain the asserted element; browser-qa-agent screenshot discipline; any evaluator flip of a UI journey.

## iter-4 — 2026-06-10T20:10:46Z

**Verdict:** CONTINUE
**Lesson:** `CREATE TABLE IF NOT EXISTS` schema changes silently no-op on the pre-existing journal DB, and the entire test stack (unit tests AND the QA-validation step) injects fresh temp DBs — so a missing migration (verdict_events lacked rule_first_true_ts/rule_first_true_price; store.py has a schema_version table but applies no versioned migrations) shipped through review + QA-PASS and 503'd every `POST /research/thesis` in browser QA. Any column/table change to `apps/backend/app/research/store.py` MUST ship a versioned migration AND at least one check against the persistent dev DB (or a committed old-schema DB fixture). Also: multi-row creation (insert_thesis → initial verdict event) must be one writer transaction — the partial failure orphaned an active thesis that 409-blocked the ticker. Separately, the binding evidence rule was violated a 4th time, now by the FAIL captures themselves (chart fragments, asserted error not in pixels) — browser-qa must scroll-into-view/full-page mechanically, and the closure auditor must open PNGs.
**Applies to:** any iter touching `apps/backend/app/research/store.py` schema or adding persisted columns; any iter whose QA passes on temp-DB injection alone; every browser-qa capture of below-the-fold surfaces (thesis strip, forms, event log)

## iter-5 — 2026-06-10T21:48:47Z

**Verdict:** CONTINUE
**Lesson:** Verdict-state screenshots are time-critical: a sim thesis auto-expires when its scenario stream ends, so a capture taken after the assertion (UT-04) shows the idle declare strip instead of the witnessed CONFIRMING chip — screenshot the strip AT the asserted verdict moment, before scenario end/teardown. Separately, the ui-test-designer silently dropped 4 of the spec's 10 mandated journey legs (J-42 confirm, J-43/SIM-SHIFT, J-45 latch, J-46) — a spec's named journey matrix must be diffed against the designed plan before execution. And the run engine halted at qa_complete for the second consecutive full iteration (status "complete" but next_action "audit"), so audit/ux-regression/closure never ran.
**Applies to:** any iter capturing live verdict/stance transitions on sim scenarios; any full-depth iter (verify the test plan covers every spec-mandated journey, and verify the audit/closure artifacts actually exist before trusting "complete"); the evaluator should keep opening PNGs while the closure gate is unreliable.

## iter-6 — 2026-06-11T09:55:00Z

**Verdict:** CONTINUE
**Lesson:** Browser QA ran against a uvicorn process started BEFORE the iteration's code was written (22:07 server vs 23:15 patches), so two correct on-disk fixes failed in pixels — the journal DB itself proved it (thesis bff5cff3 declared at 00:25 froze the OLD inverted `ask_absorption`-for-long params that no longer exist in `apps/backend/app/research/taxonomy.py`). Restart (or freshly start) the QA backend AFTER dev completes, and verify the running server's code identity with a cheap canary probe before any capture — e.g. `GET /research/taxonomy` must reflect the patched templates.
**Applies to:** every browser-qa run in every future iteration — make "server start time > newest patched-file mtime" (or a response-content canary) a mandatory pre-capture check, especially for backend-only iterations where no rebuild step forces a restart.

## iter-7 — 2026-06-11T01:40:00Z

**Verdict:** CONTINUE
**Lesson:** A direction-aware fix verified only on the ADVERSE tape can silently break the favorable tape: iter-6's `directional_impact` rewrite in `apps/backend/app/research/monitor.py::_evaluate_statement` checks the adverse-side cutoff FIRST (`sell_price_impact <= -0.02` for long) with no dominance weighing, so SIM-BUYER's minority sell flow (-0.06..-0.16) brands a CONFIRMING thesis's progress statement "violated" — directly under evidence saying "the tape confirms your thesis". The iter-6 acceptance rationale "old/new statement code coincide on the favorable tape" was wrong; only fresh-server pixels on BOTH tapes exposed it.
**Applies to:** any iter touching verdict/statement semantics in `apps/backend/app/research/monitor.py` or `verdict.py` — always demand four-quadrant proof (favorable + adverse tape × long + short), in pixels, never just the quadrant the defect was reported on.

## iter-8 — 2026-06-11T03:22:00Z

**Verdict:** CONTINUE
**Lesson:** When a spec names explicit numeric truth anchors, verify the committed tests actually exercise those values — the iter-8 dev handoff claimed the four-quadrant suite pinned "SIM-BUYER long (buy +0.42 vs sell −0.14) → met", but `test_directional_impact_long_favorable_is_met` uses sell_impact=0.0 (only-favorable, not both-material); the favorable-dominant both-material quadrant ended up proven only in pixels, leaving a unit-regression gap the reviewer caught and the evaluator confirmed by reading the test file.
**Applies to:** any iter whose spec lists named truth-anchor values for `apps/backend/app/research/` rule logic — the reviewer/evaluator must diff the anchor values against the actual test parameters, not trust the handoff's "proven by tests" claim.

## iter-9 — 2026-06-11T05:32:03Z

**Verdict:** CONTINUE
**Lesson:** The engine's `stream_status` string alone cannot distinguish a user Stop from natural stream exhaustion (both flip to `closed`), so the in-scope requirement `expired(watch_stopped)` vs `expired(stream_closed)` structurally forced an additive engine touch (`TapeEngine.set_stream_status(status, end_reason=None)` + `end_reason` property) even though the spec listed engine files as out of scope. The deviation was safe because it is lifecycle metadata never read by classification (observer signature unchanged, equivalence suite green) — but future specs that demand lifecycle-reason distinctions should name the engine status seam as the legitimate owner up front instead of blanket-excluding engine files.
**Applies to:** any iter needing new lifecycle/teardown reasons or status semantics (e.g. J-51 restart legs, J-64 stance freshness) — check whether the canonical status owner (tape_engine.py / watch_manager.py) must carry the new metadata before declaring engine files out of scope.

## iter-10 — 2026-06-11T07:40:26Z

**Verdict:** CONTINUE
**Lesson:** lightweight-charts does NOT extend the price-scale autoscale to include a price-line far outside the candle range — the declared Level line at 115.00 was invisible in the pre-cross capture (candles at ~106–109, scale topped ~110/112.50) even though geometry served it, and it only appeared in pixels once price approached. A "price-line visible" browser assertion must either declare prices within/near the visible candle range or accept REST-geometry + a later in-range frame as the pixel evidence (as iter-10's confirming/entry/closed frames did). Separately: `logical_ts` resets per watch, so the geometry segment rule had to discriminate pre/post-gap MARKS by `wall_ts` (monotonic across re-watches) while timeline rows are sliced positionally — any future feature placing per-watch events on the chart must use the same two-discriminator pattern.
**Applies to:** any iter asserting chart price-line/marker pixels (J-49 chip captures are strip-side, but J-53 distance-to-invalidation visuals, demo scripts, and any future chart overlay), and any feature mapping persisted research events onto a per-watch logical timeline.

## iter-11 — 2026-06-11T09:49:17Z

**Verdict:** CONTINUE
**Lesson:** Sim-calibrated research thresholds can sit razor-thin against the scenarios that must demo them: SIM-BUYER's favorable impact return is ~0.0033 at warm-up vs the 0.0040 chase threshold a few seconds later, so the J-49 "clean no-flags" frame measured 0.003956 — only ~1% under the threshold — and needed a REST polling loop to time the declare. Any change to SIM-BUYER pacing, the 30s primary window, or chase_return_threshold will silently flip which J-49 frames are reachable. Also confirmed: SIM-CHOP's unclear comes from mixed ratios, NOT a wide spread (~14.9bps < the 30bps gate), so wide_spread_illiquid is browser-undemonstrable on the current sims — only low_trade_speed fires (prompt declare on a fresh watch).
**Applies to:** any iter touching `apps/backend/app/config.py` research defaults, the sim scenario pacing, or any future browser leg that must reproduce a specific risk-flag combination (J-54/J-55/J-57 review surfaces re-rendering frozen flags should reuse iter-11's frames rather than re-stage them).

## iter-12 — 2026-06-11T11:50:46Z

**Verdict:** CONTINUE
**Lesson:** When a browser-qa run is continued after exhausting its tool budget, the rewritten report can desync from reality: iter-12's header said "11/11" while the table listed 15 tests, and UT-J49's no-regression rationale claimed "ThesisStrip.tsx untouched" when that file WAS in changed_files (the emoji→class chip cleanup) — so a spec-mandated pixel check (req 8, firing-flag chip) was silently skipped under a false premise. Evidence filenames also drifted (J-51-journal-filtered-expired.png shows the UNfiltered "Any status" view; the real filter proof is in ...-filter-expired-working.png).
**Applies to:** any iteration whose browser-qa run is budget-continued — QA must re-diff its "untouched, no regression possible" claims against status.json changed_files before writing them, and the evaluator must open ALL same-claim frames, not just the one cited. Next strip/J-49-touching iter owes a firing-flag chip pixel capture.

## iter-13 — 2026-06-11T14:05:14Z

**Verdict:** CONTINUE
**Lesson:** Statement statuses are LIVE-only: the monitor recomputes them per event for the active projection, but neither the thesis row nor the verdict_events rows persist a per-statement FINAL status — so the /journal/[id] page cannot render J-55's "statements with their final statuses" clause without violating no-recompute-at-read, and the iteration shipped a deferral note instead. Any value a review surface must show "frozen" needs persisting at its defining moment (the execution-checks pattern); iter-14 must persist final statement statuses at terminal resolution alongside the J-56 grades.
**Applies to:** iter-14 (J-55 completion + J-56/J-57) and any future iter adding review/detail fields — check FIRST whether the value is persisted, not just whether the live projection shows it.

## iter-14 — 2026-06-11T16:31:36Z

**Verdict:** CONTINUE
**Lesson:** Browser-qa cited three evidence PNGs that are blank dark frames (UT-J57-other-selected.png, UT-J57-tags-and-note-filled.png, UT-J57-after-save.png — all exactly 6,303 bytes, captured during transient/mid-interaction UI states). The journey still passed because the end states had real full-page captures and the validation matrix was REST-verified, but a capture taken mid-render can silently produce an empty frame. Browser-qa should sanity-check capture file size / non-uniform pixels before listing a PNG as evidence, and prefer full-page captures over element-timed shots for transient states.
**Applies to:** every future browser-qa run that captures transient UI states (disabled buttons, inline validation, mid-save spinners) — and evaluators should keep opening pixels rather than trusting the evidence column.
