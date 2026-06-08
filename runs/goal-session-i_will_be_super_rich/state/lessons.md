# Goal Session i_will_be_super_rich — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

---

## iter-0 — 2026-06-04T00:20:39Z

**Verdict:** CONTINUE (baseline)
**Lesson:** Browser QA found that switching tickers via the **Watch** button does NOT stop the
previous backend watch — only the explicit **Stop** button tears a watch down, so re-submitting
SIM-BUYER→SIM-SELLER→… leaves every prior engine instance alive (each `…/state` still 200). Harmless
for the in-memory sim, but with the live provider this becomes a **real vendor WebSocket/connection
leak** every time a user switches symbols without pressing Stop.
**Applies to:** any iter wiring the live provider / watch lifecycle (J-12 live, J-15 stale-recover,
and the J-10 data-source selector) — make a new Watch (or a source/symbol switch) implicitly
`DELETE` the prior watch and close its socket.

## iter-1 — 2026-06-04T09:39:35Z

**Verdict:** CONTINUE
**Lesson:** A latent credential-name mismatch is waiting to break the first real-data wiring: the
stale `apps/backend/.env` uses `ALPACA_SECRET_KEY`, but the new adapter (`app/providers/adapters/alpaca.py`)
reads `ALPACA_API_SECRET` — and nothing loads `.env` at all (no dotenv loader; `start-backend.sh`
doesn't source it). It was harmless this iteration (verification was credentials-absent, so the gate
*should* report unavailable), but the moment J-11/J-12 add real creds, `real_data_available()` will
wrongly return False with valid keys present unless the env names are aligned to the adapter's
(`ALPACA_API_KEY` / `ALPACA_API_SECRET`) AND a loader/export is added.
**Applies to:** any iter wiring real Alpaca credentials or a real provider (J-11 historical, J-12 live,
J-13 symbol search) — align env-var names to `adapters/alpaca.py` and add a dotenv loader/export before
expecting the creds-present branch to work. Also: J-11+ "real fetch" needs a credentialed verification
path (gated run or a recorded real-vendor fixture — never synthesized data, per the no-fabrication
anti-goal); plan it before building.

## iter-2 — 2026-06-04T12:13:04Z

**Verdict:** CONTINUE
**Lesson:** A committed REAL captured Alpaca fixture (VCR-style, real epochs + prices, self-documented `note: REAL … not synthesized`) is what makes J-11 deterministic and offline-reproducible *in-loop* — reuse this capture-once pattern for every real-data journey rather than depending on live creds being present in QA. Two real-data gotchas surfaced and will recur: (1) the free **IEX** top-of-book is wide/noisy for high-priced names — AAPL honestly reads `unclear` because the spread gate is calibrated for tight tapes (correct, and out of scope to change since it would regress J-01–J-09), so any clean-state demo/fixture must use a **penny-spread** name (Ford → clean `bid_absorption`); (2) the historical window picker sends **naive** datetimes that the backend treats as **UTC**, so an operator must enter UTC times (15:00 UTC = 11:00 ET) — a market-local/tz picker is unbuilt.
**Applies to:** any iter wiring real-vendor data (J-12 live streaming / J-15 stale-recover) or authoring real-data fixtures/demos; anything choosing a symbol for a clean-state walkthrough.

## iter-3 — 2026-06-04T13:35:26Z

