# Phase goal-rapid-microscope-iter-15 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-15
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness → new "Sealed Tranche (Aggregate Only)" block (`data-testid="micro-readiness-sealed-tranche-block"`, table `micro-readiness-sealed-tranche-table`, cells `micro-readiness-sealed-shard-count` / `micro-readiness-sealed-symbol-days` / `micro-readiness-withheld-excluded`, per-universe table `micro-readiness-sealed-by-universe-table` or empty state `micro-readiness-sealed-by-universe-empty`) | New sub-block (inside an existing section, no new top-level section) | Surfaces `sealed_tranche` and `joinable_corpus.withheld_excluded` — both already served by `GET /research/desk/micro/readiness`, previously fetched by nothing (the type didn't have the fields) | Navigate to `http://localhost:3301/desk`, click the "Microscope Readiness" header, scroll to the new block directly below "Corpus Totals". Verify "Sealed shard count" and "Sealed symbol-days" both read `0`, "Joinable corpus — withheld (excluded)" reads `0`, and the empty state "No sealed shards recorded." renders in place of a per-universe table — matches the real store's genuinely all-zero state. |
| `/desk` | Scout Ledger family header (inside `scout-ledger-families-block`) | Changed behavior (copy) | Renders `family.family_root_id` beside `family.family_id`/`variants_tried`, closing a gap between the phase's own "new information displayed" scope and what previously rendered | Navigate to `http://localhost:3301/desk`, click "Scout Ledger". The real ledger has zero registered families today, so only "No candidates ledgered." is observable live — the family-header text itself cannot be exercised through the browser until a family exists. Confirm instead that the section still renders its empty state cleanly (no error, no missing testid) and that `tsc --noEmit` (already run by dev/review) type-checks `family.family_root_id: string` against the fetched `ScoutFamily`. |
| `/desk` | Walk-Forward empty-sequences state (`data-testid="walk-forward-sequences-empty"`) | Changed behavior (copy) | Title changed from the reused "No candidates ledgered." to "No walk-forward sequences run." | Not exercisable live today — the real Walk-Forward ledger already has one recorded sequence (`seq-d39d20e47af24671`), so the `sequences.length === 0` branch this fix touches cannot render on the running app. Confirm by reading `page.tsx:6520`: the `EmptyState` `title` prop is the literal string `"No walk-forward sequences run."` |
| `/desk` | Walk-Forward sequence-verdict block (`<div>` wrapping "Sequence verdict: ..." + the inline `<details>`/`<summary>detail</summary>`/`<pre>` under each `data-testid="walk-forward-sequence-<sequence_id>"` card) | Bugfix (invalid HTML nesting → hydration error) | The wrapping element changed from `<p>` to `<div>` so the block-level `<details>`/`<pre>` pair it contains is legally nested | Navigate to `http://localhost:3301/desk`, click "Walk-Forward" (the real ledger has one non-trivial sequence, so this renders real data, not a stub). Open the browser DevTools console (F12 → Console), then click the "detail" text under that sequence's "Sequence verdict:" line. Verify the `<details>` expands to show the verdict JSON, AND that no new console error appears and no red Next.js dev-overlay "Issues" badge appears anywhere on screen (this is the exact interaction that previously produced a "5 Issues" badge). |
| `/desk` | Validation Vault (`data-testid="validation-vault-section"` now wraps the loading AND unavailable branches, not only the success branch) | Bugfix (missing testid in 2 of 3 states) | Previously only the loaded/success return had the wrapper testid; the loading and unreachable/error early returns skipped it entirely | Part A (success, baseline): navigate to `http://localhost:3301/desk`, click "Validation Vault", confirm the section renders "No shards recorded."/"No universes registered." with no button anywhere. Part B (loading, new): open DevTools → Network tab → set throttling to "Slow 3G", reload `/desk`, immediately click "Validation Vault", right-click the pulsing loading skeleton → Inspect → confirm the nearest ancestor `<div>` carries `data-testid="validation-vault-section"`. Part C (unavailable, new): stop the backend process, reset throttling to "No throttling", reload `/desk`, click "Validation Vault", confirm the amber "could not be loaded" panel appears AND Inspect Element confirms its wrapping `<div>` also carries `data-testid="validation-vault-section"`. |
| Backend machine surface (no browser page) | 4 new MCP tools: `desk_micro_readiness`, `desk_scout`, `desk_walkforward`, `desk_vault` (`apps/backend/app/mcp/__init__.py`) | New capability, backend-only | Byte-identical read-only proxies of the 4 already-shipped `GET /research/desk/micro/*` routes; grows the MCP contract 22→26 tools | Not a browser-testable UI surface — no page, button, or link exposes these. Verifiable only via an MCP client (`call_tool("desk_micro_readiness", {})` etc.) or by reading `apps/backend/tests/test_mcp_server.py`'s new byte-identity tests, which the dev/review passes already ran. |
| Backend endpoint, no dedicated page (J-07 re-verification) | `GET /research/desk/micro/graduation` | Regression re-verification (route itself unchanged this iteration) | Confirms the era's own J-07 capability still works; this route deliberately has no frontend page or golden replay script by design | Navigate DIRECTLY to `http://localhost:8301/research/desk/micro/graduation` in the browser (backend port, not 3301). Verify HTTP 200 and a JSON body containing `"families":[]`, `"message":"No candidates ledgered."`, and `"chain_verification":{"ok":true,"failed_at_row":null,"reason":null}` against today's real, empty graduation state. |
| `/desk` | Playbook Signals panel (always-visible, `Panel title="Playbook Signals"`) + Referee Registry / Referee Adjudications / Referee Runs sections (pre-existing `CollapsibleSection`s) | Regression (unchanged) | Share the page and the same `CollapsibleSection`/`toggleSection` machinery this iteration's fixes sit beside | Navigate to `http://localhost:3301/desk`. Confirm the "Playbook Signals" panel is visible without needing to click anything (it is not collapsible). Then click each of "Referee Registry", "Referee Adjudications", and "Referee Runs" in turn and confirm each still expands to its own content with no error panel. |
| `/desk` | Microscope Readiness's PRE-EXISTING "Corpus Totals" table (`micro-readiness-totals-table`) and "Legacy Tick Shards" block (`micro-readiness-shards-block`, table `micro-readiness-shards-table`) | Regression (unchanged) | Sit directly beside the new Sealed Tranche block, inside the same section this iteration edited | With "Microscope Readiness" expanded, confirm the "Corpus Totals" table (5 rows: Distinct symbol-days / Distinct datasets / RTH minutes covered / Session-equivalents / Referee tick-gate) renders above the new Sealed Tranche block exactly as before, and "Legacy Tick Shards" renders below it unchanged. |
| `/structure` | Tradable Map (`data-testid="tradable-map-table"`) + Comparison dropdown (`data-testid="comparison-dataset-select"`) | Regression (unchanged, different route) | Confirms the `/desk`-only diff did not affect a sibling route | Navigate to `http://localhost:3301/structure`. Verify the page loads without an error banner, the Tradable Map table renders, and the comparison dropdown (`comparison-dataset-select`) is present and selectable. |
| `/` (Cockpit) | Live tape + chart, symbol input (`aria-label="Ticker"`, placeholder "Ticker e.g. SIM-BUYER") + "Watch" button | Regression (unchanged, different route) | Confirms the `/desk`-only diff did not affect the home route | Navigate to `http://localhost:3301/`. Type `SIM-BUYER` into the ticker field (Simulated mode is the default) and click "Watch". Verify the chart renders and the tape begins updating. If the chart looks static in a headless capture, cross-check against the backend payload before calling it a failure — `visibilityState: "hidden"` is known to freeze this specific chart in headless Chrome. |
| All pages | `NavBar` (`data-testid="nav-link"`, `data-label` of "Cockpit" / "Structure" / "Desk") | Regression (unchanged) | No new route was registered in `app/meta.py`'s `UI_ROUTES` this iteration | From any page, verify the top navigation shows exactly 3 links labeled "Cockpit", "Structure", "Desk" and no fourth link. |

<!-- Change Type options used above: New sub-block | Changed behavior | Bugfix | New capability (backend-only) | Regression re-verification | Regression -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/mcp/__init__.py` — 4 new `_STATIC_PATHS` entries + 4 new `types.Tool` entries
  (`desk_micro_readiness`, `desk_scout`, `desk_walkforward`, `desk_vault`), inserted after
  `desk_referee_registry` and before `pnl_ledger`; module docstring's shipped-endpoint list updated.
  Byte-identical GET proxies of already-shipped, already-UI-consumed endpoints — no new REST route,
  no new response shape, nothing a browser can reach.
- `apps/backend/tests/test_mcp_server.py` — `EXPECTED_TOOLS` widened 22→26; 9 new tests (4 tools ×
  empty+populated byte-identity, plus 1 new MCP-surface TR-2 inference sweep). Test-only; no UI
  surface.
- `apps/backend/tests/test_desk_ui_guards.py` — `_PRICE_ARITHMETIC_FIELDS` regex allow-list widened
  to cover the two new readiness numerics (`sealed_tranche.shard_count`/`.symbol_days`,
  `joinable_corpus.withheld_excluded`) plus the per-universe destructured binding
  (`universeCounts.shard_count`/`.symbol_days`). A CI guard test that constrains what the frontend
  is allowed to compute client-side — it renders nothing to a user and has no UI surface of its
  own.
- `micro_readiness.py`, `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
  `walkforward_ledger.py`, `micro_routes.py` — **not touched this iteration.** Every field this
  round's UI/MCP changes surface was already computed and served by unchanged code; this iteration
  only adds readers. Confirmed via `git status`/`git diff` (only 5 files show as modified) and the
  dev handoff's SHA-256 re-check of the six `referee_*.py` modules plus `micro_chain_ledger.py`.

---

## Summary

- **Frontend surfaces changed:** 1 existing route (`/desk`) — 1 new sub-block inside an existing
  section, 1 copy fix, 1 HTML-structure bugfix, 1 testid-coverage bugfix; no new page, no new
  top-level section
- **New pages/routes:** 0
- **Modified components:** 2 frontend files — `apps/frontend/app/desk/page.tsx`
  (`MicroReadinessSection`, `ScoutLedgerSection`'s family header, `WalkForwardSection`'s empty state
  + verdict block tag, `ValidationVaultSection`'s two early returns), `apps/frontend/lib/types.ts`
  (`MicroReadinessResponse` gains `joinable_corpus` + `sealed_tranche`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (4 new MCP proxy tools + their contract tests, and a test-guard
  allow-list widening — zero product-computation backend files touched)
