# goal-i_will_be_super_rich-iter-0 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-0
**Date:** 2026-06-04
**Agent:** developer
**Mode:** baseline (verify-only) — INITIAL BUILD
**Status:** complete

## Summary

This is the **baseline assessment iteration** of a session whose goal was expanded (commit
`544267c`) to add **real US-equity market data** — live streaming + historical replay behind a
vendor-agnostic adapter (Alpaca, free IEX feed) — on top of the already-shipped **simulated**
tape cockpit. Per the iter spec, this iteration is **verify-only**: both the Backend and
Frontend IN SCOPE sections are explicitly **"No code changes. Verification only."**

Accordingly, **no product code was written or modified**, and none should have been — writing
code here would violate the DEFINITION OF DONE ("No source files were modified") and would jump
the one-time human blueprint-approval gate that `run-goal.sh` enforces after the baseline.

The developer's job this iteration is narrow: (1) confirm the starting point — that the
simulated half (J-01–J-09) is the **green floor** the real-data work must not regress, and that
the real-data half (J-10–J-15) is genuinely **unbuilt**; (2) confirm the coherence blueprint is
in place for human review; (3) hand off so the browser-qa stage can record the per-journey
baseline. **The journey attempts themselves are the browser-qa-agent's responsibility, not the
developer's** — the notes below are code-level presence/absence evidence, not pass/fail verdicts
(the goal-evaluator classifies each journey from the recorded evidence).

## What Was Built

