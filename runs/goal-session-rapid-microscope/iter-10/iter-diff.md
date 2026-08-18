# Iteration diff (bounded)

Files changed: 6. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/micro_graduation.py` (271 lines not shown)
- `apps/backend/tests/test_micro_graduation.py` (162 lines not shown)

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 220a509..1f07a4c 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -1,11 +1,17 @@
 """``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, J-02's three
 snapshot routes, J-04's Scout routes, J-05's three walk-forward routes, J-06 step 2's recorder
-routes, and J-06 step 3's ONE read-only vault route. A fresh router/file mounted separately in
-``main.py``, mirroring ``referee_routes.py``'s own precedent and rationale (that file's own
-docstring: "the SAME rationale desk_routes.py itself gives for splitting off routes.py"). The
-era's own Data Contract table (``docs/goal.md``'s Product Shape) names ONE more micro route
-landing in a later iteration (graduation) under this SAME ``/research/desk/micro`` prefix -- a
-dedicated file is the right home from the start.
+routes, J-06 step 3's ONE read-only vault route, and J-07's ONE read-only graduation route. A
+fresh router/file mounted separately in ``main.py``, mirroring ``referee_routes.py``'s own
+precedent and rationale (that file's own docstring: "the SAME rationale desk_routes.py itself
+gives for splitting off routes.py"). The era's own Data Contract table (``docs/goal.md``'s Product
+Shape) named this exact route ("graduation states + export bundles") as landing in a later
+iteration under this SAME ``/research/desk/micro`` prefix -- this file was always its right home.
+
+``GET /graduation`` is GET-only this iteration, exactly like ``GET /vault`` above it -- J-07 is
+keyless/automated (no operator compute act triggers graduation; a candidate's state is read back
+from whatever ``micro_graduation.py``'s own evaluation functions have already recorded, called
+directly -- by a test today, by a future J-08/J-09 wiring later), so it needs no compute manager
+and no ``POST``/cancel sibling routes.
 
 ``GET /vault`` is GET-only this iteration -- no ``/vault/compute`` route and no CLI (the phase
 spec's own OUT OF SCOPE: "no operator act in this iteration or the next calls registration
@@ -40,6 +46,7 @@ from .desk_playbook import PlaybookStore
 from .desk_routes import get_playbook_store, get_universe_store
 from .desk_universe import UniverseStore
 from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
+from .micro_graduation import EMPTY_LEDGER_MESSAGE, GraduationLedger, list_graduation_families, resolve_micro_graduation_dir
 from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
 from .micro_snapshots import (
     MicroSnapshotComputeManager,
@@ -531,3 +538,35 @@ def get_vault(vault_dir: str = Depends(get_vault_dir)) -> dict:
     before any universe is ever registered (registration is a step-4, operator-attended act, out of THIS iteration's
     scope)."""
     return vault.build_vault_state(vault.VaultShardLedger(vault_dir), vault.VaultUniverseLedger(vault_dir))
+
+
+# --- J-07: Graduation (micro_graduation.py) -- GET-only this iteration ------------------------------
+
+
+def get_micro_graduation_dir() -> str:
+    """The graduation ledger's directory -- ``TAPEOLOGY_MICRO_GRADUATION_DIR`` if set, else a
+    SIBLING of the config-owned dataset directory (``micro_graduation.resolve_micro_graduation_dir``
+    -- see that function's own docstring)."""
+    return resolve_micro_graduation_dir(CONFIG.dataset_dir_resolved())
+
+
+@router.get("/graduation")
+def get_graduation(graduation_dir: str = Depends(get_micro_graduation_dir)) -> dict:
+    """Serves ``micro_graduation.py``'s own recorded state verbatim (``list_graduation_families`` --
+    see that function's own docstring): every family_root_id ever recorded here, each with its
+    current stage-vocabulary state, complete transition history, and complete sealed-evaluation
+    history -- beside the ledger's own chain-verification verdict (the ``GET /scout``/``GET
+    /walkforward``/``GET /vault`` precedent: surfaced beside the data, never silently accepted if
+    tampered). Never 404/500 on an empty ledger (TC-9) -- no operator has run graduation yet on a
+    fresh install, so an honest ``EMPTY_LEDGER_MESSAGE`` ("No candidates ledgered.", goal.md's own
+    Design Direction example) accompanies the empty ``families`` list at HTTP 200, never a
+    fabricated row. Page-load GETs never compute (T-8): J-07 is keyless/automated -- a candidate's
+    state is recorded by calling ``micro_graduation.py``'s evaluation functions directly (a test
+    today; a future J-08/J-09 wiring act later), never by this route."""
+    ledger = GraduationLedger(graduation_dir)
+    families = list_graduation_families(ledger)
+    return {
+        "families": families,
+        "message": None if families else EMPTY_LEDGER_MESSAGE,
+        "chain_verification": ledger.verify_chain(),
+    }
diff --git a/docs/goal.md b/docs/goal.md
index 4a5031f..f988cf3 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -564,10 +564,14 @@ operator-attended act inside the era.
        the published sha256 split beside the HMAC seal assignment
        (`TAPEOLOGY_VAULT_SECRET_FILE`, commitment recorded), one-way
        `sealed → assigned → exposed` exposure ledger keyed on the computed `family_root_id`,
-       **opaque pre-exposure metadata (spec §7.5 r3: surrogate shard id, salted commitment,
+       **opaque pre-exposure metadata (spec §7.5 r3–r5: surrogate shard id, salted commitment,
        no symbol/date until assignment, sealed dataset ids refused on the dataset + MCP
-       surfaces — aggregates only on readiness)**, TR-2 join-resistance sweep, TR-4
-       cherry-pick refusal, TR-12 single-shot exposure, TR-20 root-lineage refusal.
+       surfaces, corpus enumerators excluding withheld shards with a disclosed
+       `withheld_excluded` count, and the r5 opaque-pool rule — aggregates only on readiness
+       for BOTH sides, no complete per-shard list of either while any member is unexposed;
+       aggregate-only recorder progress with no operator bypass)**, TR-2 join-resistance +
+       inference sweep, TR-4 cherry-pick refusal, TR-12 single-shot exposure, TR-20
+       root-lineage refusal.
     4. Operator act, inside the era: resolve Tier-B by the spec §7.2 mandatory order (screen
        by the frozen Card-5.2 criteria → record criteria hash, as-of, provenance, full output,
        resolved list → freeze the list → `symbol_rule` → register the universe → commitment +
@@ -576,16 +580,18 @@ operator-attended act inside the era.
        trades+quotes to the spec §7.6 minimums (≥30 symbol-days, ≥8 panel symbols incl. PG +
        ≥3 Tier-B + ≥1 ETF, ≥10 dates over ≥6 weeks, the concentration caps, ≥60%
        full-session), with a restart mid-run proving resume.
-    5. Refresh readiness: the new shards appear with completeness reporting (including
-       `quote_size_unit` and preservation-field presence); sealed members show opaque
-       aggregates only.
+    5. Refresh readiness: the new tranche appears as ONE pool with aggregate completeness
+       reporting (including `quote_size_unit` and preservation-field presence); while any
+       member is unexposed, neither side is listed per-shard.
   - Acceptance: TR-2/4/12/19/20 pass; every legacy dataset and committed fixture loads
     byte-identically with checksums verifying and the engine equivalence/golden-trace tests
     byte-unmodified; the tranche exists on disk meeting every §7.6 minimum (readiness serves
     the arithmetic) with every new shard carrying `schema_basis`, preservation fields, and a
     stamped `quote_size_unit`; at least the HMAC-assigned subset of tranche shards is `sealed`
     with zero exploratory reads recorded before sealing and no symbol/date served
-    pre-exposure; the recorder run ledger shows the mid-run restart resuming without duplicate
+    pre-exposure; the TR-2 inference trap passes against the tranche's own registered universe
+    (no unexposed shard identifiable with certainty from any served artifact, either side);
+    the recorder run ledger shows the mid-run restart resuming without duplicate
     registration; the legacy 12 symbol-days remain `exploratory`; the readiness gate line
     still reads the ~150-symbol-day research gate as unmet.
 
@@ -732,6 +738,15 @@ no confirmatory output without a verified oracle attestation; no annualized metr
 - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one
   evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
   travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
+- **A recorded tranche is one opaque research pool until its shards are exposed.** No served
+  surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
+  graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
+  versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
+  unexposed; the registered universe is public by construction, so a complete list of one side
+  identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
+  identity becomes public only at real exposure or assignment. The governing test is the TR-2
+  inference trap: given the registered universe plus every public artifact, no still-unexposed
+  vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
 - **Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a
   graduation transition, a certificate, a promotion, or a pooled statistic with
   `historical_oos` rows; nothing in this era emits `live_confirmatory`. *(critical)*
diff --git a/docs/rapid-validation-spec.md b/docs/rapid-validation-spec.md
index 6f66625..f79779c 100644
--- a/docs/rapid-validation-spec.md
+++ b/docs/rapid-validation-spec.md
@@ -52,6 +52,26 @@
 > that "a partial report is a misleading report", which forbids the silent variant. Rejected:
 > aborting a whole sweep whenever any sealed shard exists (renders the edge report unusable the
 > moment the vault holds anything) and accepting the bypass (re-opens exactly what r3 closed).
+>
+> **Revision r5 (2026-08-18, owner ruling — the opaque research pool).** The FINAL
+> pre-implementation clarification of the vault surface: applied while ZERO shards are sealed and
+> ZERO tranches recorded, so it **re-keys nothing** — no spec id, parameter hash, ledger row, or
+> recorded verdict moves, and it changes no statistical rule, constant, grid, fold geometry, or
+> gate. It is recorded as a named revision only because this file's own rule makes ANY change to
+> it a named revision, never because recorded meaning changed. The iteration-9 audit proved that
+> r3+r4 still leave the partition reconstructible by SUBTRACTION: §7.2 requires the symbol rule
+> and date rule to be registered before any fetch, so the operator already knows the universe;
+> serving a complete identity-labelled list of the exploratory (non-sealed) side then reveals the
+> withheld set as its complement. Hiding the axes from readiness does not erase that prior
+> knowledge, so the r5 closure is structural rather than cosmetic: **a newly recorded tranche is
+> ONE OPAQUE RESEARCH POOL until individual shards are actually exposed or assigned** (§7.5
+> points 4, 7, 8; §7.1 recorder progress). The HMAC is reframed accordingly — an internal
+> deterministic, auditable assignment mechanism, NOT a public global partition whose complement
+> can be reconstructed. TR-2 is widened from join resistance to a deterministic inference trap.
+> Explicitly rejected by the owner: accepting the residual with a disclosed caveat, and breaking
+> the cartesian shape with recording-cost decoys. Where the shipped architecture requires every
+> non-sealed shard to become individually visible at record time, the ARCHITECTURE changes. The
+> one-way exposure history and the single-shot `family_root_id` rules are preserved unchanged.
 
 ---
 
@@ -431,6 +451,20 @@ symbol-days so band context joins. Recording failure modes (vendor timeout, part
 credential absence) are per-chunk `failed` outcomes with detail — never a raise, never a
 fabricated row.
 
+**Recorder progress is AGGREGATE-ONLY while the pool is unexposed (r5).** `GET
+/research/desk/micro/recorder/compute` — and every other progress surface, UI or MCP — serves
+only non-identifying aggregates: chunks completed / total, successful / failed / pending counts,
+aggregate retry and failure counts, total bytes, total trades and quotes, percent complete, and
+deterministic elapsed/throughput diagnostics. It MUST NOT serve symbol, date, dataset id, shard
+id, per-shard byte or event counts, or any other per-chunk identity-bearing metadata, because
+watching a live recording would otherwise reveal pool membership before assignment. The detailed
+per-chunk identities remain in the INTERNAL recorder ledger for recovery, idempotency and audit;
+recovery and debugging read that persisted state, never an identity-bearing public response.
+Once a shard is legitimately exposed, its identity appears through the normal exposure surfaces.
+**There is no operator-only bypass** — using one would itself be a human exposure event that
+destroys the tranche's blindness, and it is unnecessary for ordinary monitoring. TR-2's
+inference trap (§7.5) covers the recorder progress path explicitly.
+
 **The Card-5.1 data-preservation prerequisite (r2) — a HARD gate before any bulk recording.**
 Before the recorder may record ANY universe (starter tranche included), the event schema ships
 the preservation fields: optional `conditions: list[str]` and `exchange: str` on
@@ -515,8 +549,13 @@ surface serves. Therefore:
    the `datasets` MCP tool, and any `get_endpoint` path resolving to them REFUSE a sealed
    dataset id with a typed refusal until its exposure is recorded. The refusal states only that
    the id is sealed — never symbol, window, counts, or universe.
-4. **Readiness serves sealed-tranche AGGREGATES only** (shard count, total symbol-days,
-   per-universe totals) — never a per-shard row, never a per-shard `exposure_state`.
+4. **Readiness serves tranche AGGREGATES only, on BOTH sides (r5).** While ANY member of a
+   recorded pool remains unexposed, readiness serves counts and coarse per-universe totals and
+   NOTHING per-shard — not for the sealed side and **not for the exploratory side either**. A
+   complete identity-labelled list of the non-sealed side is forbidden precisely because its
+   complement against the registered universe (§7.2, known to the operator by construction)
+   reveals the withheld set. No served artifact may present a complete identity-labelled
+   partition of "exploratory" versus "sealed".
 5. Recorder run logs commit per-shard identity and counts by hash while sealed.
 6. **Corpus enumerators honour the seal (r4).** A refusal wired only into a route is bypassed by
    any module that enumerates the store itself. Therefore every corpus-wide enumerator —
@@ -528,10 +567,29 @@ surface serves. Therefore:
    already hold that "a partial report is a misleading report", and the era's denominator rail
    forbids a corpus that shrinks without saying so. A run whose entire eligible corpus is
    withheld reports that honestly rather than emitting an empty-but-shaped result.
+7. **The opaque research pool (r5).** A newly recorded tranche is ONE POOL. Membership in it is
+   public (the operator registered the universe); **position within it is not**. A shard's
+   identity becomes public ONLY when that shard is actually exposed for exploratory use or
+   assigned to a candidate family — at which moment it leaves the pool through the normal
+   exposure surfaces governed by the exposure ledger. Unused pool members stay opaque and
+   **indistinguishable from one another**: no served id, ordering, index, timestamp, size, state
+   label, or per-shard statistic may separate an unexposed exploratory shard from an unexposed
+   sealed one. The internal vault and exposure ledgers retain exact identities and HMAC
+   decisions for audit; no API, UI, or MCP surface may serve enough of them to reconstruct the
+   hidden partition. If an implementation requires every non-sealed shard to become individually
+   visible immediately after recording, the IMPLEMENTATION changes — decoy recordings and
+   accepted residual leakage are both rejected.
+8. **The HMAC's role, restated (r5).** `HMAC(vault_secret, …)` is an INTERNAL deterministic and
+   auditable assignment mechanism. It is not, and must never be served as, a public global
+   partition — a partition whose complement is computable is not a vault.
 
 No pre-exposure field may equal, contain, or be derivable from any field the public surfaces
-serve for the same shard, and no exploratory statistic may be computed from one. TR-2 proves
-this by construction, not by whitelist review — and it exercises the operator compute acts
+serve for the same shard, and no exploratory statistic may be computed from one. **The
+governing test is a deterministic inference trap (r5), not a field whitelist: given the
+registered universe (§7.2) plus EVERY public artifact the system serves — readiness, recorder
+progress, datasets, backtests, PnL ledger, Scout, walk-forward, graduation, MCP, UI — an
+attacker must not be able to determine the identity of ANY still-unexposed vault-eligible shard
+with certainty.** TR-2 proves this by construction — and it exercises the operator compute acts
 (snapshot build, Scout run, edge report, PnL sweep) BEFORE sweeping, so it cannot pass merely
 because the rig computed nothing.
 
@@ -589,7 +647,7 @@ No state ever moves backward except by a voiding event (§6.2), which is itself
 | Trap | Asserts |
 |---|---|
 | TR-1 prefix/tail | Truncated-dataset snapshot rows byte-identical to the full run's prefix (3 cut points incl. i=1); appending one tail event changes no prior row |
-| TR-2 sealed sweep (r3: join-resistance) | Every registered route + MCP tool serves only §7.5 metadata (or a typed refusal) for a sealed shard — AND the sweep is adversarial, not a whitelist review: seal a fixture shard, collect every value any surface serves for it pre-exposure, and assert none equals, contains, or derives the dataset id, raw `content_checksum`, symbol, window, or event counts. Explicitly includes `/research/datasets{,/{id}}`, the `datasets` MCP tool, `get_endpoint`, and `micro_readiness` (which must expose no per-shard row at all) |
+| TR-2 sealed sweep (r3: join-resistance; r5: inference trap) | Every registered route + MCP tool serves only §7.5 metadata (or a typed refusal) for a sealed shard — AND the sweep is adversarial, not a whitelist review: seal a fixture shard, collect every value any surface serves for it pre-exposure, and assert none equals, contains, or derives the dataset id, raw `content_checksum`, symbol, window, or event counts. Explicitly includes `/research/datasets{,/{id}}`, the `datasets` MCP tool, `get_endpoint`, `micro_readiness` (no per-shard row at all, EITHER side) and the recorder progress path. **r5 inference trap** — the decisive assertion: record a fixture pool under a registered universe (§7.2) whose symbol rule and date rule the trap KNOWS, expose a proper subset, then assert that the union of every public artifact (readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward, graduation, MCP, UI) plus that known universe leaves ≥2 candidate identities for every still-unexposed vault-eligible shard — i.e. no unexposed shard is identifiable with certainty, and no complete identity-labelled exploratory/sealed partition is derivable by subtraction |
 | TR-3 accessor fence | Origin-T accessor refuses reads > T with a typed error; corpus aggregates exclude > T exactly; import-ban: only `micro_accessor` opens snapshot/vault data paths |
 | TR-4 cherry-pick refusal | A recording batch ≠ its universe rule's computed set (net of disclosed failures) is refused |
 | TR-5 class mixing | Pooling `historical_exposed_diagnostic` with `historical_oos` rows in one statistic is refused; diagnostic folds contribute zero to graduation |
@@ -640,3 +698,21 @@ discipline, MCP contract, replay-script static sweep.
    diagnostic, decide admissibility.
 6. Nothing in this era emits `live_confirmatory` evidence; the Referee remains the only source
    of confirmatory claims, unchanged.
+7. **`referee_evidence.strategy_trade_readiness` is seal-unaware — a deliberate, disclosed
+   compatibility limitation of this era (r5 owner ruling).** It counts dataset FILES through its
+   own enumeration and may therefore include withheld, unexposed Rapid-Microscope shards. The
+   era's byte-freeze rail on `referee_*.py` is PRESERVED: the file is not edited, and
+   `DatasetStore` is NOT intercepted to change frozen Referee behaviour indirectly (that would
+   breach the freeze's behavioural meaning even with identical bytes). Instead, wherever that
+   metric is served, it carries the caveat verbatim: *"Legacy Referee readiness metric —
+   seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope
+   shards and must not be used as the canonical Rapid-Microscope readiness count."* The new
+   seal-aware `micro_readiness` surface is the CANONICAL owner of every Rapid-Microscope
+   corpus/readiness decision. Enforced: the stale count awards ZERO gate or graduation credit; no
+   Scout, walk-forward, vault, graduation, or readiness-floor decision may consume it; no UI, API,
+   or MCP surface may present it as equivalent to the seal-aware count, and where both appear
+   their differing semantics are labelled explicitly; a guard/source-scan proves Rapid-Microscope
+   gates read only the seal-aware owner. The actual Referee fix is deferred to a future named
+   Referee revision. **Escalation condition:** if audit finds `strategy_trade_readiness` is
+   consumed by a live promotion or certificate decision rather than being a readiness/reporting
+   value, STOP and escalate — that case requires a named Referee revision, not disclosure.
diff --git a/docs/research-directions.md b/docs/research-directions.md
index 1ec5739..7d37fa2 100644
--- a/docs/research-directions.md
+++ b/docs/research-directions.md
@@ -1748,6 +1748,15 @@ so in the purchase decision: a dead L1 imbalance LOWERS the depth prior).
 > `historical_oos`-class evidence there, which both raises the depth prior and becomes 15.3's
 > named comparison baseline. Those families dying at the Scout LOWERS the prior, exactly as
 > Card 9.3's kill note already says. Diagnostic-class results count for neither direction.)*
+>
+> *(Follow-up 2026-08-18, "The Rapid Microscope" J-07 step 3, documentation-only — no code, no
+> threshold, no purchase decision: the mechanism the amendment above promised now exists.
+> `micro_graduation.py` (`docs/rapid-validation-spec.md` §8) implements the literal
+> `walkforward_survivor`/`sealed_survivor` states this amendment names as the Depth-purchase
+> evidence; either verdict for an L1 liquidity-family candidate — including a diagnostic-class
+> `no survivor` at the Scout, which counts for neither direction per the amendment above and this
+> era's own §10 disclosed L1-only-measurement limits — reads directly off that ledger when a
+> future Era-15 kickoff needs it, rather than requiring re-derivation.)*
 
 ---
 
diff --git a/apps/backend/app/research/micro_graduation.py b/apps/backend/app/research/micro_graduation.py
new file mode 100644
index 0000000..442e741
--- /dev/null
+++ b/apps/backend/app/research/micro_graduation.py
@@ -0,0 +1,665 @@
+"""``micro_graduation.py`` -- Era "The Rapid Microscope" J-07 (``docs/rapid-validation-spec.md``
+
+section 8): the stage vocabulary ``exploratory -> walkforward_survivor -> sealed_survivor ->
+referee_handoff_ready`` and the provenance-complete export bundle. This module OWNS no research
+computation of its own -- it is a pure bookkeeping/state-machine layer that reads already-computed,
+already-ledgered evidence from three sibling modules and records WHICH state a candidate family has
+earned, with full provenance and nothing laundered out.
+
+**A fourth ``HashChainedLedger``, reusing the SAME shared primitive -- never a hand-rolled chain**
+(the carried iter-4 lesson, named explicitly in this iteration's own spec). ``walkforward_ledger.py``
+already established the "one global chain, N row kinds, discriminated by ``row_kind``" shape for
+exactly this reason; this module's ``GraduationLedger`` is a third instance of that SAME shape
+(``state_transition`` rows and ``sealed_evaluation`` rows share one physical file), built on
+``micro_chain_ledger.HashChainedLedger`` directly -- the tail-anchor discipline (a truncated LAST
+row is otherwise invisible to a hash chain alone) comes for free.
+
+**Two identity spaces this era has never joined -- and this module does not invent a join.** A
+Scout candidate's identity is ``family_root_id`` (``scout_ledger.compute_family_root_id`` --
+``sha256(feature_family_name, structure_context_kind, outcome_horizon_family)``). A walk-forward
+SEQUENCE's identity is ``sequence_id`` (``walkforward.sequence_id_for`` --
+``sha256(corpus_id, rule_identity)``). No fold_result row anywhere carries a ``family_root_id``
+field (confirmed by reading ``register_mode_a_origin``/``evaluate_mode_b_fold``'s own row_fields --
+neither stamps one), and OUT OF SCOPE forbids adding one (no change to ``walkforward_ledger.py``'s
+persisted row shape). So every function below that needs BOTH identities (``evaluate_walkforward_
+survivor_transition``, ``build_export_bundle``) takes ``sequence_id`` as an explicit, caller-supplied
+argument alongside ``family_root_id`` -- exactly the same "caller already knows both, this module
+never guesses a join" discipline ``evaluate_mode_b_fold`` itself uses for ``spec``/``fold``. A real
+future join (a Scout candidate registering ITS OWN sequence_id at Mode-B spec time) is a natural
+J-08/J-09 wiring concern, not invented here.
+
+**The sealed-shard EVALUATION verdict is caller-supplied, not computed here -- a disclosed T-1
+interpretation call.** Spec section 8 state 3 requires "additionally passed its single-shot
+root-family-level sealed-shard evaluation (section 7.4, keyed on family_root_id) under a spec frozen
+before assignment" as a CONDITION -- it does not prescribe the statistical MACHINERY that produces a
+pass/fail verdict from a sealed shard's exposed event data (that would be a Mode-B-style evaluation
+run through the accessor against real vault data, which does not exist anywhere in this codebase yet
+and is out of THIS iteration's scope: zero real sealed shards exist this era, J-06 step 4 is
+human-blocked, and TR-3/accessor territory is explicitly deferred to a dedicated J-10 hardening
+iteration). ``vault.py`` itself carries no pass/fail concept at all -- only shard LIFECYCLE state
+(sealed/assigned/exposed). So ``record_sealed_evaluation`` below is handed an ALREADY-COMPUTED
+``passed`` verdict (mirroring ``walkforward.py``'s own "a corpus-specific reader feeds a
+corpus-agnostic statistical core" split for its Mode-B evaluator) and is responsible for exactly the
+TWO things spec section 8 DOES specify: (1) confirming, via ``vault.py``'s existing, UNMODIFIED
+``build_vault_state`` (never a new vault.py function), that the named shard genuinely reached
+``exposed`` for this EXACT ``family_root_id`` before any verdict is ever recorded against it -- never
+trusting the caller's claim alone; and (2) recording that verdict PERMANENTLY, exactly once per
+(family_root_id, dataset_id) (TR-12) -- pass OR fail, since spec section 7.4's own words are "a
+failed sealed verdict is a permanent root-family fact carried in every later export bundle".
+
+**The export bundle is buildable for ANY ledgered family, at ANY state -- not gated to
+``sealed_survivor``+.** This is what makes TC-6's "a failed-sealed twin's permanent failed verdict
+is carried into its own bundle" possible at all: if bundle-building required ``sealed_survivor``, a
+family that legitimately reached only ``walkforward_survivor`` (its sealed attempt having FAILED)
+could never have its own failure inspected through this function. ``build_export_bundle`` therefore
+always returns the complete provenance on record PLUS the family's own current ``state`` field --
+``referee_handoff_ready`` is a STATE TRANSITION (``evaluate_referee_handoff_ready_transition``)
+earned by attempting to build a bundle for a ``sealed_survivor`` candidate and having it VALIDATE
+(``bundle_validates``); the bundle-building primitive itself carries no gate.
+
+**No new module constant, no ``graduation_parameters()``.** Every sibling module with its own tuned
+constants (``scout.py``'s ``SCOUT_SCREEN_ALPHA``, ``walkforward.py``'s ``WF_MIN_SUFFICIENT_FOLDS``,
+...) embeds a ``*_parameters()`` function so a persisted record can key on their hash (the era's
+Parameters discipline, goal.md Constraints). This module introduces NO tunable numeric constant of
+its own -- ``WF_SURVIVOR_RULE_V1`` is evaluated ENTIRELY by ``walkforward.sequence_verdict``
+(consulted, never reimplemented, per this iteration's own spec), and the sealed-shard verdict is
+caller-supplied. A ``graduation_parameters()`` function would have nothing genuine to embed, so none
+exists -- inventing one would be exactly the "config for behavior the spec fixed" the simplicity bar
+forbids.
+
+**Idempotent, identity-keyed, replay-safe (the iter-5 lesson, named for this exact journey in this
+iteration's own spec).** Every state-advancing function below checks FIRST whether the target
+transition (or, for sealed evaluation, the identical (family_root_id, dataset_id) verdict) is
+ALREADY recorded and returns ``{"transition": "replayed", ...}`` without touching the ledger file --
+mirroring ``walkforward_ledger.register_fold_spec``'s own "re-registering the IDENTICAL content is an
+idempotent replay; a genuinely DIFFERENT one is refused" split. A repeated advancement check with no
+new ledgered evidence therefore NEVER appends a second row (TC-7); a genuinely conflicting second
+claim is refused outright, never silently accepted (the sealed-evaluation half of this split)."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from datetime import datetime, timezone
+from pathlib import Path
+
+from . import vault
+from . import walkforward as wf
+from .micro_chain_ledger import HashChainedLedger
+from .scout_ledger import ScoutLedger, distinct_variant_count
+
+__all__ = [
+    "GRADUATION_STATE_EXPLORATORY",
+    "GRADUATION_STATE_WALKFORWARD_SURVIVOR",
+    "GRADUATION_STATE_SEALED_SURVIVOR",
+    "GRADUATION_STATE_REFEREE_HANDOFF_READY",
+    "GRADUATION_STATES_ORDER",
+    "TRANSITION_APPENDED",
+    "TRANSITION_REPLAYED",
+    "ROW_KIND_STATE_TRANSITION",
+    "ROW_KIND_SEALED_EVALUATION",
+    "REFEREE_FUTURE_REVISION_SENTENCE",
+    "EMPTY_LEDGER_MESSAGE",
+    "GraduationTransitionRefusedError",
+    "GraduationLedger",
+    "resolve_micro_graduation_dir",
+    "state_transitions_for_family",
+    "current_graduation_state",
+    "sealed_evaluations_for_family",
+    "evaluate_walkforward_survivor_transition",
+    "record_sealed_evaluation",
+    "evaluate_sealed_survivor_transition",
+    "build_export_bundle",
+    "bundle_validates",
+    "evaluate_referee_handoff_ready_transition",
+    "list_graduation_families",
+]
+
+# === spec section 8's four states, strictly ordered (transcribed verbatim) ==========================
+
+GRADUATION_STATE_EXPLORATORY = "exploratory"
+# Reuses `walkforward.WF_VERDICT_SURVIVOR` verbatim -- single source of truth for the token: the
+# SAME string names both "the WF_SURVIVOR_RULE_V1 verdict" (walkforward.py's own vocabulary) and
+# "the graduation state a candidate earns by satisfying it" (spec section 8's own vocabulary),
+# because spec section 8 point 2 defines the state to BE exactly that verdict. Minting a second,
+# independently-spelled constant here would risk the two silently drifting apart.
+GRADUATION_STATE_WALKFORWARD_SURVIVOR = wf.WF_VERDICT_SURVIVOR
+GRADUATION_STATE_SEALED_SURVIVOR = "sealed_survivor"
+GRADUATION_STATE_REFEREE_HANDOFF_READY = "referee_handoff_ready"
+
+# Documents the invariant (spec section 8's opening line: "States, strictly ordered") -- not used as
+# a generic "advance N states" lookup anywhere below (no code path needs one; each transition
+# function names its own single, specific predecessor state), so this stays a plain tuple, never a
+# rank-comparison helper this iteration has no tested use for.
+GRADUATION_STATES_ORDER = (
+    GRADUATION_STATE_EXPLORATORY,
+    GRADUATION_STATE_WALKFORWARD_SURVIVOR,
+    GRADUATION_STATE_SEALED_SURVIVOR,
+    GRADUATION_STATE_REFEREE_HANDOFF_READY,
+)
+
+TRANSITION_APPENDED = "appended"
+TRANSITION_REPLAYED = "replayed"
+
+ROW_KIND_STATE_TRANSITION = "state_transition"
+ROW_KIND_SEALED_EVALUATION = "sealed_evaluation"
+
+# spec section 8 point 4, transcribed close to verbatim -- TC-4. A module-level constant (never
+# re-composed per call) so `bundle_validates` can compare byte-exactly and every caller (the bundle
+# builder, the test suite) reads the identical sentence.
+REFEREE_FUTURE_REVISION_SENTENCE = (
+    "This referee_handoff_ready state does not imply the current Referee can register or "
+    "adjudicate this candidate: a flow-context predicate requires a future named revision of "
+    "docs/referee-statistical-spec.md. Where a candidate maps onto the existing referee vocabulary "
+    "(setup, side, existing context predicates, existing measures), the bundle is registrable "
+    "through the existing operator act unchanged."
+)
+
+# goal.md's own Design Direction example, verbatim ("Honest empty/degraded states are first-class
+# copy") -- TC-9's own literal string.
+EMPTY_LEDGER_MESSAGE = "No candidates ledgered."
+
+_GRADUATION_DIR_ENV = "TAPEOLOGY_MICRO_GRADUATION_DIR"
+_LEDGER_FILENAME = "graduation_ledger.jsonl"
+
+
+class GraduationTransitionRefusedError(Exception):
+    """A graduation transition was refused -- never silently skipped, never silently advanced (spec
+    section 8; TC-5). Carries the exact ``family_root_id``/``target_state``/``reason`` so a caller
+    can report WHY without parsing prose (the ``vault.ShardLifecycleOrderError`` structured-args
+    precedent)."""
+
+    def __init__(self, family_root_id: str, target_state: str, reason: str) -> None:
+        self.family_root_id = family_root_id
+        self.target_state = target_state
+        self.reason = reason
+        super().__init__(
+            f"graduation transition to {target_state!r} refused for family_root_id "
+            f"{family_root_id!r}: {reason}"
+        )
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def resolve_micro_graduation_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_MICRO_GRADUATION_DIR`` if set, else a ``micro_graduation`` SIBLING of the
+    caller's already-resolved dataset directory -- the ``scout_ledger.resolve_scout_ledger_dir``/
+    ``vault.resolve_vault_dir`` pattern verbatim. Never a ``Config`` field (an operational
+    storage-location knob, goal.md Constraints)."""
+    override = os.environ.get(_GRADUATION_DIR_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "micro_graduation")
+
+
+class GraduationLedger:
+    """A thin domain wrapper over ONE ``HashChainedLedger`` -- the ``walkforward_ledger.
+    WalkForwardLedger`` "one global chain, N row kinds" shape, mirrored exactly."""
+
+    def __init__(self, root_dir: str | Path) -> None:
+        self._chain = HashChainedLedger(root_dir, _LEDGER_FILENAME)
+
+    def verify_chain(self) -> dict:
+        return self._chain.verify_chain()
+
+    def all_rows(self) -> list[dict]:
+        return self._chain.all_rows()
+
+    def rows_of_kind(self, row_kind: str) -> list[dict]:
+        return [row for row in self._chain.all_rows() if row.get("row_kind") == row_kind]
+
+    def append_row(self, fields: dict) -> dict:
+        """The pure storage primitive (the ``WalkForwardLedger.append_row`` precedent -- enforces
+        no business rule of its own; every function below is the validated entry point)."""
+        return self._chain.append_row(fields)
+
+
+# === read-only queries over THIS module's own ledger =================================================
+
+
+def state_transitions_for_family(ledger: GraduationLedger, family_root_id: str) -> list[dict]:
+    """Every ``state_transition`` row ever recorded for ``family_root_id``, append order --
+    including every state it has EVER held, never merely the current one (nothing laundered out)."""
+    return [
+        row for row in ledger.rows_of_kind(ROW_KIND_STATE_TRANSITION)
+        if row.get("family_root_id") == family_root_id
+    ]
+
+
+def current_graduation_state(ledger: GraduationLedger, family_root_id: str) -> str:
+    """The family's current state: the LAST recorded ``state_transition`` row's ``to_state``, or
+    ``GRADUATION_STATE_EXPLORATORY`` when none exists -- spec section 8 point 1's own "any ledgered
+    candidate [is exploratory]" needs no row of its own; a candidate's mere existence in the Scout
+    ledger already establishes it, so exploratory is the implicit default this function reads back
+    rather than a fact this module ever appends. Append order IS chronological order here (every
+    transition function below only ever appends the SINGLE next state after checking its own
+    precondition), so the last row is always the current one -- never a rank comparison needed."""
+    transitions = state_transitions_for_family(ledger, family_root_id)
+    if not transitions:
+        return GRADUATION_STATE_EXPLORATORY
+    return transitions[-1]["to_state"]
+
+
+def sealed_evaluations_for_family(ledger: GraduationLedger, family_root_id: str) -> list[dict]:
+    """Every ``sealed_evaluation`` row ever recorded for ``family_root_id`` -- pass AND fail alike,
+    permanent, never filtered (TR-12/TC-6: a failed verdict is a permanent root-family fact)."""
+    return [
+        row for row in ledger.rows_of_kind(ROW_KIND_SEALED_EVALUATION)
+        if row.get("family_root_id") == family_root_id
+    ]
+
+
+# === state 2: exploratory -> walkforward_survivor (spec section 8 point 2, TC-1/TC-5/TC-7) ==========
+
+
+def evaluate_walkforward_survivor_transition(
+    graduation_ledger: GraduationLedger,
+    wf_ledger: "wf.WalkForwardLedger",
+    *,
+    family_root_id: str,
+    sequence_id: str,
+    evaluated_at: str | None = None,
+) -> dict:
+    """Reads this sequence's fold rows via ``walkforward.fold_results_for_sequence`` (existing,
+    read-only) and its corpus's voiding state via ``walkforward.is_corpus_era_voided`` (existing,
+    read-only) -- ``corpus_id`` is read OFF the ledgered fold rows themselves (``fold_results[0]
+    ["corpus_id"]``), never a second caller-supplied value that could drift from what is actually
+    ledgered. Delegates the ENTIRE five-condition ``WF_SURVIVOR_RULE_V1`` predicate to
+    ``walkforward.sequence_verdict`` -- consulted, never reimplemented (this iteration's own spec):
+    the rule's conditions live in exactly ONE function in this codebase, and duplicating them here
+    would be the "second, independently-valued copy" this codebase's own conventions warn against.
+
+    Idempotent + identity-keyed (``family_root_id`` + this target state, iter-5 lesson): a
+    ``family_root_id`` that already carries a ``walkforward_survivor`` transition row is answered
+    ``replayed`` with the EXISTING row -- walk-forward evidence is read-only from this module's own
+    vantage, so re-evaluating could only ever reproduce the identical verdict from the identical
+    ledgered folds (TC-7). Raises ``GraduationTransitionRefusedError`` (never silently advances,
+    never returns a fabricated verdict) when the ledgered evidence does not satisfy the rule --
+    covering BOTH "fewer than WF_MIN_SUFFICIENT_FOLDS sufficient folds exist" (``sequence_verdict``'s
+    own floor refusal) and "sufficient folds exist but the rule's five conditions are not jointly
+    met" (e.g. TC-5's diagnostic-only twin, whose folds are all ``historical_exposed_diagnostic`` and
+    so never become ``eligible``, failing condition 1)."""
+    already = [
+        row for row in state_transitions_for_family(graduation_ledger, family_root_id)
+        if row["to_state"] == GRADUATION_STATE_WALKFORWARD_SURVIVOR
+    ]
+    if already:
+        return {"transition": TRANSITION_REPLAYED, "state": GRADUATION_STATE_WALKFORWARD_SURVIVOR, "row": dict(already[-1])}
+
+    fold_results = wf.fold_results_for_sequence(wf_ledger, sequence_id)
+    corpus_id = fold_results[0]["corpus_id"] if fold_results else None
+    sidedness = fold_results[0]["sidedness"] if fold_results else None
+    econ_floor = fold_results[0]["econ_floor"] if fold_results else None
+    voided = wf.is_corpus_era_voided(wf_ledger, corpus_id) if corpus_id is not None else False
+
+    verdict = wf.sequence_verdict(fold_results, sidedness=sidedness, econ_floor=econ_floor, voided=voided)
+    if verdict.get("refused"):
+        raise GraduationTransitionRefusedError(
+            family_root_id, GRADUATION_STATE_WALKFORWARD_SURVIVOR,
+            f"walkforward.sequence_verdict refused: {verdict['reason']}",
+        )
+    if verdict["verdict"] != wf.WF_VERDICT_SURVIVOR:
+        raise GraduationTransitionRefusedError(
+            family_root_id, GRADUATION_STATE_WALKFORWARD_SURVIVOR,
+            f"WF_SURVIVOR_RULE_V1 not satisfied -- conditions: {verdict['conditions']}",
+        )
+
+    fields = {
+        "row_kind": ROW_KIND_STATE_TRANSITION,
+        "family_root_id": family_root_id,
+        "sequence_id": sequence_id,
+        "corpus_id": corpus_id,
+        "from_state": GRADUATION_STATE_EXPLORATORY,
+        "to_state": GRADUATION_STATE_WALKFORWARD_SURVIVOR,
+        "rule_name": verdict["rule_name"],
+        "conditions": verdict["conditions"],
+        "n_sufficient_folds": verdict["n_sufficient_folds"],
+        "n_eligible_folds": verdict["n_eligible_folds"],
+        "evaluated_at": evaluated_at if evaluated_at is not None else _iso_utc_now(),
+    }
+    row = graduation_ledger.append_row(fields)
+    return {"transition": TRANSITION_APPENDED, "state": GRADUATION_STATE_WALKFORWARD_SURVIVOR, "row": row}
+
+
+# === state 3: walkforward_survivor -> sealed_survivor (spec section 8 point 3, TC-2/TC-6) ===========
+
+
+def record_sealed_evaluation(
+    graduation_ledger: GraduationLedger,
+    vault_shard_ledger: "vault.VaultShardLedger",
+    vault_universe_ledger: "vault.VaultUniverseLedger",
+    *,
+    family_root_id: str,
+    dataset_id: str,
+    spec_hash: str,
+    passed: bool,
+    detail: dict | None = None,
+    evaluated_at: str | None = None,
+) -> dict:
+    """Records a single-shot sealed-shard evaluation verdict (module docstring: the verdict itself
+    is caller-supplied; this function's own job is the confirmation + the permanent recording).
+    Confirms, via ``vault.build_vault_state`` (existing, unmodified), that ``dataset_id`` is
+    genuinely ``exposed`` and bound to this EXACT ``family_root_id`` -- refusing
+    (``GraduationTransitionRefusedError``) a claimed evaluation against a shard that was never
+    actually exposed to this family, rather than trusting the caller's say-so.
+
+    Single-shot (TR-12): a SECOND call for the identical ``(family_root_id, dataset_id)`` pair is an
+    idempotent ``replayed`` no-op when it repeats the SAME ``(passed, spec_hash)`` verdict (a benign
+    repeat of an operator act, the ``register_fold_spec`` precedent), but is REFUSED outright when it
+    would record a DIFFERENT verdict -- "sealed exposure is ... never a second draw" (goal.md
+    anti-goal) means even a caller HONESTLY re-evaluating never gets to overwrite or supplement a
+    verdict already on permanent record."""
+    existing_for_shard = [
+        row for row in sealed_evaluations_for_family(graduation_ledger, family_root_id)
+        if row.get("dataset_id") == dataset_id
+    ]
+    if existing_for_shard:
+        prior = existing_for_shard[-1]
+        if prior["passed"] == bool(passed) and prior["spec_hash"] == spec_hash:
+            return {"transition": TRANSITION_REPLAYED, "row": dict(prior)}
+        raise GraduationTransitionRefusedError(
+            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
+            f"a sealed-shard evaluation for dataset_id {dataset_id!r} is ALREADY recorded "
+            f"(passed={prior['passed']!r}, spec_hash={prior['spec_hash']!r}); a second, DIFFERENT "
+            f"evaluation attempt (passed={bool(passed)!r}, spec_hash={spec_hash!r}) is refused "
+            "(spec section 7.4/TR-12): sealed exposure is single-shot, never a second draw",
+        )
+
+    vault_state = vault.build_vault_state(vault_shard_ledger, vault_universe_ledger)
+    shard_entry = next((s for s in vault_state["shards"] if s.get("dataset_id") == dataset_id), None)
+    if (
+        shard_entry is None
+        or shard_entry.get("exposure_state") != vault.STATE_EXPOSED
+        or shard_entry.get("family_root_id") != family_root_id
+    ):
+        raise GraduationTransitionRefusedError(
+            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
+            f"dataset_id {dataset_id!r} is not an EXPOSED vault shard bound to this exact "
+            "family_root_id -- refused (spec section 7.4): a sealed-shard evaluation can only be "
+            "recorded against a shard genuinely exposed to this family",
+        )
+
+    fields = {
+        "row_kind": ROW_KIND_SEALED_EVALUATION,
... [diff_bound] apps/backend/app/research/micro_graduation.py: 271 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_graduation.py b/apps/backend/tests/test_micro_graduation.py
new file mode 100644
index 0000000..e82e849
--- /dev/null
+++ b/apps/backend/tests/test_micro_graduation.py
@@ -0,0 +1,556 @@
+"""``micro_graduation.py`` (Era "The Rapid Microscope" J-07) -- test-first contract: TC-1 through
+TC-9, per ``docs/phases/goal-rapid-microscope-iter-10.md``. Fixture-only throughout (no real
+sealed shard exists this era; J-06 step 4 is human-blocked) -- every scenario builds its OWN
+ledgered evidence directly through the sibling modules' existing public functions
+(``walkforward_ledger.append_fold_result``, ``vault.seal_shard``/``assign_shard``/``expose_shard``,
+``scout_ledger.ScoutLedger.append_row``) and then exercises ``micro_graduation.py``'s own
+evaluation functions against it -- mirroring ``test_walkforward.py``'s own "hand-built,
+ledgered-but-not-re-deriving-the-producer's-own-machinery" style for testing a CONSUMER's logic in
+isolation."""
+
+from __future__ import annotations
+
+import ast
+import re
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.main import app
+from app.research import micro_graduation as g
+from app.research import scout_ledger
+from app.research import vault
+from app.research import walkforward as wf
+from app.research import walkforward_ledger as wl
+from app.research.micro_routes import get_micro_graduation_dir
+from app.research.scout_ledger import ScoutLedger
+from test_copy_discipline import find_violations
+
+# === helpers ==========================================================================================
+
+_ECON_FLOOR = {"floor_bps": 5.0}
+_FIXTURE_VAULT_SECRET = b"a-graduation-fixture-vault-secret"
+
+
+def _append_sufficient_fold(
+    wf_ledger: wl.WalkForwardLedger,
+    *,
+    fold_index: int,
+    sequence_id: str,
+    corpus_id: str,
+    spec_hash: str = "spec-fixture-hash-1",
+    sidedness: str = "long",
+    econ_floor: dict | None = _ECON_FLOOR,
+    evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS,
+    process_label: str = wf.PROCESS_LABEL_RULE,
+    effect: float = 10.0,
+    sign: str = "positive",
+    registered_at: str = "2026-01-01T00:00:00.000000Z",
+) -> dict:
+    """A hand-built, already-SUFFICIENT ``fold_result``-shaped row, appended through the REAL
+    ``walkforward_ledger.append_fold_result`` (so it is genuinely retrievable via
+    ``walkforward.fold_results_for_sequence``, the same door ``micro_graduation.py`` itself reads
+    through) -- the exact field shape ``walkforward.evaluate_mode_b_fold`` produces, without
+    re-deriving ITS OWN exposure-registry/observation-crunching machinery (already covered by
+    ``test_walkforward.py``'s own suite; this file tests graduation's consumption of the result,
+    not walk-forward's own production of it)."""
+    fields = {
+        "sequence_id": sequence_id, "corpus_id": corpus_id, "mode": "B", "rule_id": "fixture-rule",
+        "spec_hash": spec_hash, "fold_index": fold_index, "sidedness": sidedness, "econ_floor": econ_floor,
+        "evidence_class": evidence_class, "process_label": process_label, "registered_at": registered_at,
+        "status": wf.FOLD_STATUS_SUFFICIENT, "n": 40, "n_sessions": 10, "n_symbols": 3,
+        "effect": effect, "sign": sign, "missing": {},
+    }
+    return wl.append_fold_result(wf_ledger, fields)
+
+
+def _three_survivor_folds(wf_ledger: wl.WalkForwardLedger, *, sequence_id: str, corpus_id: str, **overrides) -> None:
+    for i in range(3):  # exactly WF_MIN_SUFFICIENT_FOLDS
+        _append_sufficient_fold(wf_ledger, fold_index=i, sequence_id=sequence_id, corpus_id=corpus_id, **overrides)
+
+
+def _exposed_shard(
+    tmp_path, *, family_root_id: str, dataset_id: str = "dataset-1", symbol: str = "PG",
+    session_date: str = "2026-06-09",
+) -> tuple["vault.VaultShardLedger", "vault.VaultUniverseLedger"]:
+    """seal -> assign -> expose ONE fixture shard to ``family_root_id`` -- the ``test_vault.py``
+    ``_sealed_shard_ledger``/assign/expose sequence, mirrored (no universe registration needed:
+    shard serialization does not depend on it, exactly as ``test_vault.py``'s own helper omits
+    it)."""
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    vault.seal_shard(
+        shard_ledger, dataset_id=dataset_id, universe_id="u1", content_checksum="a" * 64,
+        event_count=12_345, vault_secret=_FIXTURE_VAULT_SECRET,
+    )
+    vault.assign_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, symbol=symbol, session_date=session_date)
+    vault.expose_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id)
+    return shard_ledger, universe_ledger
+
+
+def _scout_row(*, family_root_id: str, family_id: str, candidate_id: str, decision: str) -> dict:
+    return {
+        "family_id": family_id, "family_root_id": family_root_id, "candidate_id": candidate_id,
+        "decision": decision, "reason": None, "notes": "",
+    }
+
+
+# === TC-1: exploratory -> walkforward_survivor =======================================================
+
+
+def test_tc1_all_five_conditions_hold_advances_to_walkforward_survivor(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-1"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
+
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    result = g.evaluate_walkforward_survivor_transition(
+        grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
+    )
+
+    assert result["transition"] == g.TRANSITION_APPENDED
+    assert result["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
+    row = result["row"]
+    assert row["rule_name"] == wf.WF_SURVIVOR_RULE_V1
+    assert all(row["conditions"].values())
+    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
+
+
+# === TC-5: a diagnostic-only twin is refused at the first transition =================================
+
+
+def test_tc5_a_diagnostic_only_twin_is_refused_and_state_stays_exploratory(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("cumulative_delta_divergence", "level_test", "clock_60s")
+    corpus_id = "graduation-fixture-corpus-diagnostic"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    # every fold is historical_exposed_diagnostic -- never eligible, so condition 1 fails.
+    _three_survivor_folds(
+        wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id,
+        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
+    )
+
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    with pytest.raises(g.GraduationTransitionRefusedError) as exc_info:
+        g.evaluate_walkforward_survivor_transition(
+            grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
+        )
+    assert exc_info.value.family_root_id == family_root_id
+    assert exc_info.value.target_state == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
+    # never silently advanced -- and no row was ever appended for the refused attempt.
+    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_EXPLORATORY
+    assert g.state_transitions_for_family(grad_ledger, family_root_id) == []
+
+
+def test_a_below_floor_candidate_with_zero_ledgered_folds_is_also_refused_never_a_fabricated_verdict(tmp_path):
+    """The OTHER refusal path ``sequence_verdict`` itself owns (below ``WF_MIN_SUFFICIENT_FOLDS``,
+    here zero) -- exercised directly so this module's own refusal wiring covers both of
+    ``sequence_verdict``'s ways of saying no, not just the "five conditions evaluated and failed"
+    one TC-5 already covers."""
+    family_root_id = scout_ledger.compute_family_root_id("burst_intensity", "playbook_signal", "trades_20")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    with pytest.raises(g.GraduationTransitionRefusedError, match="sufficient folds"):
+        g.evaluate_walkforward_survivor_transition(
+            grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id="seq-never-evaluated",
+        )
+    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_EXPLORATORY
+
+
+# === TC-7: replay idempotency -- a repeated advancement check never appends a duplicate row ==========
+
+
+def test_tc7_a_second_advancement_check_with_no_new_evidence_is_replayed_not_duplicated(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_60")
+    corpus_id = "graduation-fixture-corpus-replay"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    first = g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
+    assert first["transition"] == g.TRANSITION_APPENDED
+    rows_after_first = len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION))
+
+    second = g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
+    assert second["transition"] == g.TRANSITION_REPLAYED
+    assert second["row"] == first["row"]
+    assert len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION)) == rows_after_first  # unchanged
+
+
+# === TC-2: walkforward_survivor -> sealed_survivor ====================================================
+
+
+def test_tc2_a_passing_sealed_evaluation_advances_to_sealed_survivor(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-sealed-pass"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
+
+    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-pass")
+    eval_result = g.record_sealed_evaluation(
+        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-pass",
+        spec_hash="spec-fixture-hash-1", passed=True,
+    )
+    assert eval_result["transition"] == g.TRANSITION_APPENDED
+    assert eval_result["row"]["passed"] is True
+
+    result = g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-pass")
+    assert result["transition"] == g.TRANSITION_APPENDED
+    assert result["state"] == g.GRADUATION_STATE_SEALED_SURVIVOR
+    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_SEALED_SURVIVOR
+
+
+def test_sealed_evaluation_is_refused_against_a_shard_never_exposed_to_this_family(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("a", "b", "c")
+    other_family_root_id = scout_ledger.compute_family_root_id("x", "y", "z")
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    # the shard is exposed, but to a DIFFERENT family entirely.
+    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=other_family_root_id)
+
+    with pytest.raises(g.GraduationTransitionRefusedError, match="not an EXPOSED vault shard"):
+        g.record_sealed_evaluation(
+            grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+            spec_hash="spec-x", passed=True,
+        )
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+
+def test_a_second_identical_sealed_evaluation_call_is_replayed_a_second_different_one_is_refused(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("microprice_drift", "band_wall_touch", "trades_20")
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id)
+
+    first = g.record_sealed_evaluation(
+        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+        spec_hash="spec-x", passed=True,
+    )
+    assert first["transition"] == g.TRANSITION_APPENDED
+
+    replay = g.record_sealed_evaluation(
+        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+        spec_hash="spec-x", passed=True,
+    )
+    assert replay["transition"] == g.TRANSITION_REPLAYED
+    assert replay["row"] == first["row"]
+    assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # never a duplicate row
+
+    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
+        g.record_sealed_evaluation(
+            grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+            spec_hash="spec-x", passed=False,  # a genuinely DIFFERENT verdict for the same pair
+        )
+    assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # still never a duplicate
+
+
+def test_sealed_survivor_transition_is_refused_before_walkforward_survivor_is_reached(tmp_path):
+    """States are strictly ordered (spec section 8) -- a candidate that never earned
+    ``walkforward_survivor`` cannot skip straight to ``sealed_survivor`` even with a passing sealed
+    evaluation on record."""
+    family_root_id = scout_ledger.compute_family_root_id("spread_change", "band_wall_touch", "trades_20")
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id)
+    g.record_sealed_evaluation(
+        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+        spec_hash="spec-x", passed=True,
+    )
+    with pytest.raises(g.GraduationTransitionRefusedError, match="strictly ordered"):
+        g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1")
+
+
+# === TC-6: a failed-sealed twin's permanent failed verdict is carried into its own bundle =============
+
+
+def test_tc6_a_failed_sealed_evaluation_never_advances_and_is_carried_into_the_bundle(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("response_asymmetry", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-sealed-fail"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
+
+    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-fail")
+    eval_result = g.record_sealed_evaluation(
+        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-fail",
+        spec_hash="spec-fixture-hash-1", passed=False, detail={"reason": "fixture: sealed effect below floor"},
+    )
+    assert eval_result["row"]["passed"] is False
+
+    with pytest.raises(g.GraduationTransitionRefusedError, match="permanent"):
+        g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-fail")
+    # the state never advanced past walkforward_survivor.
+    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
+
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, sequence_id=sequence_id,
+    )
+    assert bundle["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
+    failed_verdicts = [e for e in bundle["sealed_evaluations"] if e["passed"] is False]
+    assert len(failed_verdicts) == 1
+    assert failed_verdicts[0]["dataset_id"] == "dataset-fail"
+    assert bundle["family_multiplicity"]["prior_sealed_verdicts"] == bundle["sealed_evaluations"]
+
+
+# === TC-3/TC-4: sealed_survivor -> referee_handoff_ready, and the bundle's own content ================
+
+
+def test_tc3_and_tc4_the_full_pipeline_produces_a_validating_bundle_and_referee_handoff_ready(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-e2e"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
+
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
+
+    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-e2e")
+    g.record_sealed_evaluation(
+        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e",
+        spec_hash="spec-fixture-hash-1", passed=True,
+    )
+    g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e")
+
+    # every ledgered trial for the family, including a kill -- across two SIBLING family_ids that
+    # share the SAME family_root_id (TC-3: "every ledgered trial ... including kills").
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    scout.append_row(_scout_row(family_root_id=family_root_id, family_id="fam-a", candidate_id="cand-1", decision="survive"))
+    scout.append_row(_scout_row(family_root_id=family_root_id, family_id="fam-b", candidate_id="cand-2", decision="killed_null"))
+    # an unrelated family's trial must NEVER leak into this bundle.
+    scout.append_row(_scout_row(family_root_id="unrelated-root", family_id="fam-c", candidate_id="cand-3", decision="survive"))
+
+    result = g.evaluate_referee_handoff_ready_transition(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, sequence_id=sequence_id,
+    )
+    assert result["transition"] == g.TRANSITION_APPENDED
+    assert result["state"] == g.GRADUATION_STATE_REFEREE_HANDOFF_READY
+    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_REFEREE_HANDOFF_READY
+
+    bundle = result["bundle"]
+    assert g.bundle_validates(bundle)
+    # TC-3: frozen spec hash; family_root_id lineage; every ledgered trial including kills
+    # (union-N); every fold with its evidence_class and process_label; every shard touched; the
+    # proposed confirmation boundary; family/multiplicity metadata.
+    assert bundle["family_root_id"] == family_root_id
+    assert bundle["spec_hash"] == "spec-fixture-hash-1"
+    assert bundle["union_n_variants_tried"] == scout_ledger.distinct_variant_count(
+        [row for row in scout.all_rows() if row["family_root_id"] == family_root_id]
+    )
+    assert bundle["union_n_variants_tried"] == 2  # cand-1 survives, cand-2 is killed -- both counted
+    decisions = {row["candidate_id"]: row["decision"] for row in bundle["scout_trials"]}
+    assert decisions == {"cand-1": "survive", "cand-2": "killed_null"}  # the kill IS present
+    assert all("unrelated" not in row["candidate_id"] for row in bundle["scout_trials"])
+    assert {row["evidence_class"] for row in bundle["fold_results"]} == {wf.EVIDENCE_CLASS_HISTORICAL_OOS}
+    assert {row["process_label"] for row in bundle["fold_results"]} == {wf.PROCESS_LABEL_RULE}
+    assert len(bundle["fold_results"]) == 3
+    assert [s["dataset_id"] for s in bundle["shards_touched"]] == ["dataset-e2e"]
+    assert bundle["proposed_confirmation_boundary"] is not None
+    assert bundle["family_multiplicity"]["sibling_family_ids"] == ["fam-a", "fam-b"]
+
+    # TC-4: the bundle's own copy states, verbatim, that this does not imply current-Referee
+    # registrability of a flow predicate.
+    assert bundle["referee_registration_note"] == g.REFEREE_FUTURE_REVISION_SENTENCE
+    assert "future named revision" in bundle["referee_registration_note"]
+    assert "docs/referee-statistical-spec.md" in bundle["referee_registration_note"]
+
+    # replay: a second call re-derives the SAME live bundle rather than appending a duplicate row.
+    rows_after_first = len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION))
+    replay = g.evaluate_referee_handoff_ready_transition(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, sequence_id=sequence_id,
+    )
+    assert replay["transition"] == g.TRANSITION_REPLAYED
+    assert g.bundle_validates(replay["bundle"])
+    assert len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION)) == rows_after_first
+
+
+def test_referee_handoff_ready_is_refused_before_sealed_survivor_is_reached(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("quote_imbalance", "band_wall_touch", "trades_20")
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    with pytest.raises(g.GraduationTransitionRefusedError, match="strictly ordered"):
+        g.evaluate_referee_handoff_ready_transition(
+            grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+            family_root_id=family_root_id, sequence_id="seq-never-evaluated",
+        )
+
+
+def test_bundle_is_buildable_and_honestly_partial_for_a_family_with_no_evidence_at_all(tmp_path):
+    """The export bundle is never gated to sealed_survivor+ candidates -- buildable for ANY
+    ledgered family_root_id, always carrying its OWN current state (module docstring)."""
+    family_root_id = scout_ledger.compute_family_root_id("never_evaluated", "band_wall_touch", "trades_20")
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
... [diff_bound] apps/backend/tests/test_micro_graduation.py: 162 more diff lines omitted — Read the file for full detail
```
