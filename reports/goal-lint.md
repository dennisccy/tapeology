# goal-lint report — docs/goal.md

Run: 2026-07-17 · deterministic exit: 0 · semantic findings: 1

## Deterministic lint (goal_lint.py)

clean (exit 0, no output)

## Semantic findings

### risky-surface / steps-require-guessing (which backend do the browser & replay lanes hit?) — line 263

> `- **Test discipline:** the default suite stays hermetic and keyless — committed fixtures only; no test`

- **Problem:** J-04's browser flow ("browser-verified: button → progress → cells", line 413) has a
  state-changing click, and nothing in the file pins the browser-QA / golden-replay lanes to a SCOPED
  fixture backend — era-5B iter-10 documented exactly this failure (the replay lane hit the CPU-pinned
  real-corpus backend and false-FAILed J-05), and here the stakes are higher: a QA agent clicking
  "Compute edge report" against the real-corpus backend starts a genuine long sweep on the operator's
  machine — the precise surprise-compute this interlude exists to eliminate.
- **Suggested rewrite (append to the Test-discipline bullet, line 263-265):** `browser-QA and
  golden-replay lanes run against a SCOPED fixture backend (the era-5B recipe: TAPEOLOGY_DATASET_DIR /
  TAPEOLOGY_BAR_DIR pointed at committed fixtures, plus scoped TAPEOLOGY_EDGE_REPORT_CACHE_DB /
  TAPEOLOGY_EDGE_SWEEP_CACHE_DB / TAPEOLOGY_SETUPS_CACHE_DB / TAPEOLOGY_DATASET_INDEX_DB paths), never
  the real-corpus backend — a "Compute edge report" click in a QA lane must only ever start a
  fixture-sized sweep.`

## Summary

Structurally clean and semantically tight: 7 journeys with concrete steps, named UI texts, and
verifiability tags; the empty `AUTO:journeys` block is in place; rails are verbatim; every accelerator
carries a byte-identity acceptance. Two calibration notes, deliberately NOT findings: J-04's operator-run
pnl-history tail copies era-5B J-08 step 3's structure (that era certified GOAL_ACHIEVED with the tail
outstanding, so it is precedent-safe, not a stall risk), and Success Criterion 2's "interactive budget" is
operationalized by J-01's zero-compute spy + instant not-computed payload. **Highest-impact fix:** the one
finding above — pin the browser/replay lanes to the scoped fixture backend so no QA lane can ever trigger
a real-corpus sweep (the era-5B iter-10 false-FAIL is the proof this happens in practice).
