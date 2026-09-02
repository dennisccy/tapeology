# Iteration diff (bounded)

Files changed: 4. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `docs/goal-archive/goal-2026-09-02.md` (1062 lines not shown)
- `docs/goal.md` (1907 lines not shown)

```diff
diff --git a/docs/goal-archive/goal-2026-09-02.md b/docs/goal-archive/goal-2026-09-02.md
new file mode 100644
index 00000000..9ff4eb01
--- /dev/null
+++ b/docs/goal-archive/goal-2026-09-02.md
@@ -0,0 +1,1456 @@
+# Tapeology — Project Goal (The Hypothesis Foundry — freeze the finite universe, then exhaust it)
+
+> **OPERATIVE GOAL — v2.1, ratified 2026-08-26 after adversarial review + final verification (READY_TO_COMMIT). Predecessor archived at [docs/goal-archive/goal-2026-08-26.md](goal-archive/goal-2026-08-26.md).**
+>
+> This chapter begins after **The Rapid Microscope** is formally closed and integrated into `main`.
+> Its terminal Goal Mode session, ledgers, reports, and research verdicts are immutable foundation.
+> The Rapid Microscope proved that Tapeology can falsify candidates honestly: thirteen exploratory
+> candidates were recorded, none survived, Study 2 was killed, Studies 1 and 3 were left
+> `PARKED_PENDING_OWNER_SPEC`, no candidate earned `historical_oos`, graduation remained empty, and
+> the Validation Vault remained untouched.
+>
+> **Zero survivors is not a defect.** The new problem is upstream: the repository contains more
+> tape-reading ideas than mechanically complete hypotheses. This era builds a finite, deterministic
+> Foundry that distinguishes those two things, freezes every legal candidate before the first new
+> Foundry outcome read, then exhausts that frozen universe through the existing Scout decision rail.
+>
+> **Binding owner policy for this era:** unresolved science is **blocked, not guessed**. The owner is
+> deliberately NOT pre-filling Study 1 / Study 3 case-by-case choices. If the ratified sources plus
+> the general rules in this goal do not uniquely determine a feature meaning, threshold, sequence lag,
+> direction, comparator, or other scientific choice, the Foundry records a typed `BLOCKED_*`
+> disposition and continues. A sparse or even empty first epoch is an acceptable result. This one
+> policy replaces case-by-case owner rulings during the run.
+>
+> **No Goal-Proposer research loop in this era.** The scientific workload is finite and predeclared.
+> All research execution belongs to the fixed human-authored journeys below. The project-specific
+> continuous-improvement proposer must be inactive before final `GOAL_ACHIEVED`; no AUTO journey is
+> allowed to create or schedule scientific work for this chapter.
+
+---
+
+## Vision
+
+Tapeology already owns the measurement rails needed to reject weak microstructure ideas, but candidate
+construction is still bespoke enough to create discretion: an agent can choose a feature, pick a legal
+window, decide how a deferred condition joins an anchor, write a family-specific extractor, inspect a
+result, then rationalize the next variant. **The Hypothesis Foundry removes that loop.** It turns the
+repository's already-ratified microstructure statements into a checked-in declarative source registry,
+compiles every scientifically complete statement into a finite `CandidateSpec` universe without reading
+candidate outcomes, freezes that entire universe behind a Git-visible pre-outcome barrier, and then runs
+a deterministic checkpointed exhaust pass over the already-exposed diagnostic corpus. Every evaluable
+candidate is judged by the existing Scout statistical rail; every unresolved statement is visibly
+blocked; every kill is permanent for the epoch; every correctly signed Scout survivor is labelled only
+as a `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`, never as proof of edge. The era stops before any fresh OOS
+resource or protected evidence is spent.
+
+## Target Users
+
+- **Primary:** the Tapeology owner/operator, who wants to define the methodology once and let Goal Mode
+  perform the implementation, compilation, freezing, and finite diagnostic exhaustion unattended.
+- **Secondary:** a future scientific auditor, who must be able to reconstruct every source statement,
+  compiler decision, blocked reason, variant denominator, freeze hash, outcome-read boundary, Scout
+  decision, and survivor rule without trusting agent prose.
+
+The operator should not be asked routine scientific questions during the run. If the constitution does
+not answer a question mechanically, the correct machine action is a typed block, not an owner prompt.
+
+---
+
+## Success Criteria
+
+The era succeeds when all of the following are true:
+
+1. **The era boundary is explicit and auditable.** Rapid Microscope is archived as the previous goal;
+   its terminal session and research ledgers are unmodified; the Foundry has its own goal/session/branch
+   identity and a dated opening note in the research catalog.
+2. **Continuous improvement is disabled for this finite research era.** The old active
+   `project-extensions/proposer-guidance.md` no longer causes `run-goal.sh` to dispatch a post-achievement
+   proposer. The Foundry finishes through ordinary Goal Mode finalization, not goal self-extension.
+3. **One finite source registry exists.** Every source statement named by this goal is represented
+   exactly once as a canonical source record or explicit alias/exclusion, with source references,
+   supersession provenance, and a deterministic disposition rule.
+4. **Source compilation is outcome-blind at the command layer.** The real manifest generator cannot
+   import, call, open, or query Scout results, forward-return outputs, walk-forward results, graduation,
+   Vault outcomes, Referee results, PnL/champion scans, or protected datasets. Static and dynamic
+   tripwires enforce the boundary.
+5. **The source-authoring leakage surface is disclosed and constrained.** Checked-in source records may
+   be authored by agents that cannot un-know historical repository state, but every enumeration,
+   threshold provenance, direction implication, alias, supersession, and block decision is audited
+   against cited ratified text under the general rules frozen in this goal. No result-dependent
+   rationale is permitted.
+6. **Routine ambiguity is automated; new science is not.** Finite alternatives explicitly preserved by
+   ratified current sources are enumerated. Any alternative requiring a new numeric value, new semantic
+   interpretation, new primitive, fitted boundary, unsupported study statistic, or post-hoc selection is
+   typed `BLOCKED_*` and no candidate is invented to rescue it.
+7. **The real epoch is complete before its first outcome read.** All compiled families, variants,
+   directions, populations, coordinate rules, thresholds, comparators, horizons, Foundry-family
+   denominators, and hashes are generated as one immutable manifest before any Foundry candidate
+   outcome is read.
+8. **The freeze is Git-visible, not merely timestamped.** The real manifest and freeze record exist in a
+   committed ancestor before real evaluation. The freeze record pins all science-affecting source,
+   compiler, extractor/interpreter, Scout-screen, access-control, schema, and configuration hashes.
+9. **After the first Foundry outcome read, science code drift is impossible inside the epoch.** Every
+   resume verifies the freeze hashes. A changed science-affecting file, manifest, source registry,
+   CandidateSpec, compiler, extractor, screen contract, or fingerprint causes a typed integrity halt;
+   Goal Mode may not patch and continue after seeing results.
+10. **Candidate construction is generic.** Multi-coordinate / deferred candidate membership is produced
+    by the Foundry interpreter from `CandidateSpec`, then encoded as a precomputed boolean membership
+    for the existing `scout.screen_candidate` statistical core. The Foundry does not add a second null,
+    p-value, sample floor, direction gate, concentration gate, economic gate, fragility gate, or survivor
+    score.
+11. **Scalar equivalence is mechanically proven.** For every current one-scalar candidate shape the
+    Foundry adapter and the existing direct Scout path produce byte-identical decision/statistical
+    outputs on hermetic fixtures. Any additive Scout API seam required only for descriptive provenance
+    keeps current callers byte-identical and cannot affect verdict ordering.
+12. **Temporal legality is population-symmetric.** An anchor enters a candidate/comparator population
+    only when every conditioning component needed by that CandidateSpec has resolved. Both cells use
+    the same eligible population and the same per-anchor `outcome_start = max(component.available_at)`;
+    unresolved deferred anchors are excluded and counted, never backdated or placed only in the
+    comparator.
+13. **Direction is frozen before evidence.** Every evaluable Foundry candidate is registered in thesis
+    space with a predeclared `long|short` semantic direction. Existing Scout `killed_direction` is the
+    only direction gate. A result can never be flipped to the opposite direction after discovery.
+14. **Multiplicity is visible and conservative at the Foundry-family level.** The complete Foundry
+    family denominator is frozen before evaluation; a family with more than
+    `SCOUT_MAX_VARIANTS_PER_FAMILY` variants is blocked whole rather than truncated or split to evade
+    the cap; every result shows the Foundry denominator and the Scout best-of-N disclosure. No new alpha
+    correction is invented in this era.
+15. **Every ready candidate gets one deterministic diagnostic attempt recorded on one canonical trial rail.**
+    The exhaust runner visits the frozen manifest in canonical order, never ranking by effect, p-value,
+    n, sample density, or apparent promise. Every Foundry trial — scalar or composite — is recorded in
+    the Foundry's own hash-chained append-only trial ledger with the full Scout screen payload and frozen
+    identities. The era invokes `scout.screen_candidate` directly and does not register Foundry trials in
+    the Scout ledger. Exact resume/replay is idempotent at the Foundry layer; conflicting replay is refused.
+16. **All real Foundry evaluations remain `historical_exposed_diagnostic`.** They use only the already-
+    exposed legacy diagnostic corpus through the existing access/evidence controls. No withheld/sealed
+    member is read; no result is relabelled as OOS.
+17. **A Scout survivor becomes only `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`.** The label means the exact
+    pre-outcome CandidateSpec already contains the membership rule, direction, comparator, horizon,
+    economic-floor rule, provenance, deterministic future `rule_id`, and prospective-root status needed
+    for a future OOS campaign. This era does NOT create a corpus-bound Walk Forward Mode B
+    predeclaration, because no new OOS corpus exists.
+18. **Fresh evidence remains unspent.** No corpus-era registration, retention probe, storage
+    provisioning, new recording/fetch, withheld release, Vault assignment/exposure, historical-OOS
+    evaluation, graduation, or Referee run occurs in this era.
+19. **The full scientific state is observable from one canonical backend read model.** `/desk` renders
+    source dispositions, freeze identity, family/variant state, blocked reasons, denominators,
+    unavailable counts, Scout decisions, diagnostic survivors, protected-read counts, and integrity
+    state verbatim. A read-only MCP proxy is optional, not goal-blocking.
+20. **The era can honestly finish with zero compiled candidates, zero survivors, or multiple diagnostic
+    survivors.** Success is defined by precommit integrity and exhaustive execution, never by positive
+    return, profitability, or finding an edge.
+21. **Foundation remains intact.** Existing Rapid Microscope / Referee leakage, evidence-class,
+    no-lookahead, no-execution, opacity, unit, and isolation guards stay green with no weakened tests.
+
+---
+
+## Key Capabilities
+
+1. **Foundry Methodology Spec** — a checked-in `docs/hypothesis-foundry-spec.md` that defines only
+   candidate-construction / freeze / exhaustion semantics; the existing Rapid Validation statistical
+   decision rail remains unchanged.
+2. **Declarative Source Registry** — one finite, auditable translation of the ratified source scope,
+   with formula-scoped supersession, alias, exclusion, and block provenance.
+3. **CandidateSpec Contract** — a canonical machine-readable schema that deterministically defines an
+   evaluable candidate or explains why the source cannot produce one.
+4. **Generic Candidate Interpreter** — supported population filters, side normalization, conjunction,
+   deferred availability composition, complement comparator, and boolean-membership projection into the
+   existing Scout screen. Unsupported ordered/statistical forms block rather than trigger bespoke code.
+5. **Foundry Family Registry** — pre-outcome family identity, full variant denominator, hard cap,
+   immutable order, and no-late-insertion enforcement owned by Foundry rather than misattributed to the
+   Scout ledger.
+6. **Git-visible Freeze Barrier** — deterministic manifest generation, idempotent generation replay,
+   committed freeze identity, outcome-access tripwires, and post-first-read science-hash lock.
+7. **Checkpointed Exhaust Runner** — canonical-order evaluation, crash-safe resume, at-most-once Foundry
+   attempt semantics, typed terminal states, and integrity refusal on drift/conflict.
+8. **Exact Scout Reuse** — `screen_candidate` remains the only statistical discovery judge; descriptive
+   continuous reports cannot alter verdicts.
+9. **Foundry Trial Ledger + Read Model** — one canonical hash-chained append-only trial record for all
+   Foundry scalar/composite evaluations, carrying the complete Scout screen payload plus frozen
+   identities, and one canonical REST/Desk truth; optional read-only MCP mirrors it if scope permits.
+10. **Hermetic Oracle Suite** — synthetic known-null, known-effect, direction, deferred-timing,
+    multiplicity, block, freeze, replay, and leakage fixtures that exercise the same production paths as
+    the real epoch.
+
+---
+
+# Foundry Constitution
+
+Everything in this section is binding methodology. Implementation may factor code differently, but it
+may not change scientific meaning. If the implementation proves that exact Scout statistical reuse is
+impossible without changing a frozen Rapid Validation decision contract, Goal Mode must halt before the
+real epoch freeze and report `METHODOLOGY_REVISION_REQUIRED`; it must not silently amend
+`docs/rapid-validation-spec.md`.
+
+## 1. Source scope — finite and ratified
+
+The first real Foundry epoch may consider **only** source statements already ratified in the repository
+before this goal opens.
+
+### 1.1 Required source objects
+
+The declarative registry MUST account for all of the following:
+
+**Rapid Microscope parked mechanisms**
+
+- Study 1 — `range_wall_failed_aggression`
+- Study 3 — `capitulation_exhaustion`
+
+**Era 9 Wave-1 concepts explicitly brought forward by the Rapid-Microscope opening note**
+
+- Card 9.3 — top-of-book imbalance
+- Card 9.4 — burst / climax detection
+- Card 9.5 — spread-dynamics regime
+- Card 9.6 — same-side flow-runs persistence
+- Card 9.7 — event-time feature windows
+
+**Frozen Rapid-Microscope pilot proxy declarations**
+
+- the existing Study 1 proxy candidate request
+- the existing Study 3 proxy candidate request
+
+These proxies are source objects for provenance, **not permission to launder a partial proxy as the
+full mechanism**. Unless the current ratified mechanism explicitly says otherwise, their disposition is
+`ALIASED_PROXY_ONLY` under the corresponding parked study and their existing `do_not` restriction is
+preserved.
+
+### 1.2 Explicit source exclusions
+
+- Card 9.1 / Study 2 → `EXCLUDED_PREVIOUSLY_KILLED`. It may not be recompiled, reversed, rethresholded,
+  or rerun in this epoch.
+- Card 9.2 → `EXCLUDED_PREREQUISITE_UNMET` while its required delta-by-price binning prerequisite is
+  absent.
+- Cards 9.8–9.11 → `EXCLUDED_GATE_CLOSED` while their catalog gate lacks the required prior OOS-class
+  evidence.
+- Era 10+ cards, web-sourced ideas, free-form feature combinations, LLM-generated strategies,
+  unratified new theory, and any mechanism outside this registry.
+
+### 1.3 Formula-scoped supersession law
+
+Supersession is **formula/meaning scoped, not card-number scoped**.
+
+When the Rapid Microscope opening note or a named Rapid Validation revision carried a concept forward
+while replacing an operational formula/window/threshold, the newer frozen rule wins for that specific
+field and the older value becomes provenance only. A source-record auditor must not copy an older card
+constant merely because the card itself was brought forward.
+
+Examples the registry must handle explicitly rather than by enthusiasm:
+
+- Card 9.7 is not itself a directional Scout hypothesis. Its event-time-window content may be
+  `ALIASED_VARIANT_VOCABULARY` where current frozen feature windows already embody it.
+- Card 9.6 may contain more than one study statement: a shuffled-side persistence statistic and a
+  run-length-at-touch conditional. They receive separate dispositions if their statistical forms differ.
+- Study 3 and Card 9.4 are adjacent exhaustion lineages; the registry must record whether each statement
+  is distinct, aliased, or blocked rather than letting two names silently duplicate one mechanism.
+
+### 1.4 Source-record decision audit
+
+Each checked-in source record must include:
+
+- canonical `source_id`
+- exact source path + stable section/card/study reference
+- exact quoted source span(s) + precise location for every load-bearing compile/audit decision
+- source hash
+- mechanism statement
+- current operative formula/feature references
+- superseded fields and their superseding refs
+- every finite alternative the compiler is allowed to enumerate
+- threshold provenance for every threshold-like boundary
+- direction derivation rule or `BLOCKED_DIRECTION`
+- comparator derivation or `BLOCKED_UNSUPPORTED_STUDY_FORM`
+- final source disposition
+- aliases/lineage ids
+- an audit note explaining why each compiler decision follows from the source rules **without citing any
+  candidate outcome, p-value, effect, observation count, Scout verdict, or PnL result**
+
+Mechanical registry lint verifies that every quoted span is an exact substring of the cited ratified
+source at the recorded location. It deliberately does **not** use keyword matching as a proxy for
+scientific meaning.
+
+A **fresh-context independent source-registry audit** must verify **decisions**, not just citations:
+enumeration vs block, threshold provenance, direction implication, formula supersession, proxy aliasing,
+and lineage dedup. The auditor receives the ratified source documents, the Foundry constitution/spec,
+and the proposed registry, but not session outcome/history artifacts. It must state whether the quoted
+text actually supports each decision under the general compile rules. The audit may not justify a
+choice by saying it is more likely to survive or has more observations.
+
+## 2. Owner meta-policy — block unresolved science
+
+This section is the owner ruling that replaces case-by-case interaction.
+
+### 2.1 Enumerate only genuinely frozen alternatives
+
+If the current ratified source/spec/code explicitly leaves a finite set of legal alternatives, enumerate
+all of them **within the same Foundry family** before any outcome read, subject to the family cap.
+
+Examples of eligible finite enumeration include only alternatives whose scientific meanings are already
+present and fixed, such as two already-defined feature windows or two already-supported legal outcome
+horizons.
+
+Do **not** treat the mere existence of two features in code as permission to enumerate them. Feature
+choice is only mechanical when the source statement or current frozen vocabulary identifies them as
+alternative representations of the same mechanism.
+
+### 2.2 New science blocks
+
+The source/variant is blocked if compilation would require any of the following:
+
+- a new numeric threshold or percentile
+- choosing between scientifically different features without a ratified equivalence/alternative rule
+- defining what words such as `high`, `extreme`, `collapse`, `strong`, `fast`, or `near` mean numerically
+- inventing an ordered-sequence lag/window
+- inventing a new null/statistical question
+- inventing a new population restriction or wall-quality filter
+- inventing a direction not mechanically implied by the ratified statement
+- inventing a fitted score, feature weight, z-score mixture, or learned transform
+- choosing the variant with more observations, better effect, lower p-value, or better apparent economics
+
+Typed states include at least:
+
+- `BLOCKED_SPEC_GAP`
+- `BLOCKED_MISSING_PRIMITIVE`
+- `BLOCKED_UNSUPPORTED_STUDY_FORM`
+- `BLOCKED_UNSUPPORTED_RELATION`
+- `BLOCKED_DIRECTION`
+- `BLOCKED_VARIANT_EXPLOSION`
+- `BLOCKED_UNIT_CONTRACT`
+
+A block is a legitimate scientific output, not an implementation failure.
+
+### 2.3 Natural-boundary law
+
+A threshold may compile only when its provenance is one of:
+
+1. a literal current ratified threshold tied to the operative formula;
+2. a threshold already frozen in the current Rapid Validation / feature contract and explicitly
+   applicable to this mechanism; or
+3. a genuine semantic boundary intrinsic to the variable's definition, such as boolean `true` or a
+   signed variable's zero boundary when the source itself says positive-vs-negative / bid-heavy-vs-
+   ask-heavy.
+
+A zero boundary may **not** be used to reinterpret `high`, `extreme`, `climax`, or equivalent magnitude
+language. That is a block.
+
+## 3. CandidateSpec — the frozen scientific object
+
+Every compiled variant is represented by a canonical `CandidateSpec`. Serialization order never changes
+its hash; every science-affecting field does.
+
+Required fields:
+
+- `foundry_spec_version`
+- `epoch_id`
+- `source_ids[]`
+- `lineage_id`
+- `foundry_family_id`
+- `variant_id`
+- `variant_ordinal`
+- `population`
+  - `structure_context_kind`
+  - any source-legal side filter (`support|resistance|...`)
+  - any source-legal setup id / context id
+- `coordinates[]`, each carrying:
+  - frozen feature/construct identifier
+  - semantic role
+  - transform/orientation
+  - threshold/corner predicate where applicable
+  - threshold provenance
+  - aggressor-derived flag
+  - unit/basis requirements
+  - `anchor_at` / `available_at` semantics
+  - `resolution_join_rule` for deferred constructs, bound to the observer's own provenance identity;
+    if a deferred completion cannot be uniquely joined back to this source anchor without inventing a
+    new key/order choice, compilation blocks
+- `relation`
+  - supported relation kind (initially conjunction / direct scalar membership; ordered forms may block)
+  - relation parameters only when source-frozen
+- `availability_rule = max_conditioning_available_at`
+- `unresolved_component_policy = exclude_and_count`
+- `membership_corner`
+- `comparator = complement_within_same_eligible_population`
+- `outcome`
+  - canonical `return_bps`
+  - `horizon_key`
+  - predeclared `sidedness: long|short`
+- `economic_floor_rule`
+  - existing Scout quoted-spread rule and multiple
+  - **formula frozen here; numeric floor value materializes later before outcome read**
+- `foundry_family_variant_count`
+- `manifest_hash`
+- `source_registry_hash`
+- `compiler_hash`
+- `candidate_spec_hash`
+
+### 3.1 Legal outcome horizons
+
+For the current Scout screen, Foundry candidates may use only horizon keys actually accepted by the
+existing block-length rail. The expected legal set is `trades_20|trades_100`; implementation must verify
+this from current code rather than infer it. A source that requires a clock/share horizon not supported
+by the Scout screen is blocked, not approximated.
+
+### 3.2 Direction is mandatory
+
+A Foundry candidate without a mechanically predeclared `long|short` direction is not evaluable and is
+`BLOCKED_DIRECTION`.
... [diff_bound] docs/goal-archive/goal-2026-09-02.md: 1062 more diff lines omitted — Read the file for full detail
diff --git a/docs/goal.md b/docs/goal.md
index 9ff4eb01..2e681d2a 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1,58 +1,59 @@
-# Tapeology — Project Goal (The Hypothesis Foundry — freeze the finite universe, then exhaust it)
+# Tapeology — Project Goal (Observation Contract v1 — one time-safe, provenance-complete tape observation, exposed)
 
-> **OPERATIVE GOAL — v2.1, ratified 2026-08-26 after adversarial review + final verification (READY_TO_COMMIT). Predecessor archived at [docs/goal-archive/goal-2026-08-26.md](goal-archive/goal-2026-08-26.md).**
+> **OPERATIVE GOAL — v1, ratified 2026-09-02 after three adversarial revision rounds (READY TO COMMIT ERA-OPEN DOCS). Predecessor archived at [docs/goal-archive/goal-2026-09-02.md](goal-archive/goal-2026-09-02.md).**
 >
-> This chapter begins after **The Rapid Microscope** is formally closed and integrated into `main`.
-> Its terminal Goal Mode session, ledgers, reports, and research verdicts are immutable foundation.
-> The Rapid Microscope proved that Tapeology can falsify candidates honestly: thirteen exploratory
-> candidates were recorded, none survived, Study 2 was killed, Studies 1 and 3 were left
-> `PARKED_PENDING_OWNER_SPEC`, no candidate earned `historical_oos`, graduation remained empty, and
-> the Validation Vault remained untouched.
+> This chapter begins after **The Hypothesis Foundry** is formally closed (`GOAL_ACHIEVED` 2026-08-27,
+> session `hypothesis-foundry`, `epoch:afd19e9c11a6534f`) and its closure artifacts plus the §0.8
+> source-authoring laws are on `main`. Its epoch manifest, freeze set, trial ledger, reports and standing
+> dispositions are immutable foundation. No research question is opened or reopened here.
 >
-> **Zero survivors is not a defect.** The new problem is upstream: the repository contains more
-> tape-reading ideas than mechanically complete hypotheses. This era builds a finite, deterministic
-> Foundry that distinguishes those two things, freezes every legal candidate before the first new
-> Foundry outcome read, then exhausts that frozen universe through the existing Scout decision rail.
+> **Thesis.** Tapeology says *"this is what the tape observed."* It never says *"therefore trade."* This era
+> exposes the EXISTING deterministic tape observation — the immutable `EngineSnapshot` the engine already
+> builds once per tick — as one versioned, machine-readable artifact, **`TapeObservation`**, that an external
+> composite-policy consumer can use without reconstructing, recomputing or guessing any Tapeology semantics.
+> It is not a new tape engine, not a trading-signal goal, and not the consumer's implementation.
 >
-> **Binding owner policy for this era:** unresolved science is **blocked, not guessed**. The owner is
-> deliberately NOT pre-filling Study 1 / Study 3 case-by-case choices. If the ratified sources plus
-> the general rules in this goal do not uniquely determine a feature meaning, threshold, sequence lag,
-> direction, comparator, or other scientific choice, the Foundry records a typed `BLOCKED_*`
-> disposition and continues. A sparse or even empty first epoch is an acceptable result. This one
-> policy replaces case-by-case owner rulings during the run.
+> **Core principle.** Tapeology distinguishes **market-event time**, **actual system availability time when
+> measured**, and **artifact-generation time**, and never manufactures historical information availability
+> that was not recorded. *Retrospective evidence establishes compatibility, not prospective proof.*
 >
-> **No Goal-Proposer research loop in this era.** The scientific workload is finite and predeclared.
-> All research execution belongs to the fixed human-authored journeys below. The project-specific
-> continuous-improvement proposer must be inactive before final `GOAL_ACHIEVED`; no AUTO journey is
-> allowed to create or schedule scientific work for this chapter.
+> **Deterministic-evidence rule.** No mandatory journey or test depends on Alpaca, the network, credentials
+> or market hours. The binding contract is proven with Sim mode, committed fixtures and the deterministic
+> provider harnesses; a real-provider smoke test is optional, environment-gated, and can never block
+> `GOAL_ACHIEVED`.
+>
+> **No Goal-Proposer.** The framework goal-proposer was retired upstream (`3d0d07c2`); `docs/goal.md` is
+> human-owned and never auto-extended. The journey set J-01…J-06 is finite and fixed.
 
 ---
 
 ## Vision
 
-Tapeology already owns the measurement rails needed to reject weak microstructure ideas, but candidate
-construction is still bespoke enough to create discretion: an agent can choose a feature, pick a legal
-window, decide how a deferred condition joins an anchor, write a family-specific extractor, inspect a
-result, then rationalize the next variant. **The Hypothesis Foundry removes that loop.** It turns the
-repository's already-ratified microstructure statements into a checked-in declarative source registry,
-compiles every scientifically complete statement into a finite `CandidateSpec` universe without reading
-candidate outcomes, freezes that entire universe behind a Git-visible pre-outcome barrier, and then runs
-a deterministic checkpointed exhaust pass over the already-exposed diagnostic corpus. Every evaluable
-candidate is judged by the existing Scout statistical rail; every unresolved statement is visibly
-blocked; every kill is permanent for the epoch; every correctly signed Scout survivor is labelled only
-as a `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`, never as proof of edge. The era stops before any fresh OOS
-resource or protected evidence is spent.
+Tapeology already has a single-source-of-truth architecture: exactly one `EngineSnapshot` per tick owns
+the ticker, scenario, logical timestamp, stream status, bid/ask/spread/last, per-window features, primary
+window, tape state, confidence, observations, epoch anchor and delivery lag, and REST, WebSocket, the UI and
+the read-only MCP surface all project from that one object. What is missing is an **external contract**:
+today a consumer must combine the logical timestamp with an epoch anchor served on a different endpoint,
+infer the feed basis from a scenario prefix, guess whether a snapshot is warm or stale, and has no
+engine/config identity or integrity hash on any tape surface at all.
+
+**Observation Contract v1** adds the smallest stable artifact that answers, for one symbol, from one
+engine: *what was observed, at what market time, when (if ever) it was actually available, from which
+feed and watch session, under which engine semantics and configuration, in which lifecycle state, and
+which exact evidence object this is.* Every value is a verbatim projection of something the engine, the
+watch manager or the configuration already owns. Nothing is recomputed, nothing is decided. The same
+engine remains the single semantic producer for simulation, historical replay and live ingestion, and the
+era proves that invariant under an identical valid event stream.
 
 ## Target Users
 
-- **Primary:** the Tapeology owner/operator, who wants to define the methodology once and let Goal Mode
-  perform the implementation, compilation, freezing, and finite diagnostic exhaustion unattended.
-- **Secondary:** a future scientific auditor, who must be able to reconstruct every source statement,
-  compiler decision, blocked reason, variant denominator, freeze hash, outcome-read boundary, Scout
-  decision, and survivor rule without trusting agent prose.
-
-The operator should not be asked routine scientific questions during the run. If the constitution does
-not answer a question mechanically, the correct machine action is a typed block, not an owner prompt.
+- **Primary:** the Tapeology owner/operator, who wants one canonical, versioned observation artifact whose
+  time and provenance semantics are honest enough to be composed with other evidence later.
+- **Secondary:** a future **external composite-policy consumer** (generic; it lives in its own repository;
+  the dependency direction is consumer → Tapeology contract, never the reverse), which must obtain one
+  observation through one read-only machine path and never reconstruct Tapeology semantics.
+- **Tertiary:** a future scientific auditor who must be able to say which exact Tapeology evidence object a
+  later evaluation consumed, and under which engine semantics, configuration and implementation source.
 
 ---
 
@@ -60,897 +61,433 @@ not answer a question mechanically, the correct machine action is a typed block,
 
 The era succeeds when all of the following are true:
 
-1. **The era boundary is explicit and auditable.** Rapid Microscope is archived as the previous goal;
-   its terminal session and research ledgers are unmodified; the Foundry has its own goal/session/branch
-   identity and a dated opening note in the research catalog.
-2. **Continuous improvement is disabled for this finite research era.** The old active
-   `project-extensions/proposer-guidance.md` no longer causes `run-goal.sh` to dispatch a post-achievement
-   proposer. The Foundry finishes through ordinary Goal Mode finalization, not goal self-extension.
-3. **One finite source registry exists.** Every source statement named by this goal is represented
-   exactly once as a canonical source record or explicit alias/exclusion, with source references,
-   supersession provenance, and a deterministic disposition rule.
-4. **Source compilation is outcome-blind at the command layer.** The real manifest generator cannot
-   import, call, open, or query Scout results, forward-return outputs, walk-forward results, graduation,
-   Vault outcomes, Referee results, PnL/champion scans, or protected datasets. Static and dynamic
-   tripwires enforce the boundary.
-5. **The source-authoring leakage surface is disclosed and constrained.** Checked-in source records may
-   be authored by agents that cannot un-know historical repository state, but every enumeration,
-   threshold provenance, direction implication, alias, supersession, and block decision is audited
-   against cited ratified text under the general rules frozen in this goal. No result-dependent
-   rationale is permitted.
-6. **Routine ambiguity is automated; new science is not.** Finite alternatives explicitly preserved by
-   ratified current sources are enumerated. Any alternative requiring a new numeric value, new semantic
-   interpretation, new primitive, fitted boundary, unsupported study statistic, or post-hoc selection is
-   typed `BLOCKED_*` and no candidate is invented to rescue it.
-7. **The real epoch is complete before its first outcome read.** All compiled families, variants,
-   directions, populations, coordinate rules, thresholds, comparators, horizons, Foundry-family
-   denominators, and hashes are generated as one immutable manifest before any Foundry candidate
-   outcome is read.
-8. **The freeze is Git-visible, not merely timestamped.** The real manifest and freeze record exist in a
-   committed ancestor before real evaluation. The freeze record pins all science-affecting source,
-   compiler, extractor/interpreter, Scout-screen, access-control, schema, and configuration hashes.
-9. **After the first Foundry outcome read, science code drift is impossible inside the epoch.** Every
-   resume verifies the freeze hashes. A changed science-affecting file, manifest, source registry,
-   CandidateSpec, compiler, extractor, screen contract, or fingerprint causes a typed integrity halt;
-   Goal Mode may not patch and continue after seeing results.
-10. **Candidate construction is generic.** Multi-coordinate / deferred candidate membership is produced
-    by the Foundry interpreter from `CandidateSpec`, then encoded as a precomputed boolean membership
-    for the existing `scout.screen_candidate` statistical core. The Foundry does not add a second null,
-    p-value, sample floor, direction gate, concentration gate, economic gate, fragility gate, or survivor
-    score.
-11. **Scalar equivalence is mechanically proven.** For every current one-scalar candidate shape the
-    Foundry adapter and the existing direct Scout path produce byte-identical decision/statistical
-    outputs on hermetic fixtures. Any additive Scout API seam required only for descriptive provenance
-    keeps current callers byte-identical and cannot affect verdict ordering.
-12. **Temporal legality is population-symmetric.** An anchor enters a candidate/comparator population
-    only when every conditioning component needed by that CandidateSpec has resolved. Both cells use
-    the same eligible population and the same per-anchor `outcome_start = max(component.available_at)`;
-    unresolved deferred anchors are excluded and counted, never backdated or placed only in the
-    comparator.
-13. **Direction is frozen before evidence.** Every evaluable Foundry candidate is registered in thesis
-    space with a predeclared `long|short` semantic direction. Existing Scout `killed_direction` is the
-    only direction gate. A result can never be flipped to the opposite direction after discovery.
-14. **Multiplicity is visible and conservative at the Foundry-family level.** The complete Foundry
-    family denominator is frozen before evaluation; a family with more than
-    `SCOUT_MAX_VARIANTS_PER_FAMILY` variants is blocked whole rather than truncated or split to evade
-    the cap; every result shows the Foundry denominator and the Scout best-of-N disclosure. No new alpha
-    correction is invented in this era.
-15. **Every ready candidate gets one deterministic diagnostic attempt recorded on one canonical trial rail.**
-    The exhaust runner visits the frozen manifest in canonical order, never ranking by effect, p-value,
-    n, sample density, or apparent promise. Every Foundry trial — scalar or composite — is recorded in
-    the Foundry's own hash-chained append-only trial ledger with the full Scout screen payload and frozen
-    identities. The era invokes `scout.screen_candidate` directly and does not register Foundry trials in
-    the Scout ledger. Exact resume/replay is idempotent at the Foundry layer; conflicting replay is refused.
-16. **All real Foundry evaluations remain `historical_exposed_diagnostic`.** They use only the already-
-    exposed legacy diagnostic corpus through the existing access/evidence controls. No withheld/sealed
-    member is read; no result is relabelled as OOS.
-17. **A Scout survivor becomes only `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`.** The label means the exact
-    pre-outcome CandidateSpec already contains the membership rule, direction, comparator, horizon,
-    economic-floor rule, provenance, deterministic future `rule_id`, and prospective-root status needed
-    for a future OOS campaign. This era does NOT create a corpus-bound Walk Forward Mode B
-    predeclaration, because no new OOS corpus exists.
-18. **Fresh evidence remains unspent.** No corpus-era registration, retention probe, storage
-    provisioning, new recording/fetch, withheld release, Vault assignment/exposure, historical-OOS
-    evaluation, graduation, or Referee run occurs in this era.
-19. **The full scientific state is observable from one canonical backend read model.** `/desk` renders
-    source dispositions, freeze identity, family/variant state, blocked reasons, denominators,
-    unavailable counts, Scout decisions, diagnostic survivors, protected-read counts, and integrity
-    state verbatim. A read-only MCP proxy is optional, not goal-blocking.
-20. **The era can honestly finish with zero compiled candidates, zero survivors, or multiple diagnostic
-    survivors.** Success is defined by precommit integrity and exhaustive execution, never by positive
-    return, profitability, or finding an edge.
-21. **Foundation remains intact.** Existing Rapid Microscope / Referee leakage, evidence-class,
-    no-lookahead, no-execution, opacity, unit, and isolation guards stay green with no weakened tests.
+1. **The era boundary is explicit and auditable.** The Hypothesis Foundry goal is archived byte-identically
+   at `docs/goal-archive/goal-2026-09-02.md`; its session, epoch artifacts, ledgers and reports are
+   unmodified; this era has its own goal, session id (`observation-contract`) and a dated opening note in
+   `docs/research-directions.md`.
+2. **One artifact, one producer.** `TapeObservation` (`schema_version = tape-observation-v1`,
+   `provider = tapeology`) is a pure projection of `EngineSnapshot` plus manager-owned provenance. No tape
+   feature, state, confidence, freshness or feed basis is recomputed outside the engine and the one existing
+   feed-basis function; there is no second classifier, no second state engine.
+3. **Three time concepts are distinct and tested.** `observed_at_utc` (market/event time of the latest
+   processed quote or trade), `available_at_utc` (actual system availability when measured, else null) and
+   `generated_at_utc` (artifact projection time) are three separate fields with pinned definitions.
+4. **Historical availability is honestly unknown.** For historical and dataset replay `available_at_utc`
+   is null and `availability_basis` is `historical_arrival_unknown`; event time is never copied into
+   availability and the replay wall clock is never presented as historical availability.
+5. **Live availability is measured, never derived.** On the live basis `available_at_utc` equals the
+   manager-recorded settled wall-clock instant of the exact snapshot serialized; it is never
+   `observed_at_utc + delivery_lag_seconds`.
+6. **The observation read is atomic.** Snapshot, source/session descriptor and settled time come from one
+   manager-controlled read that belongs to the same settled observation; the route never snapshots an
+   engine.
+7. **Feed basis is explicit and never pooled.** `source.data_feed ∈ {sim, iex, sip}` and
+   `source.source_mode ∈ {sim, live, historical, dataset_replay}` are served verbatim from their single
+   owners; no two bases are ever treated as equal.
+8. **Session identity is present.** Every managed watch (sim, live, historical) carries a stable
+   `source.session_id` and `source.session_started_at_utc`; dataset replay is identified by
+   `dataset_id + dataset_checksum`. Session identity is provenance only and never enters engine computation.
+9. **Lifecycle is honest.** `connecting`, `waiting`, `live`, `stale`, `paused`, `closed`, `failed` remain
+   distinct; `tape_state` and `confidence` are never rewritten, suppressed or nulled because of lifecycle;
+   Tapeology never returns READY, NO_TRADE, NO_VERDICT, `trade_allowed` or any equivalent.
+10. **Semantic identity is separate from implementation provenance.** `engine_identity`
+    (`engine_semantics_version`, `config_fingerprint`, `profile_id`, closed vocabularies) is the semantic
+    identity; `implementation_provenance` (`engine_source_hash`, `source_revision`, `worktree_dirty`) is
+    fail-closed provenance, disclosed honestly including dirty worktree state, and never claims a semantic
+    change by itself.
+11. **Prose is outside identity.** `observations[]` is explanatory metadata; a wording change never changes
+    machine observation identity.
+12. **Two hashes with normative roles.** `observation_hash` is the machine-observation equivalence
+    identity; `artifact_hash` identifies the exact evidence artifact instance and is the reference a
+    downstream consumer must record.
+13. **Ingestion-path equivalence is proven under the narrow claim.** The same valid ordered event stream fed
+    through the replay feeder and through the live feeder into the same frozen engine/configuration yields
+    an identical machine-observation semantic set; the claim explicitly excludes equality between
+    independently sourced IEX and SIP data.
+14. **One read-only machine path.** `GET /tape/{ticker}/observation` (transport only) serves the artifact;
+    its parsed JSON equals the builder's output field-for-field and value-for-value; the existing MCP
+    `get_endpoint` proxies it byte-identically; a consumer needs nothing else.
+15. **English canonical core.** Every new identifier, schema name, enum value, field name, test and
+    persisted value is English-only ASCII.
+16. **Deterministic evidence only.** No mandatory journey or test requires Alpaca, the network, credentials
+    or market hours; an optional real-provider smoke test is environment-gated and non-blocking.
+17. **Guards are real.** Every guard added by this era is structural, proven non-vacuous, and ships a seeded
+    counter-test proving it can fail.
+18. **Foundation remains intact.** `config_fingerprint` stays `08e471b10130e1e2`; the `default` engine, the
+    five tape states and thresholds, archived-era surfaces, the MCP contract (v8, 28 tools) and every
+    existing determinism / observer / epoch-anchor / lifecycle / feed-basis / profile suite stay green and
+    unweakened.
 
 ---
 
 ## Key Capabilities
 
-1. **Foundry Methodology Spec** — a checked-in `docs/hypothesis-foundry-spec.md` that defines only
-   candidate-construction / freeze / exhaustion semantics; the existing Rapid Validation statistical
-   decision rail remains unchanged.
-2. **Declarative Source Registry** — one finite, auditable translation of the ratified source scope,
-   with formula-scoped supersession, alias, exclusion, and block provenance.
-3. **CandidateSpec Contract** — a canonical machine-readable schema that deterministically defines an
-   evaluable candidate or explains why the source cannot produce one.
-4. **Generic Candidate Interpreter** — supported population filters, side normalization, conjunction,
-   deferred availability composition, complement comparator, and boolean-membership projection into the
-   existing Scout screen. Unsupported ordered/statistical forms block rather than trigger bespoke code.
-5. **Foundry Family Registry** — pre-outcome family identity, full variant denominator, hard cap,
-   immutable order, and no-late-insertion enforcement owned by Foundry rather than misattributed to the
-   Scout ledger.
-6. **Git-visible Freeze Barrier** — deterministic manifest generation, idempotent generation replay,
-   committed freeze identity, outcome-access tripwires, and post-first-read science-hash lock.
-7. **Checkpointed Exhaust Runner** — canonical-order evaluation, crash-safe resume, at-most-once Foundry
-   attempt semantics, typed terminal states, and integrity refusal on drift/conflict.
-8. **Exact Scout Reuse** — `screen_candidate` remains the only statistical discovery judge; descriptive
-   continuous reports cannot alter verdicts.
-9. **Foundry Trial Ledger + Read Model** — one canonical hash-chained append-only trial record for all
-   Foundry scalar/composite evaluations, carrying the complete Scout screen payload plus frozen
-   identities, and one canonical REST/Desk truth; optional read-only MCP mirrors it if scope permits.
-10. **Hermetic Oracle Suite** — synthetic known-null, known-effect, direction, deferred-timing,
-    multiplicity, block, freeze, replay, and leakage fixtures that exercise the same production paths as
-    the real epoch.
+1. **Observation contract spec** — the checked-in, consumer-facing `docs/observation-contract-spec.md`
+   (field/owner table, time law, lifecycle table, partition, hash laws, canonical encoding, consumer path).
+   Its normative content is this constitution; the run may add implementation notes, never change field
+   semantics.
+2. **`build_tape_observation`** — one public pure builder in `apps/backend/app/observation_contract.py`
+   (reads no clock, no git, no engine internals) plus the frozen schema constants and both hash laws.
+3. **Atomic managed observation read** — `WatchManager.get_observation_source(ticker)` returning the
+   settled `EngineSnapshot`, its source/session descriptor, its settled wall-clock time and the engine's
+   `end_reason` from one manager-held settled pair.
+4. **Source/session descriptor** — manager-owned provenance recorded at watch creation (mode, scenario,
+   window, session id, session start, profile id), with `data_feed` from the one existing feed-basis
+   function.
+5. **Implementation provenance resolver** — `engine_source_hash` over the fixed engine-module tuple plus
+   process-level `source_revision` / `worktree_dirty`, resolved once per process.
+6. **`GET /tape/{ticker}/observation`** — the transport-only route beside its `/tape/*` siblings, 404 on an
+   unwatched ticker, proxied by the existing MCP `get_endpoint`.
+7. **Deterministic proof suite** — projection, time-law, lifecycle/feed, ingestion-path equivalence and
+   route tests on Sim mode, committed fixtures and the `HistoricalProvider` / `LiveProvider` harnesses with
+   a controlled clock.
+8. **Guard suite** — recompute guard, mutator-call-site guard, copy-discipline and compound-identifier ban,
+   external-system reference guard, English-only guard, real-provider isolation guard, each with a seeded
+   counter-test.
 
 ---
 
-# Foundry Constitution
-
-Everything in this section is binding methodology. Implementation may factor code differently, but it
-may not change scientific meaning. If the implementation proves that exact Scout statistical reuse is
-impossible without changing a frozen Rapid Validation decision contract, Goal Mode must halt before the
-real epoch freeze and report `METHODOLOGY_REVISION_REQUIRED`; it must not silently amend
-`docs/rapid-validation-spec.md`.
-
-## 1. Source scope — finite and ratified
-
-The first real Foundry epoch may consider **only** source statements already ratified in the repository
-before this goal opens.
-
-### 1.1 Required source objects
-
-The declarative registry MUST account for all of the following:
-
-**Rapid Microscope parked mechanisms**
-
-- Study 1 — `range_wall_failed_aggression`
-- Study 3 — `capitulation_exhaustion`
-
-**Era 9 Wave-1 concepts explicitly brought forward by the Rapid-Microscope opening note**
-
-- Card 9.3 — top-of-book imbalance
-- Card 9.4 — burst / climax detection
-- Card 9.5 — spread-dynamics regime
-- Card 9.6 — same-side flow-runs persistence
-- Card 9.7 — event-time feature windows
-
-**Frozen Rapid-Microscope pilot proxy declarations**
-
-- the existing Study 1 proxy candidate request
-- the existing Study 3 proxy candidate request
-
-These proxies are source objects for provenance, **not permission to launder a partial proxy as the
-full mechanism**. Unless the current ratified mechanism explicitly says otherwise, their disposition is
-`ALIASED_PROXY_ONLY` under the corresponding parked study and their existing `do_not` restriction is
-preserved.
-
-### 1.2 Explicit source exclusions
-
-- Card 9.1 / Study 2 → `EXCLUDED_PREVIOUSLY_KILLED`. It may not be recompiled, reversed, rethresholded,
-  or rerun in this epoch.
-- Card 9.2 → `EXCLUDED_PREREQUISITE_UNMET` while its required delta-by-price binning prerequisite is
-  absent.
-- Cards 9.8–9.11 → `EXCLUDED_GATE_CLOSED` while their catalog gate lacks the required prior OOS-class
-  evidence.
-- Era 10+ cards, web-sourced ideas, free-form feature combinations, LLM-generated strategies,
-  unratified new theory, and any mechanism outside this registry.
-
-### 1.3 Formula-scoped supersession law
-
-Supersession is **formula/meaning scoped, not card-number scoped**.
-
-When the Rapid Microscope opening note or a named Rapid Validation revision carried a concept forward
-while replacing an operational formula/window/threshold, the newer frozen rule wins for that specific
-field and the older value becomes provenance only. A source-record auditor must not copy an older card
-constant merely because the card itself was brought forward.
-
-Examples the registry must handle explicitly rather than by enthusiasm:
-
-- Card 9.7 is not itself a directional Scout hypothesis. Its event-time-window content may be
-  `ALIASED_VARIANT_VOCABULARY` where current frozen feature windows already embody it.
-- Card 9.6 may contain more than one study statement: a shuffled-side persistence statistic and a
-  run-length-at-touch conditional. They receive separate dispositions if their statistical forms differ.
-- Study 3 and Card 9.4 are adjacent exhaustion lineages; the registry must record whether each statement
-  is distinct, aliased, or blocked rather than letting two names silently duplicate one mechanism.
-
-### 1.4 Source-record decision audit
-
-Each checked-in source record must include:
-
-- canonical `source_id`
-- exact source path + stable section/card/study reference
-- exact quoted source span(s) + precise location for every load-bearing compile/audit decision
-- source hash
-- mechanism statement
-- current operative formula/feature references
-- superseded fields and their superseding refs
-- every finite alternative the compiler is allowed to enumerate
-- threshold provenance for every threshold-like boundary
-- direction derivation rule or `BLOCKED_DIRECTION`
-- comparator derivation or `BLOCKED_UNSUPPORTED_STUDY_FORM`
-- final source disposition
-- aliases/lineage ids
-- an audit note explaining why each compiler decision follows from the source rules **without citing any
-  candidate outcome, p-value, effect, observation count, Scout verdict, or PnL result**
-
-Mechanical registry lint verifies that every quoted span is an exact substring of the cited ratified
-source at the recorded location. It deliberately does **not** use keyword matching as a proxy for
-scientific meaning.
-
-A **fresh-context independent source-registry audit** must verify **decisions**, not just citations:
-enumeration vs block, threshold provenance, direction implication, formula supersession, proxy aliasing,
-and lineage dedup. The auditor receives the ratified source documents, the Foundry constitution/spec,
-and the proposed registry, but not session outcome/history artifacts. It must state whether the quoted
-text actually supports each decision under the general compile rules. The audit may not justify a
... [diff_bound] docs/goal.md: 1907 more diff lines omitted — Read the file for full detail
diff --git a/docs/observation-contract-spec.md b/docs/observation-contract-spec.md
new file mode 100644
index 00000000..cf14acc5
--- /dev/null
+++ b/docs/observation-contract-spec.md
@@ -0,0 +1,361 @@
+# Tapeology Observation Contract — `TapeObservation` v1
+
+**Status:** frozen at era open (2026-09-02). Normative content lives in the Contract Constitution of
+`docs/goal.md` (Observation Contract v1); this document is the consumer-facing copy. The implementing run
+may add implementation notes below the line marked *Implementation notes*; it may not change any field
+semantics, enum value, null rule, partition or hash law without a new schema version.
+
+`schema_version = "tape-observation-v1"` · `provider = "tapeology"`
+
+## 1. Purpose
+
+`TapeObservation` is a versioned, machine-readable envelope around Tapeology's existing deterministic tape
+observation — the immutable `EngineSnapshot` that the tape engine builds once per processed event. It lets
+an external consumer answer, for one symbol from one engine:
+
+- What did Tapeology observe? (`tape_state`, `confidence`, `warm`, `features`, `market`)
+- For which symbol? (`ticker`)
+- At what market time? (`observed_at_utc`)
+- When was that observation actually available, if that was measured? (`available_at_utc`,
+  `availability_basis`)
+- From which feed, watch session or dataset? (`source`)
+- Under which engine semantics, configuration and implementation? (`engine_identity`,
+  `implementation_provenance`)
+- In which lifecycle state? (`lifecycle`)
+- Which exact evidence object is this? (`artifact_hash`), and which observation is it equivalent to?
+  (`observation_hash`)
+
+It carries observation, timing, provenance, lifecycle and integrity facts only. It never carries a
+trading conclusion, a readiness verdict, a freshness judgment or any actionability.
+
+## 2. The generic path
+
+```
+market/provider event
+  → TapeEngine.process_event            (clock-free; the one semantic producer)
+  → WatchManager stamps status/lag and records settled_at for THAT snapshot
+  → atomic ManagedObservationRead {EngineSnapshot, SourceDescriptor, settled_at, end_reason}
+  → pure build_tape_observation(...)     (no clock, no git, no engine access)
+  → TapeObservation
+  → GET /tape/{ticker}/observation       (transport only; nothing recomputed)
+```
+
+No field is recomputed by the route. The route owns transport only.
+
+## 3. Shape (illustrative values)
+
+```json
+{
+  "schema_version": "tape-observation-v1",
+  "provider": "tapeology",
+  "ticker": "SIM-BIDABS",
+  "observed_at_utc": "2024-01-02T14:31:07.250000Z",
+  "available_at_utc": null,
+  "availability_basis": "simulated_not_applicable",
+  "generated_at_utc": "2026-09-02T13:05:41.118204Z",
+  "tape_state": "bid_absorption",
+  "confidence": 0.71,
+  "warm": true,
+  "primary_window": "30s",
+  "features": {"10s": {"...": 0.0}, "30s": {"...": 0.0}},
+  "trade_event_count": 123,
+  "market": {"bid": 149.01, "ask": 149.03, "spread": 0.02, "last": 149.02},
+  "observations": ["human-readable explanatory text"],
+  "lifecycle": {"stream_status": "live", "paused": false, "end_reason": null},
+  "timing": {
+    "logical_timestamp": 67.25,
+    "epoch_anchor": 1704205800.0,
+    "settled_at_utc": "2026-09-02T13:05:41.104913Z",
+    "delivery_lag_seconds": 0.0
+  },
+  "source": {
+    "source_mode": "sim",
+    "data_feed": "sim",
+    "scenario": "bid_absorption",
+    "window_start_utc": null,
+    "window_end_utc": null,
+    "dataset_id": null,
+    "dataset_checksum": null,
+    "session_id": "6f1c…",
+    "session_started_at_utc": "2026-09-02T13:04:59.000000Z"
+  },
+  "engine_identity": {
+    "engine_semantics_version": "tape-engine-v1",
+    "config_fingerprint": "08e471b10130e1e2",
+    "profile_id": "default",
+    "tape_state_vocabulary": ["buyer_control", "seller_control", "bid_absorption", "ask_absorption", "unclear"],
+    "windows": ["10s", "30s", "60s", "180s", "300s"],
+    "warmup_min_events": 40
+  },
+  "implementation_provenance": {
+    "engine_source_hash": "…64 hex…",
+    "source_revision": "…40 hex or null…",
+    "worktree_dirty": false
+  },
+  "observation_hash": "…64 hex…",
+  "artifact_hash": "…64 hex…"
+}
+```
+
+## 4. Fields and owners
+
+Every field has exactly one owner and belongs to exactly one partition (§8). Nothing is recomputed.
+
+| Field | Owner | Partition |
+|---|---|---|
+| `schema_version` | constant `tape-observation-v1` | semantic |
+| `provider` | constant `tapeology` | semantic |
+| `ticker` | `EngineSnapshot.ticker` | semantic |
+| `observed_at_utc` | `EngineSnapshot.epoch_anchor + EngineSnapshot.timestamp` (§5) | semantic |
+| `available_at_utc` | manager-recorded settled time per `availability_basis` (§5) | metadata |
+| `availability_basis` | fixed by `source.source_mode` (§5) | metadata |
+| `generated_at_utc` | route-supplied projection time (§5) | metadata |
+| `tape_state` | `EngineSnapshot.tape_state` | semantic |
+| `confidence` | `EngineSnapshot.confidence` | semantic |
+| `warm` | `EngineSnapshot.warm` | semantic |
+| `primary_window` | `EngineSnapshot.primary_window` | semantic |
+| `features` | `EngineSnapshot.features` (window → feature name → value) | semantic |
+| `trade_event_count` | `EngineSnapshot.event_count` — the existing trade-only counter, verbatim | semantic |
+| `market.bid`, `market.ask`, `market.spread`, `market.last` | `EngineSnapshot.bid/ask/spread/last` | semantic |
+| `observations[]` | `EngineSnapshot.observations` | explanatory |
+| `lifecycle.stream_status` | `EngineSnapshot.stream_status` | metadata |
+| `lifecycle.paused` | `EngineSnapshot.paused` | metadata |
+| `lifecycle.end_reason` | `TapeEngine.end_reason` (via the atomic read) | metadata |
+| `timing.logical_timestamp` | `EngineSnapshot.timestamp` | semantic |
+| `timing.epoch_anchor` | `EngineSnapshot.epoch_anchor` | semantic |
+| `timing.settled_at_utc` | `WatchManager` settled pair (§5) | metadata |
+| `timing.delivery_lag_seconds` | `EngineSnapshot.delivery_lag_seconds` (telemetry) | metadata |
+| `source.source_mode` | manager descriptor (validated watch mode; `sim` registry path; `dataset_replay` in-process) | metadata |
+| `source.data_feed` | `data_feed_for_scenario` for watches; the immutable dataset manifest for `dataset_replay` | metadata |
+| `source.scenario` | `EngineSnapshot.scenario` | metadata |
+| `source.window_start_utc`, `source.window_end_utc` | manager descriptor: parsed UTC request window (historical), else null | metadata |
+| `source.dataset_id`, `source.dataset_checksum` | dataset manifest (`dataset_replay`), else null | metadata |
+| `source.session_id` | manager descriptor: stable id of the watch instance; null for `dataset_replay` | metadata |
+| `source.session_started_at_utc` | manager descriptor: wall clock at watch creation; null for `dataset_replay` | metadata |
+| `engine_identity.engine_semantics_version` | constant `tape-engine-v1` in `app/engine/tape_engine.py` | semantic |
+| `engine_identity.config_fingerprint` | `Config.config_fingerprint()` | semantic |
+| `engine_identity.profile_id` | manager descriptor (`default`) | semantic |
+| `engine_identity.tape_state_vocabulary[]` | the classifier's closed state list | semantic |
+| `engine_identity.windows[]` | `Config.windows` labels | semantic |
+| `engine_identity.warmup_min_events` | `Config.warmup_min_events` | semantic |
+| `implementation_provenance.engine_source_hash` | process-level resolver over the fixed `app/engine/*.py` tuple (§7) | metadata |
+| `implementation_provenance.source_revision` | process-level git resolver (§7) | metadata |
+| `implementation_provenance.worktree_dirty` | process-level git resolver (§7) | metadata |
+| `observation_hash` | §8 | integrity |
+| `artifact_hash` | §8 | integrity |
+
+Deliberately excluded: `recent_trades`, `event_log` (served by `/tape/{ticker}/events`), and any verdict,
+decision, readiness, freshness-acceptability or actionability field.
+
+## 5. Time semantics — three distinct concepts
+
+Tapeology distinguishes **market-event time**, **actual system availability time when measured**, and
+**artifact-generation time**. It never manufactures historical information availability that was not
+recorded.
+
+### `observed_at_utc` — market-event time
+
+The UTC market/event timestamp of the latest processed event (quote or trade) represented by this
+`EngineSnapshot`: `iso(epoch_anchor + timing.logical_timestamp)`. It is not "last trade time" and not the
+time the tape state last changed. It is **null** if and only if `timing.epoch_anchor` is null or the
+engine has processed no event (`market.bid`, `market.ask` and `market.last` all null). `connecting` and
+`waiting` imply null; `stale`, `closed` and `failed` with zero events are null; `paused` after events keeps
+the last observation.
+
+### `timing.settled_at_utc` — measured processing-settled time
+
+The wall-clock instant, recorded by the watch manager, at which THIS snapshot became settled and externally
+readable (after the event was processed and the status and delivery-lag fields were stamped). Recorded in
+every managed mode (sim, live, historical); null for in-process dataset replay. A lifecycle-only change
+(stale flip, pause, resume, close, fail) carries the previous settled time forward. The engine never reads
+it.
+
+### `available_at_utc` — actual availability when measured, else null
+
+Never derived from event time and never `observed_at_utc + delivery_lag_seconds`.
+
+| `source.source_mode` | `availability_basis` | `available_at_utc` |
+|---|---|---|
+| `live` | `live_settled_wall_clock` | `= timing.settled_at_utc` (null until the first settled event) |
+| `historical`, `dataset_replay` | `historical_arrival_unknown` | null — original vendor-arrival, receive, processing and external-availability times were never recorded |
+| `sim` | `simulated_not_applicable` | null — the synthetic clock (`epoch_anchor = 2024-01-02T14:30:00Z`) carries no market information |
+
+The live value is a measurement; under vendor clock skew it may precede `observed_at_utc`, and the
+contract does not clamp. No ordering between `available_at_utc` and `generated_at_utc` is asserted.
+
+### `generated_at_utc` — artifact-generation time
+
+The wall clock at which this artifact projection was generated. It is distinct from both of the above and
+is excluded from `observation_hash` (§8).
+
+### `timing.delivery_lag_seconds` — telemetry only
+
+The feeder's existing measurement (live: wall clock minus `epoch_anchor + logical_timestamp`, clamped at
+zero; paced replay: backlog against the pacing schedule). It is provenance, never a source of truth for
+availability.
+
+### Atomic-read invariant
+
+`timing.settled_at_utc` belongs to the exact `EngineSnapshot` serialized in the same artifact. The watch
+manager holds one immutable settled pair per ticker and serves snapshot, source descriptor and settled time
+from that pair in one read; the route never snapshots the engine.
+
+### Instant format
+
+Every instant is ISO-8601 UTC with microseconds and a `Z` suffix, produced by
+`datetime.fromtimestamp(x, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")`.
+
+### Composed-validation note (binding disclosure)
+
+Historical `TapeObservation` artifacts can support deterministic composed replay using `observed_at_utc`,
+the declared event ordering and the frozen engine semantics/configuration. That establishes retrospective
+event-time compatibility under the declared replay assumptions. **It does not prove that an equivalent
+observation would have been externally available at exactly the historical market-event timestamp in a
+prospective live system.** The limitation is machine-visible (`availability_basis =
+historical_arrival_unknown`, `available_at_utc = null`) and is never patched with an assumed latency.
+Retrospective evidence establishes compatibility, not prospective proof. A future dataset with actual
+recorded receive timestamps may support a stronger availability basis in a later schema version.
+
+## 6. Source, feed and session provenance
+
+- `source.source_mode ∈ {sim, live, historical, dataset_replay}` — recorded from the validated watch
+  request (or set by the sim registry path); `dataset_replay` exists for in-process callers and is not
+  served by REST in v1.
+- `source.data_feed ∈ {sim, iex, sip}` — from the one existing feed-basis function for watches
+  (`live ` → `iex`, `historical ` → `sip`, else `sim`) and from the immutable dataset manifest for
+  `dataset_replay`. Bases are never pooled, equated or converted.
+- `source.window_start_utc` / `source.window_end_utc` — the parsed UTC request window of a historical
+  watch (request identity, distinct from the observed extent); null otherwise.
+- `source.dataset_id` / `source.dataset_checksum` — dataset identity for `dataset_replay`; null otherwise.
+- `source.session_id` / `source.session_started_at_utc` — the watch instance that produced the
+  observation and when it started. A Tapeology snapshot is path-dependent (it reflects every event
+  consumed since the watch began), so two observations for the same symbol at the same market time from
+  different sessions are different evidence. Null for `dataset_replay`, whose path is fully identified by
+  `dataset_id + dataset_checksum`. Session identity is provenance only and never enters engine
+  computation.
+
+## 7. Engine identity vs implementation provenance
+
+**`engine_identity`** is the semantic identity of the producer:
+
+- `engine_semantics_version` — `tape-engine-v1`. It changes only by an explicit owner act when classifier,
+  feature, aggressor or warm-up semantics change.
+- `config_fingerprint` — the configuration identity (`08e471b10130e1e2` at era open).
+- `profile_id` — `default` (the frozen legacy profile that every watch runs).
+- `tape_state_vocabulary`, `windows`, `warmup_min_events` — readable closed vocabularies derived from the
+  same configuration.
+
+**`implementation_provenance`** is exact implementation provenance, resolved once per process:
+
+- `engine_source_hash` — sha256 over the source bytes of a fixed tuple of engine modules. **It identifies
+  exact implementation source and is fail-closed provenance. A changed source hash does not by itself claim
+  that the tape semantics changed** (a comment-only edit changes it).
+- `source_revision` — the git commit hash the process started from, or null when unavailable.
+- `worktree_dirty` — `true`, `false` or `null` under the declared dirty-state check (tracked files under
+  `apps/backend/app`): `(abc123, false)` means the process started from commit `abc123` with the checked
+  source clean; `(abc123, true)` means HEAD was `abc123` but the running implementation includes
+  uncommitted changes — `engine_source_hash` is then the exact engine-source provenance; `(null, null)`
+  means git/source identity was unavailable. Nothing is invented.
+
+## 8. Partition, canonical encoding and the two hashes
+
+**Partition** (leaf paths):
+
+- **Machine observation semantics** → `observation_hash`: `schema_version`, `provider`, `ticker`,
+  `tape_state`, `confidence`, `warm`, `primary_window`, `features`, `trade_event_count`, `market.bid`,
+  `market.ask`, `market.spread`, `market.last`, `observed_at_utc`, `timing.logical_timestamp`,
+  `timing.epoch_anchor`, `engine_identity.*`.
+- **Provenance / source / lifecycle metadata**: `available_at_utc`, `availability_basis`,
+  `generated_at_utc`, `timing.settled_at_utc`, `timing.delivery_lag_seconds`, `lifecycle.*`, `source.*`,
+  `implementation_provenance.*`.
+- **Explanatory metadata**: `observations[]` — human-readable prose for understanding, audit and
+  debugging. A wording change never changes machine identity. Policies must not depend on it.
+- **Integrity**: `observation_hash`, `artifact_hash`.
+
+**Canonical encoding**: `json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")`, then
+sha256 hex. Serialization order never changes either hash.
+
+**`observation_hash`** = sha256(canonical encoding of the machine-observation semantic set). It is a
+**machine-observation equivalence identity**. Two artifacts may share an `observation_hash` even if they
+came from different watch sessions, different generation times, different source metadata or different
+implementation source hashes, provided their declared semantic set is identical. It is not the unique
+identifier of the exact evidence object another system consumed.
+
+**`artifact_hash`** = sha256(canonical encoding of the whole artifact with `artifact_hash` removed). It
+**identifies the exact `TapeObservation` evidence artifact instance**, including its provenance,
+source/session/lifecycle metadata, explanatory text, implementation provenance and generation time under
+the declared canonical encoding. It is intentionally different on every projection.
+
+**Evidence-identity rule.** An external consumer that needs to record *which exact Tapeology evidence
+object an evaluation used* references `artifact_hash`, not only `observation_hash`.
+
+Recomputation recipe: parse the served JSON; drop `artifact_hash`; canonical-encode and hash → must equal
+the served `artifact_hash`. Then select the semantic leaf paths listed above; canonical-encode and hash →
+must equal the served `observation_hash`.
+
+## 9. Lifecycle honesty
+
+| `lifecycle.stream_status` | Meaning | Times | A consumer may conclude |
+|---|---|---|---|
+| `connecting` | engine constructed, stream not yet open | null | not yet observing |
+| `waiting` | stream open, no event yet | null | healthy but waiting |
+| `live` | at least one event processed, no gap flagged | per basis | healthy current observation |
+| `stale` | live watchdog saw no event for the configured gap (live basis only; possible with zero events) | unchanged (or null with zero events) | stale observation |
+| `paused` | operator pause | unchanged | paused |
+| `closed` | natural end (`end_reason = stream_closed`) or cancel/switch (`end_reason` null) | unchanged | closed stream |
+| `failed` | feeder exception (`end_reason` null in v1) | unchanged (or null with zero events) | failed feed |
+| watch stopped | the watch was removed | REST answers 404 | not watched |
+
+`stale` never occurs on the historical, dataset-replay or sim bases. The artifact never rewrites,
+suppresses or nulls `tape_state` or `confidence` because of lifecycle status. The consumer receives both
+`tape_state` and `lifecycle` and decides usability under its own policy.
+
+## 10. Ingestion-path equivalence under an identical valid event stream
+
+When the exact same valid ordered event stream is fed through different ingestion mechanisms (the replay
+feeder and the live feeder) into the same frozen engine semantics and configuration/profile, the resulting
+machine-observation semantic set — and therefore `observation_hash` — is identical. Only provenance, source
+and lifecycle metadata may differ.
+
+A valid ordered event stream has non-decreasing epochs; at equal epoch every quote precedes every trade;
+relative order within a kind is preserved.
+
+**This does not assert semantic equality between independently sourced IEX and SIP market data**, which
+may contain different events. Feed bases are never pooled.
+
+## 11. The consumer path
+
+- `GET /tape/{ticker}/observation` — 200 with the artifact for a watched ticker; 404 for an unwatched
+  ticker (like every other `/tape/*` route).
+- The route's parsed JSON is field-for-field and value-for-value equal to the builder's output for the
+  same atomic read and projection time. HTTP key order is not part of the contract; both hashes are
+  recomputable from the served JSON with the recipe in §8.
+- The read-only MCP `get_endpoint` tool proxies the route byte-identically.
+- A GET never starts a watch, a computation, a git call or a recording.
+- A consumer never scrapes UI text, combines endpoints, derives timestamps, recalculates freshness,
+  recomputes confidence or tape state, or infers feed basis.
+
+## 12. Provider ownership
+
+Tapeology owns: tape state, confidence, features, the timing facts it can honestly know, feed/source/session
+provenance, lifecycle, observation identity and artifact identity.
+
+The external consumer owns: whether an observation satisfies its composite policy, whether the
+observation's freshness is acceptable for that policy, whether its policy remains pending, and whether its
+complete system returns READY, NO_TRADE or NO_VERDICT. Tapeology does not know those concepts and never
+returns them or any equivalent.
+
+## 13. Canonical core language
+
+All identifiers, schema names, enum values, field names and persisted values in this contract are
+English-only ASCII.
+
+## 14. Versioning
+
+`tape-observation-v1` is frozen. Any change to a field's meaning, an enum value, a null rule, the
+partition or a hash law is a new `schema_version`, never a silent change. A later version may add a
+stronger availability basis when actual receive timestamps are recorded.
+
+---
+
+*Implementation notes* (the implementing run may append below this line; nothing above changes).
diff --git a/docs/research-directions.md b/docs/research-directions.md
index 7931db86..7e3a015b 100644
--- a/docs/research-directions.md
+++ b/docs/research-directions.md
@@ -1248,6 +1248,41 @@ a documented basis decision.
 >   Part 5.3's amendments remain historical record.
 >
 > This note is the dated record required by §5.6.
+>
+> **OBSERVATION-CONTRACT OPENING NOTE (2026-09-02, operator pivot, under §5.6 "goal.md wins").**
+> The Hypothesis Foundry is CLOSED — GOAL_ACHIEVED 2026-08-27 (session `hypothesis-foundry`,
+> `epoch:afd19e9c11a6534f`; an honest empty epoch; its sealed artifacts, trial ledger and the §0.8
+> standing dispositions are immutable). The operator opened **"Observation Contract v1"**
+> (constitution `docs/goal.md`; consumer-facing spec `docs/observation-contract-spec.md`; predecessor
+> archived at `docs/goal-archive/goal-2026-09-02.md`) — a contract-hardening era that exposes the
+> EXISTING immutable `EngineSnapshot` as one versioned external artifact, `TapeObservation`
+> (`GET /tape/{ticker}/observation`, schema `tape-observation-v1`), for a future composite-policy
+> consumer that lives in its own repository. Binding rules, from `docs/goal.md`:
+>
+> - No new tape engine, classifier, threshold, feature, strategy condition or research primitive
+>   (§0.8 law 5 is not applicable: an operator pivot outside the catalog that builds no research
+>   engineering). No trading or actionability semantics of any kind — Tapeology says what the tape
+>   observed, never "therefore trade".
+> - Three time concepts stay distinct and honest: `observed_at_utc` (market/event time of the latest
+>   processed quote or trade), `available_at_utc` (only a manager-measured settled wall-clock instant on
+>   the live basis; NULL with `availability_basis = historical_arrival_unknown` for historical and
+>   dataset replay, NULL with `simulated_not_applicable` for simulation), and `generated_at_utc`
+>   (artifact projection time). No historical arrival latency is modelled or guessed; retrospective
+>   evidence establishes compatibility, not prospective proof.
+> - Every artifact carries feed basis (`sim|iex|sip`, never pooled), watch `session_id`, semantic
+>   identity (`engine_semantics_version`, `config_fingerprint`, `profile_id`) and implementation
+>   provenance (`engine_source_hash`, `source_revision`, `worktree_dirty`); `observation_hash` is the
+>   machine-observation equivalence identity and `artifact_hash` the exact evidence-instance identity
+>   that downstream references must use.
+> - Ingestion-path equivalence is claimed only under an identical valid ordered event stream — never as
+>   equality between independently sourced IEX and SIP data.
+> - Mandatory evidence is deterministic and local (Sim mode, committed fixtures, provider harnesses); no
+>   journey depends on Alpaca, the network, credentials or market hours.
+> - `config_fingerprint` stays `08e471b10130e1e2` (zero Config fields); no UI change; no named MCP tool
+>   (the existing `get_endpoint` proxy suffices); the goal-proposer is retired at framework level
+>   (`3d0d07c2`) and the journey set is finite (J-01…J-06).
+>
+> This note is the dated record required by §5.6.
 
 ---
 
```
