**Verdict:** COHERENCE-PASS

---

## Coherence Audit — iter-12 (True-clock chart axis + dd-MM-yyyy dates, J-31 / J-35)

Session: `i_will_be_super_rich` · Iteration index: 12
Snapshot SHA: `4bdec1f9dcafa6644a8009a3784cbda01dc241d1`
Blueprint status: APPROVED (iter-12 extension is additive — row 13 added, no IA change)

---

### Step 1 — Data Contract check

**Row 13 (new — Canonical display/epoch anchor):**
The iteration correctly introduces row 13 with a single computing owner and single serving endpoint:

- Owner: the engine/feeder. `epoch_anchor` is set once per watch via `_provider_anchor()` in
  `apps/backend/app/watch_manager.py` (reads `provider.epoch_anchor` defensively). Each provider
  computes it once at construction time:
  - `SimulatedProvider`: reads `CONFIG.sim_session_anchor_epoch` (a config constant in
    `apps/backend/app/config.py`) — no inline literal.
  - `HistoricalProvider`: `min(epochs)` over the loaded window records — the same `t0` the logical
    timeline subtracts, computed once.
  - `LiveProvider`: `None` — the live path has no chart.
- Serving endpoint: the existing `GET /tape/{ticker}/history` projection. `apps/backend/app/main.py`
  passes `engine.epoch_anchor` to `serialize_history()`; `apps/backend/app/serializers.py` includes
  it verbatim in the response JSON as `epoch_anchor`. No second endpoint, no second producer.
- Frontend read: `apps/frontend/lib/api.ts` reads `epoch_anchor` from the response verbatim.
  `apps/frontend/components/PriceChart.tsx` applies the additive offset `anchor + logical_ts` at
  display time — it recomputes no price, side, or state (row-10 OHLC/markers are still read from
  the same `/history` endpoint unchanged).

No duplicate computation and no non-canonical source found. Row 13 conforms to the blueprint
contract.

**Rows 1–12 (existing):**

- The shared formatters `formatDateDMY` / `formatDateTimeDMY` in `apps/frontend/lib/datetime.ts`
  are pure presentation functions — they format a received value, they do not compute any
  engine/tape value. Not a violation.
- `formatWatchedSource` in `apps/frontend/lib/datetime.ts` reformats ISO-8601 instants embedded
  in the backend's row-6 `scenario` descriptor string for display (`dd-MM-yyyy HH:mm`). It does
  not re-derive the descriptor or the watched-source value — the backend's canonical string is read
  verbatim and only its embedded timestamps are reformatted for display. This is a re-format, not
  a re-computation (rule: "A value that is read from its canonical endpoint and merely re-formatted
  for display is not a violation").
- `parseDMYToIsoDate` in `apps/frontend/lib/datetime.ts` converts the user's `dd-MM-yyyy` text
  input to the internal `YYYY-MM-DD` format consumed by the existing row-12 resolver
  `resolveLocalWindowInstant`. This is input normalisation feeding the same row-12 canonical
  resolver — no second timezone resolver, no second window computation.
- No new function computing any registered value (tape state, features, spread, trade side, stream
  status, symbol search, market clock, real-data availability, OHLC bars/markers, paused state,
  resolved historical window) was introduced in this diff.

No Data Contract violations.

**New displayed values not yet in the contract:**

- `epoch_anchor` (row 13) is registered in the blueprint as of this iteration — no unregistered
  value warning needed.
- The `dd-MM-yyyy` format is presentation-only, as declared in the blueprint. No new contract row
  is required.

---

### Step 2 — Information Architecture check

All surfaces changed in this iteration remain on the single `/` HOME cockpit:

| Changed surface | IA location | Status |
|---|---|---|
| `PriceChart` axis / crosshair / marker timestamps | `/` price-chart pane (J-17/J-18/J-31 canonical home) | Correct home |
| `TopBar` Historical date input (`dd-MM-yyyy` text field) | `/` Historical date/time picker (J-20/J-35 canonical home) | Correct home |
| `TopBar` watched-source descriptor date reformatting | `/` cockpit top bar (J-11/J-35) | Correct home |
| `MarketStatusIndicator` next-open/close time formatting | `/` app shell (J-12 canonical home) | Correct home |

No new routes, pages, or nav-skeleton changes. The blueprint's IA section explicitly maps J-31 and
J-35 to these surfaces on `/`. The nav file inspected is `apps/frontend/components/TopBar.tsx` —
no new nav link was added or removed.

No IA violations (no hidden feature, no undiscoverable route, no duplicate home, no parallel shell).

---

### Step 3 — Advisory observations

None. The iteration is tightly scoped to the declared additive work (row 13 + presentation
formatters) and all changes conform to the blueprint.

The pre-existing `localTimeAnnotation` call at `apps/frontend/lib/datetime.ts:159` uses
`toLocaleTimeString` for quick-pick time annotations (a display helper, not a date). This path
predates iter-12 and was not introduced by this diff — no new advisory note warranted.

---

### Verdict rationale

- Part A (Data Contract): 0 violations. Row 13 has one owner (`engine/feeder`), one endpoint
  (`GET /tape/{ticker}/history`), and the UI reads it verbatim. All rows 1–12 remain single-owner,
  single-endpoint, with no new parallel computation introduced.
- Part B (Information Architecture): 0 violations. All changes land on the single `/` HOME,
  in the surfaces the blueprint IA designates as canonical homes for J-31/J-35.
- Part C (Advisory): 0 notes.

**Verdict: COHERENCE-PASS**
