# goal-i_will_be_super_rich_with_my_loved_ones-iter-16 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-16
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

Segregated journal analytics (capability 31, J-59) — the Review pillar's analytics half. The user can
now open an **Analytics** view on `/journal` and read honest, segregated aggregates of their own
journal: per `setup_type` × `direction`, partitioned by (`data_feed`, `config_fingerprint`), with the
abandonment bucket always visible and median spread/R beside every +1R figure. Plus the iter-15
carry-along: the honest-absence copy split on `/journal/[id]`.

- **New single-owner analytics module** `apps/backend/app/research/analytics.py` — `compute_analytics(store, config)`
  aggregates from **persisted rows ONLY** (theses, verdict_events, actions, review tags, the persisted
  excursion records). It NEVER recomputes any canonical value: no re-derived verdict, no second excursion
  math, no second R formula. Realized-R for the acted-trade block reuses `marks.marks_projection` (the ONE
  registered row-27 R path).
- **New endpoint `GET /research/analytics`** — the single serving path; returns the module's projection
  verbatim. Empty journal => honest empty payload `{"partitions": [], "min_sample_size": N}` (not an error).
- **Partitioning is structural** — the response is a list of `partitions` keyed by (`data_feed`,
  `config_fingerprint`); within each, `groups` are per `setup_type` × `direction`. NO "all"/pooled rollup
  anywhere. Each partition carries the full fingerprint + a short form for display.
- **Per group**: `n` (abandoned theses kept in it), an always-visible `abandonment` count (even 0), the
  per-horizon **confirmation-anchored** ternary distribution (`+1R_first | -1R_first | neither_within_horizon`)
  with a **separate** `truncated` count, `median_spread_per_r` per horizon, `median_time_to_confirm`
  (logical time; `null` = honest omission), `tag_frequencies` (USER-confirmed reviews only — machine
  suggestions never counted), and a structurally-disjoint `acted_trade` block (entry+exit realized-R via marks.py).
- **Insufficient-sample gating** — new config key `analytics_min_sample_size` (default 5); a group below it
  carries `insufficient_sample: true` with `n` still present. The key is **serving-only** and **excluded
  from `config_fingerprint`** (iter-12 page-size precedent + documented rationale).
- **Analytics display copy via taxonomy** — all labels/captions/the measurement-framing line are served by
  `GET /research/taxonomy` (`analytics` block); the frontend hardcodes none.
- **Frontend Analytics view** on `/journal` (a view toggle, thesis table stays the default), rendering the
  payload verbatim (display rounding only).
- **Carry-along** — the three honest-absence fallbacks in `JournalDetailView.tsx` (grades / excursions /
  execution checks) now split by resolved status: a still-active thesis reads "not yet"; a resolved
  pre-feature thesis reads "predates".

## Files Changed

- `apps/backend/app/config.py` -- added `analytics_min_sample_size` (serving-only) + excluded it from `config_fingerprint`.
- `apps/backend/app/research/analytics.py` -- NEW single-owner read-only aggregator.
- `apps/backend/app/research/routes.py` -- added `GET /research/analytics` (serves the module projection verbatim).
- `apps/backend/app/research/taxonomy.py` -- added `ANALYTICS_COPY` + wired it into `taxonomy_payload()`.
- `apps/backend/tests/test_analytics.py` -- NEW 16 module-invariant tests.
- `apps/backend/tests/test_analytics_api.py` -- NEW 5 endpoint + fingerprint-stability tests.
- `apps/frontend/lib/types.ts` -- added Analytics/partition/group/horizon/acted-trade + AnalyticsTaxonomy types.
- `apps/frontend/lib/api.ts` -- added `fetchAnalytics()`.
- `apps/frontend/app/journal/page.tsx` -- added the Theses/Analytics view toggle (Theses default).
- `apps/frontend/components/AnalyticsView.tsx` -- NEW analytics view (partitions, groups, all chips verbatim).
- `apps/frontend/components/JournalDetailView.tsx` -- honest-absence copy split (`isResolved`/`absentCopy`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **607 passed, 1 skipped** (full suite green, exit 0). The 1 skip pre-exists (unrelated).

Frontend type-check: `cd apps/frontend && npx tsc --noEmit` -> **clean, exit 0**.
(`next lint` is not configured in this repo — it prompts interactively — so it is not a gate; the
type-check is the project-template's frontend validation. `npm run build` was deliberately NOT run to
avoid the shared `.next` harness caution noted in operator memory.)

Live verification (not mocked):
- Backend boots; `GET /health` -> `{"status":"ok"}`; `GET /research/analytics` over a fresh DB -> the
  honest empty payload `{"partitions":[],"min_sample_size":5}` (the iter-6 canary for the new shape);
  `GET /research/taxonomy` carries the `analytics` copy block.
- **Real data:** ran `compute_analytics` over the persistent dev journal DB (`apps/backend/tapeology_journal.db`,
  ~50 theses) — **4 distinct `config_fingerprint` partitions render separately** (the never-pool /
  partition-split assertion, exceeding the required 2), the abandonment bucket is populated and kept in `n`
  (e.g. trend_continuation/long n=37, abandoned=25), insufficient-sample groups are marked with `n` present,
  median time-to-confirm is computed from the timeline, and the acted-trade population is counted separately.

## Known Issues

- **Browser QA pending (the qa step's job).** Dev verified J-59 via the unit/integration matrix + a live
  backend canary + a real-DB aggregation run, but the pixel assertions (two-fingerprint partition split on
  screen, abandonment chip visible, insufficient-sample marker with n, median spread/R beside a +1R figure,
  acted-trade block visually separate, no currency/equity-curve anywhere, the two carry-along captures) run
  in browser-qa. The persistent dev DB already holds the multi-fingerprint substrate the spec recommends for
  the split assertion; QA should start the backend with `TAPEOLOGY_JOURNAL_DB=apps/backend/tapeology_journal.db`
  (or seed equivalently) so the analytics view is non-empty, and use full-page captures (the analytics view
  sits below the toggle and may need scrolling — sanity-check capture bytes per the iter-3/4/14 lesson).
- **`min_sample_size` default 5.** Some real-DB groups fall below it and show the insufficient-sample marker;
  that is correct behaviour (n present, distributions withheld). To force a group to clear the threshold for
  a "full stats" capture, QA can add fresh sim theses in one group or, per the spec note, rely on the
  trend_continuation/long groups that already clear it.
- **No schema change / no migration** this iteration (analytics is pure read-time aggregation). store.py
  stays at v7.
