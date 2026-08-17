# Iteration State — rapid-microscope

**After iteration:** 2 · **Date:** 2026-08-17 · **Verdict:** CONTINUE

## Journeys

2 passing (J-01 J-02) · 7 failing (J-03..J-09) · 1 partial (J-10) — 10 total

## Active blockers

- OWNER RULING (human) — audit B5: a price-change-terminated `quote_depletion` stamps `available_at`
  one quote before the evidence closing the window (`micro_observer.py:636`/`:657`, pinned by
  `tests/test_micro_observer.py:291`). Harmless today; a live no-lookahead violation once J-05
  conditions outcome starts on `max(available_at)`. Spec silent — T-1 bars inventing a reading.
- TEST-RIG (dev, MINOR) — J-10's sentinel plan asks for `/structure` bands on PG (rig has no PG bars)
  and playbook filters on the rig's default session (never computed), so its browser lane FAILs for
  non-product reasons every run. Repoint to AAPL as-of `2026-06-22` + a session with signals; repair
  `journey-scripts/J-10.json` step 9 (volatile hash `b06e0bc289c54d77`).
- DISCLOSURE (dev, MINOR) — audit B4/T1: §4 spread cost-proxy column + §3 window-mean
  `quote_imbalance`/`microprice` unimplemented; TR-1/TR-17b exclude the close-out row. Record in
  Known Issues before J-05 reads those files.
- EVIDENCE MAKE-UP (dev, passenger task only) — J-01's screenshot shows the rig's 2-shard PG corpus,
  not the 12/18/~3.0 real totals. Re-photograph once a wider tick corpus is seeded; never a rebuild.

## Last 2 verdicts

- iter 2: CONTINUE — J-02 built and evaluator-verified (117 tests, 18/18 identity-verified snapshots,
  3,815,933 rows); J-01's browser half captured on real fixture data; J-10 still partial.
- iter 1: ESCALATE — J-01's endpoint half proven on the real corpus, browser half blocked by an empty
  QA rig; full depth mandated for the observer work.

## Do not redo

- `micro_readiness.py` + `GET /research/desk/micro/readiness` + the `/desk` Microscope Readiness
  section — built, verified on the real store (iter-1), photographed (iter-2), byte-unchanged.
- `micro_observer.py`/`micro_snapshots.py`/`micro_features.py`, the additive `observer=` kwarg on
  `DatasetStore.replay`, the pinned `micro-snapshot-v1` benchmark, the 18/18 real-corpus build; the
  QA-rig fixture seeding; the `test_desk_ui_guards.py` move; audit B1/B2/B3 fixes (corpus rebuilt).
- Era-open invariants re-verified iter-2: fingerprint `08e471b10130e1e2`, 6/6 referee SHA-256 match
  iter-0, MCP 22-tuple, suite 2,828 pass / 8 skip, store-scope guard CLEAN.
