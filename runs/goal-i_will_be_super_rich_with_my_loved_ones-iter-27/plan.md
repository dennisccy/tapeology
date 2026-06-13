# goal-i_will_be_super_rich_with_my_loved_ones-iter-27 Execution Plan

> **Iteration type: VERIFICATION / EVIDENCE-CAPTURE ONLY.** No new product capability,
> no new endpoint, no new component, no new config key. Backend + frontend code is
> expected **byte-identical** at the end (J-68 byte-identity sentinel) unless a genuine
> real-data defect surfaces during verification — in which case a minimal, config-owned,
> re-pinned fix is scoped in place on an existing surface. Today is Sat 2026-06-13; the US
> market is CLOSED until **Mon 15-06-2026 14:30 UTC+01:00**, so only the off-hours-verifiable
> legs are in scope. Live-only legs (J-15, J-67 live-IEX pixels) are explicitly DEFERRED to a
> Monday iteration — their absence is scheduled, not a stall.

## What to Build
- **Nothing new.** This iteration produces *evidence*, not capability. Re-exercise the
  already-shipped real-data flows end-to-end and capture positive pass evidence sufficient
  for the evaluator to flip the target journeys from `partial` to `passing`.
- **Re-run the full backend suite** and confirm the anchor suites are green, citing exact
  pass/skip counts by suite name in the dev handoff (expect 848 passed / 1 skipped, exit 0,
  zero re-pins, no `apps/backend/` diff):
  - J-11: `test_historical_provider.py`
  - J-16: `test_aggressor.py`
  - J-18: `test_history.py` + `test_history_api.py`
  - J-22 / J-28-anchor: `test_vendor_timeout.py` + `test_vendor_responsiveness.py`
    (confirm the backend timeout is enforced at the **vendor-call boundary**, not just an
    async wrapper, and is **shorter than the frontend client timeout**)
  - J-23 / J-27: `test_stream_lifecycle.py`
  - J-29: `test_progressive_fetch.py` + `test_chunked_fetch.py`
  - J-32: `test_speed_api.py`
  - J-36 / J-37 regression: the committed SIP real-data fixtures
- **Browser-capture the credentialed historical-replay legs** (J-11/J-16/J-18/J-20/J-29/J-32):
  a credentialed Historical replay of a real liquid symbol (AAPL and/or TSLA) over a known
  past intraday RTH window, exercised in the browser end-to-end. Each capture MUST visibly
  contain the asserted element (recent-trades side column with `unknown` far lower than
  before; candlestick chart matching `…/history` at each bar size with markers at transitions;
  picker local-zone label + quick-picks; busy window loads within the configured bound +
  near-instant re-watch; in-progress 1×→10× speed change continues from current position with
  no re-Watch / re-fetch). **If credentials are unavailable or the date-entry input cannot be
  driven, follow the documented fallbacks** (see Risks).
- **Browser-capture the honest-failure / edge-case legs:**
  - J-14: closed-market panel ("market is closed" + next open 15-06-2026 14:30 UTC+01:00),
    unknown-symbol ("not a tradable symbol"), empty-window ("no data for that window") — three
    distinct honest states, never a fabricated cockpit.
  - J-22: a slow/non-resolving request resolving to a distinct timeout/unreachable error within
    the client-side bound.
  - J-23: backend killed mid-watch surfacing explicit "couldn't connect to the tape stream"
    within bounds (no infinite spinner, no swallowed rejection).
  - J-27: no-first-event / feeder-failure watch resolving to an explicit
    `stale`/`closed`/no-data/error state owned by `stream_status` (never a fabricated `live`,
    never stuck `connecting`).
- **Assert anti-goals on every honest-failure capture:** no trades/quotes/prices/tape-state
  synthesized (no fabricated `live` over an empty tape); no trading advice; single-source-of-truth
  (chart + cockpit read the registered canonical endpoints `…/history`, `…/state`, `…/features`,
  `…/summary` verbatim — no UI-side recomputation of side/state/price/time); no tape persistence.

## Agents Required
- backend-data: no -- no backend code change planned. Backend work is limited to **running the
  full suite** and citing per-suite pass counts in the handoff. The dev agent owns this run.
  (A genuine real-data defect surfaced during verification escalates to a minimal, config-owned,
  re-pinned fix here — but no fix is planned.)
- frontend-ux: no -- no frontend code change planned (byte-identical). A genuine UI defect
  (e.g. an honest-state message that does not render) would be fixed in place on the existing
  error-banner / failure-panel / honest-status-dot surface, reusing backend taxonomy copy — no
  new surface, no hardcoded copy.
- developer: yes -- run the backend suite, cite anchor-suite counts, drive the credentialed
  historical `POST /watch/{ticker}` REST path if needed to substitute for the date input, and
  write the per-leg honesty-stamped dev handoff. Implements a fix ONLY if a defect surfaces.
