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

## iter-1 — goal-evaluator

**Ambiguity:** The iteration spec's "New information displayed" prose says both `detail` AND
`dataset_count` "become newly visible" in the not-computed panel, but the shipped `NotComputedPanel`
renders only the headline + `detail` (`dataset_count` reaches typed frontend state but is never
painted) — flagged non-blocking by both coherence.md and the audit (F1).
**We chose:** Score J-01 `passing` by treating the goal.md journey acceptance + TC-11 (which require
only the "Edge report not computed yet." headline and the verbatim `detail`, and are met exactly) as
authoritative over the downstream iter-spec prose's stronger "dataset_count also visible" claim; the
unrendered `dataset_count` is a spec-completeness gap, not a J-01 acceptance miss.
**Reversible:** yes — a later iteration can render `dataset_count` in the same panel with no contract
change; if the human deems its visibility binding, J-01 can be reopened for that one addition.

## iter-2 — goal-evaluator

**Ambiguity:** The methodology's stable-journey re-verification model assumes the golden-replay lane
runs for the Required-still-passing set (J-01, J-07), but this backend-only iteration
(`Frontend Present: no`) SKIPPED the whole browser-qa step, so neither UI journey got a fresh
screenshot or replay this iteration.
**We chose:** Score J-01 and J-07 `passing` (and bump `last_verified_iter` to iter-2) on a
mechanical non-regression argument — a UI end-state can change only if frontend code or the served
response bytes change, and both are proven unchanged (zero-frontend git diff + TC-8/TC-14
byte-identity + green suite 1427/0-fail + `config.py`-untouched-so-fingerprint-frozen) — rather than
downgrading either to `unknown` for lack of a fresh browser pass.
**Reversible:** yes — the next frontend-touching iteration re-runs their golden replay; if either
ever fails there, it flips to `regressed` and this reading is revisited.

## iter-3 — goal-decomposer

**Ambiguity:** J-03's acceptance says "the committed tick-fixture structure backtests complete
within an interactive test budget" but names no concrete number.
**We chose:** This iteration's TC-11 pins that budget at a concrete, generous 10-second
wall-clock ceiling on a newly-added fixture whose tick stream crosses at least 5 distinct
`level_change_points` intervals — chosen to be clearly satisfiable once the memo works and
clearly diagnostic of a regression back to per-tick recomputation, without being flaky on a
loaded CI box. The real proof of the throughput fix is the counting-spy call-count collapse
(TC-9/TC-10), not the wall-clock number itself.
**Reversible:** yes — a later iteration can tighten or loosen this specific number without
touching the underlying contract (byte-identity + call-count collapse), which is the
acceptance's real substance.

## iter-3 — goal-evaluator

**Ambiguity:** This is the first iteration to MODIFY the canonical owners behind a `passing` browser journey's UI (`levels.py`/`tradability.py` back J-07's `/structure` Tradable Map + Case Studies) while running `Frontend Present: no` — so J-07's continued pass has no fresh screenshot and the replay lane did not run.
**We chose:** Score J-07 (and J-01/J-02) `passing` on a mechanical byte-identity non-regression argument — the served bytes of the modified owners are proven unchanged (TC-15 pinned-value tests + my own targeted `test_levels.py`/`test_tradability.py` run + frozen `config_fingerprint` 4d665603569b9dbf), and a UI end-state can move only if the served bytes move — rather than downgrading J-07 to `unknown` for lack of a browser pass. This extends iter-2's mechanical-carry precedent to the harder case where the journey's OWN backing computation changed (not just an unrelated file).
**Reversible:** yes — the next frontend-touching iteration (J-04) re-runs J-01's and J-07's browser/golden-replay leg; if either fails there it flips to `regressed` and this reading is revisited.
