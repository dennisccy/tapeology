# Iteration 2 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration (J-02) is backend-only and test-infrastructure-only: zero `.tsx`/frontend files
touched (confirmed via `git status` and corroborated by `reports/phase-goal-rapid-microscope-iter-2-ui-surface-map.md`,
which independently confirms "Frontend surfaces changed: 0" via its own repo-wide grep). It ships
five new/changed backend product files (`micro_observer.py`, `micro_snapshots.py`,
`micro_features.py` new; `datasets.py`, `micro_routes.py` modified), one new benchmark script, three
new test modules, one test-hygiene move (`test_desk_ui_guards.py`), and a QA-rig fixture-seeding
change (`qa_playbook_iter7_fixture_scoped_backend.sh`). Diffed against snapshot SHA
`25d404f96956bb80991d65433e7c51b25ad7082c` (tracked files) plus direct reads of the new untracked
product files (git diff does not show untracked files).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Aggressor `side` | OK — read verbatim | `apps/backend/app/research/micro_observer.py:417` (`side = snapshot.recent_trades[0].side`), never re-derived |
| `tape_state`, `bid`/`ask`/`spread` | OK — read verbatim off `EngineSnapshot` | `micro_observer.py:419,504` |
| `absorption_score` | OK — read verbatim, never recomputed | `micro_observer.py:478` (`snapshot.primary_features["absorption_score"]`) |
| `config_fingerprint` | OK — single owner, read verbatim | `micro_snapshots.py:129` calls `config.config_fingerprint()`; sole definition remains `apps/backend/app/config.py:1351` |
| Corpus readiness truth (`micro_readiness.py`) | OK — untouched this iteration (Do Not Redo honored) | not in `git status` modified list |
| Feature snapshot metadata + build progress/runs (pre-registered blueprint row) | OK — this iteration's first concrete elaboration, matches the blueprint's registered module/endpoints exactly | `micro_routes.py:61-145` (`GET /snapshots`, `POST/GET/POST-cancel /snapshots/compute`, `GET /snapshots/runs`) vs. blueprint.md:55 |
| `GET /research/desk/micro/snapshots` boundary (build metadata only, never raw per-event rows) | OK — enforced and counter-tested | `micro_routes.py:69` returns `list_snapshot_meta(...)` only; `apps/backend/tests/test_micro_snapshots.py:376` asserts `"deferred" not in ... and "cumulative_delta" not in ...` |
| `DatasetStore.replay` (the one replay entry point) | OK — additive `observer=None` kwarg, no second replay implementation | `apps/backend/app/research/datasets.py:376-390`; existing call sites unaffected (default `None`) |
| §2.6 cross-basis unit gate (`quote_depletion`, execution/replenishment ratio) | OK in final state — a review-caught CRITICAL gap (ungated `quote_depletion` magnitude) was fixed pre-audit and is counter-tested | `micro_observer.py:680-687` (`_resolve_depletion` calls `mf.require_share_denominated_magnitude_allowed`); `docs/handoffs/goal-rapid-microscope-iter-2-dev.md:245-321` documents the fix; corpus-wide sweep shows 0 rows serving a raw magnitude under `unverified` |
| `side_source` (new, per-row) | UNREGISTERED-BUT-EXPECTED — a field of the already-registered "Feature snapshot metadata" row, not a separate top-level value; see advisory note below on its relationship to `micro_readiness.py`'s `fallback_frac` | `micro_observer.py:397-407` |

No registered value is computed a second time by a new, independent implementation living outside
its registered module, and no new UI surface fetches a registered value from a non-canonical
endpoint (there is no new UI surface this iteration at all).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET/POST /research/desk/micro/snapshots(/compute\|/runs)` | OK — backend-api only, intentionally not yet wired to any page; the blueprint's IA already names the wiring iteration (`/desk` → all four Rapid-Microscope sections, "J-08") | `reports/phase-goal-rapid-microscope-iter-2-ui-surface-map.md:57-61` (repo-wide grep of `.tsx`/`.ts` found zero references); `runs/goal-session-rapid-microscope/state/blueprint.md:42` (J-08 row) |
| `/desk` Microscope Readiness panel | OK — no code change; only the QA rig's fixture data changed | `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (staging 2 fixtures); zero `data-testid`/copy diff per ui-surface-map |

No new page, route, or nav-reachable feature ships this iteration, so there is nothing to check for
hidden-feature, reachability, duplicate-home, or parallel-shell violations. The three new backend
routes are correctly unexposed rather than prematurely half-wired — a route with no UI consumer yet
is not itself a "feature lacking a nav path" under this gate's rule, since it is explicitly staged
for a later, already-planned iteration in the IA, not left permanently orphaned.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Duplicated (but currently byte-identical) quote-rule precondition logic.** `micro_readiness.py`'s
  `_quote_rule_decides` (`apps/backend/app/research/micro_readiness.py:152-157`, shipped iter-1,
  untouched this iteration) and `micro_observer.py`'s `_side_source` (`micro_observer.py:397-407`)
  independently re-implement the identical condition mirroring `classify_aggressor`'s undisclosed
  stage-1 precondition (`quote.price >= quote.ask or trade.price <= quote.bid`). They compute
  *different* statistics at different granularities (a shard-level aggregate `fallback_frac` for
  the readiness floors vs. a per-row/per-window `side_source`/`fallback_frac_Nt` inside snapshot
  rows) — not the same registered Data Contract value, so this does not meet the FAIL bar — and the
  module docstring is explicit and well-reasoned about why it can't simply import a shared helper
  (the mirrored fact isn't on the engine's public surface at all). Today the two conditions are
  textually identical, so there is no live divergence. Worth a shared helper (e.g. a
  `classify_aggressor_stage()` primitive both modules import) the next time either is touched, so a
  future edit to one can't silently drift from the other and produce two different fallback-rate
  readings for the same underlying trades.
- No other advisory issues found.
