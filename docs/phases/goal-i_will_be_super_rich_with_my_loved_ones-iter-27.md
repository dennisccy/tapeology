# Goal Iteration 27 — J-68 backlog: weekend-verifiable real-data legs (historical / fixture / REST), live legs deferred to Monday

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 27
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-11, J-14, J-16, J-18, J-20, J-22, J-23, J-27, J-29, J-32
- **Required-still-passing journeys:** J-01, J-02, J-08, J-10, J-17, J-19, J-31, J-35, J-36, J-37, J-38, J-65, J-66, J-67, J-68 (byte-identity + additive-toggle clauses)
- **Explicitly deferred to a Monday market-hours iteration (NOT a stall — see NOTES):** J-15 (live-feed-gap stale→recover), J-67's live-IEX badge/disclosure **pixel** leg over a real live feed + the live-declared `iex`-stamped journal row, and any live-only confirmation of J-12/J-25/J-26 (those journeys are already green on non-live evidence). Next US open: **15-06-2026 14:30 UTC+01:00 (Monday)**.
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - No stock scanning or screening.
  - No news, theme, or sentiment analysis.
  - No chart-pattern scanning, technical-indicator studies, drawing tools, or multi-symbol / multi-pane charting. *(The one allowed chart is the focused price candlestick + tape-state-marker overlay for simulated/historical replay, used to evaluate whether a state predicts direction — not a general charting platform.)*
  - No fundamental analysis.
  - No trade execution, order placement, or broker/brokerage integration.
  - No portfolio or position management.
  - No machine learning in the first version — the MVP classifier is rule/threshold-based.
  - No multi-ticker dashboard or watchlist grid — the UI shows one ticker at a time.
  - No persistence of market/tape data. *(Amended: a journal-scoped SQLite store is in scope for research records only; trades/quotes/candles/feature series remain unpersisted, committed test fixtures excepted.)*
  - No claim or implication that the system is profitable, and nothing presented as trading advice.
  - No auto-detection or scanning: theses are user-declared on the one watched ticker; hints exist only there; studies run only over explicitly chosen windows; nothing watches the market for you.
  - No position sizing, account, capital, or P&L management; no currency P&L, equity curves, or win-rate-as-edge presentation anywhere.
  - No parameter optimizer, grid search, or auto-tuning of thresholds.
  - No new market indicators: confirmation, stance, hints, and studies compose the EXISTING engine features and states only.
  - **Real-data journeys are proven with real data** — an "operator-gated" manual note is explicitly insufficient where the acceptance is satisfiable off-hours via committed fixtures / historical replay / REST / unit tests.

## GOAL

Convert the weekend-verifiable real-data backlog legs (historical replay, edge-case honesty, vendor responsiveness, and lifecycle-failure handling — all satisfiable now without a live market feed) from `partial` to positive browser/credentialed/fixture/REST evidence, advancing J-68's "J-01–J-37 all remain green" clause as far as is possible before the Monday market open.

## BACKGROUND

