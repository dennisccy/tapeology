# Goal Iteration 29 — Market-hours live-feed close-out: J-15 stale→recover + J-67 live-IEX pixels

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 29
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-15, J-67
- **Required-still-passing journeys:** J-01, J-02, J-08, J-11, J-12, J-14, J-16, J-18, J-22, J-23, J-25, J-27, J-32, J-68
- **Anti-goal reminders:**
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit: a provider gap/feed lull → `stale`; an unknown/untradable symbol → an explicit error; an empty historical window → explicit no-data; a live watch while the market is closed → explicit closed (with the next open); missing credentials → explicit "unavailable". Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **Honesty stamps / feed labeling.** Live surfaces MUST label the IEX basis wherever SIP-derived research is shown nearby; the feed-per-mode seam stays config-owned so a SIP-entitled operator can upgrade live with one config value. No aggregate pools SIP with IEX rows. *(critical)*
  - **No execution path.** No order/broker/trading-API surface anywhere. *(critical)*

## GOAL

Close the two remaining market-hours-gated legs — a real live IEX feed visibly flipping `live → stale → live` across a natural feed lull (J-15) and the live-cockpit IEX feed-basis badge + disclosure pixels plus a live-declared `iex`-stamped journal row (J-67 live leg) — so the last `unknown`/deferred Must-have evidence is captured and J-68's "all J-01–J-37 green" sentinel clause closes, making GOAL_ACHIEVED reachable.

## BACKGROUND

Every Must-have journey is `passing`/`already_passing` except J-15 (`unknown`) and J-67's live-IEX **pixel** leg (J-67 is `passing` on its non-live SIP feed-basis evidence; only its live-declared/live-badge pixels are deferred). Iterations 26–28 repeatedly scheduled these for "the Monday market-hours pass (next US open 15-06-2026 14:30 UTC+01:00)" because both require a real live socket: the engine only auto-flips `connecting→live`; the feeder's stale watchdog (`watch_manager.py`, `config.stale_gap_seconds = 10.0`) owns the `live→stale` flip on a real delivery gap and the `stale→live` recovery — there is no way to fabricate that flip without violating the no-fabricated-data anti-goal. **It is now Tuesday 2026-06-16, ~14:00 ET — the US regular session is OPEN, and `apps/backend/.env` carries `ALPACA_API_KEY`/`ALPACA_API_SECRET`** (the same credentialed path iter-27 used for SIP historical), so the live legs are reachable this iteration. This is a verification + evidence-capture pass: NO application source change is expected (app source is byte-identical to HEAD going in; the stale seam, FeedBasisBadge, feed_basis mapping, and the gated `test_live_integration.py` all already exist). **Depth is FULL** per the iter-28 evaluator's standing escalation clause: J-15 is the single `unknown` gate to GOAL_ACHIEVED and a genuine live stale/recover is hard to capture in a bounded browser session, so this iteration must back the browser legs with the operator-gated credentialed integration run (`TAPEOLOGY_LIVE_INTEGRATION=1`) and run the full pipeline's audit + ux-regression scrutiny on the final gate.

## IN SCOPE

### Backend
- [ ] No production code change expected. This is verification/evidence only — app source must stay byte-identical to HEAD (J-68). If a GENUINE live-feed defect is surfaced (e.g. the stale watchdog mis-times, the recovery flip drops, or the feed-basis stamp is wrong on a real IEX watch), fix it in place on the existing owner module (`apps/backend/app/watch_manager.py` for the stale seam; `apps/backend/app/research/feed_basis.py` / `apps/backend/app/research/store.py` stamp for the feed label) and re-pin — no new module, no new endpoint, no new value.

### Frontend (if applicable)
- [ ] No production code change expected. The live status indicator (reads canonical row-6 `stream_status`: connecting | live | stale | paused | closed) and the `FeedBasisBadge` (reads canonical row-29 current-watch feed basis) already render. If a genuine UI defect is surfaced on a real live feed (e.g. the badge does not render over a live IEX watch, or `stale` is not visibly distinct from `live`), fix it in place on the existing component — no new surface.

### New user-facing capability
None — verification only. The user can already watch a live symbol, see the status flip to `stale` on a lull and recover, and read the live IEX feed-basis badge + disclosure; this iteration proves it in pixels on a real feed.

### New information displayed
None. Every value read is already in the Data Contract and served from its single canonical endpoint: `stream_status` (row 6, `GET /tape/{t}/summary` + WS), the feed-basis badge value (row 29, additive metadata on the row-6 snapshot projection), the live-declared thesis row's `data_feed` stamp (row 26, `GET /research/journal`).

### New user actions
None.

### UI surface changes
None — no new pages, panels, or controls. The `/` cockpit status area and the `/journal` rows are exercised on a real live feed; the surfaces themselves are unchanged.

