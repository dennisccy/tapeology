# Phase goal-structure_ui-iter-4 — User-Visible Changes

**Phase:** goal-structure_ui-iter-4
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

**Status: zero-diff evidence-capture iteration.** Independently confirmed: `git diff --stat -- apps/backend` and `git diff --stat -- apps/frontend` are both empty, and `git status --short` shows only goal-mode bookkeeping/trace files (this phase's spec, plan, dev handoff, test-plan, review, dispatch markers, `runs/goal-session-structure_ui/trace/trace.jsonl`) — nothing under `apps/`. This matches the dev handoff's claim exactly; no application file changed this iteration.

`Frontend Present: yes` in the plan because a real, already-shipped `/structure` frontend exists and is the direct subject of this iteration's work — not because anything new was built. J-01 (levels/zones chart), J-02 (strategy registry + champion), and J-03 (structure_tape-vs-v1 comparison) were fully implemented in iterations 1–3. This iteration's entire deliverable is procedural: bring both services up, curl-confirm them, and hand a live, populated app to an independent browser-qa-agent run — so J-03 (and re-checked J-01/J-02/J-04) can move from "built but never independently photographed live" to "independently verified live," clearing iter-3's standing CLOSURE-FAIL. Every item below describes pre-existing capability, restated only because it is what this iteration's re-verification pass targets — none of it is new.

---

## What Users Can Now Do

Nothing new. Zero new capability this iteration. The following already existed before iter-4 started and renders identically today (verified unchanged via the empty `apps/frontend` diff):

- (since iter-1) Enter a symbol and as-of time on `/structure`, click Load, and see a populated price chart with S/R level lines plus an A/B/C confluence-zone table below it.
- (since iter-2) Scroll to the Registry section and see the `v1` and `structure_tape` strategy cards (entry rule, exit rules, class-scaled stop/reward/size maps) plus the champion badge (`v1`/`default`).
- (since iter-3) Scroll to the Comparison section, choose a registered dataset, click "Run comparison," and watch both strategies' backtests progress independently to `done` with side-by-side aggregates (n, net R, net $, win rate, max drawdown), a per-class A/B/C breakdown with honest `insufficient_sample` chips, a read-only Champion cross-check panel, and a Founding-baseline (PnL ledger) reference panel.

What actually changed this iteration is evidentiary, not functional: before iter-4, browser-qa-agent had never successfully photographed the Comparison section in its populated state — iter-3's run recorded SKIPPED 0/26 because the frontend had gone unreachable by the time it dispatched, leaving J-03 at `unknown` in the goal tracker even though the underlying code was complete and had been verified live by the auditor. This iteration's developer step proved the missing precondition: both services (`bash scripts/dev.sh`) start cleanly and respond with real content — `GET /health` → `{"status":"ok"}`, `GET /` → the app shell, `GET /structure` → HTTP 200 with the Comparison section's testids present in the server-rendered shell, `GET /meta/ui-routes` → the 5-route nav array including `/structure` — confirmed across both a cold start and a kill-and-restart cycle. That clears the ground for the next pipeline step (browser-qa-agent) to actually capture the populated-state evidence this report's sibling surface map is scoped for.

---

## What Changed in the Visible UI

Nothing. No page, route, component, label, layout, or copy changed anywhere in the app — `apps/frontend` carries a byte-empty diff this iteration (confirmed directly via `git diff --stat -- apps/frontend`).

---

## What Old Behavior Changed

None. No existing behavior was added to, removed, or altered — there is no code diff for any behavior to change in.

---

## Not Visible Yet

Carried forward from iter-3, unchanged (not addressed this iteration — no code changed, so none of these moved):

- `result.null_baseline` (the seeded random-entry baseline aggregate) is returned by every `GET /research/backtests/{id}` payload and is typed in the frontend (`BacktestResult.null_baseline`), but the Comparison section's result cards never render it.
- No cancel control on the Comparison section — `POST /research/backtests/{id}/cancel` exists and is used elsewhere (Studies page) but has no button wired here.
- No history of past comparisons — reloading `/structure` always starts from the idle state; `GET /research/backtests` (the plural list endpoint) is never called by the frontend, so a comparison run in an earlier session or via curl/MCP cannot be browsed back to.
- A `/datasets` library/inventory page (browsing full dataset metadata — event counts, checksum, source, timeframe coverage) still does not exist — explicit non-goal (roadmap Card 5.9).
- `apps/frontend/components/PriceChart.tsx`'s latent z-index empty-state occlusion (Cockpit/J-04, carry-forward finding F2) remains unfixed — correctly out of scope this iteration since it touches neither the Cockpit route nor `PriceChart.tsx`.