- **Nothing** — by design. This is a verify-only baseline iteration (IN SCOPE: "No code
  changes. Verification only." for both backend and frontend). No engine, classifier, provider,
  adapter, API, or frontend code was created or modified.

## Baseline Findings (codebase state verified)

The prior session (`i_will_be_rich`) built and shipped the **simulated** half over seven
iterations. This baseline confirms the split concretely:

### Simulated half — present and GREEN (J-01–J-09)
- **Backend engine + API exist** under `apps/backend/app/`:
  - Engine: `engine/tape_engine.py`, `features.py`, `classifier.py`, `aggressor.py`,
    `market_state.py`, `observations.py`, `snapshot.py`; `config.py` (no-magic-numbers home);
    `serializers.py`; `watch_manager.py`.
  - Provider seam: `providers/base.py` (interface) + `providers/simulated.py` (the only
    concrete provider). `providers/__init__.py` exports the simulated provider.
  - REST/WS routes in `app/main.py`: `GET /health`, `POST /watch/{ticker}`,
    `DELETE /watch/{ticker}`, `GET /tape/{ticker}/state`, `/features`, `/events`, `/summary`,
    `WS /tape/{ticker}/stream`.
- **Frontend cockpit exists** under `apps/frontend/`: `app/page.tsx` + `components/`
  (`Cockpit`, `QuotePanel`, `RecentTradesPanel`, `FeaturesPanel`, `TapeStatePanel`,
  `ObservationsPanel`, `EventLogPanel`, `IdleState`, `Panel`, `TopBar`) + `lib/`
  (`api.ts`, `useTapeStream.ts`, `types.ts`, `format.ts`, `config.ts`).
- **Backend test suite is green: 68 passed** (see Tests Run). This is the green floor the
  real-data work must not regress.

### Real-data half — ABSENT (J-10–J-15 surfaces do not exist yet)
A targeted sweep confirms **none** of the real-data surfaces exist:
- **No live provider, no historical-replay provider, no Alpaca/vendor adapter.** `app/providers/`
  contains only `base.py` + `simulated.py`. A grep for `alpaca|Alpaca|historical|LiveProvider|
  live_provider` across `app/` returns nothing.
- **No `GET /symbols/search`** and **no `GET /market/clock`** in `app/main.py` (route list above
  is complete).
- **No `mode` body on `POST /watch`** — `app/main.py` has no `mode` / `WatchRequest` / `start` /
  `end` / `speed` handling; the watch is simulated-only.
- **No real-data UI controls.** `components/TopBar.tsx` is the simulated-only bar: a **ticker
  input**, a **Watch** button, a **watched-source (scenario) label**, a **Stop** button, and a
  **stream-status dot**. There is **no** data-source selector (Live / Historical / Simulated),
  **no** symbol search, **no** market-status indicator, **no** date/time-window picker, and
  **no** replay-speed control. (Notable: the dot's `STREAM_DOT` map already includes a `stale`
  entry, so the *rendering* path for J-15 exists — but nothing produces `stale` because there is
  no live feed.)

### Per-journey code-level observations (evidence for the QA/evaluator stages — NOT verdicts)
| Journey | Code surface present? | Baseline note |
|---|---|---|
| **J-01** Watch + live cockpit | ✅ full | Cockpit + WS + sim provider all present; `SIM-BUYER` registered. |
| **J-02** buyer_control | ✅ full | `SIM-BUYER` → buyer_control ~0.87 within ~3–4s (per project-template). |
| **J-03** seller_control | ✅ full | `SIM-SELLER` registered + classifier rule present. |
| **J-04** bid_absorption | ✅ full | `SIM-BIDABS` + absorption/refresh features present (price-impact rule). |
| **J-05** ask_absorption | ✅ full | `SIM-ASKABS` + ask-refresh features present. |
| **J-06** unclear/chop | ✅ full | `SIM-CHOP` + low-confidence `unclear` path present. |
| **J-07** transition messages | ✅ full | `observations.py` emitter + event-log panel present. |
| **J-08** REST == UI | ✅ full | Canonical `/state` + `/features` reads + cockpit present. |
| **J-09** Stop / re-watch | ✅ full | `DELETE /watch` + `Stop` button + `IdleState` present. |
| **J-10** data-source selector | ❌ absent | TopBar has no Live/Historical/Simulated selector or mode-specific reveal. |
| **J-11** historical replay | ❌ absent | No historical provider, no `{mode,start,end,speed}` body, no Historical controls. |
| **J-12** live streaming | ❌ absent | No live provider, no Live controls, no `/market/clock`. (Status dot can render `live`/`stale` but nothing real produces it.) |
| **J-13** symbol search | ❌ absent | No `GET /symbols/search`, no search box. |
| **J-14** honest real-data edge cases | ❌ absent | No `provider unavailable` / `not a tradable symbol` / `no data for window` / `market closed` states (real modes unbuilt). |
| **J-15** stale → recover | ⚠️ partial (render only) | `stale` dot mapping exists in `TopBar.tsx`, but there is no live feeder to flip to `stale` or recover. |

> Expected baseline reading (the **evaluator** decides, not this handoff): J-01–J-09
> `already_passing`; J-10–J-15 failing / to-build. Credential gating on J-11/J-12/J-13/J-15 is
> expected and is **not** a failure of the baseline — the honest record is "surface not present /
> not runnable," never "pass."

## Coherence Blueprint (DoD: must exist & be ready for human approval)

- **Verified present** at `runs/goal-session-i_will_be_super_rich/state/blueprint.md` (status:
  **DRAFT — awaiting human approval after baseline iter 0**). It:
  - **Carries forward the APPROVED simulated blueprint** (J-01–J-09, in force, unchanged) and
    **extends** it with the real-data half (J-10–J-15).
  - **Information Architecture** — still exactly one `/` "tape cockpit" screen across all modes;
    the app shell adds the **data-source selector** + mode-specific controls (Simulated → ticker
    input; Live → symbol search + market-status; Historical → symbol search + date/time-window +
    replay-speed). No second page, no watchlist grid, no execution controls (anti-goals upheld).
  - **Data Contract** — rows 1–6 are the already-built simulated contract (in force, unchanged);
    rows 7–9 register the **new** real-data values with a single canonical owner + endpoint each:
    symbol search → vendor adapter → `GET /symbols/search`; market clock → adapter → `GET
    /market/clock`; real-data availability/failure → live/historical provider (explicit error
    from `POST /watch`, mid-stream gap → `stream_status="stale"`). Live/historical reads flow
    through the **same** rows 1–6 — no parallel state/feature path.
  - Documents the **provider + vendor seam** singularity (one provider interface; vendor SDK in
    exactly one adapter module) and the singularity guardrails the coherence-auditor enforces.
- The developer made **no changes** to the blueprint; it is left intact for the human
  review/approval pause.

## Files Changed

- `runs/goal-i_will_be_super_rich-iter-0/status.json` — created; `current_step: dev_complete`,
  `status: in_progress`, `changed_files: []`, `tests_run: true` (existing suite re-run as the
  baseline confirmation).
- `docs/handoffs/goal-i_will_be_super_rich-iter-0-dev.md` — this handoff.

**No product source files were created or modified.** (`git status` shows only `docs/` and
`runs/` artifacts as changes; `apps/` is untouched.)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **68 passed** in ~14s (0 failed). This is the green floor — the existing engine /
classifier / provider / API tests all pass. **No new tests were added this iteration** (none are
required for a verify-only baseline; the real-data tests belong to the iterations that build
those surfaces).

> Browser journey attempts (J-01–J-15) and live error-path checks (unknown sim ticker → 400,
> not-watched read → 404, post-Stop 404 / WS rejected) are exercised and recorded by the
> **browser-qa-agent** in the QA stage — not here.

## Anti-goal check

- **No anti-goal was touched.** No code was written, so no execution path, no out-of-scope
  feature (scanner/news/charting/portfolio), no fabricated data, no recomputation outside the
  engine, no committed secrets, no magic numbers, and no ML were introduced. The blueprint
  preserves single-source-of-truth, the provider-agnostic seam, and the honest-failure contract.
  The verify-only constraint is satisfied.

## Known Issues / Notes

- This handoff intentionally reports **"nothing built."** That is the **correct** outcome for a
  baseline iteration — not a gap. Any retry that "fixes" this by writing product code would
  violate the spec and the human blueprint-approval gate.
- **Next-iteration direction (iter 1, after blueprint approval):** the real-data half is the
  actual work of this session. A natural first slice that conforms to the drafted blueprint is
  the **vendor-agnostic adapter seam + the credentials/availability contract** so that J-14's
  honest **"provider unavailable"** (no-credentials path) becomes verifiable without a live
  feed — then build outward to `GET /symbols/search` (J-13) and `GET /market/clock`, the `mode`
  watch body + historical-replay provider (J-11), the live provider + stale/recover (J-12/J-15),
  and the TopBar data-source selector + mode-specific controls (J-10) — sequencing the
  no-feed-verifiable surfaces first. Each must reuse the existing engine rows 1–6 unchanged and
  must not regress J-01–J-09.
- After this baseline, `run-goal.sh` pauses for human review/approval of `blueprint.md`; resume
  with `--resume` (or `--auto-approve-blueprint`) to begin iteration 1.
