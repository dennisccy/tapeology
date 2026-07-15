# goal-tradable_wall-iter-8 Execution Plan

## What to Build
- **Cleanup A (frontend, closes iter-7 audit F1)** — gate `PriceChart.tsx`'s tradability-band fetch
  on `history?.epoch_anchor != null`; drop the wall-clock `asOf` fallback entirely so the cockpit
  band overlay never briefly draws **today's**-basis bands during the sub-second window before a
  watched session's own anchor resolves (a residual, self-correcting transient — the *persistent*
  form of this bug was already fixed in iter-7; this closes the last piece).
- **Cleanup B (backend test-only, closes iter-7 audit T1)** — correct the stale module docstring and
  test #5 in `apps/backend/tests/test_price_chart_confluence.py` so both describe the actual shipped
  (post-Cleanup-A) behavior instead of a stale pre-fix description that QA was observed echoing
  verbatim in the iter-7 report.
- **Verification only, no code** — confirm the backend's existing read paths (`GET /research/setups`,
  `GET /research/setups/{pinned AAPL 06-22 id}`, `GET /research/edge-report`, `GET /research/datasets`)
  now return populated, non-degraded data against the operator's persisted event-window datasets
  (18 files on disk today at `apps/backend/.data/datasets/`, including
  `5c7f1a44aa71412eb874cb639dde56e2.json` — the pinned AAPL 2026-06-22 window cited in the spec —
  exceeding the ≥10-window/≥5-symbol headline). This closes J-03 and the iter-4 "synthetic-only edge
  report" gap with **zero new backend code** — `setups.py`/`edge_report.py` already own these reads.
- **Browser re-verification** of J-06 (chip + band overlay on a real credentialed AAPL 2026-06-22
  replay, post-Cleanup-A), J-05 (Tradable Map still the default, unaffected), and J-07 (nav +
  regression sentinel, full suite).

No scope drift from `docs/goal.md`: this iteration is a direct continuation of Era 5B, closing the
last open journey (J-03) and the two carried audit findings — nothing here is new capability. The
phase spec's OUT OF SCOPE list (no dataset commits, no new credentialed act, no frozen-file touch, no
cockpit numeric edge figure, no survivor manufacturing, no era-6/`/datasets`/nav work) is honored as
written; flagging none of it as needing plan-level pushback.

