# Goal Session fast_wall — Assumption Ledger

Append-only. Each entry records a scoring/interpretation call the goal-evaluator
made when the goal or a journey left something open — so the human can see (and
veto) these silent calls early. Routine evidence-reading is not an assumption.

## iter-0 — goal-evaluator

**Ambiguity:** J-07's acceptance names a live `/structure` era-5/5B interactive spot-check, but
loading `/structure` against the default real-corpus backend triggers the never-completing
edge-report sweep (hours of CPU pin), so the live leg was withheld and only the backend suite +
SSR-probe (curl GET 200, all era-5/5B markers present) + the other four surfaces' live screenshots
cover it.
**We chose:** Score J-07 `passing` on the strength of the green suite + pinned `config_fingerprint` +
equivalence 22/22 + four verified screenshots + zero-code diff (nothing could have regressed), treating
the spec-sanctioned code-citation/SSR substitution as sufficient for the `/structure` leg at a
zero-diff baseline, rather than downgrading to `partial`/`unknown`.
**Reversible:** yes — the deferred `/structure` live-interactive spot-check is re-run the first
iteration that makes the cold GET safe (J-01); if it ever fails, J-07 flips to `regressed` there.

## iter-1 — goal-decomposer

**Ambiguity:** J-01 step 2 says the not-computed payload embeds "the current compute snapshot (or `null`)", but the compute manager (`edge_report_compute.py`) is J-04's deliverable and does not exist yet within this iteration's scope.
**We chose:** `peek_strategy_comparison_report`'s not-computed payload always emits `compute: null` this iteration (the key is present now for forward shape-compatibility with J-04's frontend polling logic; its value is honestly `null` because no compute manager exists yet to query). J-04 wires the real snapshot into the same key without a shape change.
**Reversible:** yes — J-04 only needs to supply a non-null value for the existing `compute` key; no payload restructuring required.

## iter-1 — goal-decomposer

**Ambiguity:** J-07's deferred acceptance (iter-0 `assumptions.md`) says its live `/structure` interactive spot-check should be "re-run the first iteration that makes the cold GET safe (J-01)", but a full `/structure` page load on the default real-corpus backend still separately waits on `GET /research/setups`'s cold-scan cost (268.95s measured at iter-0) until J-06 ships — a hazard J-01 does not touch.
**We chose:** Scope this iteration's J-07 closure to the specific leg J-01 actually fixes (the Edge-Report mount-time GET, mechanically proven safe by the compute-spy test and by the old hazardous code path no longer existing) rather than requiring a full live page load that would still cost several minutes for an unrelated, already-diagnosed reason. A full live spot-check is encouraged as bonus evidence if time allows, not required to close this gap.
**Reversible:** yes — if future evidence shows the Edge-Report leg was NOT actually safe, J-07 flips to `regressed` and this reading is revisited; the setups-leg speed gap remains explicitly tracked for J-06, not silently closed.
