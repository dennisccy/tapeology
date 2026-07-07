# Phase goal-structure_ui-iter-4 — UI Surface Map

**Phase:** goal-structure_ui-iter-4
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## Code Change Classification

No files were changed this iteration — there is nothing to classify. Confirmed directly:

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| *(none — `apps/backend/` diff empty)* | — | — | `git diff --stat -- apps/backend` returns nothing. |
| *(none — `apps/frontend/` diff empty)* | — | — | `git diff --stat -- apps/frontend` returns nothing. |
| `runs/goal-session-structure_ui/trace/trace.jsonl` | automation artifact | none | Goal-mode session trace log, updated by pipeline instrumentation, not hand-written; not application code, no UI surface. |
| `docs/handoffs/goal-structure_ui-iter-4-dev.md`, `docs/phases/goal-structure_ui-iter-4.md`, `reports/*iter-4*`, `runs/goal-structure_ui-iter-4/**` | process artifact | none | Goal-mode bookkeeping (spec, plan, handoffs, dispatch markers) — not rendered in the running app. |

Because nothing in `apps/` changed, every row in the "Affected UI Surfaces" table below is a **re-verification of an already-shipped surface**, not a new or modified one. Change Type is marked `Re-verification (no code change)` throughout — the surfaces themselves are identical to iter-3; what this iteration adds is independent, live, populated-state photographic evidence that they still render correctly, which is the actual deliverable browser-qa-agent produces from this map.

---

## Testing Precondition (gates every row below)

