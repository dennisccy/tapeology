# goal-i_will_be_super_rich_with_my_loved_ones-iter-29 Execution Plan

## Nature of this iteration

This is a **verification + live-evidence-capture pass — NOT a feature build**. No application
source change is expected. The app source must stay byte-identical to HEAD (J-68 sentinel). The
stale seam (`watch_manager.py`, `stale_gap_seconds = 10.0`), the `FeedBasisBadge`, the
`feed_basis` mapping, the live status indicator, and the gated `test_live_integration.py` all
already exist. The desired outcome is an EMPTY application diff plus captured live evidence.

The whole point is to capture two market-hours-gated legs that have been honestly deferred since
iter-24 because they require a REAL live IEX socket flipping `live → stale → live` across a
natural feed lull — a flip that CANNOT be fabricated without violating the no-fabricated-data
anti-goal. Credentials (`ALPACA_API_KEY` / `ALPACA_API_SECRET`) are in `apps/backend/.env`, and
per the spec the US regular session is OPEN this iteration (Tue 2026-06-16, ~14:00 ET), so the
live legs are reachable now.

## What to Build

- Nothing in application code. Only fix-in-place IF a GENUINE live-feed defect is surfaced on the
  real socket (see "Conditional fix scope" below).
- **J-15 (the sole `unknown` gate to GOAL_ACHIEVED):** capture pixel evidence that a real Live
  watch shows the status indicator at `live`, then visibly at `stale` across a genuine feed lull
  (recent-trades count NOT advancing during the gap — no fabricated trades), then recovering to
  `live` when prints resume. The `stale` indicator must be visibly distinct from `live` in the
  same status area.
- **J-67 live leg (currently `passing` on its non-live SIP evidence; only the live pixels are
  deferred):** capture the live IEX cockpit rendering the `FeedBasisBadge` reading the `iex`
  basis with the IEX-vs-SIP disclosure line, and a live-declared thesis producing a `/journal`
  row stamped `data_feed = iex` (proving no SIP/IEX pooling).
- **The operator-gated credentialed live-socket integration run** as the authoritative pipeline
  proof: `TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest apps/backend/tests/test_live_integration.py -v -s`
  against the real Alpaca IEX socket during market hours.

## Agents Required

