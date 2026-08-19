# goal-rapid-microscope-iter-11 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration shipped zero new user-facing capability. It is a backend data-visibility
correctness fix: closing a real gap where a dataset belonging to a registered-but-unresolved vault
recording plan could have been fully identifiable (symbol, date) on public surfaces the instant it
finished recording — even though nothing in the product had explicitly "sealed" it (a repo-wide
grep the developer ran found zero production call sites of `seal_shard`/`assign_shard`/
`expose_shard`). Independently confirmed via `git status`/`git diff --stat HEAD -- apps/`: all 9
changed files sit under `apps/backend/`; zero files under `apps/frontend/` changed.

## What Changed in the Visible UI

None. Zero `.tsx`/`.ts` files were touched this iteration. No page, panel, button, table column,
or label changed shape, text, or layout anywhere in the product.

## What Old Behavior Changed

None observable today, on the real product. Two backend response dependencies that already feed
shipped UI surfaces changed underneath them, but both changes are provably inert against the
operator's actual data store right now, because that store has zero registered vault recording
universes — confirmed in the dev handoff two independent ways: no `micro_vault` ledger directory
exists anywhere under `apps/backend/.data` (the only code path that ever creates one is the first
vault write, which has never happened), and a full before/after hash of the store is identical.

- The `/desk` page's "Microscope Readiness" section — specifically its "Legacy Tick Shards" table
  — is fed by a per-shard withhold check that now also excludes any dataset belonging to a
  registered-but-unresolved vault universe, not just datasets an explicit "seal" action already
  flagged (which, in practice, has never happened against the real store). Result today: the table
  renders the identical row set it rendered before this iteration.
- The `/structure` page's "Comparison" panel — its "Dataset" dropdown — is fed by
  `GET /research/datasets`, whose withhold filter was rewired through the same broadened check
  (this specific call site was a gap the plan's own file list missed; the developer found and
  fixed it during test-writing — see `docs/handoffs/goal-rapid-microscope-iter-11-dev.md`
  §"Beyond the plan"). Result today: the dropdown lists the identical dataset set it listed before
  this iteration — 18 datasets, per the developer's live-server verification immediately before
  handoff.
- The same broadened check also reaches (with no code change of their own) `/structure`'s "Edge
  Report" panel and "Case Studies" panel, and `/desk`'s screen-related panels ("Run Screen…",
  "Screen History", "Screen Runs", "Screen Comparison") — all downstream, through one shared choke
  point (`micro_snapshots.exclude_withheld`), of the same dataset corpus the withhold check filters.
  Same story: provably unchanged output today, because there is nothing new to filter out.

**What will change, the next time it matters:** the moment an operator registers a vault recording
universe and records real tape under it, every one of that tape's datasets will now automatically
disappear from all of the surfaces above until it is deliberately exposed — with no separate manual
"seal" step required, unlike before this iteration. That is the actual fix; it simply has nothing
to act on yet on the real store.

Separately, `/desk`'s live "recording in progress" view (what a user would see while polling a
tick-recorder job) changed its response shape — it no longer carries each chunk's symbol/date as it
fetches, only aggregate counts — but no UI element renders this view at all today (see below), so
there is nothing on screen for this specific change to affect, now or later, until a future
iteration builds a panel for it.

## Not Visible Yet

- **The live recorder-progress view's new aggregate fields** (`chunks_fetched`, `chunks_reused`,
  `chunks_unchanged`, `chunks_failed`, `trades_total`, `quotes_total`, `percent_complete`,
  `elapsed_seconds`, served by `GET /research/desk/micro/recorder/compute`) exist in the API today,
  but no `/desk` panel displays them — confirmed by a repo-wide search of the frontend for any
  reference to this endpoint or these field names (zero matches anywhere in `apps/frontend`). The
  dev handoff notes this is intentional: the panel that would eventually bind these fields is
  future (J-08) work, and the developer deliberately did not extend the frontend's
  `_PRICE_ARITHMETIC_FIELDS` guard list for fields nothing binds yet.
- **The underlying "is this dataset part of an unresolved pool" safety predicate**
  (`vault.py:unresolved_pool_universe_by_dataset_id`) has no UI of its own — it is a backend rule
  reachable only through the already-shipped surfaces described above, and has nothing to withhold
  against the real store today (zero registered universes).
- **The mechanism for eventually releasing a non-sealed pool member to ordinary research use** was
  explicitly out of scope this iteration (a genuine, named open design gap per the phase spec's
  NOTES) — there is no UI for it because there is no backend mechanism for it yet either.
