# Phase goal-fast_wall-iter-6 — User-Visible Changes

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Nothing new. This iteration adds no new button, page, panel, filter, field, or control anywhere in the product. `git status`/`git diff` confirm zero changes to any file under `apps/frontend/` — every file this iteration touched is backend caching internals plus their tests (`apps/backend/app/research/setups_scan_cache.py` (new), `apps/backend/app/research/setups.py`, and four test files).

---

## What Changed in the Visible UI

- Nothing renders differently. `/structure`'s Tradable Map, Case Studies, Edge Report, Registry, and Comparison sections are byte-unchanged this iteration, and the separate `/studies` page (an unrelated feature — see note below) is untouched. The developer's own live browser pass confirms every section matches the iter-5 visual baseline exactly: zero `-loading`-suffixed testid remained after 10 seconds, zero new/removed elements, zero console errors beyond the standard React DevTools info line.

---

## What Old Behavior Changed

- **Case Studies data — load time after a backend restart, on the real/populated dataset only.** `/structure`'s "Case Studies" panel (the band-touch-event list, served by `GET /research/setups`) and its row-click drill-in (`GET /research/setups/{id}`) are backed by a scan that used to be remembered only in the backend's memory. Restarting the backend used to throw that memory away, forcing the very next Case Studies load to re-run the full multi-minute scan from scratch. That scan result is now also saved to disk the moment it finishes, so the next load after a restart is served almost instantly instead of triggering a fresh scan. The rows/fields shown are byte-identical either way — only the wait changes.
  - This also means the scan now recognizes "the same settings and the same recorded price data," not "the exact same settings object still sitting in memory" — a technical fragility invisible to any user on its own, but one that could previously force an occasional unneeded re-scan even without a restart. That no longer happens.
- **Edge Report compute — same underlying scan, indirectly.** Clicking "Compute edge report" on `/structure`'s Edge Report panel runs a comparison sweep that internally resolves each dataset's touch events by calling the same scan function twice. That operator-triggered compute action now also benefits from (and is subject to) the same restart-surviving, content-keyed cache — its output is required to stay byte-identical to before (verified this iteration by the required-still-passing regression pass covering J-01/J-04/J-05), and a compute run that reuses inputs already scanned for Case Studies no longer re-pays that portion of the work.
- **Caveat — neither change above was actually observable in this iteration's own test evidence.** The scoped/keyless environment used for this iteration's browser verification (ports 8391/3391) points at a deliberately empty bar directory, so the scan was already near-instant with or without this change (`GET /research/setups` returned in 7ms; Case Studies correctly rendered its honest "No band-touch events scanned yet." empty state, same as before). The "Compute edge report" button itself was not clicked during this iteration's verification (running the real sweep to completion is explicitly out of scope this iteration). Both behavior changes above are real and code-verified, but only become observable to someone using the actual populated `.data/` corpus.

---

## Not Visible Yet

- There is no on-screen indicator anywhere (badge, timestamp, "served from cache" label) showing whether a given Case Studies or Edge Report load was served from the new durable cache, the existing in-memory shortcut, or a fresh scan — the only externally observable signal is how long the load takes, and the product does not display timing as a number anywhere.
- The new environment variable this iteration introduces (`TAPEOLOGY_SETUPS_CACHE_DB`, overriding where the durable cache file is written on disk) is deployment/operator-level configuration only — nothing in the UI reads, displays, or lets a user set it.

**Note on scope — a naming collision worth flagging:** `docs/goal.md` describes this iteration's benefit as reaching "the Case Studies list (`/structure`) and `/studies` page's underlying scan." Direct inspection of the frontend code shows the separate `/studies` route (`apps/frontend/app/studies/page.tsx`) is an unrelated feature — deterministic replay studies of the setup *grammar* (create/monitor/cancel a study, `fetchStudies`/`fetchStudy`/`createStudy`/`cancelStudy`) — and it never calls `GET /research/setups` or `GET /research/setups/{id}`. Grepping the whole frontend confirms the only two call sites of those two endpoints (`fetchSetups`, `fetchSetupDetail` in `apps/frontend/lib/api.ts`) are both used exclusively from `apps/frontend/app/structure/page.tsx`. This does not affect this iteration's correctness — the backend change and its tests are unaffected by this naming — but it does mean `/studies` needs no re-verification for this iteration, and is called out here so a tester does not spend time on it expecting to find a change that isn't there.
