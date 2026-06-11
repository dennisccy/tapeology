**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-16 (goal-i_will_be_super_rich_with_my_loved_ones-iter-16)

**Iteration:** Segregated journal analytics (J-59) + honest-absence copy split
**Snapshot SHA:** 323f948fb1e5a9d78f5c7bc71aa10e4395563956
**Diff files changed:** 9 (backend analytics module + routes + taxonomy + config, frontend journal page + AnalyticsView + JournalDetailView + api + types, blueprint update)

---

## Part A — Data Contract check

### Row 21 — Journal rows + analytics aggregates (aggregates half)

**Blueprint contract:** Single owner `apps/backend/app/research/analytics.py`; served ONLY by `GET /research/analytics`; computed at read over persisted rows ONLY (never pools across `data_feed` or `config_fingerprint`).

**Findings:**

- **Single owner confirmed.** The new module `apps/backend/app/research/analytics.py` is the sole site where analytics aggregates are computed. The `compute_analytics` function lives exclusively there. No other module or route introduces an independent analytics aggregation. The iter-16 blueprint additive note (row 21) registers this module by name — the implementation exactly matches the registration.

- **Canonical serving endpoint confirmed.** In `routes.py`, the new `GET /research/analytics` endpoint (lines 261–271) calls `compute_analytics(registry.store, registry._config)` and returns the projection verbatim. This is the only endpoint serving analytics. No secondary route (`GET /research/journal/analytics` or similar) appears anywhere in the diff.

- **No client-side recomputation.** `AnalyticsView.tsx` and `apps/frontend/app/journal/page.tsx` fetch from `fetchAnalytics()` (which calls `GET /research/analytics` — `apps/frontend/lib/api.ts` line 630). All values rendered in `AnalyticsView.tsx` are read from the payload verbatim. Display helpers `fmtR`, `fmtSpreadR`, and `fmtSeconds` apply only decimal rounding — no arithmetic, no aggregation, no percentage computation. No client-side violation.

- **Acted-trade R reuses row-27 `marks_projection`.** In `analytics.py` lines 47 and 183–191, `marks_projection` is imported from `.marks` and called over the persisted action records. The `realized_r` and `r_basis` values are read from the projection's output, never computed inline. This is the third registered consumer of the row-27 R path (per the blueprint's iter-16 additive note on row 27), not a new formula.

- **Spread/R from persisted values only.** The `horizon_spreads[h].append(spread_at_anchor / r_basis_value)` at `analytics.py:148` computes `spread / r_basis` for the median, reading both values from the already-persisted excursion record (`pop.get("r_basis")` and `pop.get("spread_at_anchor")`). The blueprint row 21 explicitly registers this pattern ("median spread/R (persisted `spread_at_anchor`/`r_basis`)"). This is aggregation over persisted values, not a second R formula or recomputation.

- **Never pools.** `compute_analytics` partitions by `(data_feed, config_fingerprint)` before any aggregation; there is no "all" or pooled rollup anywhere in the function. The frontend renders one `PartitionBlock` per partition key and never merges them.

### Row 24 — Taxonomies + research display copy

**Blueprint contract:** Single owner `taxonomy_payload()` in `taxonomy.py`; served by `GET /research/taxonomy`; frontend hardcodes none.

**Findings:** The iteration adds `ANALYTICS_COPY` to `taxonomy.py` and extends `taxonomy_payload()` to include an `"analytics"` key (`taxonomy.py` lines 313–373 and 602–605). The `AnalyticsView.tsx` component reads all labels via the `copyOf(copy, key, fallback)` helper, which reads from `taxonomy?.analytics` — no string is hardcoded in the component. The fallback strings are present as a resilience measure for a pre-J-59 taxonomy payload; they do not constitute a second copy register that diverges from the backend. Contract intact.

### Row 27 — Realized move in R + R basis (third registered consumer)

**Blueprint contract:** One function (`marks_projection` in `marks.py`); row 27, row 20, and now row 21 are the three registered consumers (iter-16 additive note).