- browser-qa-agent (pipeline step): yes -- this is the gating step. Owns all UI captures.

## Frontend Present
yes

## Files to Create/Modify
- `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-27-dev.md` -- dev handoff:
  per-leg verification result (credentialed-historical / REST / fixture), exact suite pass/skip
  counts, and every deferred live leg with its gating reason + the Monday open time. An
  "operator-gated" note is INSUFFICIENT for any leg satisfiable off-hours.
- **No source files are expected to change.** If a defect fix is required, the dev handoff must
  name the exact file(s), justify the change as a genuine real-data defect, and re-prove
  J-01–J-09 sims + classifier suite + J-36/J-37 fixtures stay green.

## UI Evolution (required if Frontend Present: yes)
- New user-facing capability: **None.** Verification only — the product experience is unchanged.
- New information displayed: **None.**
- New user actions: **None.**
- UI surface changes: **None planned.** A genuine UI defect surfaced during verification would
  be fixed in place on an existing surface (error banner / failure panel / honest status dot).
- Navigation changes: **none.**

## Visual Requirements (required if Frontend Present: yes)
- Component patterns: existing cockpit panels only — historical mode controls (source selector,
  symbol search, dd-MM-yyyy date input, time-window picker + quick-picks, replay-speed control),
  candlestick chart + tape-state markers, recent-trades list (side column), tape-state +
  confidence panel, honest-state panels (market-closed / unknown-symbol / empty-window), error
  banner, stream-status dot + feed-basis badge. **No new component.**
- Layout: the single `/` Cockpit, unchanged (chart above the panel grid; honest-failure surfaces
  in place). One ticker at a time.
- Key visual effects: existing dark instrument-panel palette — green = buy/positive, red =
  sell/negative, amber = absorption/unclear; mono numerics. The verdict/stance/status-dot
  semantics are unchanged. No new effect.
- States to handle (capture as evidence, not as new code): populated-historical (loading →
  populated within the configured bound), market-closed, unknown-symbol, empty-window,
  vendor-timeout error, backend-killed-mid-watch failure, no-first-event stale/closed. Each
  capture must visibly contain the asserted element (lesson iter-3 line 33).

## Key Test Scenarios
- **Backend suite green, zero re-pins:** full suite 848 passed / 1 skipped, exit 0; each anchor
  suite cited by name + count; `apps/backend/` diff is empty (J-68 byte-identity holds).
- **J-11/J-16/J-18/J-20/J-29/J-32 (browser, credentialed historical AAPL/TSLA, past RTH window
  e.g. a recent trading day 14:30–14:40 BST = 09:30–09:40 ET):** cockpit panels populate with
  real values; recent-trades shows resolved buy/sell sides with `unknown` fraction far lower
  than the quote-only baseline; chart matches `…/history` at each bar size with markers at
  transitions; picker shows local-zone label + quick-picks and the fetched window equals the
  selected local window; busy window loads within the configured bound and re-watch is
  near-instant; an in-progress 1×→10× speed change continues from current position with no
  re-Watch / re-fetch. Each with a capture visibly containing the asserted element + REST/UI
  agreement where acceptance calls for it.
- **J-14 (three distinct honest states):** closed-market panel ("market is closed" + next open
  15-06-2026 14:30 UTC+01:00), unknown-symbol ("not a tradable symbol"), empty-window ("no data
  for that window") — each a separate capture, never a fabricated cockpit. (No-credentials leg
  noted honestly as covered by the provider-unavailable path / unit evidence, not faked — see
  Risks; keys may in fact be incomplete, which makes this leg directly exercisable.)
- **J-22:** slow/non-resolving request → distinct timeout/unreachable error within the
  client-side bound (backend bound < frontend bound), anchored by `test_vendor_timeout.py` +
  `test_vendor_responsiveness.py`.
- **J-23:** backend killed mid-watch → explicit "couldn't connect to the tape stream" within
  bounds (no infinite spinner), anchored by `test_stream_lifecycle.py`.
- **J-27:** no-first-event / feeder-failure → explicit `stale`/`closed`/no-data/error state owned
  by `stream_status` (never fabricated `live`, never stuck `connecting`), anchored by
  `test_stream_lifecycle.py`.
- **Required-still-passing regression:** J-01, J-02, J-08, J-10, J-17, J-19, J-31, J-35, J-36,
  J-37, J-38, J-65, J-66, J-67, J-68 remain green. J-67 stays `passing` (live pixel leg deferred,
  NOT failed). The iter-26 always-rendered sound toggle is still an additive cue-area surface on
  the no-thesis cockpit (J-68 / J-66 sentinel).
