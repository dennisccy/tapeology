# Phase goal-rapid-microscope-iter-7 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-7
**Date:** 2026-08-18
**Written by:** ui-impact-analyst

---

**Context (read this first):** this iteration's entire diff is backend/CLI Python — 6 source files
(`apps/backend/app/providers/adapters/base.py`, `apps/backend/app/providers/base.py`,
`apps/backend/app/providers/historical.py`, `apps/backend/app/providers/adapters/alpaca.py`,
`apps/backend/app/research/datasets.py`, `apps/backend/app/research/walkforward.py`) plus 2 test
files, confirmed independently via `git status` (0 `.tsx`/`.ts`/`.css` files in the diff — matches
the dev handoff's own claim exactly). The plan declares `Frontend Present: yes` not because any UI
shipped, but as a documented mechanical workaround: the browser-QA harness's
`detect_frontend_in_plan` check otherwise skips the ENTIRE browser lane — including the
required-still-passing regression journeys — whenever a plan says `Frontend Present: no`, which
silently happened in iterations 4 and 5 (`iteration-state.md`). So the sections below are short and
factual: there is genuinely no new UI to describe this iteration.

---

## What Users Can Now Do

None, in the product's web UI. This iteration's two pieces of work both land beneath the surface:

- **J-06 step 1** adds optional storage fields to the trade/quote data pipeline
  (`RawTrade`/`RawQuote` → `TradeEvent`/`QuoteEvent` → the stored dataset row), but nothing reads or
  displays them yet — no endpoint response shape changed, and the one `/desk` section that reads
  data from this same pipeline (Microscope Readiness) shows an unchanged set of columns (verified
  directly against `apps/frontend/app/desk/page.tsx`: still exactly the same 12 shard-table columns
  and 5 totals-table rows as before this iteration — see the UI Surface Map for the exact list).
- **J-05** adds a new command-line flag (`--family tick_legacy` on
  `python -m app.research.walkforward`) that an operator can run from a terminal — not a button, a
  form, or any control anywhere in the app. Confirmed by grep: zero references to "tick_legacy" or
  "family" (in this sense) anywhere under `apps/frontend/`.

## What Changed in the Visible UI

None. No page, component, section, or navigation element changed this iteration. Independently
confirmed against the current `apps/frontend/app/desk/page.tsx`: the same 10 collapsible sections
exist before and after this diff (`topupRuns`, `indexReconciliation`, `screenRuns`,
`screenComparison`, `provenance`, `playbookEvidence`, `refereeRegistry`, `refereeAdjudications`,
`refereeRuns`, `microReadiness`) — no new section, no new column, no new field.

## What Old Behavior Changed

None. Every change in this iteration is purely additive with an absent-key default — this matches
the dev handoff's own claim ("Changed Behavior: None... existing behavior, existing stored data, and
every existing screen render exactly as before") and is why the DEFINITION OF DONE requires (and the
dev handoff reports) all 18 real on-disk tick datasets plus every committed fixture loading
byte-identically after the change. Unlike the previous iteration (iter-6), which changed what an
*existing* CLI path does when a corpus is too small, this iteration adds two entirely new entry
points (the optional storage fields, the new `--family` flag) rather than altering an existing one's
behavior.

## Not Visible Yet

- **Trade/quote "preservation" fields** — `conditions`, `exchange`, `tape`, `trade_id` on trades, and
  the matching condition/tape/bid-exchange/ask-exchange fields on quotes — can now be stored per
  event, but nothing populates them from a real recording yet (that is J-06 steps 2-5, not built this
  iteration) and no screen renders them. The Microscope Readiness section's shard table has no
  column for any of these — confirmed against the live table markup, which still lists only Symbol,
  Session date, Feed, Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac, Checksum,
  Split provenance, and Exposure state.
- **The dataset "schema basis" / "quote size unit" stamp** — a dataset can now optionally carry a
  note about its data format and share-vs-round-lot quote-size convention, but no caller supplies
  these values yet, so no dataset on disk carries the stamp and no UI reads it.
- **The `--family tick_legacy` CLI check** — reachable only from a terminal running
  `python -m app.research.walkforward --family tick_legacy`; run today (by an operator, not through
  the app) it honestly reports the corpus is too small (the exact string `"11 < 105"`) rather than
  silently doing nothing. There is no button or page anywhere in the product that triggers this —
  the sibling web route, `POST /research/desk/micro/walkforward/compute`, does not accept this
  parameter this iteration (explicitly deferred, per the plan's own assumption ledger).

---

## Regression note (why a test plan exists despite no UI change)

Because `Frontend Present: yes` forces the browser lane to genuinely dispatch this iteration, the
test plan and operator guide below are a **regression pass over pre-existing, unmodified surfaces**,
not a walkthrough of new capability: the Microscope Readiness section on `/desk` (J-01) and the
13-step whole-product kept-product sentinel (`journey-scripts/J-10.json`, reused byte-unmodified —
cockpit `/`, `/structure`, and several `/desk` sections). One correction versus the equivalent pass
last iteration: the Microscope Readiness expectations below are pinned to what the store-scoped QA
rig actually seeds — **1 distinct symbol-day / 2 datasets, both symbol PG, session date 2026-06-09**
— never the real store's 12 symbol-days / 18 datasets, which the rig structurally cannot show
(`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` seeds exactly the two committed
PG fixtures and nothing else). Iteration 6's equivalent check asserted the real store's larger
numbers against this same rig and failed spuriously as a result
(`docs/handoffs/goal-rapid-microscope-iter-6-audit.md`, finding E3) — that mistake is not repeated
here. See `reports/phase-goal-rapid-microscope-iter-7-ui-surface-map.md` for the full
surface-by-surface breakdown.
