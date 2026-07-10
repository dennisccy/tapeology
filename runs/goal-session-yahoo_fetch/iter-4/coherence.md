# Iteration 4 — Coherence Audit

**Iteration:** goal-yahoo_fetch-iter-4
**Date:** 2026-07-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration's diff

The bounded diff file (`runs/goal-session-yahoo_fetch/iter-4/iter-diff.md`) did not exist, so I
used the invocation prompt's fallback: `git diff 1c833c4172d801d9dc4ded0636db3faafdd9dc5d` with
the standard noise excludes, plus `git status` / `git diff HEAD`.

The snapshot SHA (`1c833c4...`) is a stash-merge commit parented on `17f4f36` (the iter-3 commit),
taken **before** `49b73c9` ("chore(goal): iter 3 showcase artifacts") landed on the branch. Diffing
against it therefore also surfaces `49b73c9`'s already-committed content (README.md's "Instant
reuse of already-fetched bar data" bullet, iter-3 showcase HTML/summary files) as if it were new.
It is not — `git status --porcelain README.md` is empty and `git diff HEAD -- README.md` is empty,
confirming that bullet was committed in `49b73c9`, describing J-03 (already GOAL-passed), not
introduced by iter-4. I cross-checked with `git diff HEAD` (working tree vs. current branch tip)
to isolate iter-4's actual uncommitted work, which is exactly:

- `apps/backend/tests/test_levels_api.py` (+156 lines: 2 new tests + helpers)
- `apps/backend/tests/test_mcp_server.py` (+55 lines: 1 new test)

Zero production source files changed. This matches the iter-4 spec's explicit expectation ("No
production source change is expected to `research/levels.py`, `routes.py`'s `get_levels`, or
`app/mcp/__init__.py`") and "Frontend: None."

I additionally confirmed byte-identity directly: `git diff <snapshot-sha> -- apps/backend/app/research/levels.py apps/backend/app/research/routes.py apps/backend/app/mcp/__init__.py apps/backend/app/research/bars.py apps/backend/app/research/bar_index.py` returns empty. The excluded-path stat showed only harness/runs bookkeeping and the iter-3 showcase files noted above — no lockfile or dependency-manifest changes.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| S/R levels (price / timeframe / type) | OK | `apps/backend/app/research/levels.py` byte-identical to snapshot (empty diff); new tests only call the existing `compute_levels` (imported at `test_levels_api.py:35`) and `GET /research/levels` |
| A/B/C confluence-zone class + score | OK | Same owner/endpoint; new test `test_get_levels_confluence_zones_exact_values_on_the_committed_yahoo_fixture` (`test_levels_api.py:112-150`) asserts `zone["class"]`/`zone["score"]` read verbatim from the route response, no client-side or test-side re-derivation |
| Bar-series provenance `feed="yahoo"` | OK | New tests seed bars only through the canonical `BarStore.record()` (`test_mcp_server.py:265-272`, imported from `app.research.bars`) or the real `POST /research/bars` route (`test_levels_api.py:98-109`) — no second store, no route bypass that fabricates a `feed` value |
| Bar series + checksums | OK | Same canonical `BarStore`; the no-lookahead test's temp store (`test_levels_api.py:182-191`) is a second **instance** of the same `BarStore` class in a temp dir for test isolation, not a second store implementation — mirrors the existing PG-fixture lookahead test's established pattern |

No new displayed value/entity was introduced (spec explicitly states none; independently confirmed
— the tests assert only already-registered fields: `levels`, `confluence_zones[].class`,
`confluence_zones[].score`, `no_bar_series_for_symbol`, `feed`).

The no-lookahead test (`test_levels_no_lookahead_holds_on_real_committed_yahoo_bars`,
`test_levels_api.py:153-196`) calls `compute_levels(...)` directly on a truncated store and compares
the result to the live route's output. This is invoking the single canonical function twice (once
via the route, once directly) to prove as-of truncation — not a second computation path — exactly
mirroring the pre-existing PG-based lookahead test's pattern. Not a violation.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `reports/phase-goal-yahoo_fetch-iter-4-ui-surface-map.md`: "Status: N/A — Backend-only phase (Frontend Present: no). No UI surfaces affected." Iter spec confirms `/structure`'s existing Levels & Zones section is the already-registered canonical home for J-04 with no new route. |

`apps/frontend/components/NavBar.tsx` and the nav skeleton were not touched (not present in the
diff); no check needed beyond confirming the diff contains zero frontend files, which it does.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The independent audit report (`docs/handoffs/goal-yahoo_fetch-iter-4-audit.md`, finding B1) notes
  that frozen `compute_levels` pools all feeds for a symbol rather than feed-segregating, so the
  "never pooled across feeds" anti-goal is currently satisfied only because the tested keyless path
  gives a symbol a single `feed="yahoo"` series. This is **pre-existing frozen behavior** untouched
  by this iteration (confirmed byte-identical above) and is already logged in the blueprint's own
  NOTES / iter-4 spec NOTES as a deliberate, deferred interpretation — not a new coherence violation
  introduced by iter-4. Carrying forward as a WARN-level watch item for whenever a symbol first
  accumulates more than one feed (flagged for J-05+, not actionable now since fixing it would
  require mutating the fingerprint-locked `levels.py`, itself a critical anti-goal).
- README.md gained a bullet describing J-03's already-shipped capability; this was committed in the
  prior iter-3 showcase commit (`49b73c9`), not this iteration — noted above only to explain why it
  appeared in the snapshot-based diff, not as an iter-4 coherence concern.
