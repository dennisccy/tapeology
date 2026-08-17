# Iteration 1 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-1
**Date:** 2026-08-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Corpus readiness truth — `totals.{distinct_symbol_days,distinct_datasets,rth_minutes_covered,session_equivalents,referee_tick_gate_symbol_days}` | OK | Computed once in `apps/backend/app/research/micro_readiness.py:776-861` (`build_readiness`); served solely by `GET /research/desk/micro/readiness` (`apps/backend/app/research/micro_routes.py:41-47`) — exactly the module+endpoint pair pre-registered in `runs/goal-session-rapid-microscope/state/blueprint.md`'s Data Contract. |
| Per-shard `checksum`/`trade_count`/`quote_count`/`data_feed`/`window_start_utc`/`window_end_utc`/`split` | OK — read verbatim, no second parse | `apps/backend/app/research/micro_readiness.py:790-830` reads straight off `DatasetStore.list()`'s own metadata dict (`meta["checksum"]`, `meta["event_counts"]["trades"]`, etc.); confirmed by `TC-4` (`apps/backend/tests/test_micro_readiness.py:419-430`) which asserts byte-identity against the store's own records. |
| `referee_tick_gate_symbol_days` (150) | OK — imported verbatim, no duplicate constant | `apps/backend/app/research/micro_readiness.py:564` imports `REFEREE_TICK_GATE_SYMBOL_DAYS` from `referee_evidence.py`; used directly at `:852`. Repo-wide grep confirms no second definition of this constant anywhere outside `referee_evidence.py` and this one import site. |
| `fallback_frac` (per-shard Stage-2-fallback rate) | OK — genuinely new metric, no existing canonical source to collide with | Grep-confirmed `fallback_frac` does not exist anywhere else in the codebase before this iteration. Its Stage-1 precondition mirror (`_quote_rule_decides`, `micro_readiness.py:645-651`) is a byte-for-byte match of the actual precondition in the canonical `classify_aggressor` (`apps/backend/app/engine/aggressor.py:43-47`), and is cross-validated against that real function's own observable output (not merely against a second hand-copy of the same formula) in `apps/backend/tests/test_micro_readiness.py:1029-1054`. `classify_aggressor` itself is never reimplemented — only a boolean it does not itself expose ("which stage fired") is newly derived. Not a duplicate computation of the registered "engine features/side" value. |
| `WF_TRAIN_MIN_SESSIONS` (40) / `WF_TEST_MIN_SESSIONS` (20) → `study_floors[].required_sessions` (60) | OK — first code representation, not a duplicate | Repo-wide grep confirms these two names are defined nowhere else. `micro_readiness.py:580-581`'s own docstring self-discloses this is a provisional transcription of `docs/rapid-validation-spec.md §1`, pending a future `walkforward.py` (J-05) becoming the canonical owner — logged as a reversible interpretation call in `runs/goal-session-rapid-microscope/state/assumptions.md` (iter-1). |
| UI display of every value above | OK — fetched only from the canonical endpoint, zero client-side arithmetic | `apps/frontend/lib/api.ts:2152-2177` (`fetchMicroReadiness`) fetches only `${API_BASE}/research/desk/micro/readiness`. `apps/frontend/app/desk/page.tsx`'s `MicroReadinessSection` (~line 5849 on) renders every numeric via `.toFixed()`/`.toLocaleString()` (formatting only). Mechanically enforced by the widened `_PRICE_ARITHMETIC_FIELDS` guard in `apps/backend/tests/test_desk_ui_guards.py:39-52`, with a seeded counter-test proving it actually fires on injected arithmetic (`test_desk_ui_guards.py:521-539`). |

No new displayed value in this iteration falls outside the pre-registered Data Contract row — the blueprint registers the module+endpoint pairing at the endpoint granularity, and every field served by `GET /research/desk/micro/readiness` is the natural elaboration of that one row (confirmed against the iteration spec's own "Data-contract additions" section, which transcribes the identical response shape).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| "Microscope Readiness" section on `/desk` | OK | New `<section aria-label="Microscope Readiness">` appended as the last section on the existing `/desk` page (`apps/frontend/app/desk/page.tsx`), directly below the shipped "Referee Runs" section and before the page's closing `</main>` — exactly the home the blueprint's IA table pre-registers ("Rapid Microscope … rendered BELOW the Referee sections … Microscope Readiness (J-01)"). No new route/page file was created (`git status` shows only `apps/frontend/app/desk/page.tsx` touched under `apps/frontend/app/`). Reachable in 1 click (persistent top nav → Desk) plus an in-page expand — well inside the ≤2-click bar. `app/meta.py` (`UI_ROUTES`, the nav skeleton) is confirmed untouched by this iteration's diff. |
| Shared-component reuse (no parallel shell) | OK | `CollapsibleSection` has exactly one definition, `apps/frontend/components/CollapsibleSection.tsx:25`, imported and reused by the new section rather than redefined. `LoadingPanel`/`UnavailablePanel`/`EmptyState` each have exactly one definition inside `desk/page.tsx` (lines 442/455/469, pre-existing, shared by every other desk section) — the new section calls these, it does not add competing copies. |
| Duplicate-home check | OK | This is the era's first Rapid-Microscope UI surface; no other page currently shows tick-corpus inventory data, so there is no existing home to collide with. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Out-of-scope FYI, not a coherence finding (does not affect this verdict): the new counter-test `test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic` (`apps/backend/tests/test_desk_ui_guards.py:521-548`) was spliced into the middle of the pre-existing `test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmetic` (the J-11 counter-test). The older test's body now contains only 1 of its docstring-claimed 5 assertions (`:517-518`); the other 3 (`seeded_signal_sessions`, `seeded_baseline_truncated`, `seeded_baseline_unmeasured`, now at `:541-548`) were silently absorbed into the new iter-1 test instead. Every assertion still executes — no test coverage is actually lost — but both tests' docstrings now misdescribe their own bodies. This is a test-file hygiene defect, not a Data Contract or Information Architecture violation, so it is out of this gate's scope; noting it for the reviewer/dev to tidy.
- Labeling, numeric formatting (`.toFixed(2)` for `fallback_frac`, `.toFixed(4)` for `session_equivalents`, `.toLocaleString()` for counts), and visual style (`text-xs`, slate palette, `font-mono` for numeric columns) are consistent with the adjacent shipped Referee sections on the same page — no drift observed.
