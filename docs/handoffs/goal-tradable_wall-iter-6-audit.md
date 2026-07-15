# goal-tradable_wall-iter-6 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05 is genuinely achieved. `/structure` now leads with the Tradable Map (verbatim from `GET /research/tradability`), moves the raw 1,800-level view behind an off-by-default toggle, and adds Case Studies (+drill-in) and Edge Report sections — every displayed value is `String(value)`-verbatim off its owning endpoint with no client recomputation (I traced every new rendering component). The single backend touch — the B3 scan-cache atomic-rebind hardening in `setups.py` — is correct, byte-transparent, and covered by a real structural regression guard plus a concurrency test (both run green). Frozen foundations hold (`config_fingerprint` still `4d665603569b9dbf`, diff scoped to exactly the 6 allowed files). It is PASS_WITH_GAPS rather than a clean PASS because one documented minor UX limitation is carried forward and the browser-QA pass was materially thinner than its own 20-case plan on a few DoD-adjacent states (verified instead via the dev's endpoint smoke test + my code reading) — neither compromises the goal.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified-clean): B3 scan-cache atomic publish is genuinely torn-read-free**
`apps/backend/app/research/setups.py:369` declares `_SCAN_CACHE: tuple[tuple, dict] | None = None`; `compute_setups` (`setups.py:402-409`) reads it ONCE into a local (`cached = _SCAN_CACHE`) and publishes a cache miss via ONE rebind of the whole slot (`_SCAN_CACHE = (key, result)`). Under CPython a name rebind is a single bytecode store, so a concurrent reader observes either the entire prior `(key, result)` pairing or nothing — never a fresh key paired with a stale/`None` result. This exactly matches the iter-5-audit-named fix (tuple rebind, no lock, no new import) and is byte-identical to the pre-fix output (the scan body `_run_full_panel_scan` is unchanged). Verified by reading the code and running the two new tests.

**B2 — OBSERVATION (verified-clean): frozen foundations preserved**
`git diff --name-only -- apps/` touches exactly `setups.py`, `test_setups.py`, and the four frontend files — no `tradability.py`/`edge_report.py`/`levels.py`/`strategies.py`/`backtests.py`/`config.py`/`datasets.py`/engine/adapter leakage. `Config().config_fingerprint()` prints `4d665603569b9dbf` live, and the 43 fingerprint-pinning tests pass. The `setups.py` change is confined to the cache mechanism; no config field, signature, or scan-output change.

### Frontend Findings