### Product surface delta
None structurally. The product behaves identically; this pass captures the live-feed evidence that has been market-hours-deferred since iter-24.

### Blueprint conformance
No new surfaces. Both legs live at already-registered homes: J-15 at `/` Cockpit (the status indicator, row 6); J-67's live badge at the `/` cockpit status area (row 29, registered iter-24) and the live-declared row at `/journal` (row 21/26). The blueprint gains only an additive iter-29 verification build-out note (no Data Contract row added/changed, no IA/nav change).

### Data-contract additions
None. No NEW displayed value. Every value is read verbatim from its registered canonical source: row 6 (`stream_status`), row 29 (current-watch feed basis), row 26 (`data_feed` stamp on the live-declared journal row), row 1–5 (the live cockpit panels). No second computation, no second endpoint, no new route — the coherence-auditor must confirm zero drift.

## OUT OF SCOPE

- Any new feature, page, endpoint, control, config key, or schema change. If nothing genuinely broken is found on the live feed, the application diff is empty (the desired J-68-preserving outcome).
- The J-29 `<3s` near-instant re-watch cache fast-path (ruled a soft/P2 aspiration in iter-28; J-29 is already `passing` on its hard clauses). Do NOT build a cache/pre-warm fast-path — it would risk the byte-identity/observer-equivalence discipline to chase a non-binding aspiration.
- Re-litigating any already-`passing` journey beyond the Required-still-passing spot-checks below.
- Any artificial inducement of the stale state that fabricates or suppresses real feed events (e.g. dropping the socket to simulate a gap is acceptable as an honest disconnect, but injecting fake quiet by discarding real prints is not). The natural IEX delivery cadence on a moderately-quiet liquid symbol already produces gaps >`stale_gap_seconds` (10s) — observe the genuine flip; do not manufacture it.

## DEFINITION OF DONE

