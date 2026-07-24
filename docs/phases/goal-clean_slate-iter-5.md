# Goal Iteration 5 — The kept product stands: full regression sentinel + Case Studies restore + inventory close-out

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** clean_slate
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(This era's one sanctioned exception, operator-approved 2026-07-23: the journal/studies/performance product surfaces are REMOVED outright — never mutated-in-place — and their historical records stay readable; nothing else moves.)* *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **No research-value change beyond the documented epoch bump.** Every number a KEPT surface serves (levels, bands, touch events, edge cells, pnl rows) stays byte-identical on identical inputs; the ONLY sanctioned change is the `config_fingerprint` value itself, moved once via the J-04 Path B journey; cross-epoch pooling is forbidden forever. *(critical)*
  - **Deletion is complete, never cosmetic.** No orphaned imports, dead components, unreachable routes, dangling MCP tools, or skipped tests survive; a deleted surface is gone from code, routes, nav, MCP, types, and tests alike — grep-provably. *(critical)*
  - **No new features.** This era ships zero new product capabilities, pages, endpoints, strategies, or Config fields; anything new belongs to the next eras. *(critical)*
  - **Relocations are moves, not rewrites.** `r_basis` and the dataset-source constants keep byte-identical behaviour at their new homes; every kept caller's output is proven unchanged. *(critical)*
  - **Never modify the charts beyond the one named edit.** No commit in this era may edit `StructureChart.tsx` at all, or edit `PriceChart.tsx` beyond removing its thesis-geometry overlay build (I-7 chart clause); the three chart guard suites must pass byte-unmodified; any other chart diff — visual or behavioral — is a veto-class defect. *(critical)*
  - **Never touch a historical record.** No commit in this era may delete, rewrite, truncate, or re-stamp journal.db's existing rows or tables, any PnL-ledger row, anything under `docs/goal-archive/` or `runs/goal-session-*`, or any `reports/goal-session-*-delivered.md` — a diff touching any of these is a veto-class defect (deleting CODE is the mandate; deleting RECORDS is forbidden). *(critical)*
  - **No guard weakening.** `test_no_execution_path.py`, the source-introspection guards, and every kept test stay as written; the fingerprint pins change ONLY inside J-04 per Path B, never to make a red test green. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block in `docs/goal.md` — it MUST NOT edit human-authored journeys, the Anti-goals section, or any other part of that file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Prove the four-journey demolition genuinely stands as a whole product: a full-suite-green regression pass under the new fingerprint epoch, a complete browser walk of every kept surface (both charts, tradable map, a restored Case Studies drill-in, the honest Edge Report state), and a session-wide diff-vs-inventory close-out — closing J-05, the interlude's last Must-have journey.

## BACKGROUND

J-01–J-04 are all independently re-confirmed `passing` across four prior iterations (each with its own byte-level re-verification, not just a trusted handoff); J-05 is the only remaining non-passing journey and the era's own closing sentinel — goal.md's Success Criteria list it last because its acceptance (full suite green + a complete browser walk + a cumulative diff-vs-inventory cross-check) is only evaluable once J-01–J-04 have landed. Iter-4's evaluator explicitly recommended `full` depth for this reason and named one blocking carry-forward, open since iter-0's lesson: `SHOW_CASE_STUDIES = false` (`apps/frontend/app/structure/page.tsx:335`, set by an unrelated commit `e60f6a7` three days before goal.md was authored) makes J-05's literal "Case Studies drill-in" clause unsatisfiable as shipped. This iteration resolves that ambiguity by restoring the flag (see `assumptions.md` iter-5 entry) as its one code change, then runs the full regression + browser sentinel + inventory cross-check. **Depth is `full`** (not because of an ESCALATE — the prior verdict was `CONTINUE` — but per the "Picking depth" triggers): the work is browser-verified with veto-class charts (T-8), crosses backend (full suite + multiple grep audits) and frontend (the restore + browser walk), and requires the audit/coherence/closure lanes to produce the session-wide diff-vs-inventory cross-check that goal.md's Success Criteria #2 demands — none of which a lean developer→reviewer→browser-qa cycle can produce. Lessons applied: iter-1's ("full suite green" is now a literal, no-carve-out claim — TC-1 asserts 0 failed, not "0 modulo one"); iter-2's (grep `apps/backend/tests` for stray `read_text()`/`open()` references to a deletion target before trusting "nothing else touched" — re-applied here across the FULL cumulative diff, not just this iteration's); iter-4's (a derived-fingerprint pin can hide from a literal-string grep — the cross-check re-confirms the 14th, derived pin site by name, not only by grepping the retired literal).

## IN SCOPE

### Backend
- [ ] Run the full backend pytest suite fresh; confirm `0 failed` under the current pin `08e471b10130e1e2` (no pre-authorized red test remains — J-03 already closed the one iter-1 carried).
- [ ] Re-run `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, and the four fast_wall source-introspection/chart guards (`test_backtests.py`'s two pinned blocks, `test_setups.py`'s two pinned blocks, `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`) in isolation; confirm byte-identical file content vs. iter-4 (`git diff` on the test files themselves is empty).
- [ ] Grep-confirm the final surface inventory: all 15 I-1 deleted routes 404 on the running backend; `app/mcp/__init__.py`'s `list_tools()` returns exactly the 15 I-6 names; `app/meta.py` `UI_ROUTES` has exactly 2 nav rows (Cockpit, Structure); a T-12 import-grep for all 11 deleted modules (`journal_rows`, `monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`, `studies`) returns zero hits under `apps/` outside read-only history.
- [ ] Produce the FINAL I-9 byte-comparison re-capture (`kept-route-after.txt`) against iter-4's capture; expect 0 NEW diffs (the two already-sanctioned J-04 diffs — `research.pnl_ledger`, `research.backtests.list` — persist as-is; no other kept route may differ).
- [ ] Assemble the session-wide diff-vs-inventory cross-check (the cumulative diff from iter-0's baseline snapshot through this iteration) against I-1…I-9 + I-8's test dispositions + J-04's already-landed pin/baseline updates — confirm nothing outside that union was touched, independently re-confirming the derived-fingerprint pin site (`test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`) by name.

### Frontend
- [ ] Restore Case Studies visibility on `/structure`: flip `const SHOW_CASE_STUDIES` (`apps/frontend/app/structure/page.tsx`, currently observed at line 335) from `false` to `true`. Do not remove or simplify the conditional/gate structure itself — flip the literal value only (keeps the toggle reversible, matching the original commit's own stated intent).
- [ ] Reinstate the one sentence commit `e60f6a7` dropped from the `data-testid="structure-framing"` paragraph: insert "Case Studies lists every band-touch event with its reaction, forward returns, and — once recorded — its tape timeline; " immediately before the existing "Edge Report compares v1, structure_tape, and structure_tape_map..." sentence. No other text in that paragraph changes.
- [ ] `rm -rf apps/frontend/.next` and rebuild/start fresh (T-9) before any browser verification — a stale build bakes the wrong API base and ghost pages.
- [ ] No other frontend file changes. `StructureChart.tsx` is untouched; `PriceChart.tsx` receives zero further edits this iteration (its thesis-overlay removal already landed in J-02).

### New user-facing capability
The Case Studies panel on `/structure` becomes visible and clickable again — selecting a listed band-touch event opens its drill-in (tape timeline once recorded, honest "not recorded" otherwise). This is the only literal capability change; everything else this iteration is verification that the already-delivered demolished, two-page product (Cockpit + Structure, both charts, tradable map, Edge Report) continues to work exactly as shipped under the new fingerprint epoch.

### New information displayed
The restored Case Studies list/drill-in (event reaction, forward returns, tape timeline) — a pre-existing data view (`setups.py` / `GET /research/setups`, already in the Data Contract), simply un-hidden. No new field or value is introduced.

### New user actions
None new. The Case Studies row-click-to-drill-in control and its state/handlers already existed (era-5B/5C); only its rendering gate changes from off to on.

### UI surface changes
`/structure`'s "Case Studies" `<section>` (previously withheld by `SHOW_CASE_STUDIES=false`) renders again at its pre-existing position, between the Levels & Zones/raw-toggle area and the Edge Report section; the framing paragraph regains its one dropped sentence. No new page, no new section beyond what already existed pre-suppression.

### Product surface delta
Nav, page count, and every other panel are unchanged (still exactly Cockpit + Structure, 2 nav rows). The sole visible delta this iteration is the Case Studies panel reappearing on `/structure`; everything else browser-verified this iteration is a re-confirmation of already-shipped behavior, not a change.

### Blueprint conformance
Structure (`/structure`) — an existing Information Architecture home; `blueprint.md`'s nav skeleton already lists "case studies" under Structure's description (drafted at baseline directly from goal.md's Product Shape), so **no blueprint edit is required**. Cockpit (`/`) is the existing home for the sim-cockpit + PriceChart browser-verification steps. No new page, no nav-skeleton change — `blueprint.reapproval-requested` is NOT written this iteration.

### Data-contract additions
None. Case Studies' underlying value (touch events / setups) is already registered in `blueprint.md`'s Data Contract, owned by `setups.py` and served by `GET /research/setups`, unchanged by this iteration — only its client-side rendering visibility changes. No new endpoint, module, or field is introduced.

## OUT OF SCOPE

- Any new features, pages, endpoints, strategies, or Config fields (Non-Goal, verbatim).
- Any further `Config` field deletion or fingerprint-pin edit beyond J-04's already-landed, closed work — the pins move ONCE, in J-04, never again (T-3).
- Any engine change — `app/engine/` stays untouched.
- Any edit to `StructureChart.tsx`, or any `PriceChart.tsx` edit beyond what J-02 already landed (T-8).
- Re-implementing or re-litigating J-01–J-04's own code — this iteration only RE-VERIFIES them; they are already `passing`.
- Removing or simplifying the `SHOW_CASE_STUDIES` conditional itself (only its literal value changes).
- Any new data recording — the browser walk relies on the already-persisted AAPL 2026-06-22 recorded window and committed fixtures; no live Yahoo/Alpaca fetch is required or in scope this iteration.
- Editing `docs/goal-archive/`, `runs/goal-session-*`, `reports/goal-session-*-delivered.md`, or any existing `reports/pnl/pnl-history.md` row.
- Extending/replacing the `journey-scripts/J-05.json` golden script is a testing-artifact task the ui-test-designer/browser-qa lane may perform (see NOTES) — it is not itself new product scope and does not require a separate iteration.

## DEFINITION OF DONE

- [ ] Target journey J-05 passes via browser-qa-agent — full screenshot set for: sim cockpit settle + both charts (candles, timeframe switch, band overlay, live tape bars), `/structure` Load of AAPL as-of 2026-06-22 (wall band renders), Case Studies drill-in, Edge Report honest current state (TC-4–TC-11).
- [ ] Full backend suite reports `0 failed` under pin `08e471b10130e1e2` (TC-1).
- [ ] Every guard/chart-guard suite passes byte-unmodified (TC-2).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain `passing` (TC-3, TC-12, TC-13, TC-14 — deterministic replay of `journey-scripts/J-02.json` + LLM fallback for J-01/J-03/J-04's keyless backend surfaces).
- [ ] Session-wide diff-vs-inventory cross-check reports zero out-of-inventory changes (TC-15).
- [ ] `SHOW_CASE_STUDIES` restored to `true` and the framing-copy sentence reinstated (TC-16).
- [ ] No historical record touched (TC-17).
- [ ] No anti-goal violation introduced.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-clean_slate-iter-5-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (the full walk: sim cockpit + both charts, `/structure` Load + wall band, Case Studies drill-in, Edge Report state). Regression smoke replay: `journey-scripts/J-02.json` (deterministic golden) plus an LLM-fallback confirmation touch of J-01/J-03/J-04's kept surfaces (nav, MCP tool count, 404s) since those three have no dedicated browser golden (they are keyless/backend journeys).
- Unit/integration: full `pytest` (77 test files); the named guard/chart-guard files in isolation; the I-9 fingerprint-site check (13 base-literal sites + the 1 derived-pin site, by name); the T-12 import-grep sweep for all 11 deleted modules; the I-1 404 sweep for all 15 deleted routes; MCP `list_tools()` name/count check.
- Error cases: each of the 15 deleted routes must return exactly HTTP 404 (not 200, not a redirect, not a "coming soon" body); the Edge Report panel must render its honest "Edge report not computed yet." + Compute-button state when no warm cache exists (never a blank/broken panel).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract
addition above maps to at least one concrete scenario line, numbered
sequentially, of exactly this shape:

- TC-1: given the backend on committed fixtures at pin `08e471b10130e1e2`, when the full backend `pytest` suite is run fresh, then it reports `0 failed` and exits `0` (no pre-authorized red test remains).
- TC-2: given `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, `test_backtests.py`'s two pinned guard blocks, `test_setups.py`'s two pinned guard blocks, `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, and `test_price_chart_confluence.py`, when each is re-run in isolation, then each passes AND `git diff` on those file contents (outside the already-landed J-04 pin-assertion lines) is empty.
- TC-3: given the `default` profile fed the same fixture input as iter-4's capture, when levels/bands/setups are recomputed, then the returned VALUES are byte-identical to iter-4's captured values and only the embedded `config_fingerprint` stamp reads `08e471b10130e1e2`.
- TC-4: given `apps/frontend/.next` is deleted and the frontend is rebuilt fresh, when the operator opens `/`, then the top nav shows exactly two items — "Cockpit" and "Structure" — with no `/journal`, `/studies`, or `/performance` link anywhere on the page.
- TC-5: given the rebuilt cockpit at `/`, when the operator types `SIM-BUYER` into the ticker field and clicks "Watch", then the page displays "Buyer Control" text in the tape-state panel AND the PriceChart renders candlesticks for the simulated series.
- TC-6: given the cockpit is watching `SIM-BUYER`, when the operator switches the chart's timeframe control, then the PriceChart re-renders candles at the newly selected timeframe (a visibly different bar width/count) with no error panel shown.
- TC-7: given the cockpit is watching `SIM-BUYER` with ticks streaming, when several ticks elapse, then the PriceChart's rightmost bar visibly extends/moves (the live-tape-moving-bars behavior) and any rendered S/R band overlay stays anchored to its price level.
- TC-8: given the cockpit is watching `SIM-BUYER`, when the operator clicks "Stop", then the cockpit displays "No ticker watched".
- TC-9: given `/structure` with symbol `AAPL` and as-of `2026-06-22T21:00:00Z` (the pinned recorded window) entered, when the operator clicks "Load", then the StructureChart renders AAPL candles for that date AND the tradable-map wall band (the golden script's own concrete assertion checks the `300.11` substring; goal.md's acceptance names the ~300–302.4 band) is visible as an overlay.
- TC-10: given `SHOW_CASE_STUDIES` is restored to `true` and the AAPL 2026-06-22 window is loaded, when the operator clicks a listed band-touch event row in the Case Studies panel, then a drill-in view opens showing that event's tape timeline, or its honest "not recorded" state if no dataset was captured around that event — screenshot required (T-13).
- TC-11: given `/structure`'s Edge Report panel, when the operator views its current state, then the panel shows either populated edge cells (a warm cache exists) OR the exact text "Edge report not computed yet." alongside a visible "Compute" button — never a blank panel.
- TC-12: given the 15 I-1 deleted routes (e.g., `GET /research/journal`, `GET /research/analytics`, `POST /research/studies`), when each is requested against the running backend, then every one returns HTTP 404.
- TC-13: given the MCP server's `list_tools()`, when invoked, then it returns exactly the 15 I-6 tool names (no `journal`/`analytics`/`studies`).
- TC-14: given a repo-wide grep for an import of any of the 11 deleted modules (`journal_rows`, `monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`, `studies`) restricted to `apps/`, when run, then it returns zero hits (T-11/T-12: history under `reports/**`/`runs/**`/`docs/goal-archive/**` does not count).
- TC-15: given this iteration's own git diff, when compared against I-1…I-9 + I-8's test dispositions + J-04's already-landed pin/baseline updates, then the only newly-touched product file is `apps/frontend/app/structure/page.tsx` (the flag flip + the one restored sentence) plus any refreshed golden/test-plan artifacts under `runs/`/`reports/` — zero other `apps/` file is touched.
- TC-16: given `apps/frontend/app/structure/page.tsx` reads `const SHOW_CASE_STUDIES: boolean = false;` before this iteration, when this iteration's change lands, then the same line reads `const SHOW_CASE_STUDIES: boolean = true;` and the `data-testid="structure-framing"` paragraph's rendered text includes the sentence "Case Studies lists every band-touch event with its reaction, forward returns, and — once recorded — its tape timeline;" immediately before its "Edge Report compares..." sentence.
- TC-17: given `docs/goal-archive/`, `runs/goal-session-clean_slate/iter-0` through `iter-4`, and `reports/pnl/pnl-history.md`'s pre-iteration-5 rows, when this iteration's diff is inspected, then none of those paths show a byte changed.

## NOTES

- **SHOW_CASE_STUDIES resolution (carried forward since iter-0):** this iteration chose RESTORE over rescope — logged as an assumption-ledger entry (`runs/goal-session-clean_slate/state/assumptions.md`, `## iter-5 — goal-decomposer`). Grounds: the flag's own code comment calls the suppression reversible and confirms only the render was gated (state/handlers/data-fetch all stayed live); goal.md is the most recent, most specific statement of operator intent and names Case Studies as KEPT in four separate places (Vision point 2, Foundation invariant #5, J-05 step 2, J-05's acceptance list); no backend test references the flag (grep-confirmed); the underlying `/research/setups` data path is unaffected by the render gate, so restoration carries negligible regression risk.
- **Spec-hygiene items from iter-4's eval are now historical/closed, not actionable:** I-9's "13 pin sites" is actually 14 (the candidate-resolved `test_profile_equivalence.py` site) and TC-3's "48→40" exclusion-set arithmetic in the iter-4 spec was actually "49→41" — both were already correctly executed and independently re-verified across four evaluator passes; flagged here only so the closure auditor doesn't treat them as open work.
- **Golden refresh (testing artifact, not product scope):** `journey-scripts/J-05.json` currently covers only a scoped subset (sim-settle + wall-band load) — its own `name` field says the fuller closure (Case Studies, full-suite-under-new-pin, diff-vs-inventory) is deferred to "J-05's own iteration," which is this one. The ui-test-designer/browser-qa-agent should extend or replace this golden to cover the full walk (chart timeframe switch + live bars, Case Studies drill-in, Edge Report state) so future regression replay exercises the complete acceptance, not just the subset.
- **If this iteration's evidence is clean** (J-05 passing, J-01–J-04 still passing, zero regression, zero anti-goal violation, session-wide diff-vs-inventory cross-check clean), all 5 Must-have journeys of this interlude are `passing`. Whether that constitutes `GOAL_ACHIEVED` is the evaluator's determination alone, per the deterministic-gates + two-key confirm protocol — this spec does not presume it.
