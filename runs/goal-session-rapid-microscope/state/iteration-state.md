# Iteration State — rapid-microscope

**After iteration:** 22 · **Date:** 2026-08-21 · **Verdict:** STALLED

## Journeys

9 passing (J-01 J-02 J-03 J-04 J-05 J-07 J-08 J-09 J-10) · 1 partial (J-06) — 10 total

## Active blockers

- **J-06 "The recorder and the Vault" — OWNER-BLOCKED (human).** Steps 1-3 built (`tick_recorder.py`, `vault.py`). Step 4 (screen+freeze Tier-B, record real Alpaca trades+quotes to spec §7.6 minimums, seal at birth) is an operator act needing the paid feed, owner attendance, and sanction for a one-way seal; step 5 depends on it. Unblock: authorise the recording · amend `docs/goal.md` J-06 · resume unfinished on polish only.
- Owner ruling open, blocks NO journey: source of a candidate's money floor / evidence label (`micro_sealed_evaluation.py:316`).
- Machine work available, moves NO journey (polish; needs nobody's permission): (1) Desk readiness 22.3s/load — `micro_routes.py:108` rebuilds a BandMapResolver per GET; cache per dataset checksum AND band map, never cache a "no touches" answer. (2) `micro_routes.py:284-287` duplicates `scout.py:1684-1689`'s selector→kind table — derive it. (3) `tests/test_scout.py:1676` cannot fail — add `screen_result["n_candidate"] + screen_result["n_comparator"] > 0` (mirrors `:1664`).

## Last 2 verdicts

- iter 22: STALLED — J-09 finished (three studies recorded + operator-reachable) and J-07 re-photographed; J-06's owner-only tape recording is the sole remaining blocker.
- iter 21: ESCALATE — Study 2 screened (J-09 failing→partial); audit repaired a floor-check row that nothing but a unit test could produce.

## Do not redo

- **J-09 DONE, passing** — three families screened to closed-vocabulary decisions + floor-check rows via `POST /research/desk/micro/scout/compute {"grid":…}` AND `python -m app.research.scout --grid …`. Do NOT re-screen; do NOT run them against the real `.data/` corpus (owner-gated: permanent rows, breaks J-10's "No candidates ledgered." golden, search is quadratic).
- **J-07 re-verified fresh** (`UT-08-result.png`, iter-22) — no make-up capture owed; the demo lane's step-07 404 is the runner rewriting research URLs onto `:3301`, never schedule a re-record.
- **Study 1 stays single-feature** (`failed_aggression_score >= 0.5`) — `refill_consistent` co-occurrence is a disclosed T-1 deferral. Do NOT record real tape; do NOT touch the sealed judge's money floor.
- **Rig rule (binding):** run the golden-replay set BEFORE any lane POSTing into the shared QA rig (J-08 step 3 / J-10 step 12 assert "No candidates ledgered.").
- Baseline: 3,322 pass / 8 skip / 0 fail; fingerprint `08e471b10130e1e2`; no `referee_*` diff.
