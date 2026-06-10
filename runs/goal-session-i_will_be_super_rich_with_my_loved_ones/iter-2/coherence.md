# Iteration 2 — Coherence Audit

**Iteration:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 15 — thesis projection | OK | `apps/backend/app/research/monitor.py:183` (`projection()`) is the single computation; `GET /research/thesis/active` (`routes.py:135`) and the WS `thesis` key (`main.py:563`) both call `registry.projection_for(ticker)` → `monitor.projection()` — one function, two read sites |
| Row 24 — taxonomies / research display copy | OK | `apps/backend/app/research/taxonomy.py` is the single owner; `GET /research/taxonomy` (`routes.py:121`) serves it verbatim; frontend calls `fetchTaxonomy()` (`api.ts:349`) which reads that one endpoint |
| Row 26 — source / data_feed / config_fingerprint stamps | OK | `config_fingerprint()` lives on the single `Config` instance (`config.py:392`); `data_feed_for_scenario()` is a single function in `monitor.py:36`, called once at declaration in `routes.py:221` — no second computation site |
| Rows 1–13 — tape state, confidence, features, bid/ask/spread, trades, etc. | OK | The research monitor reads `snap.tape_state`, `snap.primary_features`, `snap.last` from the engine snapshot handed to `on_event` — reads, never recomputes; the statement-status evaluator (`monitor.py:50`) returns a classification based on canonical snapshot fields, not a second derivation of the underlying values |
| `fetchActiveThesis` in `api.ts:408` | OK | Function is defined but never called from any component or page in this diff; the `ThesisStrip` reads `snapshot.thesis` from the WS frame only (`page.tsx:232`) — no parallel REST fetch at the UI layer |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `ThesisStrip` on `/` (J-38 thesis declaration + active display) | OK | Blueprint IA row "J-38–J-46, J-49, J-50, J-52, J-53 → `/` thesis strip"; strip inserted in `apps/frontend/app/page.tsx:220–234` on the `/` route, between PriceChart and Cockpit; reachable in 0 clicks (it is on the home/landing surface) |
| No new pages or routes introduced | OK | `apps/frontend/app/` contains only `globals.css`, `layout.tsx`, `page.tsx` — no new route directories added; confirmed by `git diff 0e482ddf1cd40737f8136935efb2442a656cc5a0 --name-only` |
| Journal/Studies nav deferred | OK — correct per spec | Blueprint IA defines `Cockpit · Journal · Studies` in the top bar, but the spec's "Out of scope" section explicitly defers `/journal`, `/studies`, and top-bar nav links; `TopBar.tsx` has no Journal/Studies links — this is correct sequencing, not a violation |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `fetchActiveThesis` (`apps/frontend/lib/api.ts:408`) is exported but unused this iteration. It exists to support the J-38 requirement that the QA harness probe `GET /research/thesis/active` verbatim-equal to the WS `thesis` key (noted in the spec's testing requirements). No coherence concern, but a future iteration should either use it for that QA probe or remove it if unused. Not a WARN — just noted.
