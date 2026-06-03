# Coherence Audit — goal-i_will_be_rich-iter-4

**Verdict:** COHERENCE-PASS

> Iteration 4 added the `seller_control` path (J-03). It rides the existing **Tape state + confidence**
> data-contract row through its single registered producer (`TapeStateClassifier`) and single canonical
> endpoint (`GET /tape/{ticker}/state`). No new value, endpoint, route, nav, or parallel shell was
> introduced. Both objective gates (Data Contract, Information Architecture) pass; no advisory issues.

---

## Scope of this iteration (diff vs `66d9640`)

Production files changed: `apps/backend/app/config.py`, `apps/backend/app/engine/classifier.py`,
`apps/backend/app/providers/simulated.py`. Test-only: `tests/test_classifier.py`,
`tests/test_scenario.py`. **No frontend file changed; no API/router file changed.** Confirmed against
the diff-stat and the ui-surface-map (0 frontend code edits, 0 new pages/routes).

---

## Part A — Data Contract check (the "numbers don't match" gate) → PASS

The relevant registered row is **Tape state + confidence** → canonical owner `TapeStateClassifier` →
canonical endpoint `GET /tape/{ticker}/state`, re-exposed read-only by `/summary` and `WS /stream`.

1. **Single producer — no duplicate computation.** `seller_control`, its confidence, and its
   observations are produced solely inside `TapeStateClassifier.classify()`
   (`apps/backend/app/engine/classifier.py:84-100`), with `_seller_confidence`
   (`classifier.py:136-153`) and `_seller_observations` (`classifier.py:155-161`) as **methods of the
   same class** — the registered canonical owner. No new module, service, or function computes the
   tape state outside the classifier. The buyer gate is only renamed (`gate` → `buyer_gate`),
   behaviour unchanged.

2. **Canonical source — no new/parallel endpoint.** `apps/backend/app/engine/tape_engine.py`
   (unchanged this iteration) instantiates one `TapeStateClassifier` (line 33), calls `classify()`
   (line 77), and builds the single snapshot by **reading** `classification.state` / `.confidence` /
   `.observations` (lines 96-98) — no recomputation. `seller_control` is served by the unchanged
   `/state` and re-exposed by `/summary` + `WS /stream`. No router/API file changed, so no second
   serving path was introduced.

3. **Features read, not recomputed.** The classifier consumes `aggressive_sell_ratio` and
   `sell_price_impact` from `primary_features` (produced by `FeatureEngine`, their canonical owner) —
   `classifier.py:58-59`. It scores them into confidence (its job); it does not recompute the features.

4. **Provider stays at the interface boundary.** `_seller_control_stream()`
   (`apps/backend/app/providers/simulated.py:71-99`) emits only `QuoteEvent` / `TradeEvent` with
   `Side.UNKNOWN`; the aggressor/side determination remains downstream in the engine
   (`classify_aggressor`). The simulator computes no contract value. The four renamed shape constants
   (`_P_SELL`→`_P_MINORITY`, `_P_LIFT_ON_BUY`→`_P_QUOTE_MOVE`, `_BUY_SIZES`→`_MAJORITY_SIZES`,
   `_SELL_SIZES`→`_MINORITY_SIZES`) keep identical values; the buyer stream is behaviourally unchanged.

5. **No new displayed value.** `seller_control` is an already-enumerated value of the existing
   Tape-state contract row (the tape-state panel already lists all five states). This iteration makes
   the engine emit it — it does not introduce a new value type. Therefore not even an A5
   "unregistered value" WARN applies. Config thresholds (`min_aggressive_sell_ratio`,
   `max_sell_price_impact`) live in `config.py` (no magic numbers); side-neutral scales/weights are
   reused, not duplicated.

No duplicate computation, no non-canonical source, no synonym/re-derivation → **no Part A violation.**

## Part B — Information Architecture check → PASS

No new page, route, or feature was added. The single `/` cockpit (the only IA home) is structurally
unchanged; `seller_control` renders through the existing `TapeStatePanel` / `FeaturesPanel` /
`ObservationsPanel` / `EventLogPanel` components (0 component edits per the ui-surface-map). Therefore:
no missing nav path, no >2-click reachability concern, no duplicate home, no parallel shell.

→ **no Part B violation.**

## Part C — Advisory observations → none

Symmetry discipline was kept: the seller label ("Seller Control") and rose color semantics mirror the
buyer side's green consistently; the transition emitter is state-generic. No label divergence, no
formatting drift, no style drift to note.

---

## Conclusion

This iteration is a textbook contract-conforming extension: an already-enumerated state value, emitted
by its one registered producer and served by its one canonical endpoint, with no new surface. Matches
the spec's declared "Data-contract additions: None" and "Blueprint conformance: no new surfaces."
No remediation required.
