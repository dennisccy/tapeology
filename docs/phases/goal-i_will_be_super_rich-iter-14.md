# Goal Iteration 14 — Real-data classification + progressive long-window load, proven by committed real fixtures (J-36, J-37)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 14
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-36, J-37
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-11, J-16, J-17, J-18, J-28, J-29, J-31, J-33, J-34 (and by extension all of J-01–J-35 — these MUST NOT regress)
- **Anti-goal reminders:**
  - **Real-data journeys are proven with real data.** A journey whose outcome depends on real market data (classification of a real move, real-window loading) is NOT done until an **automated test over committed, real captured market data** asserts the outcome and runs in CI **without** live credentials. A synthetic/hand-tuned fixture and an "operator-gated" manual check are necessary-but-**insufficient** — they MUST NOT be the sole evidence for GOAL_ACHIEVED. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide **relative to the instrument's price / typical spread**, or there is no clean price impact, the state MUST be `unclear` with low confidence. The "wide spread" and "clean price impact" tests MUST be judged **relative to the instrument's price level / recent volatility** … The spread/impact tests MUST also account for the **selected feed** and for **trading halts**: a wide or **absent** *quoted* spread (a single-venue IEX quote, or suppressed/crossed quotes during an LULD halt) MUST NOT by itself veto a move that is otherwise clearly directional (strong one-sided ratio + real price impact + elevated speed) — there the spread acts as a **graded confidence factor, not an absolute veto**. Honest uncertainty applies to genuinely illiquid/mixed tape, never to a single-venue quoting artifact. *(critical)*
  - **Price impact over raw aggression.** A tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. *(critical)*
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent). A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam; vendor specifics MUST NOT leak into the engine, providers, or API.
  - **No magic numbers.** Every threshold/cutoff/confidence boundary MUST come from config — no such literal in engine/classifier code. The per-mode feed choice and any halt/quote-artifact handling boundary likewise live in config.
  - **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed. The committed real-data fixtures contain market data only — never keys.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. *(critical)*
  - **Bounded, honest, performant vendor calls.** … For a long window, "fast by design" MUST mean **time-to-first-data is decoupled from total-window load** — the first chunk begins the replay within budget while later chunks stream in the background — not merely parallelizing a fetch that still completes entirely before responding; the "shorter range" message is a true last-resort backstop only. *(critical)*

## GOAL