- **Pre-capture hygiene (MANDATORY, lessons line 51/123/27):** before ANY browser capture,
  confirm the frontend dev server is live AND its served bundle post-dates any build this
  pipeline ran (fresh-server / content canary). If the target frontend is dead, browser-qa-agent
  must **hard-flag**, not soft-skip. Re-probe; "frontend was up earlier" is not evidence.

## Risks / Open Questions
*(Goal mode — no user questions asked. Assumptions recorded here.)*

1. **CREDENTIAL GAP — load-bearing, highest risk.** `apps/backend/.env` currently contains only
   `ALPACA_API_KEY` (27 chars, non-empty); **`ALPACA_API_SECRET` is absent**. The Alpaca adapter
   (`app/providers/adapters/alpaca.py:188`) returns `has_credentials() == True` **only if BOTH**
   `ALPACA_API_KEY` and `ALPACA_API_SECRET` are set, and `app/main.py` loads `.env` at startup
   via `app/env.py`. **With the secret missing, every real mode returns the explicit "provider
   unavailable" honest state — NOT real historical data.** The credentialed-historical legs
   (J-11/J-16/J-18/J-20/J-29/J-32) cannot capture real-value pixels in this state.
   - **Assumption / first action for the dev + browser-qa agents:** before attempting any
     credentialed-historical capture, probe `has_credentials` (e.g. via `GET /market/clock` or a
     known-symbol historical `POST /watch`). **If both creds are genuinely present** (operator
     may add the secret out-of-band before the pipeline runs), proceed with the live credentialed
     historical replay. **If the secret is missing**, do NOT fabricate or mark the legs passing on
     a unit test alone. Instead: (a) capture the credentialed-historical legs via the committed
     **SIP real-data fixtures** (`tests/fixtures/alpaca/*_sip.json`, e.g.
     `PG_20260609_170000_171000_sip.json` / `GME_..._sip.json`) replayed through the same engine +
     the same `…/history` projection + the same cockpit pixels (the J-36/J-37 fixture path — real
     vendor bytes, deterministic, no live feed), and (b) document the credential gap honestly in
     the handoff as the reason the *live-credentialed* path was substituted by the fixture path.
     This keeps the iteration honest (real vendor data, no fabrication) and is explicitly the
     spec's sanctioned substitution model. The browser-qa-agent must state which path each leg
     used. **Flag this credential state explicitly in the dev handoff regardless.**
2. **Date-entry harness limitation (iter-0 known).** The historical date is entered via the
   custom `dd-MM-yyyy` text input (J-35). If the browser harness cannot drive that input
   reliably, drive the equivalent credentialed/fixture `POST /watch/{ticker}` historical body via
   REST to populate the same engine, capture the resulting cockpit/chart pixels, and **document
   the substitution explicitly** — never mark a browser-gated leg passing on a unit test alone.
3. **Scheduled deferrals (NOT stalls):** J-15 (live-feed-gap stale→recover) and J-67's live-IEX
   badge **pixel** leg + the live-declared `iex`-stamped journal row require market hours. They
   are deferred to a Monday market-hours iteration (next open 15-06-2026 14:30 UTC+01:00). J-67
   stays `passing` on its non-live evidence — **do NOT re-open it to `failing`.** Any live-only
   re-confirmation of J-12/J-25/J-26 is also out of scope this weekend (already green).
4. **Closed-market is the natural now-state.** Because the market is closed, a *live*-mode watch
   should naturally render the "market is closed" honest panel (J-14 closed-market leg) — capture
   it directly; do not simulate it.
5. **Byte-identity vs defect-fix tension.** The spec demands byte-identical code AND treats any
   surfaced real-data defect as an in-scope minimal fix. **Assumption:** default to byte-identical;
   a fix is justified only if a verification leg shows a genuine on-screen defect (e.g. an honest
   state that does not render, a fabricated `live`, a UI-side recomputation). Any fix must be
   config-owned (no magic numbers), re-pinned if persistence is touched, and must leave J-01–J-09
   sims + classifier suite + J-36/J-37 fixtures green. Scope-creep guard: if a leg's acceptance
   needs capability outside docs/goal.md Key Capabilities, exclude it, note it, let the evaluator
   score it `partial` — do not expand scope.
6. **Frontend build caution (memorialized).** Do NOT `npm run build` against the live harness
   dev server's shared `.next`; type-check with `npx tsc --noEmit` if a check is needed. Do not
   `git checkout` unstaged iter files. (Per the project's QA frontend-build-caution memory.)
7. **Coherence guard.** No new computation path or serving path for any contract value. The chart
   and cockpit read `…/history`, `…/state`, `…/features`, `…/summary` verbatim — a second
   side/state/price/time path would FAIL the coherence-auditor. No `blueprint.reapproval-requested`.
