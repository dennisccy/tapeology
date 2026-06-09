**Verdict:** COHERENCE-PASS

---

## Coherence Audit — iter-13 (goal-i_will_be_super_rich)

**Iteration:** 13 · **Journeys:** J-32, J-33, J-34
**Snapshot SHA:** 291e4745cda0d690abb371cc55a44693c91cfc57

---

### Step 1 — Data Contract check

**Row 1 — Tape state + confidence (TapeStateClassifier)**

The classifier in `apps/backend/app/engine/classifier.py` now reads a `reference_price` value from
`primary_features` (the canonical feature engine snapshot) and uses it to convert spread and price
impact to relative (bps / return) metrics before applying the gate predicates. This is a
recalibration of the one existing row-1 computation — not a second producer. The classifier still
reads `buy_impact`, `sell_impact`, and `spread` from the same feature engine snapshot it always
did; the new `reference_price` is additional context fetched from the same source
(`primary_features.get("reference_price", 0.0)` at `classifier.py:76`). No second computation of
price, spread, or impact was introduced.

**New feature: `reference_price` in `FEATURE_NAMES`**

`apps/backend/app/engine/features.py:42` adds `"reference_price"` to `FEATURE_NAMES`. It is
computed once in `_Window.compute()` (features.py:106–110) from quote mid-prices or trade prices
already present in the window — the same raw data the existing 13 features use. It flows through
`serialize_features` → `snap.features` and is therefore present in the raw `GET /tape/{ticker}/features`
JSON and the WebSocket `features` payload.

It is NOT rendered in the cockpit: `FeaturesPanel.tsx` has a hard-coded `FEATURE_ROWS` list of 12
entries that does not include `reference_price`. It is an internal basis value — its only consumer
is the classifier (one-hop within the engine layer). It does not duplicate any existing blueprint
contract row (it is not price, spread, state, confidence, or any of the 12 rendered features). It
is genuinely new, unregistered as a displayed value, and not user-facing.

Advisory note below (Part C / A5).

**`POST /watch/{ticker}/speed` — new endpoint (J-32)**

`apps/backend/app/main.py:393` adds `POST /watch/{ticker}/speed`. The blueprint (iter-13 header
note) explicitly pre-registers this as a sibling lifecycle control on rows 6 and 12 — delivery-pacing
only, never a displayed engine value. `WatchManager.set_speed` in `watch_manager.py:154–170` mutates
the per-ticker speed cell; `_feed_paced` re-reads it each loop iteration (watch_manager.py:291).
Speed does not alter the events, their order, or their logical timestamps — features/state/confidence
are byte-identical at any speed. No new displayed value, no second computation of any row.

**Row 10 — OHLC history / chunked fetch (J-34)**

`apps/backend/app/providers/adapters/alpaca.py` adds `_split_window` (alpaca.py:170–199) and
rewrites `_fetch_trades_quotes` (alpaca.py:281–371) to fetch sub-windows with bounded concurrency
and stitch them in epoch order. This all lives inside the one vendor adapter module — the single
canonical source for historical data (row 10's serving path). No second fetch path was introduced.
The `HistoricalProvider` and engine history buffer are unchanged; OHLC and markers are still
computed once in the engine.

**Config additions**

All new constants (`max_stable_spread_bps`, `min_buy_price_impact_return`,
`max_sell_price_impact_return`, `absorption_flat_band_return`, `impact_return_scale`,
`historical_chunk_seconds`, `historical_chunk_max_concurrency`) live in
`apps/backend/app/config.py` — config values, not displayed values. No magic numbers introduced.

**Summary:** No Part A violations found.

---

### Step 2 — Information Architecture check

**No new pages or routes.** The diff touches only:
- `apps/frontend/app/page.tsx` — adds `handleSpeedChange` handler and passes `onSpeedChange` prop.
- `apps/frontend/components/TopBar.tsx` — wires the existing speed `<select>` to call
  `onSpeedChange(next)` when a historical replay is running.
- `apps/frontend/lib/api.ts` — adds `setReplaySpeed` calling `POST /watch/{ticker}/speed`.

All changes are within the existing `/` HOME and the existing Historical mode-specific controls
(the replay-speed dropdown). The blueprint IA explicitly lists the Historical replay-speed control
as part of the `/` app shell. No new nav section, no new sidebar link, no new page, no new route,
no parallel shell.

**Navigation path:** The replay-speed control is a top-bar dropdown already present and reachable
in 0 clicks (it is always visible when Historical mode is selected). No reachability issue.

**Summary:** No Part B violations found.

---

### Step 3 — Advisory observations (WARN, not FAIL)

**WARN — `reference_price` is unregistered as a data contract value.**
`apps/backend/app/engine/features.py:42` adds `"reference_price"` to `FEATURE_NAMES`, which flows
into the raw `GET /tape/{ticker}/features` response and the WebSocket stream. It is not rendered in
the cockpit and is not user-facing. However, it is now part of the public features payload that any
API consumer (including J-08 tests) would observe. The decomposer correctly documented it as an
internal basis value rather than a new contract row; it is genuinely new and not a duplicate of any
existing registered value. Recommendation: the next iteration should either add a brief row to the
Data Contract acknowledging `reference_price` as an internal feature available in the features
payload (not a new cockpit readout), or explicitly mark it as excluded from the displayed-features
contract.

---

### Verdict summary

| Rule | Result |
|------|--------|
| Part A — Duplicate computation | PASS |
| Part A — Non-canonical source | PASS |
| Part A — Unregistered new value (displayed) | PASS — `reference_price` is not displayed |
| Part B — No navigation path | PASS |
| Part B — Reachability (≤2 clicks) | PASS |
| Part B — Duplicate home | PASS |
| Part B — Parallel shell | PASS |
| Part C — Unregistered internal feature in raw payload | WARN (advisory) |

**Overall: COHERENCE-PASS.** No objective violations in Part A or Part B. One advisory note on
`reference_price` appearing in the raw features payload without a contract annotation — does not
block the goal.
