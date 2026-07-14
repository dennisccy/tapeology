# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Honest Era 5B "The Tradable Wall" baseline, verify-only (`git diff --stat apps/` empty, review PASS). One journey holds: J-07 (the eras-1–5 foundation sentinel) is `already_passing` — full suite 1201 pass / 6 skip, `config_fingerprint` `4d665603569b9dbf` live-confirmed, SIM-BUYER/SIM-SELLER settlements screenshot-verified, nav unchanged at 5 entries. The other six journeys are `failing`: J-01/J-02/J-04/J-05 have their modules/endpoints confirmed absent (404s + DOM inspection), and J-03/J-06 are additionally credential-blocked (Alpaca env unset — honestly recorded blocked, never simulated). Next: build J-01 (`tradability.py` + `GET /research/tradability`) — the natural unblocker.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The tradable level map | (new) | failing | UT-J-01 row: `GET /research/tradability` → 404, `tradability.py` absent, no MCP proxy (`reports/phase-goal-tradable_wall-iter-0-ui-test-results.md`) |
| J-02 The wide scan / case registry | (new) | failing | UT-J-02 row: `GET /research/setups` → 404, `setups.py` absent, no MCP proxy |
| J-03 Real tape at the wall (credentialed) | (new) | failing (feature absent + credential-blocked) | UT-J-03 row: Alpaca env unset (presence-only), recorder path + setups prerequisite absent, zero event-window datasets |
| J-04 The edge report | (new) | failing | UT-J-04 row + `J-05-structure-baseline-raw-levels.png`: only `v1`+`structure_tape` registered (no `structure_tape_map`); `GET /research/edge-report` → 404 |
| J-05 /structure decluttered | (new) | failing | `J-05-structure-baseline-raw-levels.png`: raw-levels-only view (1,801 level rows, ~74k px tall page), no Tradable Map / Case Studies / Edge Report section, no toggle |
| J-06 Cockpit confluence chip | (new) | failing (feature absent + credential-blocked) | `J-06-cockpit-historical-mode-baseline.png`: no band/confluence/chip in PriceChart; credentialed replay blocked (Alpaca env unset) |
| J-07 Foundation sentinel | (new) | already_passing | `J-07-sim-buyer-control.png` + `J-07-sim-seller-control.png`: buyer/seller settlements, fingerprint on /performance, nav unchanged, store-first + Yahoo provenance intact |

Notes: J-03 and J-06 are recorded `failing` (not `unknown`) because there is positive evidence their features are absent at baseline; both additionally carry an operator-credential gate for their eventual credentialed verification (see journey-history `note` fields). No screenshot exists for J-01/J-02/J-03 because no UI surface exists to capture — the API 404 + DOM-absence probes in the results file are the evidence.

## Anti-goal Check

Worked from `scan-report.md` (CLEAN) + `iter-diff.md` (single file: `docs/goal-archive/goal-2026-07-14.md`, an archived era-5 goal copy — bookkeeping, no `apps/` change). A zero-source-diff verify-only baseline cannot violate a code anti-goal; the one live risk at baseline (fabricating a credentialed J-03/J-06 result) did not occur.

| Anti-goal category | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | scan-report CLEAN; no config/env files in diff; Alpaca env vars checked presence-only, never read/logged (dev handoff + QA env probe) |
| Paid/external SaaS deps | OK | no manifest change (requirements.txt/package.json untouched); zero `apps/` diff |
| License changes | OK | no LICENSE/license-field diff; only a docs markdown archive added |
| Fabricated/substituted data | OK | J-03/J-06 credentialed acts honestly recorded `blocked`, NOT simulated — the exact honesty the rails demand; no dataset created, no Alpaca call |
| No execution path (rail 1) | OK | `test_no_execution_path.py` present, unmodified (predates session); no order/trading surface added |
| No profit claims / advice (rail 2) | OK | screenshots show "Descriptive only — not trading advice" footer; no code change to touch copy |
| Frozen foundations (rail 3) | OK | `config_fingerprint` `4d665603569b9dbf` live-confirmed; equivalence suites 22/22; `research/levels.py` byte-identical; JSON BarStore/Alpaca adapter untouched |
| Hold-out-only promotion (rail 4) | OK | champion pointer `v1`/`default` untouched (`GET /research/profiles`) |
| No lookahead (rail 5) | OK | no new as-of computation added this iteration |
| Single source of truth (rail 6) | OK | no new value/owner introduced; no second computation added |
| Deterministic/seeded (rail 7) | OK | no new random draw or artifact |
| Read-only MCP (rail 8) | OK | no MCP tool added or changed |
| Immutable data (rail 9) | OK | no dataset/bar series created, re-tagged, or deleted |
| Persistence scoped (rail 10) | OK | no recording/fetch performed; all probes read-only GET |
| Era-5B specifics (lens-not-2nd-engine, morning-markup, descriptive, feed-honesty, no gate-bending, no hand-promote, additive-strategy, keys-uncommitted, live-untouched, no vocab drift) | OK | none reachable — zero source diff; nav unchanged (screenshots), no new strategy/vocab/feed surface |

## Next-Step Recommendation

Build **J-01 alone** next: `apps/backend/app/research/tradability.py` consuming `compute_levels(symbol, as_of)` output **verbatim** (never re-detecting pivots — the critical "lens, never a second levels engine" rail), config-owned band clustering/scoring (distinct-timeframe breadth, daily touch, recency, round-number confluence), K≤5-per-side cap, morning-markup as-of discipline; `GET /research/tradability?symbol=&as_of=` + the read-only MCP `tradability` proxy. Falsifiable acceptance is ready to exercise today — the AAPL 2026-06-22 map (basis = 2026-06-18 close) must be ≤10 bands with the 300.48–302.07 resistance band ranking top-2, and the real 1,800-level / 212-zone raw output is already in the store to distill from. J-01 is the unblocker for J-02 (scans its bands), J-04 (arms `structure_tape_map` on them), and J-05/J-06 (render them).

Depth **full** is recommended for iter-1 because it establishes a NEW canonical value + owner (`tradability.py` / `GET /research/tradability`) and its central failure mode is a critical single-source-of-truth violation (forking a second levels computation instead of consuming `compute_levels` verbatim) — exactly the boundary the auditor + coherence depth of the full pipeline exist to guard, plus the no-lookahead/morning-markup rail. This is a depth recommendation from intrinsic risk, not an ESCALATE (the baseline surfaced no surprise — it confirmed every spec prediction).

Watch-item for the eventual J-04 iteration (not iter-1): `apps/backend/app/research/edge_report.py` already exists as the era-3 champion-only CLI — J-04 must EXTEND it additively for the 3-way report, never fork a second edge computation (a critical SSoT trap).
