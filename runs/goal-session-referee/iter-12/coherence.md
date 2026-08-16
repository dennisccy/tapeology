# Iteration 12 — Coherence Audit

**Iteration:** goal-referee-iter-12
**Date:** 2026-08-16
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

All changes are field-level additions to the ALREADY-registered "Registry (families, hypotheses,
withdrawals, certificates)" row (owner `referee_registry.py`, endpoint
`GET /research/desk/referee/registry/shortlist`, endpoint cell registered at iter-8). Blueprint
already carries the iter-12 note (`runs/goal-session-referee/state/blueprint.md:315-351`)
registering the exact shape shipped — no unregistered value.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `accrual_basis` block (corpus first/last date, span, recorded/pooled session counts, longest zero-session stretch) | OK | Computed inside `shortlist_response()` itself from `readiness = playbook_occurrence_readiness(...)` — a call that already existed pre-iteration (`apps/backend/app/research/referee_registry.py:1209`, unchanged line). New code only reads `readiness["distinct_sessions"]`/`readiness["stale_basis_dates"]` (`referee_registry.py:1220-1221`) and a new pure helper `_longest_zero_session_stretch()` (`referee_registry.py:1102-1116`) that walks the SAME `newest_by_date` dict `_corpus_session_span_days()` already sorts. `test_tc7_...` (`apps/backend/tests/test_referee_registry.py:343-379`) proves `PlaybookStore.list` call count stays at the pre-iteration baseline of 2 — no second scan. `playbook_occurrence_readiness()` has exactly two call sites in the whole backend (`referee_evidence.py:370` and `referee_registry.py:1209`, confirmed by grep) — no third, independent implementation exists anywhere. |
| `informative_sessions_per_pooled_session` / `projected_pooled_sessions_to_target` (new per-candidate fields) vs. shipped `accrual_rate_sessions_per_day` / `projected_days_to_target` | OK — legitimate disclosure, not duplicate computation | See judgement below. Shipped fields' computation lines (`referee_registry.py:1197-1200`, unchanged/untouched context in diff) are byte-identical pre/post iteration, asserted by `test_tc1_tc2_tc6_...` (`test_referee_registry.py:282-285`, TC-6) and `TC-9` (empty diff on `desk_playbook*.py`/`desk_forward.py`/`levels.py`/`tradability.py`/`pnl_scan.py`). |
| Frontend rendering of `accrual_basis` + new column | OK — read verbatim, zero client arithmetic | `apps/frontend/app/desk/page.tsx:4739` binds `const accrualBasis = shortlist.accrual_basis;` (destructure, not derivation); the basis line (`page.tsx:4758-4790`) and new `<td>` (`page.tsx:4842-4849`) only interpolate/format fields, never combine them. `_PRICE_ARITHMETIC_FIELDS` guard extended for exactly these new fields (`apps/backend/tests/test_desk_ui_guards.py:133-146`) with a real counter-test proving the widened pattern both catches a seeded violation on the new fields AND passes the actual shipped rendering clean (`test_desk_page_price_arithmetic_guard_catches_accrual_basis_and_pooled_projection_arithmetic`, `test_desk_ui_guards.py:154-201`). |
| Fetch path for the shortlist endpoint | OK — single canonical fetcher, single consumer | `apps/frontend/lib/api.ts:2079` is the only `fetch(".../registry/shortlist")` call site in the frontend; `RefereeShortlistResponse`/`RefereeAccrualBasis` types (`apps/frontend/lib/types.ts:2171,2185`) are consumed only by `RefereeRegistrySection()` in `page.tsx` (grep confirms no second consumer). |

**Judgement on the two "projected" columns (flagged in the dispatch note for careful review):**
`projected_days_to_target` (shipped) and the new `projected_pooled_sessions_to_target` are NOT
two computations of the same value — they are two different, explicitly and separately labelled
metrics sharing one canonical numerator:

- Both divide the SAME per-candidate `n_sessions` / `target_sessions` (each candidate's own
  already-computed, already-context-filtered session count, computed exactly once per candidate
  and reused for both — never a second or differently-filtered recomputation, per
  `referee_registry.py:1243-1251` in the diff).
- The DENOMINATORS are genuinely different measurement bases: raw calendar-day span
  (`corpus_span_days`) vs. corpus-wide recorded/pooled session count
  (`accrual_basis.pooled_sessions_at_current_basis`) — not two implementations of one basis.
- Both are additive: the shipped pair is untouched (byte-identical, TC-6/TC-9), the new pair sits
  BESIDE it in its own column with a distinct header ("Projected sessions" next to "Projected
  days") and its own `data-testid`.
- The divergence between the two is the entire POINT of the feature (a corpus recording gap makes
  the calendar-day projection overstate the wait; the session-basis projection is the honest
  correction) — documented in three independent places: the blueprint's iter-12 note, the new
  `/desk` basis line copy, and `docs/referee-statistical-spec.md` §9's dated addendum
  (`docs/referee-statistical-spec.md:379-391`, verified present and content-checked by
  `test_tc17_...`, `test_referee_registry.py:390-407`).

This is the "legitimate disclosure with distinct labelled bases" case, not the "numbers don't
match" duplicate-source failure mode the gate exists to catch — there is no risk of the two
figures silently disagreeing about the same claim, because they are not making the same claim.

## Information Architecture check

No new page, route, or nav entry. The blueprint's Navigation skeleton
(`runs/goal-session-referee/state/blueprint.md:15-27`) explicitly scopes this era to "adds
sections to Desk only, no new route," and the IA table's J-05/J-07 row (now also tagged J-11,
`blueprint.md:39`) already names `/desk` → Referee Registry as this feature's canonical home. The
diff touches zero nav/router/App-shell files (confirmed: the 6 changed files are
`referee_registry.py`, two test files, `page.tsx`, `types.ts`, and the spec doc — no
`Sidebar`/`Nav`/router file among them).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Accrual basis line + "Projected sessions" column, `/desk` → Referee Registry | OK | New markup sits inside the EXISTING `<div data-testid="referee-registry-section">` wrapper, above the EXISTING `<table data-testid="referee-shortlist-table">` (`apps/frontend/app/desk/page.tsx:4758-4790`); no new `<section>`, no new route file. Reachability unchanged from the already-shipped Referee Registry section (same nav depth as J-05/J-07). |

No `ui-surface-map` report exists for this iteration (`reports/phase-goal-referee-iter-12-ui-surface-map.md` absent) — expected for a lean iteration with no new route; surfaces derived directly from the diff instead, per the agent's no-op rule.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Minor labelling nuance: the shortlist table now has both a "Sessions" column (raw occurrence
  session count, shipped) and a "Projected sessions" column (new, a projected wait measured in
  sessions) sitting in the same row. The header text is clear and parallels the shipped "Accrual /
  day" → "Projected days" pair, so this reads correctly on inspection, but a first-glance skim
  could momentarily conflate the two "sessions" columns. Not a violation — no fix required, purely
  a polish note for whichever iteration next touches this table's header row.
- `informative_sessions_per_pooled_session` is API-only this iteration (no UI column), per an
  explicit, already-logged assumption (`runs/goal-session-referee/state/assumptions.md`, iter-12
  entry) and the iteration spec's own scoping. This is a deliberate, disclosed omission, not an
  unregistered value — no WARN needed.