- developer: yes -- Run the gated credentialed live-socket integration test against the real
  Alpaca IEX socket; run the full backend suite green with zero re-pins; re-run
  `test_observer_equivalence.py` green; verify J-68 byte-identity with a LIVE `git status` /
  `git diff --stat` (NOT the prompt's pre-baked snapshot); write the dev handoff. Make NO
  application source change unless a genuine live-feed defect is surfaced — then fix in place on
  the existing owner module only and re-pin (see Conditional fix scope). Do NOT build the J-29
  `<3s` re-watch cache fast-path (explicitly out of scope — soft/P2).

## Frontend Present
yes

## Files to Create/Modify

- `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-dev.md` -- dev handoff:
  the live integration run outcome, the J-15 / J-67 pixel evidence, byte-identity proof, test
  counts. (REQUIRED.)
- `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/` -- live capture
  stills (the `stale` indicator held visible; `live` before/after; the `FeedBasisBadge` + IEX
  disclosure; the `data_feed = iex` journal row). Run `md5sum` over the dir before citing —
  reject byte-identical idle/blank frames (iter-22 / iter-14 lesson).
- **No `apps/backend/**` or `apps/frontend/**` source file is expected to change.** A non-empty
  application diff is a DEFECT unless it is a justified, re-pinned fix for a genuine live-feed
  bug (then J-68 is re-evaluated against the change with observer-equivalence re-run green).

## Conditional fix scope (only if a GENUINE live-feed defect is surfaced)

- Stale watchdog mis-times / recovery flip drops / wrong feed-basis stamp on a real IEX watch →
  fix in place on `apps/backend/app/watch_manager.py` (stale seam) or
  `apps/backend/app/research/feed_basis.py` / `apps/backend/app/research/store.py` (feed label).
  No new module, no new endpoint, no new value, no new config key.
- Badge does not render over a live IEX watch / `stale` not visibly distinct from `live` → fix
  in place on the existing component. No new surface.
- If nothing is broken on the live feed, the application diff is empty (the desired
  J-68-preserving outcome).

## UI Evolution (verification only — no new capability)

- New user-facing capability: **None.** The user can already watch a live symbol, see the status
  flip to `stale` on a lull and recover, and read the live IEX feed-basis badge + disclosure.
  This iteration proves it in pixels on a real feed.
- New information displayed: **None.** Every value is already in the Data Contract and served
  from its single canonical endpoint — `stream_status` (row 6, `GET /tape/{t}/summary` + WS),
  the feed-basis badge value (row 29, additive metadata on the row-6 snapshot), the
  live-declared thesis row's `data_feed` stamp (row 26, `GET /research/journal`).
- New user actions: **None.**
- UI surface changes: **None** — no new pages, panels, or controls. The `/` cockpit status area
  and the `/journal` rows are exercised on a real live feed; the surfaces are unchanged.
- Navigation changes: none.

## Visual Requirements (verify existing rendering on a real live feed — do not restyle)

- Component patterns: existing hand-built cockpit panels; the live status indicator (status dot
  + label reading canonical row-6 `stream_status`: connecting | live | stale | paused | closed);
  the `FeedBasisBadge` (reads canonical row-29 current-watch feed basis); the `/journal` table
  rows.
- Layout: unchanged — `/` single-screen tape cockpit (status area + panel grid + thesis strip);
  `/journal` filterable table.
- Key visual effects: per DESIGN SYSTEM — `stale` must be visibly distinct from `live` in the
  status area (amber/neutral treatment for the degraded state vs green/live), monospaced
  numerics, calm dark surface, restrained color. The IEX disclosure line must be legible in the
  viewport.
- States to handle (verify, not build): `live`, the transient `stale` (held visible in a still),
  recovery back to `live`; the live `iex` feed-basis badge + disclosure; the unknown-symbol
  honest-failure carry (J-14, "not a tradable symbol"); the explicit failure panel (J-23).

## Key Test Scenarios (binding — the iteration is complete only when these pass)

- **J-15 flips `unknown → passing`:** a real Live watch (liquid name, e.g. `F` or `AAPL`)
  visibly shows `live`, then a held/await-stabilized still that VISIBLY contains the `stale`
  indicator across a genuine lull with the recent-trades count NOT advancing during the gap, then
  recovery to `live`. Primary proof: poll `GET /tape/{t}/summary` (canonical `stream_status`) to
  confirm the `live → stale → live` sequence (iter-19 designate-REST-primary lesson); the pixel
  is the visible corroboration; the gated integration run is the authoritative pipeline proof.
- **J-67 live leg captured:** the live IEX cockpit renders `FeedBasisBadge` reading `iex` with
  the disclosure line ("live verdicts read the single-venue IEX feed; historical replay and
  studies use SIP — spreads and prints differ") in the viewport; a live-declared thesis produces
  a `/journal` row stamped `data_feed = iex` (no SIP/IEX pooling). J-67 stays `passing`, now with
  live pixel evidence complete.
- **Operator-gated credentialed live-socket integration run executed:**
  `TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest apps/backend/tests/test_live_integration.py -v -s`
  asserts `stream_status == "live"`, `event_count > 0`, real bid/ask, a valid tape state, and the
  correct live scenario descriptor (`live <SYMBOL>`). Prefer a tight-spread liquid name
  (`TAPEOLOGY_LIVE_SYMBOL=F` default); a high-priced name on the wide free IEX top-of-book may
  honestly read `unclear` — correct, not a failure.
- **Required-still-passing spot-checks stay green:** J-01/J-02/J-08 (SIM-BUYER cockpit +
  REST==UI), J-11/J-16/J-18 (credentialed SIP historical), J-14 (unknown symbol → "not a
  tradable symbol"), J-23 (explicit failure panel still visible), J-68 (no-thesis cockpit
  unchanged — full panel grid + idle thesis strip + sound toggle render undisplaced).
- **No anti-goal violation:** during the `stale` lull NO trade/quote/price/state is fabricated
  (the no-fabricated-data anti-goal IS the heart of J-15 — no synthesized catch-up on resume; the
  feeder discards anything queued during the gap and rejoins CURRENT real data); the live IEX
  basis is explicitly labeled; no aggregate pools SIP with IEX; no order/broker surface appears.
- **J-68 byte-identity holds:** verified with a LIVE `git status --porcelain apps/` (empty) and
  `git diff --stat HEAD -- apps/backend/ apps/frontend/` (empty) — NOT the prompt's pre-baked
  git-status block (iter-28 lesson: the start-of-session snapshot can be stale).
- **Backend suite green, zero re-pins, exit 0;** `test_observer_equivalence.py` re-run green.
  (Verify via exit code — backend `addopts = "-q"` double-quiets and suppresses the count line if
  you add `-q`; iter-17 lesson.) Do NOT duplicate the already-covered `stale_gap_seconds`
  watchdog unit test — the live run is the missing real-socket evidence.

## Operating notes & assumptions (documented, not asked)

- **Assumption:** the orchestrator cannot itself confirm live market state or vendor
  reachability. The developer/QA legs surface that honestly. Per the spec's escalation clause: if
  despite open hours + configured creds the real socket cannot be reached (invalid creds, vendor
  outage, or a hyperactive feed that never lulls past 10s within a bounded session), record the
  gated run's outcome honestly, capture whatever live evidence is reachable, and let the
  evaluator decide whether J-15 holds `unknown` (scheduled, not stalled) or escalates — **do NOT
  fabricate the stale flip.**
- **Backend must be (re)started with `apps/backend/.env` loaded** so the live creds are in
  `os.environ` (the adapter reads creds from the environment only; iter-28 noted `config.py`
  does not auto-load `.env`). Verify server-code identity with a cheap canary probe before
  capture (iter-6).
- **Do NOT run `npm run build` against the live dev server's shared `.next` before browser QA**
  — it corrupts `.next` and silently downgrades browser tests to SKIP on exactly a UI-evidence
  iteration (iter-2 / iter-18). Run any build with an isolated dist dir or AFTER browser QA;
  re-probe the frontend with a fresh-server canary before declaring any SKIP unavoidable.
- **Capture discipline:** the `stale` indicator is transient (clears on the next print, which on
  a liquid IEX name can arrive within seconds). Hold/await-stabilize the capture at the moment
  `stale` is on screen, OR watch a quieter symbol / off-peak minute where lulls exceed 10s
  comfortably. Prefer full-page stills over element-timed shots for the transient state. Run
  `md5sum` over the evidence dir before citing.

## Scope-creep flags (explicitly EXCLUDED)

- The J-29 `<3s` near-instant re-watch cache fast-path — ruled soft/P2 in iter-28; J-29 is
  already `passing` on its hard clauses. Building a cache/pre-warm fast-path would risk the
  byte-identity / observer-equivalence discipline to chase a non-binding aspiration. **OUT.**
- Any new feature, page, endpoint, control, config key, schema change, or new displayed value.
  **OUT** — a non-empty application diff (absent a justified live-feed bug fix) is a defect.
- Re-litigating any already-`passing` journey beyond the Required-still-passing spot-checks.
- Any artificial inducement of `stale` that fabricates or suppresses real feed events (an honest
  socket disconnect is acceptable; injecting fake quiet by discarding real prints is not). The
  natural IEX cadence on a moderately-quiet liquid name already produces >10s gaps — observe the
  genuine flip; do not manufacture it. **OUT.**

## Path to GOAL_ACHIEVED

After these two legs land, every Must-have journey is `passing`/`already_passing` and J-68's
"all J-01–J-37 green" sentinel clause closes — the evaluator should then consider GOAL_ACHIEVED.
