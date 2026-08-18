**Verdict:** PASS

```yaml
phase: goal-rapid-microscope-iter-7
date: 2026-08-18
reviewer: reviewer
summary: |
  J-06 step 1 (Card-5.1 preservation fields) threaded additively through RawTrade/RawQuote,
  TradeEvent/QuoteEvent, historical.py, alpaca.py, and datasets.py's present-only row
  emission; J-05's tick-family fold request now reaches a real CLI entry point. Independently
  re-verified (not just trusted): all 18 real on-disk datasets + 9,145,900 events load with
  zero new manifest/row keys, full suite 3044 pass/8 skip/0 fail, fingerprint 08e471b10130e1e2
  and all 6 referee_*.py hashes unchanged, one real dataset double-replay byte-identical, real
  installed-SDK Trade/Quote field names and Exchange str-vs-.value behavior match the code's
  claims exactly, and the "11 < 105"/TR-15 CLI refusal reproduced myself against the live
  .data/datasets store with the real ledger dir left untouched.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