**Verdict:** CONTINUE
**Lesson:** The `qa` agent corrupted the harness `next dev` server on `:3650` by running `npm run build` against its **shared `.next`** (the documented "QA frontend build caution"), then a follow-on `git checkout app/page.tsx` **discarded the developer's uncommitted iter-3 `page.tsx` edits** (reconstructed verbatim from handoffs). This cascaded: the later `browser-qa-agent` saw `:3650` down and recorded all 15 UT cases SKIPPED — so this iteration had **two divergent browser-evidence sources** (qa PASS on an isolated `:3651` instance vs browser-qa SKIPPED), reconciled only by inspecting the actual screenshots + code state. Takeaway for the evaluator: a `browser-qa SKIPPED` is not automatically a failure — cross-check the `qa` agent's isolated-instance evidence and verify the working-tree code directly before concluding.
**Applies to:** any iteration with a frontend — QA must build in an isolated `.next` (never the harness's shared one) and must never `git checkout` a file carrying uncommitted iter edits; any evaluator reconciling a `browser-qa SKIPPED` against a `qa PASS`.

## iter-4 — 2026-06-04T15:50:19Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** Tearing down the Alpaca live socket must close the socket but deliberately MUST NOT call the SDK's `unsubscribe_trades/quotes()` from the generator `finally`: those run `asyncio.run_coroutine_threadsafe(...).result()`, which **deadlocks** when invoked from the event-loop thread. Closing the socket drops all subscriptions anyway, so `stream_live`'s teardown is a bounded graceful close only (`stop_ws()` → bounded wait → cancel → bounded `close()`), documented as load-bearing in `adapters/alpaca.py`. Separately: the in-loop proof for a live/operator-gated journey can opportunistically become *real* — iter-4's gated `test_live_integration.py` actually ran and passed because the US market happened to be open with creds present, giving J-12 genuine real-socket evidence beyond the planned hermetic fake (the fake stayed correctly out of the prod path).
**Applies to:** any future iter touching `app/providers/adapters/alpaca.py` `stream_live` / live-socket teardown, the `watch_with_async_provider` feeder, or adding a second vendor's live adapter; and any operator/gated journey whose real path may be exercisable when the evaluator runs during market hours.

## iter-5 — 2026-06-05T02:10:00Z

**Verdict:** CONTINUE
**Lesson:** The `ui-test-results.md` browser-QA file can be a **stale pre-build verify-only re-baseline** (it self-labels "no code changes", carries the OLD test count, and its target-journey screenshot shows the pre-fix state) even when the real build landed — the iter-3 divergent-evidence pattern recurring. For an engine-classification change whose authoritative proof is a committed real-vendor fixture replayed in-loop, the screenshot is NOT the pass evidence; re-run the suite and re-derive the metric from code. The load-bearing safety check for J-16 specifically is **"how many quote-decided prints did the tick test flip?" — it must be 0** (else J-04/J-05 absorption could be silently reclassified); the correct Lee-Ready carry is the last non-zero **price tick**, not the last **classified side**.
**Applies to:** any iter changing `app/engine/aggressor.py` or the side/tick-test logic; any evaluator reconciling a `ui-test-results.md` that may predate the build (check its self-described mode + test count vs `status.json`); any engine change where the authoritative proof is an in-loop fixture replay rather than a browser screenshot.

## iter-6 — 2026-06-05T03:25:00Z

**Verdict:** CONTINUE
**Lesson:** A purely-visual journey (chart renders / marker color / selector re-renders) cannot be scored `passing` from backend tests + code inspection alone — even when the data path and the production build are both independently proven correct. This iter, browser-qa SKIPPED (shared `:3650` returned HTTP 500: `Cannot find module './833.js'` — the iter-3 shared-`.next` corruption recurring), and the `qa` agent reported the chart tests as "PASS_SURFACE / browser automation did not complete" with a blank screenshot; that is a `partial`, not a pass. The evaluator could prove the `/history` data (live 5-scenario probe + 404/422/empty over the wire) and prove the source builds+serves cleanly in an **isolated** dist dir, but the environment had **no CDP-capable browser client** (no puppeteer/playwright/ws) and no auto-watch-on-load, so the populated canvas was never captured.
**Applies to:** any future iter whose target journey is fundamentally visual (charts, canvas, color-coded markers, animations) — require a real rendered screenshot of the populated state; AND any frontend iter — the shared harness `.next` on `:3650` has now corrupted browser-qa twice, so the next browser run MUST rebuild or fully bypass it (`NEXT_DIST_DIR` + `NEXT_PUBLIC_API_URL` → an isolated backend) before trusting (or skipping) the visual verification.

## iter-7 — 2026-06-05T03:40:00Z

**Verdict:** CONTINUE
**Lesson:** The `qa`-agent report and the `browser-qa-agent`'s `ui-test-results.md` can DISAGREE on the same visual journey, and the qa report can be the wrong one: this iter the qa report claimed chart-render PASS with screenshots `TC-01-chart-sim-buyer.png` / `TC-02-chart-sim-seller.png`, but those PNGs are actually the **idle "No ticker watched" placeholder** (Watch never clicked; TC-02's input is garbled "SIM-BUYERSIM-SELLER"). The real rendered-chart evidence was in the browser-qa-agent's `UT-13-before-pause-chart.png`. Always open the bytes of the named screenshot — a confident PASS row + a plausible filename is not evidence; the pixels are. (The good news: once a working frontend was available, J-17's 3-iteration render gap closed immediately.)
**Applies to:** any evaluator scoring a visual journey when both a `qa` report and a `browser-qa` `ui-test-results.md` exist — reconcile them by opening the actual screenshots, and prefer the browser-qa-agent's UT evidence; treat a chart/canvas screenshot that shows an idle/placeholder state as NO evidence regardless of the PASS label.

## iter-8 — 2026-06-05T05:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** When the shared :3650 .next is corrupted, the evaluator can manufacture the missing visual evidence itself rather than punting another iteration: build the working-tree source into an ISOLATED `NEXT_DIST_DIR` (e.g. `.next-eval-iter8`) wired to the already-running backend (`NEXT_PUBLIC_API_URL=http://localhost:8650`), `next start` it on a free port, and drive Chromium via Python Playwright (installed, browsers in ~/.cache/ms-playwright). Two gotchas burned time: (1) a pre-existing isolated `:3651` build (`/tmp/tapeology-fe-qa`) was STALE (pre-iter-8) — always grep the served chunks for the iter's new strings before trusting a running server; (2) the first chart screenshot tripped a naive "canvas exists + body mentions a state" heuristic while the pane was still empty/warming and the symbol dropdown overlapped it — gate the J-18 shot on the BACKEND `/history` actually having bars>=5, dismiss the dropdown (Escape + click), wait for the poll cadence, THEN screenshot and open the bytes. Remember to revert the `tsconfig.json`/`next-env.d.ts` edits `next build` injects and `rm -rf` the eval dist dir afterward.
**Applies to:** any evaluator facing a browser-qa SKIPPED/qa FAIL caused by the shared-`.next` corruption on a VISUAL target journey — you have the tools to capture real pixels in-loop; and any future frontend iteration that must verify a lightweight-charts canvas (poll `/history` for real bars first; a canvas element alone is not proof).