**Findings:** `analytics.py` imports `marks_projection` from `.marks` (line 47) and calls it for each thesis in the acted-trade block. No second R formula exists in the diff. The blueprint's iter-16 additive note on row 27 explicitly pre-registers row 21 as the third consumer. No violation.

### `analytics_min_sample_size` config key (new)

**Blueprint contract (row 21 iter-16 note):** A serving/presentation-only threshold; excluded from `config_fingerprint` with a documented rationale; pinned by a fingerprint-stability unit test.

**Findings:**
- `config.py` adds `analytics_min_sample_size: int = 5` with a detailed rationale comment excluding it from `config_fingerprint` (lines 455–471).
- The exclusion set in `config_fingerprint_hex()` includes `"analytics_min_sample_size"` (line 621).
- The rationale matches the iter-12 page-size precedent as required.
- The spec calls for a fingerprint-stability unit test; the untracked file `apps/backend/tests/test_analytics.py` appears in `git status`, confirming the test file was created this iteration. The coherence gate does not run tests but notes the test file exists.

This is a serving-only config key, never entering any persisted computation. No data contract concern.

### New displayed values not in the contract

The analytics view displays: partition blocks, per-group n, abandonment count, ternary distribution per horizon, truncated counts, median time-to-confirm, tag frequencies, acted-trade median realized-R, and median spread/R. All of these are registered under row 21 (aggregates half, iter-16 build-out note). None is a synonym or re-derivation of a previously unregistered value via a new path. No unregistered values.

**Part A result: no violations.**

---

## Part B — Information Architecture check

### New routes/pages

The iteration introduces **no new routes**. The analytics view is an in-page view toggle on the existing `/journal` page (`app/journal/page.tsx`). This is confirmed by the diff: the `JournalPage` component gains a `view` state and a `ViewTab` toggle, but the route remains `/journal`. `AnalyticsView.tsx` is a component rendered inside the journal page, not a new page or route.

### Canonical home

Blueprint IA row: "J-59 (segregated analytics) → `/journal` analytics view → Journal". The analytics view lands exactly at `/journal` behind an in-page toggle. This is the pre-approved canonical home. The spec's "Blueprint conformance" section confirms: "No new route, no nav-skeleton change, ≤2 clicks (Journal is one click; the view toggle is the second)."

### Reachability

Nav inspection (`NavBar.tsx`): the persistent top bar has `{ href: "/journal", label: "Journal", enabled: true }`. `/journal` is one click from any page. The analytics view is one click (the toggle tab) from the default theses view within `/journal`. Total: two clicks from the home/nav. Within the ≤2-click rule.

### No parallel shell / no duplicate home

No new layout shell, no new nav section, no new nav item. The `ViewTab` toggle is an in-page control, not a nav element. The analytics view is not a second home for the thesis entity — it is the analytics aggregation surface registered at `/journal`, distinct from the thesis table. No parallel shell, no duplicate home.

**Part B result: no violations.**

---

## Part C — Advisory observations (WARN only)

### Carry-along honest-absence copy split

The `JournalDetailView.tsx` changes implement the iter-15/iter-16 carry-along: the `absentCopy` helper (lines 43–51) and `RESOLVED_STATUSES` set (lines 32–38) split the absence message into "not yet resolved" vs "predates the feature" for the grades, excursions, and execution-checks sections. This is a positive coherence improvement — the same absent key now renders with two contextually accurate copies instead of the single wrong-context "predates" copy on still-active theses. No concern.

No other advisory observations.

---

## Summary

Row 21's aggregates half ships as registered: single owner `analytics.py`, served exclusively by `GET /research/analytics`, computed at read over persisted rows only, never pools across feeds or fingerprints. The acted-trade R distribution is the third consumer of the one registered `marks_projection` path — no second formula. All analytics display copy flows through row 24's `taxonomy_payload()` — the frontend hardcodes none. The analytics view lands at its pre-approved canonical home (`/journal` in-page toggle, Journal nav entry, ≤2 clicks). No new route, no new nav entry, no parallel shell, no duplicate home. The carry-along honest-absence copy split improves coherence without violating any contract.

**Verdict:** COHERENCE-PASS