**F1 — GAP (not fixed): Case Studies drill-in stays open on a filtered-out event**
`apps/frontend/app/structure/page.tsx:1840` renders `<SetupDrillIn>` whenever `selectedSetupId !== null`, independent of `filteredSetupsEvents` (`page.tsx:1476`). If a user selects a row then changes the symbol/reaction filter so that row no longer matches, the drill-in remains open on the previously-selected event. This is **not** a data-integrity or honesty issue: the drill-in has its own self-labeling header (`page.tsx:527-544` shows the event's own symbol/session/reaction), and it displays correct real data for the event it last fetched — it is not presented as a member of the filtered set. The phase spec's IN SCOPE / DoD never required the drill-in to auto-close on filter change. Self-disclosed as Known Issue #3 (dev handoff) and MINOR (reviewer). Left unfixed — auto-clearing `selectedSetupId` on filter change is a UX enhancement beyond this iteration's scope, not an audit-class defect.

**F2 — OBSERVATION (verified-clean): zero client recomputation holds (the central rail)**
Every new value is `String(value)`-verbatim: bands (`BandRow` `page.tsx:363-392`), forward returns (`ForwardReturnsList:428`, raw `return_fraction`, `null`→"—", never a %-conversion), tape timeline (`TapeTimelineList:488`), edge-report cells (`EdgeReportCellRow:596`, `insufficient_sample` shown inline), and surviving cells (`SurvivingCellRow:678`, reading the backend-served `holdout_positive_edge`/`holdout_cell` — confirmed served at `edge_report.py:416-418`, not client-derived). The Case Studies filter (`page.tsx:1476-1480`) is a pure `.filter()` over already-served rows (exact symbol/reaction match). The only arithmetic in the new code is `b.ts * 1000` chart-bar time filtering (`page.tsx:1468`), a seconds→ms display filter that mirrors the pre-existing raw-levels chart (`page.tsx:1448`) — not a domain-value recomputation.

**F3 — OBSERVATION (verified-clean): honest states + frozen raw-levels toggle**
Tradable Map covers idle/loading/error/`no_bar_series_for_symbol`/empty-bands/populated with `basis_as_of` shown (`page.tsx:1597-1644`); Edge Report renders `report.register` verbatim above an honest first-class empty state (`page.tsx:740-755`); the drill-in discloses `reaction_boundary_truncated` with `effective_reaction_horizon_bars` in a distinct amber note (`page.tsx:553-560`), never as a full-horizon reaction. `showRawLevels` defaults to `false` (`page.tsx:1156`); the "on" render is additive-only (StructureChart `bands` prop defaults `[]`, existing level-line loop untouched — diff confirms no removed lines in that path), so the era-5 view is byte-identical when toggled on. Era-5 Fetch/Registry(`:1960`)/Comparison sections preserved below the new sections.

### Test Findings

**T1 — OBSERVATION: QA browser pass incomplete vs. its own 20-case plan**
The QA report confirms 7/20 cases PASS with screenshots (Tradable Map default, toggle, Case Studies render+filters, Edge Report render, era-5 Fetch/Registry) but leaves several DoD-adjacent cases PENDING: TC-06 (pinned AAPL 06-22 drill-in = `rejected` + forward returns), TC-07 (boundary-event truncation disclosure), TC-08 (tape-timeline state), TC-10 (`insufficient_sample` cell), TC-17 (DevTools zero-recomputation spot-check). These DoD items ARE independently verified — the dev's live endpoint smoke test captured the exact real shapes (AAPL 06-22 = 2 events both `rejected`/negative returns; boundary event AAPL 2026-07-13 = `chopped`/truncated/horizon 77/`tape_timeline: []`; empty edge report), the reviewer verified field shapes line-for-line, and I traced the rendering code that consumes those shapes verbatim. So the capability is demonstrably present; what's thin is the browser-screenshot evidence for a couple of drill-in/boundary states. Not goal-compromising, but the QA verdict rests more on endpoint+code evidence than on browser proof for those specific states.

**T2 — OBSERVATION (verified-honest): concurrency test is honestly characterized**
`test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair` (16 threads, barrier-synced, 0.05s widened publish window) and the structural guard `test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes` both pass (I ran them: 2 passed). The dev honestly disclosed the behavioral test alone passes 5/5 even against the reverted old two-key-dict implementation (the vulnerable window is a couple of bytecodes, too narrow for a wall-clock trick), and therefore added the source-inspecting structural test as the real regression guard — which reliably fails against the old shape. This is correct, non-self-deceiving test design, not a test-passing-by-accident weakness.

---

## 3. Domain Assessment

The core domain contract of J-05 is "render three already-owned read surfaces verbatim, recomputing nothing" — the make-or-break the coherence-auditor hard-fails. That contract is honored precisely: I found no re-derivation of any band score/class/range, reaction, forward return, tape state, PnL/register figure, or edge-report cell anywhere in the new browser code; band membership and price-in-band are display reads, and even the `holdout_positive_edge` "clears the gate" label is a backend-served boolean, not a client gate re-evaluation. The morning-markup / no-lookahead invariant is respected on the display side (`basis_as_of` is shown, enforced server-side; the chart filters bars to the as-of instant). The honesty invariants are handled with genuine care: the empty edge report is a first-class published state (not hidden, no fabricated survivor), boundary reactions are disclosed as truncated with their effective horizon, and an unclassified band renders "Unclassified" rather than a fabricated A/B/C grade. Copy discipline holds — `test_copy_discipline.py` walks all new frontend source and passes, and my manual scan found no imperative/prediction/"win rate"/"profit"/"paper trading" vocabulary (the literal field name `win_rate` is used, matching the page's established precedent). The backend hardening is the right minimal move: it closes a real torn-read window without changing what is computed, keeping the cache a rebuildable accelerator rather than a second source of truth.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT findings were identified; the two documented gaps (F1 drill-in-stale UX nuance, T1 QA browser-evidence thinness) are GAP/OBSERVATION-level and fixing them would be scope creep (F1 is a UX enhancement the spec did not require; T1 is re-running browser QA, the browser-qa-agent's job). The implementation was left unchanged.

---

## 5. Recommended Next Step

**Proceed.** J-05 is complete and correct; `/structure` is decluttered exactly to spec with the zero-recomputation rail intact and the frozen foundations preserved. Queue **J-06 (cockpit confluence — band overlay + descriptive chip on `PriceChart`)** for iter-7 as the phase spec already sequences it. Carry two minor, non-blocking notes forward: (a) optionally auto-clear the Case Studies drill-in when a filter change hides its row (F1); and (b) when a credentialed panel-symbol tick recording lands (the parallel, operator-gated J-03 headline), have the next browser-QA pass screenshot the populated Edge Report cells and a real drill-in tape timeline, closing the T1 evidence gap for those states. The goal.md "5m chart around the event" drill-in element (reviewer NOTE) remains out of scope until the `setups/{id}` payload carries a bar window.