- [ ] **J-15** flips `unknown → passing`: a real Live watch shows the status indicator at `live`, then visibly at `stale` across a genuine feed lull (no fabricated trades during the gap — recent-trades count does not advance while `stale`), then recovering to `live` when prints resume. Captured in pixels (a still that visibly contains the `stale` indicator) AND backed by the operator-gated credentialed integration run.
- [ ] **J-67 live leg** is captured: the live IEX cockpit renders the `FeedBasisBadge` reading the `iex` basis with the disclosure line ("live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ"), and a live-declared thesis produces a `/journal` row stamped `data_feed = iex` (verifying no SIP/IEX pooling). J-67 stays `passing`, now with its live pixel evidence complete.
- [ ] **The operator-gated credentialed live-socket integration run** is executed: `TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest apps/backend/tests/test_live_integration.py -v -s` against a real Alpaca IEX socket during market hours, asserting `stream_status == "live"`, `event_count > 0`, real bid/ask, a valid tape state, and the correct live scenario descriptor. (Prefer a tight-spread liquid name per the test's own guidance — `TAPEOLOGY_LIVE_SYMBOL=F` default; a high-priced name on the wide free IEX top-of-book may honestly read `unclear`, which is correct, not a failure.)
- [ ] Required-still-passing journeys remain green (spot-check: J-01/J-02/J-08 sim cockpit; J-11/J-16/J-18 historical real data; J-14 honest-failure states; J-23 explicit failure panel; J-68 sentinel).
- [ ] **No anti-goal violation:** during the `stale` lull NO trade/quote/price/state is fabricated (the no-fabricated-data anti-goal IS the heart of J-15); the live IEX basis is explicitly labeled (feed-labeling anti-goal); no aggregate pools SIP with IEX; no order/broker surface appears.
- [ ] **J-68 byte-identity holds:** verify with a LIVE `git status --porcelain apps/` (empty) and `git diff --stat HEAD -- apps/backend/ apps/frontend/` (empty) — NOT the prompt's pre-baked git-status block (iter-28 lesson: the start-of-session snapshot can be stale). If a genuine defect required a fix, J-68's byte-identity clause is re-evaluated against the justified, re-pinned change, with observer-equivalence (`test_observer_equivalence.py`) re-run green.
- [ ] Unit tests pass; backend suite green with zero re-pins (no application logic changed unless a real defect was fixed).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-dev.md`.

## TESTING REQUIREMENTS

- **Browser:**
  - **J-15** — Live mode, real liquid symbol (e.g. `F` or `AAPL`), watch during market hours: capture (a) the `live` status, (b) a held/await-stabilized still that VISIBLY contains the `stale` indicator across a real lull with the recent-trades count NOT advancing during the gap, and (c) the recovery back to `live`. The `stale` indicator must be distinct from `live` in the same status area.
  - **J-67** — Live mode cockpit: capture the `FeedBasisBadge` reading `iex` with the IEX-vs-SIP disclosure line in the viewport; then declare a live thesis and capture the resulting `/journal` row stamped `data_feed = iex`.
  - **Required-still-passing spot-checks** — J-01/J-02/J-08 (SIM-BUYER cockpit + REST==UI), J-11/J-16/J-18 (credentialed SIP historical), J-14 (an honest-failure edge, e.g. unknown symbol → "not a tradable symbol"), J-23 (explicit failure panel still visible), J-68 (no-thesis cockpit unchanged: full panel grid + idle thesis strip + sound toggle render undisplaced).
- **Unit/integration:**
  - The operator-gated `apps/backend/tests/test_live_integration.py` MUST be run with `TAPEOLOGY_LIVE_INTEGRATION=1` against the real socket during market hours (this is the binding non-hermetic proof per `.claude/core.md` External Integration Testing — the hermetic suite alone is NOT sufficient evidence the real live pipeline works).
  - The full backend suite must pass with exit 0 and zero re-pins (verify via exit code or without an extra `-q` — the backend `addopts = "-q"` double-quiets and suppresses the count line; iter-17 lesson).
  - `test_observer_equivalence.py` re-run green (engine byte-identical with/without research observers) — J-68's automated clause.
  - The existing `stale_gap_seconds` watchdog behavior is already unit-covered; do not duplicate it. The live run is the missing real-socket evidence, not a new unit test.
- **Error cases:**
  - During the `stale` lull, assert the engine fabricates NO trade (recent-trades count frozen while `stale`; no synthesized catch-up on resume — the feeder discards anything queued during a pause/gap and rejoins CURRENT real data).
  - A live watch while the market were closed must still resolve to the explicit "market is closed" panel (J-14) — but the market is OPEN this iteration, so the positive live path is the focus.
  - An unknown symbol in Live mode still returns "not a tradable symbol" (J-14 carry).

## NOTES

- **Capture discipline (binding lessons):**
  - **iter-27 / iter-22 / iter-14:** a transient state needs the asserted element VISIBLE in a still capture, not just an `await_text` DOM hit. The `stale` indicator is transient (it clears on the next print, which on a liquid IEX name can arrive within seconds). Hold/await-stabilize the capture at the moment `stale` is on screen, OR watch a quieter symbol / off-peak minute where lulls exceed 10s comfortably. Prefer full-page captures over element-timed shots for the transient state. Run `md5sum` over the evidence dir before citing — iter-22 caught 5 byte-identical idle frames; iter-14 caught blank 6,303-byte transient frames.
  - **iter-24:** "browser-verifiable" is not "verifiable any time" — the live cockpit's honest-absence design means NO feed badge renders over a closed market. The market is OPEN this iteration (Tuesday 14:00 ET), so the live badge + status flips ARE reachable; do not defer again.
  - **iter-19:** for a transient race, designate the REST/DOM fallback as the PRIMARY evidence up front. Here, `GET /tape/{t}/summary` (re-exposed by WS) carries the canonical `stream_status` — poll it to confirm the `stale`→`live` sequence as the primary proof, with the pixel as the visible corroboration. The credentialed integration run is the authoritative pipeline proof.
  - **iter-2 / iter-18:** do NOT run `npm run build` against the live dev server's shared `.next` before browser QA — it corrupts `.next` and silently downgrades every browser test to SKIP on exactly a UI-evidence iteration. Run any build with an isolated dist dir or AFTER browser QA; re-probe the frontend with a fresh-server canary before declaring any SKIP unavoidable.
  - **iter-6:** start/restart the QA backend AFTER any change and verify server code identity with a cheap canary probe before capture. For this iteration the backend must be (re)started with `apps/backend/.env` loaded so the live credentials are in `os.environ` (the adapter reads creds from the environment only).
  - **iter-28:** verify J-68 byte-identity with a LIVE `git status --porcelain apps/` + `git diff --stat HEAD -- apps/`, never the prompt's pre-baked git-status block.
- **Escalation:** depth is FULL because J-15 is the sole `unknown` gate to GOAL_ACHIEVED and a live stale/recover is hard to reproduce in a bounded browser session — the full pipeline's gated credentialed integration run is the robust authoritative proof, and audit + ux-regression add scrutiny on the final gate. If, despite open market hours and configured credentials, the real socket cannot be reached (e.g. credentials invalid, vendor outage, or an unexpectedly hyperactive feed never lulls past 10s within a bounded session): record the gated integration run's outcome honestly, capture whatever live evidence is reachable, and let the evaluator decide whether J-15 holds `unknown` (scheduled, not stalled) or escalates further — do NOT fabricate the stale flip.
- After this iteration's two legs land, every Must-have journey is `passing`/`already_passing` and J-68's "all J-01–J-37 green" clause closes — the evaluator should then consider GOAL_ACHIEVED.