J-66 (the last cue-layer journey) flipped to passing in iter-26; the iter-26 evaluator recommends a **full-depth J-68 backlog iteration** as the only remaining gate to GOAL_ACHIEVED — a multi-journey real-data verification sweep, not a feature delivery. This iteration is **verification / evidence-capture only**; no new product capability is planned. Today is Saturday 2026-06-13 and the US market is closed until Monday 15-06-2026 14:30 UTC+01:00, so this iteration scopes to **only the legs whose acceptance can be met off-hours**: historical replay is reproducible any time credentials are present (SIP historical, free for data >15 min old), and the timeout/lifecycle/edge-case legs are provable via committed fixtures, REST, the existing unit suites, and a controlled backend kill — none of which need a live feed. The genuinely market-hours-gated legs (J-15 live-feed-gap, J-67's live-IEX badge **pixels** over a real feed) are **explicitly deferred to a Monday iteration** and named under "Explicitly deferred" above so the evaluator does not read their absence as a stall. Lessons applied: **iter-24/iter-26 (line 159, 165)** — live-mode pixels must be scheduled during market hours or the gating documented up front; **iter-2 (line 15) / iter-3 (line 27) / iter-5,iter-17 (line 51,123)** — the QA step must hard-precondition a live frontend AND re-probe with a fresh-server/content canary before any capture, especially after any build; **iter-3 (line 33)** — every UI capture must visibly contain the asserted element. No defect fix is planned, but **if a genuine real-data defect surfaces during verification it becomes its own scoped fix within this iteration** (full pipeline can absorb it).

## IN SCOPE

### Backend
- [ ] **No new product capability.** Verification only. The backend code is expected to be **byte-identical** at the end of this iteration (J-68 byte-identity sentinel must hold; the iter-26 backend suite was 848 passed / 1 skipped, exit 0, zero re-pins — keep it so).
- [ ] Re-run the full backend suite and confirm the already-green unit/fixture evidence that anchors the target legs is still green and is cited with exact pass counts in the dev handoff: `test_historical_provider.py` (J-11), `test_aggressor.py` (J-16), `test_history.py` + `test_history_api.py` (J-18), `test_vendor_timeout.py` + `test_vendor_responsiveness.py` (J-22/J-28-anchor), `test_stream_lifecycle.py` (J-23/J-27), `test_progressive_fetch.py` + `test_chunked_fetch.py` (J-29), `test_speed_api.py` (J-32), plus the J-36/J-37 committed-real-data fixtures (regression).
- [ ] **Only if a verification leg surfaces a genuine real-data defect:** scope the minimal fix here, keep it config-owned (no magic numbers), re-pin via versioned migration if persistence is touched, and re-prove the J-01–J-09 sims + classifier suite stay green. Otherwise: zero backend diff.

### Frontend (if applicable)
- [ ] **No new component or surface.** Verification only. Frontend code is expected byte-identical unless a verification leg surfaces a genuine UI defect (e.g. an honest-state message that does not render). Any such fix reuses the existing error banner / failure panel / honest status-dot surfaces — no new surface, no new copy hardcoded (copy comes from the backend taxonomy where applicable).

### New user-facing capability
None. This iteration delivers **evidence**, not capability: the historical-replay and honest-failure flows already built (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-29/J-32 surfaces) are exercised end-to-end in the browser / via REST / against committed fixtures to capture positive pass evidence.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None planned. (A genuine UI defect surfaced during verification would be fixed in place on an existing surface.)

### Product surface delta
None — the product experience is unchanged; this iteration raises the confidence/evidence level of already-shipped real-data flows.

### Blueprint conformance
No new surfaces. Every target leg lives at its already-registered canonical home: J-11/J-14/J-16/J-18/J-20/J-29/J-32 on the `/` Cockpit (historical mode controls + chart + panel grid + honest-state panels); J-22/J-23/J-27 on the `/` Cockpit honest-failure surfaces (error banner / failure panel / status dot). All are inside "J-01–J-37 (cockpit, chart, watch lifecycle, real data) → `/` → Cockpit" in `blueprint.md`. No Information-Architecture or nav-skeleton change; no `blueprint.reapproval-requested`.

### Data-contract additions
None. Every value read in verification is already registered: tape state + confidence (row 1), 14 features (row 2), bid/ask/spread/last (row 3), recent-trade side (row 4), observations/event-log (row 5), watched-source + stream status incl. `connecting/waiting/live/stale/paused/failed/closed` (row 6), real-data failure states `unavailable / unknown symbol / no data / closed / provider_timeout` (row 9), OHLC bars + markers (row 10), resolved historical window in local tz + quick-picks (row 12), display/epoch anchor / true-clock axis (row 13). No second computation or serving path is introduced for any of them — readers read the registered canonical endpoint verbatim.

## OUT OF SCOPE

- **J-15 (live-feed-gap stale→recover)** — requires a market-hours live-feed lull; the research-layer consequence of a stale flip is already integration-proven; only the real live-lull leg remains gated. **Deferred to the Monday iteration.**
- **J-67's live-IEX badge/disclosure PIXELS over a real live feed** and the live-declared `iex`-stamped journal row — require market hours. J-67 stays `passing` on its non-live evidence (badge in DOM + taxonomy copy + honest market-closed state); only the live pixel leg is deferred. **Do NOT re-open J-67 to `failing`.**
- Any live-only re-confirmation of J-12/J-25/J-26 — those journeys are already green; no live capture is attempted this weekend.
- Any new feature, new endpoint, new component, new config key, schema change, classifier re-tune, or copy change — unless strictly required to fix a genuine defect surfaced by a verification leg.
- The J-33/J-34 superseded journeys (verified through J-36/J-37, which are `already_passing`) — not re-litigated.

## DEFINITION OF DONE

- [ ] Target journeys **J-11, J-14, J-16, J-18, J-20, J-22, J-23, J-27, J-29, J-32** each carry positive evidence sufficient for the evaluator to flip them from `partial` to `passing`:
  - J-11 / J-16 / J-18 / J-20 / J-29 / J-32 — a credentialed **historical** AAPL/TSLA replay exercised **in the browser** end-to-end (cockpit panels populate with real values; recent-trades show resolved buy/sell sides with the `unknown` fraction far lower than before; the candlestick chart matches `…/history` at each bar size with markers at transitions; the picker's local-zone label + quick-picks fill a valid RTH window and the fetched window matches the selected local window; the busy window loads within the configured bound and a re-watch is near-instant; an in-progress 1×→10× speed change continues from current position with no re-Watch/re-fetch) — each with a capture that **visibly contains the asserted element**, plus REST/UI agreement where the acceptance calls for it.
  - J-14 — the **closed-market** leg (naturally available now: explicit "market is closed" panel + next open 15-06-2026 14:30 UTC+01:00, never a fabricated cockpit), the **unknown-symbol** leg ("not a tradable symbol"), and the **empty-window** leg ("no data for that window") each captured as distinct honest states. *(The no-credentials leg is not exercisable while keys are present — note it honestly as covered by the existing provider-unavailable path / unit evidence, not faked.)*
  - J-22 / J-23 / J-27 — bounded honest-failure resolution captured: J-22 a non-resolving/slow request resolving to a distinct timeout/unreachable error within the client-side bound (backend bound < frontend bound), anchored by `test_vendor_timeout.py` + `test_vendor_responsiveness.py`; J-23 the backend killed mid-watch surfacing the explicit "couldn't connect to the tape stream" failure within bounds (no infinite spinner, no swallowed rejection), anchored by `test_stream_lifecycle.py`; J-27 a no-first-event / feeder-failure watch resolving to an explicit `stale`/`closed`/no-data/error state owned by `stream_status` (never a fabricated `live`, never stuck `connecting`), anchored by `test_stream_lifecycle.py`.
- [ ] Required-still-passing journeys (J-01, J-02, J-08, J-10, J-17, J-19, J-31, J-35, J-36, J-37, J-38, J-65, J-66, J-67, J-68) remain green; J-67 stays `passing` (live pixel leg deferred, NOT failed).
- [ ] No anti-goal violation introduced (verify the no-fabricated-data, no-trading-advice, single-source-of-truth, and no-tape-persistence anti-goals explicitly against every honest-failure capture).
- [ ] Backend + frontend code byte-identical, OR any defect fix is minimal, config-owned, re-pinned, and leaves J-01–J-09 + the classifier suite + J-36/J-37 fixtures green.
- [ ] Unit tests pass; no regressions (cite exact pass/skip counts).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-27-dev.md` stating, per leg, whether the credentialed historical/REST/fixture verification succeeded, and listing every deferred live leg with its gating reason and the Monday open time (honesty stamp — an "operator-gated" note is insufficient for any leg that was satisfiable off-hours).

## TESTING REQUIREMENTS

- **Browser (named, by ID):** J-11, J-16, J-18, J-20, J-29, J-32 via a credentialed Historical replay of a real liquid symbol (AAPL and/or TSLA) over a known past intraday RTH window (e.g. a recent trading day 14:30–14:40 BST = 09:30–09:40 ET); J-14 (closed-market + unknown-symbol + empty-window honest states); J-23 (backend killed mid-watch → explicit failure); J-27 (no-first-event / feeder-failure → explicit honest state). Each capture MUST visibly contain the asserted element (recent-trades side column, chart markers + axis, picker zone label, honest-state panel text, error banner).
  - **Date-entry note (iter-0 known harness limitation):** the historical date is entered via the custom `dd-MM-yyyy` text input (J-35). If the browser harness cannot drive that input reliably, drive the equivalent credentialed `POST /watch/{ticker}` historical body via REST to populate the same engine, capture the resulting cockpit/chart pixels, and document the substitution explicitly in the dev handoff — never mark a browser-gated leg passing on a unit test alone.
- **Unit/integration:** re-run the full backend suite (expect 848 passed / 1 skipped, exit 0, zero re-pins). Cite, by name and count, the suites anchoring each target leg (listed under Backend). For J-22/J-28 confirm the backend timeout is enforced at the **vendor-call boundary** (not only an async wrapper) and is **shorter than the frontend client timeout**.
- **Error cases:** unknown symbol → "not a tradable symbol"; empty historical window → "no data for that window"; closed market → "market is closed" + next open; vendor timeout → distinct actionable error within bound; backend-down-after-watch → explicit "couldn't connect to the tape stream"; no-first-event / feeder-raise → explicit `stale`/`closed`/no-data state owned by `stream_status`. In **every** error case assert that **no** trades/quotes/prices/tape-state are synthesized (no fabricated `live` over an empty tape).
- **Pre-capture hygiene (mandatory, lessons line 51/123/27):** before ANY browser capture, confirm the frontend dev server is live AND its served bundle post-dates any build run this pipeline (fresh-server / content canary); if the target frontend is dead, browser-qa-agent must **hard-flag**, not soft-skip. Re-probe; do not treat "frontend was up earlier" as evidence.

## NOTES

- **Why full depth:** the iter-26 evaluator recommended `full` and GOAL_ACHIEVED hinges on this sweep being thorough; it spans credentialed historical legs, lifecycle-failure legs, and a multi-journey real-data verification — not a single-component edit. Full runs audit + ux-regression + closure, which is the right rigor for an evidence sweep that is the last gate to goal completion.
- **Scheduling honesty (the load-bearing constraint):** today is Saturday 2026-06-13; the US market is CLOSED until **15-06-2026 14:30 UTC+01:00 (Monday)**. This iteration deliberately scopes to the off-hours-verifiable subset and **defers** J-15 and J-67's live-IEX pixel leg to a Monday market-hours iteration. The deferred legs are named under Goal Mode Metadata "Explicitly deferred" and in OUT OF SCOPE so the evaluator treats their continued non-`passing`/gated state as **scheduled**, not stalled. The Monday iteration is the natural successor and should be a focused live-feed capture pass.
- **Lessons applied (episodic memory):**
  - *iter-24 (line 159):* "browser-verifiable without a feed" ≠ "verifiable any time" — the live cockpit's honest-absence design renders NO live-IEX badge over a closed market (it shows MARKET IS CLOSED). Hence J-67's live pixel leg is genuinely market-hours-gated and is deferred, not attempted-and-failed.
  - *iter-25/iter-26 (line 165/178):* a control's blueprint home ≠ its fresh-load visibility; not directly in scope here (no new control) but the J-68 sentinel must confirm the iter-26 always-rendered sound toggle is still an additive cue-area surface, not a displacement, on the no-thesis cockpit.
  - *iter-2 (line 15) / iter-3 (line 27):* failing-by-absence and dead-frontend discipline — hard-flag a dead frontend; this is a UI-heavy verification iteration.
  - *iter-3 (line 33):* every below-the-fold capture (recent-trades side column, chart markers, honest-state panels) must visibly contain the asserted element.
  - *iter-5,17 (line 51/123):* fresh-server / content canary before captures, especially after any build the pipeline runs.
- **Single-source-of-truth reminder:** for J-11/J-18 the chart and cockpit MUST read the registered canonical endpoints (`…/history`, `…/state`, `…/features`, `…/summary`) verbatim — do not introduce or accept any UI-side recomputation of side/state/price/time during verification (coherence-auditor will FAIL a second path).
- **Scope-creep guard:** if any target leg's acceptance turns out to require capability outside docs/goal.md Key Capabilities, exclude it, note it, and let the evaluator score it `partial` — do not expand scope.
