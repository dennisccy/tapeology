# Iteration 2 — Coherence Audit

**Iteration:** goal-yahoo_fetch-iter-2
**Date:** 2026-07-09
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration (J-02) is backend-only: `_INTERVAL_MAP` in
`apps/backend/app/providers/adapters/yahoo.py` expands from `{"1d": "1d"}` to the five
directly-fetched era-5 timeframes, plus a new `_resample_4h()` deriving `4h` from real `1h`
bars, plus a new `UnsupportedTimeframe` exception (`providers/adapters/base.py`) mapped to a
distinct 422 in `research/routes.py::record_bar_series`. Confirmed zero `apps/frontend/**`
diff (`git diff ad71dfed..HEAD --stat -- apps/frontend/` empty) and confirmed by the
ui-impact-analyst's surface map, which independently reaches the same conclusion. No new
route, page, or displayed value this iteration — reviewed against Data Contract row 3 ("Bar
series + double-sha256 checksums") and the provenance row (row 1), the only two rows this
diff's code paths touch.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Bar series + double-sha256 checksums (candles) — canonical owner `research/bars.py` `BarStore` | OK | `research/bars.py` has zero diff (absent from the bounded diff's file list); `apps/backend/app/research/routes.py:1643-1650` still routes every adapter's `raw_bars` through the one `store.record(...)` call — Yahoo's expanded `fetch_bars` (now covering 1w/1d/1h/5m/1m + derived 4h) still only ever *feeds* that single owner, never persists or serves bars itself |
| Bar-series provenance `feed="yahoo"` — sole source: the Yahoo adapter | OK | `apps/backend/app/research/routes.py:1640` (`feed = adapter.name if isinstance(adapter, YahooAdapter) else …`) is unchanged context in this diff (no `+`/`-` marker) — the stamp's single-owner logic from J-01 is untouched by J-02 |
| New backend computation this era — the `4h` resample (confinement-mandated by the iter spec, not itself a separate Data Contract row) | OK — single owner | `apps/backend/app/providers/adapters/yahoo.py:92` defines `_resample_4h` once; repo-wide grep (`grep -rn "_resample_4h" apps/` and `grep -rn "resample" --include="*.py" apps/ | grep -v /tests/`) finds it defined and called ONLY in `yahoo.py` (recursive call at `yahoo.py:169`), referenced only from test files. No second resample path in `bars.py`, `research/levels.py`, or any route, satisfying the anti-goal's explicit confinement rail |
| New displayed value / entity | N/A — none introduced | UI surface map confirms 0 frontend files changed; iter spec's own "New information displayed" field says "None on-screen this iteration" — consistent with the diff |

No duplicate computation, no non-canonical source, no new unregistered displayed value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK — N/A | `git diff ad71dfed2538b2b08b4762f072d7ef53c6c537a4 --stat -- apps/frontend/` returns empty; blueprint's nav skeleton section states "Nav skeleton is UNCHANGED this era (no re-approval)" and this iteration's spec confirms "No new page, route, or nav element." `apps/frontend/components/NavBar.tsx` (the data-driven top bar per the blueprint) was not inspected further since nothing in the diff could affect its rendered output — `GET /meta/ui-routes` (`apps/backend/app/meta.py`) is untouched |

No hidden feature, no reachability regression, no duplicate home, no parallel shell — there is nothing new to reach.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md:72` (the "Multi-timeframe historical bar store" bullet) still reads "Only the
  daily timeframe is available through this free path today; the other calendar timeframes
  are still being connected." That sentence was added by the iter-1 showcase commit
  (`9c6c62b chore(goal): iter 1 showcase artifacts`), which lands inside this diff's
  `ad71dfed..HEAD` review window purely because of snapshot timing (`ad71dfed` was captured
  before that showcase commit landed) — it is not iter-2 dev output. But as of the tip of
  this same diff, it is already stale: `apps/backend/app/providers/adapters/yahoo.py` now
  fetches five direct timeframes (`1w/1d/1h/5m/1m`) plus the derived `4h`, all through the
  same free/keyless path. This is not a Data Contract or IA violation — README prose is not a
  served value or a nav route, so it cannot itself become a second source of truth for a
  displayed value — but it is a real, easily-fixed accuracy gap. Recommend the next
  readme-maintainer pass (naturally runs again after iter-2) or iter-3's decomposer note
  updates that sentence to reflect the now-full timeframe set now that J-05 will also add the
  on-screen fetch control.
