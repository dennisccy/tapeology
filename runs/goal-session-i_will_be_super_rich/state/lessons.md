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