## iter-9 — 2026-06-06T03:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The qa-validation agent can emit a confident "PASS — screenshot shows pending state" table while writing 15 *byte-identical* placeholder PNGs (verify with `md5sum *.png | uniq -c -w32` — all 15 hashed to one value, and the file named `TC-01-pending-state.png` actually showed the idle "No ticker watched" screen). A fast-resolving state (the sim Watch returns 200 in <100ms) is genuinely hard to screenshot at the right instant — the reliable evaluator technique is to `page.route` the `POST /watch/` request with a `time.sleep` hold so the synchronous pending state is observable, and to assert on the DOM text (`Connecting to <SYMBOL>`), not just the pixels. For bounded-failure journeys (J-22/J-23), kill the isolated backend then click Watch and assert "not stuck on Connecting" + an explicit banner — far cleaner than trying to abort the WS via `page.route` (which only intercepts HTTP, not `ws://`, so frames still arrive and `gotFrame` defeats the test).
**Applies to:** any goal-mode iter whose target journeys are fast-resolving or failure-path UI states; any iter where browser-qa SKIPPED and the qa screenshots must be independently re-rendered. Always hash the evidence dir before trusting a PASS table.

## iter-10 — 2026-06-07T03:00:00Z

**Verdict:** CONTINUE
**Lesson:** To render a SNAPSHOT-BORNE lifecycle state (waiting/failed/live) in an isolated-stack browser check, the WebSocket must OPEN-AND-STAY-SILENT, not be aborted. useTapeStream (`apps/frontend/lib/useTapeStream.ts`) flips `connStatus` to `failed` on a WS onerror/early-onclose-before-first-frame, and `page.tsx` renders the J-23 PRE-snapshot StreamFailedState BEFORE it ever checks `snapshot.stream_status` — so a Playwright `route("**/stream**", abort)` (or just letting the WS fail to reach the mock backend) makes EVERY case render "Couldn't connect to the tape stream" and masks the real waiting/failed/live treatment. The fix: stand up a trivial raw-socket WS server that completes the RFC6455 handshake then sends no frame (so onopen fires, connStatus is not `failed`), and mock only the HTTP /summary|/features|/events via page.route. Playwright HTTP routes do NOT intercept WS, so the two coexist.
**Applies to:** any future iter verifying a snapshot-driven cockpit state (stream_status waiting/failed/live/stale/paused) on an isolated stack — and any iter touching the page.tsx render-priority order (pending -> connStatus failed -> snapshot failed -> snapshot waiting -> cockpit); if that order changes, re-derive which treatment wins before trusting a render.

## iter-11 — 2026-06-07T05:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A browser-qa "FAIL" can be a mis-specified TEST rather than a product defect — here
UT-02/UT-10 asserted symbol-search min-query ≥ 2, but the as-built backend `symbol_search_min_query`
(config.py:123) and frontend `SYMBOL_SEARCH_MIN_QUERY` (config.ts:34) both = 1 and MATCH exactly,
which is precisely what the spec mandated ("mirror the backend"); the journey only required "a
sensible minimum query length", never 2. The coherence-auditor had already flagged this exact pair
as an advisory WARN, and it resolved in the implementation's favor. Always trace a config-value FAIL
to the spec/contract and to BOTH sides of the mirror before treating it as a regression — a failing
assertion can encode the test author's assumption, not the requirement.
**Applies to:** any evaluator reconciling a browser-qa FAIL on a config/threshold value (min-query,
debounce, timeout ordering, large-print size) — check the spec wording and both the backend and
frontend constants for agreement before scoring it a defect; and any future iter touching the
symbol-search min-query (change both `symbol_search_min_query` and `SYMBOL_SEARCH_MIN_QUERY` together
and update UT-02/UT-10).

## iter-12 — 2026-06-09T00:30:00Z

**Verdict:** CONTINUE
**Lesson:** The dedicated browser-qa-agent run reported SKIPPED/0-of-16 (frontend not on :3650 at that moment) yet the qa-agent's own Chrome MCP pass produced real evidence PNGs and the qa.md narrated screenshots as if browser-qa had run — the two reports must be reconciled, never one trusted over the other. The load-bearing proof for a chart-axis journey is opening the PNG bytes: TC-05's axis genuinely reads '…01-2024 14:30 … 14:40' (a real clock face), which is what confirmed J-31, not the PASS label. Also: no `-audit.md` handoff was produced (status stopped at qa_complete) — full-depth iterations can finish without the audit step, so verify the gate artifacts you actually have rather than assuming the full pipeline ran.
**Applies to:** any iter whose target is a chart axis / crosshair / time-display surface, or any iter where browser-qa SKIPs but qa.md claims browser screenshots — open the evidence bytes and reconcile the two reports before scoring.