Before any row below can be exercised, both services must be confirmed live: `curl -sf http://localhost:3301` (frontend) and `curl -sf http://localhost:8301/health` (backend) must both return HTTP 200. If either is down, run `bash scripts/dev.sh` and re-confirm before proceeding — this is the exact step iter-3 skipped, producing its SKIPPED 0/26 browser-qa result. The developer step this iteration already performed and verified this precondition twice (cold start + kill-and-restart) but stopped both services again at handoff, per the standing "kill any server you start" rule — the next pipeline step (browser-qa-agent) starts its own fresh instance.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | Comparison end-to-end flow (`comparison-dataset-select`, `comparison-run-button`) | Re-verification (no code change) | Primary target (J-03) — built in iter-3 but never independently photographed populated; iter-3's browser-qa recorded SKIPPED 0/26 | With both services confirmed up, navigate to `/structure`, open the `comparison-dataset-select` dropdown, choose any populated dataset, click `comparison-run-button` ("Run comparison"); confirm the label switches to "Running…" and the button disables, then confirm both the `comparison-v1` and `comparison-structure-tape` panels reach a terminal state (`done`, `failed`, or `cancelled`) without a manual page refresh. |
| `/structure` | Per-side done aggregates (`comparison-v1-n` / `-net-r` / `-net-usd` / `-win_rate` / `-max-drawdown-r` and the `comparison-structure-tape-*` equivalents) | Re-verification (no code change) | DoD requires these to byte-match a live API call, not merely render something | After both backtests reach `done`, read all five values on both cards, then independently call `GET /research/backtests/{id}` for each id (curl or the `mcp__tapeology__backtests` tool); confirm every displayed number matches the payload byte-for-byte, and confirm the keyless `structure_tape` run (`n=0`) shows the literal text "no trades (n=0)" for `win_rate` and `max_drawdown_r` — never a bare `0`. |
| `/structure` | Per-class A/B/C table + insufficient-sample chip (`comparison-class-row`, `comparison-insufficient-sample`) | Re-verification (no code change) | DoD requires the per-class breakdown's honest `insufficient_sample` labelling to render correctly under live, populated data | Under each result card, confirm exactly three `comparison-class-row` rows render (Class A, B, C) regardless of trade count; for the reference dataset's keyless `structure_tape` run, confirm every class row shows the `comparison-insufficient-sample` chip (total n=0 puts every class below the minimum sample size); cross-check every row's n/net-R/net-$ against `result.aggregates_by_class` in the same API payload. |
| `/structure` | Per-side register line (`comparison-v1-register` / `comparison-structure-tape-register`) | Re-verification (no code change) | Anti-goal / T9 vocabulary-drift check — the honesty disclaimer must be read verbatim from the payload, never a shorter frontend paraphrase | Read both cards' amber register lines; confirm both read exactly `simulated — assumed fees/slippage — not indicative of live results` (the literal constant `REGISTER` in `apps/backend/app/research/backtests.py:142`); confirm this string byte-matches `result.register` in the same `GET /research/backtests/{id}` payload for both ids. |
| `/structure` | Comparison Champion cross-check panel (`comparison-champion`, `comparison-champion-strategy`, `comparison-champion-profile`) | Re-verification (no code change) | Anti-goal check — running a comparison must never move the champion pointer | Read `comparison-champion-strategy` / `comparison-champion-profile` before and after running a comparison to `done`; confirm both stay `v1` / `default` throughout (no change from starting or completing a comparison); cross-check that `GET /research/profiles`' champion pointer is unchanged (no `set_champion_pointer` side effect occurred). |
| `/structure` | Founding-baseline panel (`comparison-founding-baseline`; `comparison-founding-row` / `comparison-no-founding-row` states) | Re-verification (no code change) | J-03 DoD detail — the founding-baseline reference row must render correctly alongside the live comparison | Confirm the Founding-baseline card shows exactly one of: a loading pulse, an amber unavailable message, a populated `comparison-founding-row` (title + "candidate train net R" + "candidate hold-out net R"), or `comparison-no-founding-row` ("No founding row yet…"); for a populated row, cross-check both net-R values against `GET /research/pnl/ledger`'s `rows.find(r => r.founding)` entry. |
| `/structure` | `StructureChart` canvas + confluence-zone table (`structure-chart-canvas`, `zone-row`, `zone-class-badge`, `zone-score`, `zone-member-level`) | Re-verification (no code change) | J-01 regression re-check — iter-1(a)'s lightweight-charts z-index occlusion lesson, explicitly named as a watch-item this iteration | Enter a symbol/as-of combination with recorded bars and levels, click `structure-load-button`; confirm candles and dashed S/R level lines render with no empty-state/loading overlay covering the chart canvas (the overlay's z-index must sit above the `lightweight-charts` canvas per the iter-1 fix, never the reverse); confirm the `zone-row` table lists each A/B/C confluence zone with a visible `zone-class-badge` and `zone-score`. |
| `/structure` | Registry section (`strategy-card` ×2, `champion-strategy`, `champion-profile`) | Re-verification (no code change) | J-02 regression re-check, including iter-2 audit finding T2 (testid collision with the Comparison section's own champion badge) | Confirm two `strategy-card` elements render (`v1` and `structure_tape`) with distinct class-scaled stop/reward/size maps; confirm `champion-strategy` / `champion-profile` read `v1` / `default`; with the Comparison section also loaded on the same page, query the DOM for `[data-testid="champion-strategy"]` and `[data-testid="comparison-champion-strategy"]` separately and confirm exactly one element matches each selector — no duplicate-testid collision between the two same-page instances. |
| `/`, `/journal`, `/studies`, `/performance`, `/structure` | Top navigation (`app-nav`, 5× `nav-link`) | Re-verification (no code change) | J-04 regression sentinel — the 5-link data-driven nav must stay intact and unaffected by any Structure-page work | From any page, confirm `[data-testid="app-nav"]` renders exactly 5 `[data-testid="nav-link"]` elements whose `data-label` values read Cockpit/Journal/Studies/Performance/Structure; confirm each link's `href` matches the live `GET /meta/ui-routes` payload; click each link and confirm it navigates to its route with no console error. |
| `/performance` | Champion summary (`champion-summary`, `champion-strategy`, `champion-profile`) | Re-verification (no code change) | J-04 regression sentinel — `/performance` must render unaffected by anything on `/structure` | Load `/performance` directly (not via in-app navigation from `/structure`); confirm `champion-summary` still renders `v1` / `default` with no console errors. |
| `/` (Cockpit) | Sim-ticker entry flow (TopBar symbol field; `IdleState`'s "Try: SIM-BUYER" hint; `ThesisStrip`'s `entry-checklist`/`thesis-strip`/`realized-r`) | Re-verification (no code change) | J-04 regression sentinel — "sim cockpit flows (SIM-BUYER/SIM-SELLER) still settle correctly," named explicitly in this iteration's test scenarios though Cockpit code is untouched | Enter `SIM-BUYER` (then separately `SIM-SELLER`) in the Cockpit's ticker field in sim mode; confirm the idle placeholder is replaced by a populated `thesis-strip` (no `watch-validation` error, no stuck `delivery-lag` indicator); let the scenario run to a close and confirm `realized-r` / `recorded-marks` populate with a value rather than staying blank or erroring. |
| `/structure` | An honest degraded state not yet independently photographed (`comparison-run-error`, `comparison-poll-error`, `comparison-no-datasets`, or a per-side `comparison-v1-failed`/`comparison-v1-cancelled`-style state) | Re-verification, bonus (non-blocking) | Phase spec's explicit "bonus, non-blocking" scenario — iter-3's audit finding F1 named these as still-unexercised by any independent browser-qa run | If practical while services are up: stop the backend mid-poll and confirm `comparison-poll-error` ("Backend unreachable while polling…") appears within ~700ms and clears automatically once the backend restarts; OR issue `POST /research/backtests/{id}/cancel` against a queued/running id and confirm that side switches to its `-cancelled` state with no partial aggregates, class table, or register shown. |

<!-- Change Type used above beyond the template's suggested list: "Re-verification (no code change)" and "Re-verification, bonus (non-blocking)" — used throughout because this iteration's `apps/` diff is byte-empty (confirmed via git diff --stat); every row documents an already-shipped surface that this iteration's job is to independently, live re-confirm, not a surface that changed. -->

---

## Backend-Only Changes (No UI Impact)

- **Zero backend diff this iteration** (`git diff --stat -- apps/backend` empty, confirmed directly) — no backend file, endpoint, or migration was touched.
- **`config_fingerprint` regression sentinel** (not a UI surface): the developer recomputed `CONFIG.config_fingerprint()` live and reports it as `4d665603569b9dbf`, matching the pinned J-04 value. This confirms the frozen-foundation invariant (byte-identical `v1` strategy / `default` profile / tape-engine thresholds) but has no corresponding UI element — it is a backend-internal invariant check, reported here for completeness, not independently re-run by this analysis (per this role's "do not run tests" boundary; the git-diff emptiness itself was independently confirmed).
- **Backend unit suite regression sentinel** (not a UI surface): the dev handoff reports 1146 passed / 1 skipped, matching the iter-2/iter-3 baseline — a regression guard, not a user-visible surface.
- Carried forward from iter-3, still true today (unchanged, not addressed this iteration):
  - `result.null_baseline` is present in every `GET /research/backtests/{id}` terminal payload and typed in `types.ts`, but no UI anywhere renders it.
  - `GET /research/backtests` (the plural list endpoint) is not called by any frontend code — no in-app way to browse previously-run backtests.
  - `POST /research/backtests/{id}/cancel` exists and is used by the Studies page for its own jobs, but the Comparison section still has no cancel button (explicitly out of scope).

---

## Summary

- **Frontend surfaces changed:** 0 (byte-empty `apps/frontend` diff this iteration)
- **New pages/routes:** 0
- **Modified components:** 0
- **Surfaces re-verified this iteration (no code change, evidence-capture target):** 11 rows above, spanning `/structure` (J-01/J-02/J-03), the 5-route nav + `/performance` (J-04), and the Cockpit sim-ticker flow (J-04) — plus 1 bonus/non-blocking degraded-state row
- **Navigation changes:** no
- **Backend-only changes:** 0 (`apps/backend/` diff empty this iteration); 2 non-UI regression sentinels reported (`config_fingerprint`, backend unit suite) — both process/invariant checks, not UI surfaces