## Agents Required
- **backend-data: yes** — test-only fix in `apps/backend/tests/test_price_chart_confluence.py`
  (docstring + test #5 rewrite), plus a live read-path smoke verification against the persisted
  dataset store (`GET /research/setups`, `/research/setups/{id}`, `/research/edge-report`,
  `/research/datasets`). **No production backend file changes** — `config.py`, `tradability.py`,
  `setups.py`, `edge_report.py`, `levels.py`, `backtests.py`, the engine, and the adapters all stay
  byte-identical; `config_fingerprint` stays `4d665603569b9dbf`.
- **frontend-ux: yes** — one production fix in `apps/frontend/components/PriceChart.tsx` (early-return
  in the existing tradability-fetch effect). No new component, no new page, no visual redesign.

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/components/PriceChart.tsx` — modify the tradability-fetch effect (currently ~L196-218):
  early-return (stay in `phase: "loading"`, skip the fetch call — do NOT drop to `"idle"`, so the
  empty-state/`tradabilityEmpty` logic, which only fires on `phase === "ready"`, never activates
  prematurely) when `history?.epoch_anchor == null`; remove the `: new Date().toISOString()` fallback
  branch from the `asOf` computation entirely; **keep the effect's dependency array exactly
  `[ticker, history?.epoch_anchor]`** (unchanged). Update the explanatory comment block immediately
  above the effect (currently ~L180-195, which documents the iter-7 fallback behavior) to describe the
  new no-fallback behavior. Verified safe: SIM providers always set a non-null anchor
  (`apps/backend/app/providers/simulated.py:137`), so deferring the fetch never suppresses the SIM
  honest-empty-state or a legitimate historical overlay — confirmed by the iter-7 audit's own
  source-level check.
- `apps/backend/tests/test_price_chart_confluence.py` — modify: (1) module docstring bullet 2
  (~L14-16) currently claims the fetch is "keyed on `ticker` alone" and "passes the CURRENT wall-clock
  time as `as_of`" — both stale/inaccurate even before this iteration; rewrite to state the shipped
  behavior (keyed on `[ticker, history?.epoch_anchor]`, fetch deferred with no request until the
  anchor resolves, no wall-clock fallback anywhere in this computation). (2)
  `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`
  (~L128-164) — replace the now-false `assert "new Date().toISOString()" in as_of_computation` with
  an assertion that the early-return/deferred-fetch guard exists and that no wall-clock fallback
  remains in the `as_of` computation; rewrite its docstring to match. The other 8 tests must stay
  green unmodified (or with only mechanical updates if line-offset assumptions shift) — none may be
  weakened or deleted.
- No other file. No backend production module, no `/structure` page change, no new MCP tool (the
  `tradability`/`setups`/`edge_report` proxies already exist in `apps/backend/app/mcp/__init__.py`),
  no config, no migration, no dataset file staged/committed.

## UI Evolution
- **New user-facing capability:** none new — this iteration removes a transient visual glitch (a
  sub-second flash of the wrong session's tradable bands on the cockpit chart) and finishes surfacing
  already-built UI (Case Studies drill-in, Edge Report) with real data instead of empty/synthetic
  placeholders. No new page, panel, button, or control.
- **New information displayed:** the pinned AAPL 2026-06-22 Case Studies drill-in (`/structure`, built
  iter-6) now shows a populated five-state `tape_timeline` around the ~300 touch, replacing "No
  recorded tape for this event."; the Edge Report section now shows populated cells (real `n`, R
  stats, PnL register, honest `insufficient_sample` where n<5) instead of the all-empty shape — both
  through the existing sections reading existing endpoints verbatim; zero new rendering code.
- **New user actions:** none.
- **UI surface changes:** none structurally — the same `/structure` Case Studies + Edge Report
  sections and the same cockpit `PriceChart` now render true-to-data instead of empty/transiently
  wrong.
- **Navigation changes:** none.

## Visual Requirements
- Component patterns: none new — reuses the existing `EmptyHint`, confluence chip, and solid
  price-line band-overlay treatments already shipped in iter-6/iter-7.
- Layout: unchanged.
- Key visual effects: none new.
- States to handle: the "waiting for the session anchor" moment must render as the pre-existing
  `loading` state, never a flash of the empty-state or a stale/wrong-session band. Re-verify the SIM
  "no tradable map" honest empty state is unaffected (SIM tickers always carry a non-null anchor, so
  this change is a no-op for them) and that live mode still never mounts `PriceChart` at all.

## Key Test Scenarios
- `cd apps/backend && .venv/bin/python -m pytest tests/test_price_chart_confluence.py -q` — all 9
  tests green with the corrected test #5 assertions; no test weakened or deleted.
- `cd apps/backend && .venv/bin/python -m pytest tests/ -q` — full suite green, same pass/skip
  baseline as iter-7 (1348 passed / 7 skipped) modulo only this iteration's own edits; zero
  regressions.
- `npx tsc --noEmit -p tsconfig.json` (frontend) — exit 0, zero type errors.
- `test_no_credential_in_artifacts.py` green; scan-report clean — no Alpaca secret in any file, log,
  or artifact.
- `config_fingerprint()` reconfirmed `4d665603569b9dbf`; `git diff --name-only -- apps/backend/`
  contains only the one test file — no frozen file touched.
- **Browser — J-03:** Case Studies → pinned AAPL 2026-06-22 drill-in shows the populated five-state
  tape timeline at the ~300 touch (use DOM-text extraction, not a screenshot, per the iter-6
  deep-scroll lesson); Edge Report shows populated cells with honest `insufficient_sample` labelling
  where n<5; `GET /research/datasets` (or store enumeration) shows ≥10 windows / ≥5 symbols including
  the pinned AAPL 06-22 window, each append-only/checksum-verified/`feed`-stamped verbatim (`sip`).
- **Browser — J-06:** cockpit chip + band overlay re-verified on the AAPL historical replay after
  Cleanup A — correct 2026-06-18 basis from first paint with no wall-clock/today's-basis flash,
  descriptive-only chip copy, live mode still hides the whole `PriceChart` component.
- **Browser — J-05:** `/structure` still defaults to the Tradable Map (≤10 bands, pinned resistance
  band present), raw-levels toggle off by default — unaffected by this iteration's changes; re-verify
  as a regression check.
- **Browser — J-07:** full backend suite + engine equivalence pass; nav bar unchanged (Cockpit ·
  Journal · Studies · Performance · Structure); sim cockpit flows (SIM-BUYER/SIM-SELLER) unaffected.
- **Error cases:** SIM-*/no-bars symbols keep the honest "no tradable map" empty state (never a fetch,
  never a fabricated band); an all-`insufficient_sample` Edge Report remains a valid, accepted pass —
  never manufacture a survivor; `sip` recordings are never pooled with `iex`/Yahoo-bar lineages in any
  cell/row/claim.
