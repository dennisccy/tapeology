# goal-lint report — docs/goal.md

Run: 2026-09-02 · deterministic exit: 0 · semantic findings: 0

## Deterministic lint (goal_lint.py)
clean (exit 0, no output)

## Semantic findings
None.

Checks applied (judged on meaning, not keywords): journey contradictions (J-03 stops its own watch; every
other journey now performs its own `Simulated` / `SIM-BIDABS` / `Watch` setup from a fresh `/` load, so no
journey asserts state another destroys); unobservable acceptance (every Acceptance line names the visible
served-JSON state at `/tape/SIM-BIDABS/observation` — field values, the 404 body, the pause/resume status
sequence — before its test condition); steps that require guessing (every browser step names the `Data
source` group, the `Simulated` option, the `Ticker` field, the `Watch` / `Pause watching` / `Resume
watching` / `Stop watching` controls, the status-dot text `live`, or an exact URL and expected key/value);
independent runnability (the draft's "with `SIM-BIDABS` watched" openings in J-02…J-06 were replaced by
explicit setup steps during authoring — zero cross-journey state dependencies remain); mergeable pairs
(J-04 and J-05 drive the same JSON page but carry different risk classes — the ingestion-path equivalence
proof versus transport/404/MCP parity — so they stay separate, advisory only); risky surfaces (external
network calls and git access are each bounded by an era-specific anti-goal: no mandatory journey or test
requires Alpaca/network/credentials/market hours; no git call per request; null provenance when git is
unavailable); anti-goals that fool the keyword check (each era-specific bullet names a file, field, token
or count that a test can check); success criteria (each of the 18 criteria names an observable state, a
pinned value such as `08e471b10130e1e2` / v8 / 28 tools, or a named test class).

## Summary
Structurally clean and semantically consistent: six journeys, each independently runnable from a fresh
page load with a Sim-mode served-JSON browser surface and named deterministic test steps; anti-goals copy
the §0.3 rails and §0.8 laws verbatim and add checkable era-specific vetoes. Highest-impact property to
preserve during the run: no journey may be satisfied by widening the metadata partition or by an
`available_at_utc` that is not a manager-measured instant.
