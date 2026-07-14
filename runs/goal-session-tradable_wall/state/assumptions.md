# Assumption Ledger — session tradable_wall

## iter-0 — goal-evaluator

**Ambiguity:** The iteration spec instructs recording credential-gated J-03 and J-06 as `blocked` (Alpaca env unset, not simulated), but the journey-history status vocabulary (`passing`/`failing`/`partial`/`already_passing`/`regressed`/`unknown`) has no `blocked` value.
**We chose:** `failing` for both — there is positive evidence their features are entirely absent at baseline (setups.py/recorder path for J-03; PriceChart overlay+chip for J-06), so they are definitively not-passing, not merely untested. The credential gate is preserved as a `note` field on each journey rather than as the primary status. `unknown` was rejected because it means "not tested this iteration; carry over" — but both were exercised and found absent.
**Reversible:** yes
