# Iteration 3 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-3
**Date:** 2026-08-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

Backend-only iteration: zero `.tsx`/`.ts` frontend files touched (confirmed via `git status` and
`git diff --stat` against snapshot SHA `adc3f82e6d1a8c2b33e5b4309c7100f78cfcb4cc`; no
`reports/phase-goal-rapid-microscope-iter-3-ui-surface-map.md` was produced, consistent with the
iter spec's explicit "Frontend Present: no" / "This iteration ships no new UI"). It ships one new
product module (`micro_join.py`, untracked — read directly since `git diff` omits untracked files),
one new test module (`test_micro_join.py`, untracked, read directly), four modified backend product
files (`micro_features.py`, `micro_readiness.py`, `micro_routes.py`, `micro_snapshots.py`), two
modified test files, an additive-only `blueprint.md` registration edit, and a QA-journey-script-only
change (`journey-scripts/J-10.json`, excluded from the reviewed diff by design but inspected
separately since it is explicitly named in the iteration's own scope/DoD).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `joinable_corpus` (new field on the existing "Corpus readiness truth" row) | OK — single owner, single endpoint, single call site | Computed once by `apps/backend/app/research/micro_join.py:368` (`joinable_corpus_counts`); called from exactly one production site, `apps/backend/app/research/micro_readiness.py:386`; served only through the pre-existing `GET /research/desk/micro/readiness` (`micro_routes.py:126-145`, no new route). Confirmed no second call site via repo-wide grep. |
| `playbook_store` dependency feeding `joinable_corpus` | OK — reused verbatim, not redefined | `micro_routes.py:120-121` imports and depends on the EXISTING `desk_routes.get_playbook_store` / `desk_playbook.PlaybookStore`; no second provider defined |
| `desk_playbook.py` / `desk_playbook_context.py` (signal records, band maps) | OK — byte-unchanged, read-only | Neither file appears in `git status`/`git diff --stat`; `test_micro_join.py`'s TC-4 pins SHA-256 hashes of both files pre- and post-diff |
| Corpus readiness totals/shards/study_floors (pre-existing part of the same row) | OK — untouched, purely additive diff | `micro_readiness.py` diff only adds the `joinable_corpus` key to the returned dict; the totals/shards/study_floors computation above it is byte-identical |
| Snapshot rows (feature-at-trigger / outcome basis) | OK — read through the canonical owner, never re-parsed | `micro_join.py` reads only via `micro_snapshots.read_snapshot_rows` (`micro_snapshots.py:206`, co-located with the writer, the canonical "Feature snapshot metadata" owner); no raw `open()` of the rows file anywhere else in the repo (grep-confirmed) |
| Band-map wall context | OK — resolved read-only, never recomputed | `micro_join.join_band_touch` calls the caller-supplied `BandMapResolver.resolve(..., compute=False)` (`micro_join.py:706-724`); no second band-map computation |
| `spread_bps` (new cost-proxy column) | OK — reformat of an already-canonical value, not a new computation | `micro_features.py:410-422`: pure `spread / mid * 10_000.0` unit conversion of `spread`/`mid` values read verbatim off the snapshot row (`anchor_row.get("spread")`/`.get("mid")` in `micro_join.py:612`); not itself served by any endpoint yet (Part A.3 "re-format is fine") |
| `micro_join.py`'s join outputs (`feature_at_trigger`, `outcomes`) | N/A — not served by any endpoint this iteration | `join_playbook_signal`/`join_band_touch` are plain functions exercised only by tests; `micro_routes.py`'s only route change feeds `joinable_corpus`, not these. Consistent with the iter spec's own framing ("still invisible in the UI, staged for J-08") and more conservative than the J-02 precedent (not even served ahead of UI wiring) |

No registered Data Contract value is computed a second time by an implementation living outside its
registered module, and no UI surface fetches a registered value non-canonically (there is no new UI
surface this iteration at all).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/desk/micro/readiness` (`joinable_corpus` field added) | OK — additive field on an already-IA-registered endpoint, no new page/route | `runs/goal-session-rapid-microscope/state/blueprint.md`'s IA table already lists "Structure × flow join (J-03) \| keyless/automated; joinable-corpus count surfaces via Microscope Readiness \| Desk"; blueprint diff this iteration is additive-only (Data Contract row text + an explanatory HTML comment), no nav-skeleton edit |
| `journey-scripts/J-10.json` steps 9-10 | OK — QA-script data only, targets existing `/desk` testids | `git diff -- runs/.../J-10.json` shows step 9 repointed from a volatile hash to the stable `"Built from signature:"` label, and a new step 10 added using the existing `desk-playbook-date-input` testid on the already-canonical `/desk` Playbook section; no product/UI source file touched, no new page invented |

No new page, route, or nav-reachable feature ships this iteration, so there is nothing to check for
hidden-feature, reachability, duplicate-home, or parallel-shell violations.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **A second instance of the "mirrored technique, not imported" judgment call.** `micro_join.py`'s
  `_covering_dataset` (`apps/backend/app/research/micro_join.py:493-501`) is a verbatim algorithmic
  duplicate of `setups.py`'s `_matching_dataset` (`apps/backend/app/research/setups.py:503-526`) —
  identical symbol-equality + numeric `[window_start_utc, window_end_utc]` containment match,
  identical `(created_utc, id)` tie-break. The module's own docstring
  (`micro_join.py:390-396`) discloses this explicitly and justifies it as "a small, generic
  technical match over dataset METADATA, not a second implementation of any measurement rail,"
  invoking the same class of judgment call iter-2's coherence audit already reviewed and accepted
  for `micro_readiness._quote_rule_decides` vs. `micro_observer._side_source`
  (`runs/goal-session-rapid-microscope/iter-2/coherence.md`, verdict PASS, same reasoning: not a
  registered Data Contract row, so it does not meet the FAIL bar). "Which dataset window covers a
  given symbol+instant" is a technical join key, not itself a displayed/served value in the Data
  Contract, so this stays a WARN-class note, not a FAIL — but it is now the SECOND live instance of
  this exact tradeoff. Worth extracting to one shared helper (e.g. a small
  `dataset_window_match(symbol, at_epoch, records)` primitive both `setups.py` and `micro_join.py`
  import) the next time either module is touched, so a future edit to one tie-break rule cannot
  silently diverge from the other and pick a different covering dataset for what should be the same
  join concept.
- No other advisory issues found.