Make a genuine real-data directional move (GME's ~12% open drop on 14-05-2024) classify as **seller_control** rather than perpetual `unclear`, and make a long/dense historical window (Full RTH) **begin replaying within the budget** with later data streaming in — each proven by a **committed real-data fixture test that runs in CI without live credentials**, closing the two real-data defects (J-36, J-37) that the iter-13 synthetic-only "pass" shipped.

## BACKGROUND

Iter-13 declared GOAL_ACHIEVED, but the user verified that two real-data legs still fail on real Alpaca data — they had been validated only against hand-built synthetic fixtures with the real legs marked "operator-gated". Commit `f3ea17c` reopened them as **J-36** (real directional move stuck on `unclear`) and **J-37** (long/dense window times out into "very high-volume") and added the critical anti-goal *Real-data journeys are proven with real data*. Both are genuinely **unbuilt against real data** and are the only failing journeys, so they define this iteration. Depth is **full**: J-36 re-tunes the engine classifier (high-risk — must keep J-01–J-09 and J-33 green) and adds a per-mode vendor feed; J-37 restructures the historical fetch+replay seam to stream progressively (must preserve determinism + single-source-of-truth); both require new committed real-data fixtures and CI tests beyond a browser smoke. Today's root causes are concrete and verified in the code: `classifier.py:104/128/148/168` apply `spread_metric <= max_spread` as an **absolute veto** on every directional/absorption gate (so a 2,700-bps single-venue IEX quote kills an otherwise-clear move), and `alpaca.py:371` `_data_feed()` returns IEX for **both** historical and live; for J-37, `alpaca.py:_fetch_trades_quotes` fetches the **entire** window (all chunks) before `HistoricalProvider` is even constructed (`historical.py:49 stream()` materializes the whole window), so time-to-first-data is coupled to total-window load.

**Lessons applied (from `lessons.md`):**
- **iter-13 keystone (Applies to any change to `classifier.py` or the spread/impact gates):** prove the absorption/control complement on a **shared fixture at the boundary**, and assert the absolute-fallback fixtures stay **byte-identical**. J-36 weakens the spread veto into a graded factor — this MUST NOT silently reclassify J-04/J-05 absorption or the J-33 relative gates. Keep the change additive: the relaxed-veto path must only engage for the *clearly-directional-with-wide/absent-spread* case, leaving every existing fixture's state + confidence pinned.
- **iter-2 (real-data feed gotcha):** free **IEX** top-of-book is wide/noisy; a clean read needs SIP (historical) or a penny-spread name. J-36 part (a) is exactly this: historical replay must fetch the **SIP** consolidated feed.
- **iter-2 (committed REAL fixture pattern):** a committed VCR-style real Alpaca capture (real epochs + prices, self-documented `note: REAL … not synthesized`) is what makes a real-data journey deterministic and offline-reproducible in-loop. Reuse `scripts/capture_alpaca_fixture.py` + the `tests/fixtures/alpaca/*.json` + `load_fixture_window` pattern — extend it to also carry quotes-by-feed so a SIP fixture is committed.

## IN SCOPE

### Backend

**J-36 — real directional move classifies as control (not perpetual `unclear`)**
- [ ] **Per-mode vendor feed (in the ONE adapter).** Make `apps/backend/app/providers/adapters/alpaca.py` select the **SIP** consolidated feed for `fetch_historical` and keep **IEX** for `stream_live` — a config-owned per-mode feed choice (e.g. `historical_feed` / `live_feed` in `config.py`, defaulting to `sip` / `iex`), read inside the one adapter only. No vendor enum leaks outside the adapter; the `ALPACA_FEED` env override remains supported.
- [ ] **Classifier robust to quoting artifacts (spread = graded factor, not absolute veto).** In `apps/backend/app/engine/classifier.py`, change the directional gates so a **clearly directional** move (strong one-sided aggressive ratio **AND** real relative price impact **AND** elevated speed) resolves to control **even when the quoted spread is momentarily wide or quotes are absent/crossed** (e.g. around an LULD halt). The spread becomes a **graded confidence factor** in that case, not a hard gate. A genuinely wide *relative* spread on otherwise-mixed/weak tape (the J-06 / J-33 honest-uncertainty case) MUST still read `unclear`/absorption. All boundaries config-owned (no magic numbers); the absorption gates MUST remain the **exact complement** of the control impact condition (the iter-5/iter-13 keystone). The classifier still reads spread/impact/price from the **canonical feature engine** (no second computation).
- [ ] **Absent/crossed quote handling.** Define the "directional override" precisely and config-driven: it engages only when ratio ≥ floor AND |relative impact| past its cutoff AND speed ≥ floor (the existing control predicate minus the spread term); when it engages, spread enters only via the confidence score (graded), never as a veto. Document the threshold semantics in the classifier docstring.

**J-37 — long/dense window loads progressively (first chunk replays immediately, the rest streams in)**
- [ ] **Decouple time-to-first-data from total-window load.** Restructure the historical fetch+replay seam so the backend **never fetches the entire window before responding**: the **first sub-window chunk** is fetched within the bounded budget (backend bound < frontend timeout) and replay begins on it, while **subsequent chunks are fetched in the background** and appended **in epoch order** as the replay advances. Likely shape: the adapter exposes a chunk-by-chunk fetch (a generator/iterator of `HistoricalWindow` sub-windows in epoch order) and `HistoricalProvider`/the historical feeder consumes chunks progressively rather than materializing one whole `HistoricalWindow`. Keep `fetch_historical` (single-window) working for short windows / the cache.
- [ ] **Correctness preserved.** Streamed chunks MUST NOT fabricate, drop, reorder (beyond canonical epoch order), or de-duplicate real prints; quote-before-trade ordering at equal epochs is preserved per chunk and across the stitch boundary; a re-watch is near-instant from the existing window cache. Tape state and each feature stay **single-source and deterministic** — the engine still bins on its logical timeline; chunk boundaries MUST NOT change the resulting features/state/confidence vs. a single-shot fetch of the same records.
- [ ] **Engine handles real consolidated-tape density without stalling.** A ~50k-event Full-RTH window must finish processing within budget. It MAY bound/aggregate the **displayed** series (e.g. cap the history buffer / recent-trades length) but tape state and each feature stay single-source and deterministic and nothing is fabricated. Any new bound is config-owned.
- [ ] **"Very high-volume — try a shorter range" becomes a true backstop.** The advertised **Full RTH** quick-pick MUST load for a liquid symbol without that error; the message fires only when the **first chunk itself** genuinely cannot load within budget. Keep the backend bound < the frontend `WATCH_REQUEST_TIMEOUT_MS`.

### Real-data fixtures + CI tests (the anti-goal #20 gate — REQUIRED, not operator-gated)
- [ ] **J-36 fixture:** commit a **real captured** Alpaca window for **GME on 14-05-2024, 13:30–13:40 UTC** (the >10% drop into the LULD halt), captured via the **SIP** feed, into `apps/backend/tests/fixtures/alpaca/` (self-documented `source: alpaca`, `feed: sip`, `note: REAL … not synthesized`). If the operator cannot capture it (no credentials at dev time), the dev handoff MUST say so explicitly and the test MUST be written to fail loudly until the real fixture is present — a synthetic stand-in is NOT acceptable (anti-goal #20). Also capture/commit a **mirror rally** real window if feasible (a comparable fast rally → buyer_control), or document why the drop alone is the gate.
- [ ] **J-36 CI test:** an automated test replaying the committed GME SIP fixture through the real `HistoricalProvider` + `TapeEngine` asserting the drop resolves to **`seller_control`** with confidence ≥ `reasonable_confidence` and seller markers at the transition — runnable in CI **without** live credentials.
- [ ] **J-37 fixture:** commit a **real captured** long/dense window for a liquid symbol (a multi-hour or Full-RTH-representative slice large enough to exercise chunked progressive loading — e.g. a dense ~tens-of-thousands-of-event window). Keep the committed fixture size sane; if a true full-RTH capture is too large to commit, capture a dense representative slice and document the size/coverage decision in the handoff.
- [ ] **J-37 CI test:** an automated test over the committed long/dense fixture asserting (a) first-data/replay begins within the configured budget (the first chunk is consumed before the whole window is fetched), (b) **no** "very high-volume" error for the advertised path, and (c) **no fabricated/dropped/reordered/de-duplicated** prints across the streamed chunks (the streamed record set equals the single-shot record set in epoch order) — runnable in CI **without** live credentials.

### Config (no magic numbers)
- [ ] Add config-owned constants for: the per-mode feed (`historical_feed`/`live_feed`), the J-36 directional-override boundaries (any new graded-spread factor / artifact tolerance), and any J-37 displayed-series cap. No literal threshold in engine/classifier/adapter code.

### Frontend
- None. No UI surface, displayed value, route, or control changes. (The Historical replay-speed control, chart, and date picker are all unchanged; J-36/J-37 are backend correctness + performance fixes behind already-registered rows.) `Frontend Present: no` — UI-impact / UI-test-design / browser-QA / UX-regression steps are N/A for this iteration.

### New user-facing capability
A user replaying a real symbol that made a genuine sharp directional move (e.g. GME's open drop) now sees the cockpit resolve to **seller_control** (the mirror rally → buyer_control) instead of sitting on `unclear` through an obvious move; and a user picking **Full RTH** (or any long window) on a liquid symbol now sees the cockpit/chart **begin populating quickly** and keep filling in, instead of the "very high-volume — try a shorter range" refusal.

### New information displayed
None new. The same row-1 tape state + confidence and the same row-10/13 chart now read correctly on real data. No new field, panel, or value.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
The product's real-data reads become **trustworthy**: the headline tape state is correct on a real directional move, and the advertised long-window path actually works — the two defects that made the iter-13 "done" untrue are closed with real-data evidence.

### Blueprint conformance
No new surfaces. Both journeys live on the existing **`/` — Watch (the tape cockpit) — HOME**: J-36 surfaces on the **Tape-state panel** + chart markers; J-37 surfaces as the **Historical fetch wait (waiting/progress treatment) → cockpit/chart** (the row-6 `waiting` treatment already registered for J-29). No nav-skeleton change ⇒ no re-approval requested.

### Data-contract additions
**None new.** This iteration hardens the **computation** of already-registered rows, adding no new displayed value and no new contract row:
- **Row 1 (Tape state + confidence)** — the J-36 change recalibrates the **one** row-1 classifier so a clearly-directional move with a wide/absent *quoted* spread resolves to control (spread graded, not an absolute veto); it reads spread/impact/price from the canonical feature engine (no second computation, no new producer).
- **Rows 10/12 + the provider/vendor seam** — the J-37 progressive load is a fetch/delivery restructure **inside the one vendor adapter and the historical provider/feeder**; it stitches the **same real records** in epoch order (no fabricate/drop/reorder/dedup), preserves determinism and single-source-of-truth, and adds no second fetch path or recomputation outside the engine. The per-mode feed (SIP historical / IEX live) is a config value, not a displayed value.

The blueprint header gains an additive **iter-14** note recording this (computation hardening of rows 1/10/12; per-mode feed; no new row, no nav change). No Data Contract row is added or duplicated.

## OUT OF SCOPE

- Any new UI surface, route, control, panel, or displayed value (frontend untouched).
- Any change to the live-streaming feed choice (live stays **IEX** by design; only historical moves to SIP).
- The nice-to-have/later items (Level-2 `BookLevelEvent` / `liquidity_pull_score`, the predictive-edge replay/backtest harness, persistence). Excluded — outside `docs/goal.md` Key Capabilities for this goal.
- Relaxing or re-tuning any gate that would regress the five sim scenarios (J-01–J-09) or the J-33 relative gates — the directional-override is additive and must not loosen the honest-uncertainty / price-impact-over-aggression behavior on mixed/weak tape.
- Changing the aggressor side-inference (J-16) or the chart's price/side/state computation (the chart still reads the engine verbatim).

## DEFINITION OF DONE

- [ ] Target journeys **J-36 and J-37 pass** via their **committed-real-data CI tests** (run without live credentials) — the spec-designated authoritative gate for these journeys per anti-goal #20; an "operator-gated" note is explicitly insufficient.
- [ ] **J-36:** the committed GME SIP fixture replayed through the real engine resolves to **`seller_control`** (mirror rally → buyer_control where captured) with confidence ≥ `reasonable_confidence`, with seller markers at the transition; genuinely wide-relative/mixed tape still reads `unclear`/absorption (negative guards).
- [ ] **J-37:** the committed long/dense fixture begins replay within the configured budget (first chunk consumed before the whole window is fetched), with **no** "very high-volume" error on the advertised path and **no** fabricated/dropped/reordered/de-duplicated prints across the streamed chunks.
- [ ] **Required-still-passing journeys remain green:** all five sim scenarios (J-01–J-09), the J-33 relative gates, J-11/J-16/J-17/J-18 historical+chart, J-28/J-29/J-34 vendor-responsiveness — the full backend suite re-runs with **no regression** and the absolute-fallback / sim fixtures stay **byte-identical**.
- [ ] No anti-goal violation introduced (no fabricated data, single-source-of-truth held, vendor SDK confined to the one adapter, no secrets committed, deterministic, no magic numbers).
- [ ] Unit/integration tests pass; the keystone (absorption gate = exact complement of the control impact condition) is re-proven on a shared fixture at the boundary.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-14-dev.md`, explicitly stating whether the real GME SIP fixture and the long/dense fixture were captured with real credentials (and if not, that the gating tests fail loudly until they are — never silently passed on a synthetic stand-in).

## TESTING REQUIREMENTS

- **Browser:** N/A this iteration (`Frontend Present: no` — no UI surface change). The authoritative gates are the committed-real-data CI tests below (consistent with how prior real-data legs were proven, but now REQUIRED in CI per anti-goal #20 rather than operator-gated).
- **Unit/integration (REQUIRED, run without live credentials):**
  - **J-36 gate:** `test_*` replaying the committed **GME SIP** fixture through `HistoricalProvider` + `TapeEngine` → asserts `seller_control` at the drop with confidence ≥ `reasonable_confidence`; mirror rally → `buyer_control` if captured.
  - **J-36 keystone + negative guards:** absorption gate remains the **exact complement** of the control impact condition at the boundary (extend `test_classifier_relative.py`); a wide *relative* spread on weak/mixed tape still reads `unclear` (J-06/J-33 preserved); the absolute-fallback fixtures stay **byte-identical** (pinned confidence unchanged).
  - **J-37 gate:** `test_*` over the committed **long/dense** fixture → first chunk consumed before the whole window is fetched (time-to-first-data decoupled), no "very high-volume" error, and the streamed record set equals the single-shot set in epoch order (no fabricate/drop/reorder/dedup).
  - **J-37 determinism:** the same dense window via progressive chunks vs. a single-shot fetch yields **identical** tape_state / confidence / features (chunk boundaries do not perturb the engine).
  - **Per-mode feed:** an adapter-level test asserting `fetch_historical` uses the SIP feed and `stream_live` uses the IEX feed (config-owned), without leaking the vendor enum outside the adapter.
  - **Regression floor:** `test_scenario.py` (15), `test_classifier.py` (20), `test_classifier_relative.py`, `test_chunked_fetch.py`, `test_historical_provider.py`, `test_vendor_*` all green; full backend suite green (≥ the iter-13 floor of 259 passed / 1 credential-gated skip, plus the new tests, zero regressions).
- **Error cases:** an empty/anchorless window still yields an empty chart + honest read (no fabricated relative call); a window whose **first chunk** genuinely cannot load still resolves to the actionable "shorter range" backstop (J-28); genuinely illiquid/mixed real tape (weak ratio or no real impact) still reads `unclear`/absorption (the directional-override does NOT force a call on weak evidence).

## NOTES

- **Why full depth:** J-36 mutates the engine classifier (the highest-risk module — the iter-5/iter-13 keystone discipline applies) and adds a per-mode vendor feed; J-37 restructures the fetch+replay seam to stream progressively while preserving determinism + single-source-of-truth; both add new committed real-data fixtures and CI tests beyond a browser smoke. The prior verdict was GOAL_ACHIEVED (not ESCALATE), but the reopened journeys are structural/real-data and demand the full 11-step pipeline.
- **Anti-goal #20 is the load-bearing constraint this iteration.** The iter-13 J-33/J-34 "pass" was synthetic-fixture-only and shipped exactly these two defects. The evaluator MUST NOT accept an "operator-gated" note as evidence for J-36/J-37 — the committed-real-data CI tests are the gate. If real credentials are unavailable at dev time to capture the GME SIP fixture and the long/dense fixture, the iteration is **incomplete** (the gating tests must fail loudly, not be marked green on a synthetic stand-in), and the dev handoff must say so plainly.
- **J-36 root cause (verified in code):** `classifier.py` applies `spread_metric <= max_spread` as a hard term in every directional/absorption gate; on the GME window the IEX quoted spread is ~2,700 bps vs the 30-bps `max_stable_spread_bps` gate, so the spread term alone vetoes a move where ratio 0.77 / impact −4.79 / speed 1.5 all clearly pass. The fix is twofold: (a) historical fetch uses SIP so the quoted spread is realistic; (b) the spread is a **graded confidence factor** for a clearly-directional move, not an absolute veto.
- **J-37 root cause (verified in code):** `alpaca.py:_fetch_trades_quotes` fetches **all** chunks (already concurrent — J-34) before returning one whole `HistoricalWindow`, and `historical.py:stream()` materializes the entire window before yielding — so iter-13's chunking parallelized **within** the 8 s cap but never decoupled first-data from full-load. The fix is progressive streaming: first chunk → replay; remaining chunks → background fetch, stitched in epoch order.
- **Reuse the existing real-fixture seam:** `scripts/capture_alpaca_fixture.py` (extend it to support `--feed sip` and to capture quotes), `apps/backend/tests/fixtures/alpaca/*.json`, and `load_fixture_window` in `tests/fakes.py` — keep the committed fixture self-documented (`source: alpaca`, `feed`, `note: REAL … not synthesized`).
- If GOAL_ACHIEVED is reached, it requires positive **committed-real-data CI** evidence for both J-36 and J-37 (not screenshots, not operator notes) plus the full J-01–J-35 regression floor green and COHERENCE-PASS.
