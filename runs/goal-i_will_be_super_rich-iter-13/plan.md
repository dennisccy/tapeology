# goal-i_will_be_super_rich-iter-13 Execution Plan

Targets the last three unbuilt Must-have journeys (J-32, J-33, J-34) — the J-31–J-35 refinement
pass closer. Full depth: J-33 touches the classifier core, J-34 changes the vendor fetch
concurrency model, and the diff crosses backend + frontend + data model. All of J-01–J-31 + J-35
are passing and MUST stay green.

## What to Build

- **J-32 — mutable replay speed (backend + frontend).** Add `POST /watch/{ticker}/speed` so a user
  can change the speed of a **running** historical replay and have it apply within ~1s — no
  re-fetch, no engine restart, no teardown. Wire the existing Historical replay-speed control to
  issue this endpoint (not a re-Watch).
- **J-33 — relative spread/impact classifier gates.** Re-tune the directional/absorption gates so
  the "wide spread" and "clean price impact" tests are judged **relative to the instrument's price
  level / recent volatility** (spread in bps of mid/last; impact as a return), config-owned. A real
  ~$30–50 name with a proportionate spread and strong negative impact must resolve to
  `seller_control` (mirror: `buyer_control`); a genuinely wide *relative* spread or aggression with
  no proportionate progress still reads `unclear` / absorption.
- **J-34 — chunked long-window fetch.** Split a long requested historical window into bounded
  sub-windows fetched with bounded concurrency and stitch them in epoch order into one real window,
  so the Full-RTH quick-pick (and any multi-hour window) loads for a liquid symbol instead of
  returning the "very high-volume" error. No fabricated/dropped/reordered/de-duplicated prints;
  re-watch stays near-instant from the existing window cache.

## Agents Required

- developer: yes -- J-32 (`POST /watch/{ticker}/speed` + `WatchManager.set_speed` + per-ticker
  mutable speed holder + `_feed_paced` reading current speed each iteration + frontend control
  wiring), J-33 (relative gates in `classifier.py`, new boundaries in `config.py`, price-relative
  basis read once from the canonical snapshot/feature engine), J-34 (chunk-split + bounded-concurrency
  stitched fetch in `alpaca.py` / historical provider). All with TDD per the DoD test list.

## Frontend Present
yes

## Files to Create/Modify

Backend:
- `apps/backend/app/main.py` -- add `POST /watch/{ticker}/speed` (mirror the existing pause/resume
  routes): validate body speed against `CONFIG.allowed_replay_speeds` (out-of-set ⇒ **422**),
  not-watched ⇒ **404**; call `manager.set_speed(...)`; return the canonical summary projection.
- `apps/backend/app/watch_manager.py` -- own a per-ticker **mutable speed holder** (e.g.
  `dict[str, list[float]]` or a small mutable cell set at `watch_with_provider`); add
  `set_speed(ticker, speed) -> bool` (False ⇒ not watched, mirroring pause/resume); change
  `_feed_paced` to read the **current** speed each loop iteration (replace the captured local
  `divisor = speed`). Clear the holder in `stop()`.
- `apps/backend/app/engine/classifier.py` -- re-tune the four control/absorption gates to use
  **relative** spread (bps) and **relative** impact (return) instead of absolute `$` cutoffs; keep
  the absorption gates the **exact complement** of the control impact condition (mutual exclusivity
  preserved). Read the price-relative basis from the canonical snapshot/feature engine — do **not**
  add a second price/feature computation in the classifier.
- `apps/backend/app/config.py` -- new config-owned relative boundaries (e.g. max stable spread in
  bps, min/max relative price-impact return cutoffs, absorption flat band as a return), plus J-34
  sub-window size + chunk-concurrency bounds. No inline literal lands in engine/classifier/adapter
  code (no-magic-numbers anti-goal).
- `apps/backend/app/providers/adapters/alpaca.py` -- in `fetch_historical` / `_fetch_trades_quotes`,
  split a long window into bounded sub-windows, fetch with bounded concurrency, stitch in epoch
  order into one `HistoricalWindow`; no fabricate/drop/reorder/dedupe; preserve the window cache and
  the existing `VendorTimeout`/`NoDataForWindow`/`SymbolNotTradable` honesty. Any timeout raise stays
  modest; backend bound stays **shorter than** the frontend timeout.
- `apps/backend/app/providers/historical.py` -- (if the chunk orchestration lives at the provider
  seam) coordinate the chunked fetch / stitch while keeping the neutral record contract unchanged.
- `apps/backend/tests/` -- NEW/updated:
  - `POST /watch/{ticker}/speed`: valid apply, out-of-set ⇒ 422, not-watched ⇒ 404, and
    **determinism** (replay one fixed window at 1× and 10× ⇒ identical features/state/confidence).
  - J-33 classifier regression fixture (`seller_control` on the ~$30–50 reference shape) **plus**
    negative guards (wide *relative* spread ⇒ `unclear`; high aggression, no proportionate progress
    ⇒ absorption). Re-run `test_scenario` (all 5 sim) and `test_classifier` — both MUST stay green.
  - J-34 chunk-split (long window splits into the expected bounded sub-windows) and in-order stitch
    (epoch-ordered, no fabricated/dropped/reordered/de-duplicated prints); re-watch hits the cache.

