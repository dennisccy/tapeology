# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/docs/goal.md b/docs/goal.md
index ead0ede..2433f05 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -120,12 +120,18 @@ route).
    the `pnl_scan` promotion interlock — all behaviorally byte-identical.** This era READS them;
    it never touches, re-implements, re-tunes, or feeds back into any of them. There is NO
    deliberate exception this era.
-3. The **stores** — `BarStore` + `DatasetStore` formats, checksums, append-only immutability,
-   frozen splits, the accelerator DBs, the desk stores, the playbook store, the referee store
-   family — are untouched in format and discipline. The era ADDS the micro store family
-   (snapshots, scout ledger, fold ledger, vault + exposure ledger, recorder runs, graduation
-   ledger) under the same discipline, plus one additive default-`None` `observer=` kwarg on
-   `DatasetStore.replay` (counter-tested byte-identical when absent).
+3. The **stores** — every EXISTING registered `BarStore`/`DatasetStore` artifact stays
+   byte-identical with its checksum verifying; no legacy file is ever rewritten or
+   reserialized; append-only immutability, frozen splits, parsing compatibility (absent
+   fields parse exactly as before), the accelerator DBs, the desk stores, the playbook store,
+   and the referee store family are untouched in discipline. **The one r2-sanctioned additive
+   seam:** NEWLY recorded datasets MAY carry the backward-compatible OPTIONAL event/manifest
+   fields of [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §7.1/§2.6
+   (conditions/venue preservation, `schema_basis`, `quote_size_unit`) — the frozen engine
+   ignores them entirely, and immutability is not weakened anywhere. The era ADDS the micro
+   store family (snapshots, scout ledger, fold ledger, vault + exposure ledger, recorder
+   runs, graduation ledger) under the same discipline, plus one additive default-`None`
+   `observer=` kwarg on `DatasetStore.replay` (counter-tested byte-identical when absent).
 4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not move
    this era; `authorize_promotion` keeps its fail-closed contract untouched.
 5. The **kept surfaces as shipped**: the cockpit, `/structure`, and every shipped `/desk`
@@ -148,12 +154,14 @@ items, in that order.**
    `08e471b10130e1e2` every iteration; every `referee_*` module byte-identical to `main` at
    era open (SHA-256 listing recorded at iteration 0 and re-checked); every kept `/`,
    `/structure`, `/desk` behavior browser-verified as shipped.
-2. **No leakage trap fails, ever.** The TR-1…TR-16 suite of
+2. **No leakage trap fails, ever.** The TR-1…TR-22 suite of
    [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §9 is implemented and green:
    prefix discipline, origin fencing, sealed-shard sweeps, cherry-pick refusal, class-mixing
    refusal, purge exactness, screening calibration, pool invariance, ledger chain integrity,
-   single-shot sealed exposure, geometry freeze, rule identity, tick-corpus refusal, and the
-   synthetic known-null / known-effect end-to-end oracles.
+   single-shot sealed exposure, geometry freeze, rule identity, tick-corpus refusal, the
+   synthetic known-null / known-effect end-to-end oracles — and the r2 traps: TR-17
+   future-event availability, TR-18 units gate, TR-19 Card-5.1 preservation prerequisite,
+   TR-20 root-family lineage, TR-21 process-label discipline, TR-22 exposure registry.
 3. **Every trial is on the record.** The scout ledger is hash-chained append-only; every
    evaluated variant — every kill, with its closed-vocabulary reason — is a permanent row; the
    union-N denominator is served beside every family; "statistically above null" and
@@ -559,10 +567,14 @@ operator-attended act inside the era.
        **opaque pre-exposure metadata (spec §7.5 r2: no symbol, no date range until
        assignment — aggregates only on readiness)**, TR-2 route sweep, TR-4 cherry-pick
        refusal, TR-12 single-shot exposure, TR-20 root-lineage refusal.
-    4. Operator act, inside the era: register the starter-tranche universe, run the recorder
-       against real Alpaca historical trades+quotes to the spec §7.6 minimums (≥30
-       symbol-days, ≥8 panel symbols incl. PG + ≥3 Tier-B + ≥1 ETF, ≥10 dates over ≥6 weeks,
-       the concentration caps, ≥60% full-session), with a restart mid-run proving resume.
+    4. Operator act, inside the era: resolve Tier-B by the spec §7.2 mandatory order (screen
+       by the frozen Card-5.2 criteria → record criteria hash, as-of, provenance, full output,
+       resolved list → freeze the list → `symbol_rule` → register the universe → commitment +
+       HMAC → only then fetch; no re-screen or substitution afterward — vendor failures are
+       disclosed, never swapped), then run the recorder against real Alpaca historical
+       trades+quotes to the spec §7.6 minimums (≥30 symbol-days, ≥8 panel symbols incl. PG +
+       ≥3 Tier-B + ≥1 ETF, ≥10 dates over ≥6 weeks, the concentration caps, ≥60%
+       full-session), with a restart mid-run proving resume.
     5. Refresh readiness: the new shards appear with completeness reporting (including
        `quote_size_unit` and preservation-field presence); sealed members show opaque
        aggregates only.
@@ -639,9 +651,11 @@ operator-attended act inside the era.
 
 - **J-10: The kept product stands — traps armed, sentinel green**
   - Steps:
-    1. Land the full TR-1…TR-16 suite (whichever traps did not ship inside J-02…J-07 land
-       here) plus the extended guard tests (accessor import-ban, micro threshold-sweep ban,
-       copy discipline for micro copy, `_PRICE_ARITHMETIC_FIELDS` additions).
+    1. Land the full TR-1…TR-22 suite (whichever traps did not ship inside J-02…J-07 land
+       here — the r2 traps TR-17 availability, TR-18 units, TR-19 preservation, TR-20 root
+       lineage, TR-21 process labels, TR-22 exposure registry included) plus the extended
+       guard tests (accessor import-ban, micro threshold-sweep ban, copy discipline for micro
+       copy, `_PRICE_ARITHMETIC_FIELDS` additions).
     2. Run the deterministic-rerun check (byte-identical snapshot/screen/fold outputs on a
        re-run over unchanged stores).
     3. Run the kept-product sentinel: cockpit `/` live-tape and chart, `/structure` load and
diff --git a/docs/rapid-validation-spec.md b/docs/rapid-validation-spec.md
index 723ca19..12a338b 100644
--- a/docs/rapid-validation-spec.md
+++ b/docs/rapid-validation-spec.md
@@ -424,6 +424,25 @@ rule_hash}` — appended to the vault ledger first. The recorded batch must be t
 output net of disclosed vendor failures; a verifier recomputes the expected set and refuses
 cherry-picked batches (TR-4).
 
+**The Tier-B resolution order (preflight correction 2026-08-16 — a contract clarification, not
+a methodology change).** Card 5.2's Tier-B mid-cap names are PROVISIONAL; its screening
+CRITERIA are the contract and are re-evaluated at recording time. The mandatory order, which a
+weak executor may not reinterpret:
+1. evaluate the frozen Card-5.2 Tier-B screening criteria;
+2. record, in the vault ledger: the screening criteria/spec hash, the screen's as-of
+   timestamp, the input/provenance basis, the COMPLETE screening output, and the resolved
+   Tier-B symbol list;
+3. freeze that resolved list;
+4. use the resolved list — and nothing else — as the Tier-B portion of `symbol_rule`;
+5. register the recording universe;
+6. record the vault-secret commitment and compute the opaque HMAC seal assignment (§7.3);
+7. only then begin vendor fetches.
+After universe registration: **no Tier-B re-screen, no substitution because a symbol is
+inconvenient, no replacement from vendor availability or observed data** — a vendor failure is
+a DISCLOSED per-chunk/per-symbol failure in the batch report, never a silent swap. The current
+provisional names are never hard-coded as permanently valid; only the resolved, recorded list
+of step 2 is.
+
 ### 7.3 Split vs seal — two independent assignments
 - **Split** (train/holdout tag, Card 5.2's published rule, unchanged): `holdout` iff the last hex
   digit of `sha256(f"{symbol}:{YYYY-MM-DD}")` ∈ {0,1,2}.
diff --git a/docs/research-directions.md b/docs/research-directions.md
index df9fb8d..1ec5739 100644
--- a/docs/research-directions.md
+++ b/docs/research-directions.md
@@ -163,7 +163,7 @@ a weak model that improvises a third will corrupt the honesty machinery:
 | T9 | Vocabulary drift | Banned terms: "paper trading", "shadow trading", "annualized" anything, "expected profit", advice/imperative phrasing. The forward ledger is "**forward replay measurement**". |
 | T10 | Second sources of truth | Never recompute a served value in a new code path; read it from its canonical owner. If a new value is needed, create ONE owner. |
 | T11 | Quiet scope creep into frozen code | New strategies/detectors dispatch **beside** `v1`'s branch; classifier thresholds, `warmup_min_events`, and the five states are untouchable outside an explicit epoch bump. |
-| T12 | Units mixing | SIP quote sizes are **round lots**; trade sizes are **shares**. Never add or ratio them without the documented conversion. |
+| T12 | Units mixing | *(Amended 2026-08-16, rapid-microscope r2 — the old universal "SIP quote sizes are round lots; trade sizes are shares" pin is superseded: Alpaca CTA/UTP displayed quote sizes are SHARES from 2025-11-03.)* Trade sizes and displayed-liquidity sizes must never be added or ratioed except under the ACTIVE dataset-level size-unit/schema-basis contract (`quote_size_unit`, rapid-validation-spec §2.6); cross-basis arithmetic fails closed when units are unverified or incompatible; legacy datasets stay `unverified` until an auditable verification act. |
 
 ## 0.6 Idea-card template legend
 
@@ -488,8 +488,15 @@ forward + UI (5.5–5.9).
 
 #### Card 5.8 — `forward` split + champion forward replay ledger `[infra] [F2] [M]`
 - **Purpose**: true out-of-sample-by-time evidence. A strategy validated on holdout can still
-  fail forward; an append-only forward record accumulates the only evidence that cannot be
-  overfit — because it did not exist yet when the strategy was frozen.
+  fail forward; an append-only forward record accumulates the strongest genuinely-new-time
+  evidence — because those observations did not exist when the strategy was frozen — and it is
+  the only evidence that directly tests whether an effect still exists in the CURRENT/future
+  market regime. *(Amended 2026-08-16, rapid-microscope opening: the original "the only
+  evidence that cannot be overfit" wording predates the rapid era's sealed/clean historical
+  OOS class — sealed `historical_oos` evidence under a frozen spec is also independent of the
+  spec's authoring, but it tests past regimes, not the current one; the two claims are served
+  separately and neither substitutes for the other. Consistent with the Part-1
+  standing-physics amendment: only `live_confirmatory` evidence is calendar-constrained.)*
 - **Build**: (a) add `forward` to `VALID_SPLITS` (`apps/backend/app/research/datasets.py`) —
   additive; (b) recorder top-up mode registers post-era-5 days as `forward`; (c) a job replays
   the CURRENT champion once on each new forward dataset and appends one row to a new
```
