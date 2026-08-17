# Phase goal-rapid-microscope-iter-2 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** ui-impact-analyst

---

## Context

This iteration is backend-only by design (the phase spec's own "Frontend" section reads "None
... zero `.tsx` files are edited"; confirmed independently — `git diff --stat HEAD -- apps/frontend`
returns no output). It builds an invisible-to-users order-flow analysis engine (the "micro
observer") and processes all 18 already-recorded tick datasets with it. `Frontend Present: yes`
in the plan is about verification only: a browser pass must re-confirm the already-shipped
Microscope Readiness panel and re-check every other shipped page/section as a mandatory regression
sweep (triggered by last iteration's `ESCALATE` verdict) — not about any new rendering this
iteration ships.

---

## What Users Can Now Do

None. This iteration adds no new capability, page, button, or control anywhere in the app. The new
backend analysis and its three new API endpoints (build listing, trigger/poll/cancel, run history)
are reachable only by direct API call or the CLI today — see "Not Visible Yet" below.

---

## What Changed in the Visible UI

None in the deployed product. The Microscope Readiness panel on `/desk` (shipped last iteration)
is byte-unchanged: same component, same fields, same layout.

One change exists, but only inside the isolated QA/test environment used to take verification
screenshots — never in the real product a user would open:

- The store-scoped browser-QA harness (`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`,
  the launcher behind the mandated `:8301`/`:3301` verification pass) now copies two small,
  already-committed, real tick-data files into its own throwaway dataset folder before starting.
  Previously that folder was empty. This is a test-fixture change, not a code change — the actual
  product backend that real users hit has shown real tick data on this same panel since last
  iteration.

---

## What Old Behavior Changed

- **Microscope Readiness panel, QA-harness only** (not the production backend): previously, running
  the panel through the isolated store-scoped test rig showed the empty state "No tick shards
  recorded." with all totals reading zero — because that rig's dataset folder had nothing in it.
  Now, run through the same rig, it shows a populated 2-row table (both rows symbol PG, feed
  "sip", session date 2026-06-09) and totals of 1 distinct symbol-day / 2 distinct datasets. This
  closes the gap left after last iteration: the panel's real-corpus numbers were already proven
  against the operator's actual data store (12 symbol-days / 18 shards), but a browser screenshot
  of that proof was impossible until now because the isolated test rig had no tick data to show.
  The panel itself did not change — only what the test rig can feed it.

No other existing feature changed behavior anywhere in the product this iteration.

---

## Not Visible Yet

- **A record of which recorded trading days have had this new order-flow analysis run on them,
  and a control to run it.** The backend can now report, for each of the 18 recorded tick
  datasets, whether the analysis has been built, watch a build in progress, cancel it, and list
  past build runs — all three new endpoints (`GET /research/desk/micro/snapshots`,
  `POST`/`GET`/cancel on `.../snapshots/compute`, `GET .../snapshots/runs`) are live and already
  exercised against all 18 real datasets via the command line. Confirmed no page in the app calls
  any of them yet (a search of every `.tsx` file for these endpoint paths found zero matches). A
  "Build Snapshots" button and its on-screen progress are explicitly planned for a later iteration
  (J-08 in the project roadmap).
- **The order-flow analysis results themselves** — buying/selling pressure accumulation, same-side
  trade clustering, how efficiently price responds to aggressive trades, and whether the quoted
  bid/ask is thinning or refilling, computed trade-by-trade for all 18 recorded datasets — are
  stored on disk but not shown on any screen. Displaying them, and connecting them to chart
  patterns / support-resistance levels, are both future-iteration work (J-08 and J-03
  respectively).