Frontend:
- `apps/frontend/components/TopBar.tsx` (or wherever the Historical replay-speed control lives) --
  on change during a **running** replay, issue `POST /watch/{ticker}/speed` instead of a re-Watch;
  reject/disable out-of-set values client-side as a courtesy (backend 422 is authoritative).
- `apps/frontend/lib/api.ts` -- add a `setReplaySpeed(ticker, speed)` call.

## UI Evolution

- New user-facing capability: change the replay speed mid-replay and see the cadence change
  immediately (no re-Watch / no teardown); a real symbol making a clear directional move now reads
  as buyer/seller control instead of staying `unclear`; the Full-RTH / multi-hour historical window
  loads instead of being refused as "very high-volume".
- New information displayed: **none new**. The tape-state panel (row 1) may now show **control**
  where it previously showed `unclear` on real directional moves; the chart may show seller/buyer
  markers (row 10) at those transitions — same values, recalibrated computation.
- New user actions: changing the existing **replay-speed** control during a running historical
  replay (applies live).
- UI surface changes: **none new** — the Historical replay-speed control and the Full-RTH quick-pick
  already exist on `/`; only their backend behavior changes.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing Historical mode-specific controls (replay-speed control,
  quick-picks) and the existing tape-state panel + chart markers. No new components.
- Layout: unchanged — single `/` tape cockpit; chart above, panels below.
- Key visual effects: existing color semantics (green buyer_control, red seller_control, amber
  absorption/unclear); seller/buyer markers in the same green/red/amber semantics.
- States to handle: the replay-speed control should reflect the active speed; an out-of-set value is
  disabled/rejected client-side; the Full-RTH fetch wait reuses the existing row-6 waiting/progress
  treatment (no new state). Out-of-set/not-watched errors surface via the existing error path.

## Key Test Scenarios

- `POST /watch/{ticker}/speed`: valid speed applies to the in-progress replay (cadence changes,
  watch not torn down); out-of-set ⇒ 422; not-watched ⇒ 404; **determinism** — same fixed window
  replayed at 1× and 10× yields byte-identical features/state/confidence.
- J-33 deterministic fixture: warmed, high sell ratio, strong negative **relative** impact, spread
  wide in absolute `$` but normal **relative** to price ⇒ `seller_control` at confidence ≥
  reasonable threshold; mirror rally ⇒ `buyer_control`. Negative guards: wide *relative* spread ⇒
  `unclear`; high aggression with no proportionate progress ⇒ absorption.
- Regression keystone: all five sim scenarios (J-01–J-09) and the existing classifier unit tests
  stay green after the re-tuning; absorption gates remain the exact complement of the control impact
  condition (J-04/J-05 not silently reclassified).
- J-34 chunk tests: a long window splits into the expected bounded sub-windows; merged stream is
  epoch-ordered with no fabricated/dropped/reordered/de-duplicated prints; re-watch hits the window
  cache. Full-RTH liquid-symbol load is operator-gated with credentials.
- Browser (J-32): change replay speed on a running historical replay ⇒ cadence changes within ~1s,
  no re-Watch, watch not torn down. Regression smoke: J-17 (sim chart renders), J-02/J-03 (sim
  buyer/seller resolve), J-20 (historical window picker unchanged).
- Error backstop: a window genuinely too large to load within budget still resolves to the
  actionable "shorter range" message (J-28) — now a true backstop, not the routine outcome for a
  normal long session; an empty/anchorless window still ⇒ empty chart (no fabricated prints).

## Notes / Assumptions

- **Mirror lesson (iter-11):** `allowed_replay_speeds` is backend-authoritative for the 422 path;
  the frontend control disable is only a courtesy. Trace any threshold FAIL to the spec and both
  sides before scoring a regression.
- **Keystone safety (iter-5):** the authoritative proof for any classifier change is the in-loop
  deterministic fixture replay re-derived from code, not a screenshot. Keep absorption gates the
  exact complement of the control impact condition.
- **Browser-QA reconciliation (iter-12 / iter-8):** the browser-qa-agent and the qa-agent Chrome MCP
  run can disagree or SKIP on shared `:3650` `.next` corruption; open the evidence bytes and
  reconcile. For the fast-resolving speed change, observe/hold the `POST .../speed` request and
  assert the DOM/cadence, not just a PASS label.
- **Real-data legs are credential-gated:** J-33's real-GME confirmation and J-34's full-window load
  need Alpaca credentials; the gating checks are the deterministic classifier fixture (J-33) and the
  chunk-split + in-order-stitch unit tests (J-34), which run with no keys.
- **Scope:** no new displayed value, no new page/nav (blueprint additive only — speed endpoint
  registered against rows 6/12). Out of scope and excluded: live-mode classification changes, new
  chart studies/indicators/order affordances, on-disk cache/persistence, second vendor adapter,
  changes to symbol-search / pause-resume / timeout-ordering beyond keeping them green. No coherence
  re-approval owed (iter-12 was COHERENCE-PASS).
- **Dev handoff:** required at `docs/handoffs/goal-i_will_be_super_rich-iter-13-dev.md`.
