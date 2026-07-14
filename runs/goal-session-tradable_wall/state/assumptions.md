# Assumption Ledger — session tradable_wall

## iter-0 — goal-evaluator

**Ambiguity:** The iteration spec instructs recording credential-gated J-03 and J-06 as `blocked` (Alpaca env unset, not simulated), but the journey-history status vocabulary (`passing`/`failing`/`partial`/`already_passing`/`regressed`/`unknown`) has no `blocked` value.
**We chose:** `failing` for both — there is positive evidence their features are entirely absent at baseline (setups.py/recorder path for J-03; PriceChart overlay+chip for J-06), so they are definitively not-passing, not merely untested. The credential gate is preserved as a `note` field on each journey rather than as the primary status. `unknown` was rejected because it means "not tested this iteration; carry over" — but both were exercised and found absent.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-03's acceptance says ">=10 event-window datasets EXIST ... the pinned event's drill-in SHOWS the five-state timeline at the 300-test." Alpaca creds turned out present (unexpected), so the credentialed recording genuinely ran — but the process was interrupted, producing 15 real datasets in an ephemeral pytest temp dir (GC-eligible, NOT the persistent store), with only a JPM proxy timeline shown and the pinned-AAPL drill-in never demonstrated. Does "exist"/"shows" require durable persistence in the canonical store + the specific pinned-AAPL drill-in, or is a demonstrated-but-ephemeral recording run enough to score the credentialed headline met?
**We chose:** The stricter reading — the credentialed headline is met only when the datasets PERSIST in apps/backend/.data/datasets/ (append-only/checksummed/split-frozen, re-openable) AND the pinned-AAPL 06-22 drill-in five-state timeline is demonstrated end-to-end. Under this bar the credentialed portion is not-yet-met, so J-03 = partial (keyless substrate passing), matching the auditor's explicit recommendation and the spec's own stated expectation ("land partial, not full passing"). The dev/QA "MET" framing was not accepted. A human who considers a demonstrated-but-ephemeral real run sufficient could reverse this to passing.
**Reversible:** yes

## iter-4 — goal-decomposer

**Ambiguity:** J-04's acceptance ("the report compares all three strategies on identical data ... each cell either has n>=5 or is labelled insufficient_sample ... an all-insufficient report is a valid outcome") plus the tag "(Keyless via the committed fixture; full run credentialed)" leaves open whether J-04 can be scored passing on the KEYLESS committed-fixture run alone (one recorded window -> cells honestly all insufficient_sample), or whether the credentialed >=10-window recorded data (operator-gated, tied to J-03's still-blocked credentialed portion) is required before J-04 can pass.
**We chose:** The keyless reading — this iteration builds the full 3-way report machinery (structure_tape_map registration + additive arming path + edge_report.py 3-way extension + GET /research/edge-report + MCP proxy) and verifies it end-to-end over the committed datasets_j03/ fixture, treating a correct, gate-honoring, all-insufficient_sample report as J-04's passing core (success criterion 5 and the acceptance line both state an all-insufficient / empty-survivor report is a valid outcome). The credentialed >=10-window enrichment (richer n>=5 cells) is an operator-gated carry parallel to J-03's blocked recording, not a blocker for J-04's core acceptance. A human who requires credentialed multi-window data before J-04 passes could reverse this to partial.
**Reversible:** yes
