# The Rapid-Validation Spec — microstructure candidates, chronological validation, and the vault

> **This file is the single source of the Rapid Microscope era's methodology: every constant,
> contract, fold rule, sealing rule, ledger schema, graduation gate, and trap test is fixed here
> BEFORE the code that uses it.** Developers implement from this spec verbatim; a developer who
> finds a rule ambiguous or unimplementable DROPS the procedure from the iteration and surfaces it
> for an owner ruling — never improvises. A change to anything here is a **named revision** that
> re-keys future results beside old ones (new spec ids / parameter hashes), never an edit of
> recorded meaning. Nothing here is ever tuned from outcomes. The Referee's own spec
> (`docs/referee-statistical-spec.md`) is untouched and outranks this file wherever both speak
> about confirmatory claims.
>
> **Revision r2 (2026-08-16, pre-implementation).** A narrow named revision applied BEFORE any
> artifact was recorded under r1 — so nothing re-keys; r1 never produced a record. r2 adds: the
> availability law (`anchor_at` / `observed_through` / `available_at`, §0/§2.2); the dataset
> schema-basis + quote-size-unit contract (§2.6, superseding Card 5.1's universal "round lots"
> pin — Alpaca CTA/UTP displayed quote sizes are SHARES from 2025-11-03); the Card-5.1
> data-preservation prerequisite on the recorder (§7.1); every remaining Wave-1 degree of
> freedom frozen as a §1 constant (refill M, response K, burst baseline, depletion window,
> impact-flatness formula, divergence trailing window + δ); mid-only primary outcomes with a
> separate last-trade sensitivity basis (§4); `family_root_id` lineage for single-shot sealed
> evidence (§5.1/§7.4); opaque pre-exposure vault metadata (§7.5); the deterministic exposure
> registry + human/agent rules for `historical_oos` (§6.7); `rule_process` vs
> `operator_process` sequence labels (§6.8); frozen clustering semantics and the explicit
> `WF_SURVIVOR_RULE_V1` (§6.2/§6.6); and traps TR-17–TR-22 (§9).
>
> **Revision r3 (2026-08-18, owner ruling — sealed-shard join resistance).** A narrow named
> revision applied while ZERO shards are sealed, so nothing re-keys and no recorded verdict
> moves. The iteration-9 audit proved r2's §7.5 opacity is defeated in one hop: the served
> `shard_id` was the `DatasetStore` dataset id, so `GET /research/datasets/{id}` (and the
> `datasets` MCP tool, `get_endpoint`, and `micro_readiness`'s per-shard rows) returned the
> sealed shard's symbol, window and event counts. r2 already REQUIRED an "opaque `shard_id`",
> so that part was a compliance gap, not a spec gap — but r2 also MANDATED serving the
> `checksum commitment`, which is itself an equally good join key against the public dataset
> record. Resolving that tension is a genuine methodological change, hence this revision.
> r3 replaces §7.5's identity rules (surrogate ids, salted pre-exposure commitment, explicit
> refusal on the pre-existing dataset surfaces) and widens TR-2 from a field-whitelist sweep to
> a join-resistance sweep. Owner ruling recorded 2026-08-18; the alternatives considered and
> rejected were a separate sealed store path (strongest, largest build) and accepting the leak
> with a documented caveat (cheapest, materially weaker vault).
>
> **Revision r4 (2026-08-18, owner ruling — corpus enumerators honour the seal).** Applied while
> ZERO shards are sealed, so no recorded report or ledger row changes. The iteration-9 re-audit
> proved r3's refusals are route-scoped and therefore bypassable: `edge_report._all_datasets`
> and `pnl_scan._split_datasets` each enumerate the WHOLE store through their own
> `DatasetStore.list()` and drive `BacktestJobManager` directly, so a corpus-wide report would
> read a sealed shard's events and republish its id, raw checksum and outcome aggregates through
> `GET /research/backtests` and the append-only PnL ledger. r4 adds §7.5 point 6: enumerators
> EXCLUDE withheld shards and DISCLOSE the exclusion. This is a derivation, not a free choice —
> goal.md's critical rail already says event data and outcome aggregates of a sealed shard are
> "refused everywhere… fail-closed", and both call sites already carry the honesty convention
> that "a partial report is a misleading report", which forbids the silent variant. Rejected:
> aborting a whole sweep whenever any sealed shard exists (renders the edge report unusable the
> moment the vault holds anything) and accepting the bypass (re-opens exactly what r3 closed).
>
> **Revision r5 (2026-08-18, owner ruling — the opaque research pool).** The FINAL
> pre-implementation clarification of the vault surface: applied while ZERO shards are sealed and
> ZERO tranches recorded, so it **re-keys nothing** — no spec id, parameter hash, ledger row, or
> recorded verdict moves, and it changes no statistical rule, constant, grid, fold geometry, or
> gate. It is recorded as a named revision only because this file's own rule makes ANY change to
> it a named revision, never because recorded meaning changed. The iteration-9 audit proved that
> r3+r4 still leave the partition reconstructible by SUBTRACTION: §7.2 requires the symbol rule
> and date rule to be registered before any fetch, so the operator already knows the universe;
> serving a complete identity-labelled list of the exploratory (non-sealed) side then reveals the
> withheld set as its complement. Hiding the axes from readiness does not erase that prior
> knowledge, so the r5 closure is structural rather than cosmetic: **a newly recorded tranche is
> ONE OPAQUE RESEARCH POOL until individual shards are actually exposed or assigned** (§7.5
> points 4, 7, 8; §7.1 recorder progress). The HMAC is reframed accordingly — an internal
> deterministic, auditable assignment mechanism, NOT a public global partition whose complement
> can be reconstructed. TR-2 is widened from join resistance to a deterministic inference trap.
> Explicitly rejected by the owner: accepting the residual with a disclosed caveat, and breaking
> the cartesian shape with recording-cost decoys. Where the shipped architecture requires every
> non-sealed shard to become individually visible at record time, the ARCHITECTURE changes. The
> one-way exposure history and the single-shot `family_root_id` rules are preserved unchanged.
>
> **Revision r6 (2026-08-18, owner rulings — the sealed verdict has an owner).** Four rulings from
> the iteration-10 escalation, applied while ZERO shards are sealed and ZERO sealed evaluations
> exist, so nothing re-keys and no recorded verdict moves. (1) **§8.1 `SEALED_PASS_RULE_V1`** — the
> single-shot sealed verdict gets ONE scientific owner (`micro_sealed_evaluation.py`), which
> recomputes outcomes from canonical machinery and derives the verdict from already-frozen
> quantities; `record_sealed_evaluation` may no longer accept a caller-asserted `passed: bool`. This
> revision exists because the owner's ruling explicitly forbade implementing the evaluator against
> an undefined pass rule ("stop at the methodology boundary and add the smallest pre-implementation
> named clarification defining it… do not let the developer choose thresholds"). **It introduces NO
> new numeric constant** — every floor it applies is one §1 already pins or the family already
> pre-registered. (2) **§8.2 the confirmation-boundary derivation** — lineage-wide, not
> survivor-row-wide, with the Referee registration boundary kept as an independent no-backdating
> floor. (3) **§7.8 vault-ledger corruption** — fail closed on any `verify_chain()` failure, with
> recovery only through evidence-backed reconstruction; operator attestation is audit metadata,
> never proof of missing history; unknown exposure history may NEVER be read as "never exposed".
> (4) **§2.2/§3 `quote_depletion` availability** — the "one quote early" stamp on price-change-
> terminated runs is corrected to the REVEALING quote. Ruling 4 is recorded here as a note only: it
> is an implementation bug against r2's existing availability law, not a methodology change, and the
> owner directed that no revision be created solely for it.
>
> **Revision r7 (2026-08-19, owner rulings — nonced commitment + coarse pre-release volumes).** Two
> rulings from the iteration-11 audit, applied while ZERO shards are sealed and ZERO tranches
> recorded, so nothing re-keys. Both TIGHTEN r5 after the audit reproduced the subtraction attack
> through a second door. (1) **§7.2/§7.5 nonced rule commitment** — the owner REJECTED serving a bare
> deterministic `sha256` of the rule, because `symbol_rule`/`date_rule` are low-entropy and
> dictionary-enumerable, so a plain hash is not a hiding commitment: pre-release the vault serves
> ONLY `rule_commitment = sha256(nonce ‖ canonical_rule)` with a high-entropy nonce held privately,
> and the rule contents + nonce are revealed only on **whole-ORIGINAL-pool release** — never on
> "all ledger-tracked shards exposed". (2) **§7.1/§7.5 coarse pre-release volumes** — the owner
> resolved the §7.1-vs-§7.5 contradiction the audit found (a one-symbol-day run made
> `trades_total`/`quotes_total` a withheld shard's EXACT counts) in favour of §7.5's stronger
> confidentiality contract: **§7.1 no longer mandates exact totals**; event and byte volumes are
> predeclared coarse BUCKETS pre-release and exact only after whole-pool release, and the bucket
> scheme must be differencing-resistant. Rejected in both cases: accepting the residual leak.
> A third audit finding (B3, the missing `verify_chain()` call) needed no ruling — r6 §7.8 already
> settled it; the iteration-11 phase spec's claim that it is "an open owner question" is STALE.
>
> **Revision r8 (2026-08-19, owner ruling — recovery is halt-only this era).** The iteration-13
> review PROVED by execution that r6 §7.8's graded resume branch cannot be made safe on the current
> ledger: the tail anchor stores a row COUNT plus the final row's hash and no per-row identity, so a
> same-length reconstructed suffix naming an unrelated dataset passes the completeness check —
> the genuinely destroyed shard then exists in no ledger at all, `verify_chain()` reports clean, and
> `seal_shard` will re-seal it fresh under another universe as if it had never existed. **Row-count
> equality is not evidence of identity and must never authorize recovery.** r8 therefore DELETES the
> union-marking / degraded-resume branch for this era: §7.8 becomes halt-only. Graded recovery
> returns only under a FUTURE named revision built on a real identity commitment — and that
> commitment must not be a mere SET of dataset ids: it must preserve enough to prove the exact
> historical suffix (at minimum ordered row/event identities, preferably a canonical
> checkpoint/manifest or Merkle-style commitment tied to the ledger chain). That migration is not to
> be designed ad hoc inside this fix. Owner's governing sentence: **for this era, safety wins over
> degraded availability — unknown or unprovable exposure history means the vault is unavailable,
> never "fresh".** Traps → TR-29.
>
> **Revision r9 (2026-08-20, owner ruling — sealed sufficiency is shard-scoped and pinned).** The
> iteration-17 audit PROVED by execution that `SEALED_PASS_RULE_V1` condition 1 read its
> sufficiency floors from the CALLER's spec: a spec carrying `floors={1,1,1}` and a single
> observation produced a permanent `verdict: "pass"` whose `rule_hash` certified floors of 30/8/2
> that the run never applied — precisely the defect §8.1 exists to prevent. But mechanically
> pinning §1's walk-forward floors was ALSO wrong: §7.3 seals a shard per `symbol:date`, so one
> shard is one symbol-day and `WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_SYMBOLS` are
> unsatisfiable, making PASS permanently unreachable. §8.1 and §7.3 genuinely contradicted each
> other. **The owner resolved it by separating the two stages scientifically rather than by
> changing the sealing unit: the walk-forward stage owns BREADTH; the sealed stage owns UNTOUCHED
> REPLICATION on one hidden symbol-day.** r9 adds the sealed-specific pinned constant
> `SEALED_MIN_OBSERVATIONS` (§1), declares session and symbol breadth `not_applicable_single_shard`
> at shard scope (never silently 1), and REFUSES any caller-supplied floor or threshold override —
> the evaluator owns the rule. The rule hash is computed from the sealed rule actually executed.
> Single-shot semantics are preserved and reinforced: **`insufficient` still consumes that family's
> sealed evaluation on the assigned shard** — a family does NOT get a fresh shard merely because the
> first lacked observations, which would be repeated holdout sampling. **The sealing unit is
> UNCHANGED.** The auditor's honesty-only artifact-field fix is necessary but insufficient; the
> evaluator's authority must be fixed before any sealed graduation is allowed. Traps → TR-30.

> **Revision r10 (2026-08-21, owner ruling — the Tier-B resolution is operationally frozen).**
> §7.2 already fixed the mandatory ORDER (screen → record → freeze → `symbol_rule` → register →
> commitment + HMAC → only then fetch) and Card 5.2 already froze the six screening CRITERIA. The
> iteration-23 preflight found the order un-executable anyway: three of the six criteria (market
> cap, primary US listing, no pending M&A) had NO data source in the project, and — more
> fundamentally — the spec never named the candidate UNIVERSE that replacement names are drawn
> from, nor the provenance protocol for the external criteria, nor what the negative "no pending
> M&A" test actually asserts. Resolving those inside a screen would have been methodology invented
> after seeing candidates. **The six criteria are UNCHANGED by this revision** — r10 adds only the
> pre-recording operational detail needed to execute them reproducibly: the frozen candidate
> universe (Nasdaq Trader listing directories, preserved as raw bytes, not merely hashed), the
> mechanical non-common-equity exclusions, the primary-listing interpretation, the SEC-based
> market-cap basis (fail-closed on multi-class), ADV as 30 completed SESSIONS, the previously
> undefined median-RTH-spread window (5 completed sessions, which become EXPOSED data and may
> never be sealed recording dates), the pending-M&A definition and search protocol, and a
> deterministic resolution that treats the five provisional names as seeds rather than
> grandfathered passes. r10 is legal now precisely because it is PRE-EVIDENCE: no recording
> universe is registered, no sealed tranche exists, zero J-06 tape calls have occurred, and no
> Tier-B screen result has been revealed. Detail → §7.2.1. Traps → TR-32 (live-progress
> composition, which the same preflight found open on BOTH transports).

> **Revision r11 (2026-08-21, owner ruling — the market-cap source hierarchy is completed, and the
> canonical live-progress text catches up to the code).** The r10 screen ran its cheap stages and
> then HALTED at `ABORTED_PRE_RESOLUTION` / `market_cap_source_hierarchy_incomplete`: r10 (d)
> authorised "one named fallback only if the primary is unavailable" but never named one, and
> `dei:EntityCommonStockSharesOutstanding` proved to be a genuine CompanyFacts 404 for ~12% of the
> price+ADV survivors. **Missing structured extraction must not silently turn a Card-5.2 criterion
> into a test of XBRL tagging quality**, so r11 names the fallback: the cover-page shares-outstanding
> disclosure of the latest 10-Q/10-K filed and accepted at or before the cutoff, which recovers the
> SAME underlying point-in-time quantity from the authoritative filing. It is an EVIDENCE-RECOVERY
> mechanism, never a new capitalization methodology — **r10 (d)'s multi-class fail-closed rule is
> unchanged**, so a candidate whose filing discloses several common classes stays `unresolved`, and
> that outcome is acceptable. `us-gaap:CommonStockSharesOutstanding` is explicitly NOT the fallback
> (a balance-sheet fact with a different measurement date, and stale in practice), and there is no
> third source. r11 also corrects a provenance MISNOMER — the screening runner uses Yahoo Finance
> unadjusted daily `Close`, which r10 wrongly called an "official close" — and reconciles §7.1's
> stale r5/r7 progress prose with what production actually serves after the TR-32 composition
> attacks (§7.1, TR-32). **Nothing else moves**: the six criteria, the five seeds, the hash ranking,
> exactly-three resolution, the 8-symbol panel, the 80-symbol-day arithmetic, the Nasdaq parser, the
> frozen raw source bytes, the screening cutoff, and the ADV / spread / pending-M&A windows are all
> untouched, and the rerun recomputes from those SAME frozen artifacts — the universe is never
> re-cut after partial results were seen. Detail → §7.2.1 (d), §7.1. Traps → TR-32.

> **Revision r12 (2026-08-22, owner ruling — TR-4 may not manufacture its own failure provenance,
> and a disclosed pool position is permanently spent).** The J-06 starter tranche came back 79/80
> and was REFUSED as lawful completion. Two defects, both structural. **(1) TR-4 was laundering
> itself.** The J-06 caller computed `disclosed_failures = expected − recorded` and handed that set
> to the generic verifier, so ANY missing pair classified itself as a disclosed vendor failure
> merely by being missing and the check could never fail. §7.2's "net of disclosed vendor failures"
> means failures with real recorder provenance — never arithmetic. **(2) A legacy dataset could
> short-circuit the recorder.** The recorder walk treated any dataset at a registered `(symbol,
> session_date)` as already-recorded, so a pre-existing partial-window dataset made a registered
> pair silently skip. A legacy collision is now its OWN typed condition that blocks acceptance
> outright and can never be converted into a vendor failure. The repair is completion, never
> substitution: the SAME already-registered universe, the SAME nonce, rule commitment, vault-secret
> commitment and HMAC assignment, and a genuine full-session recording of the SAME registered pair.
> **(3) The operator report leaked one pool position** (naming a registered pair as NOT
> HMAC-selected). Already-happened leaks are recorded, not glossed: a fourth vault ledger holds
> named, immutable pool-position disclosure incidents, and the consequence is permanent — the
> disclosed position can never take sealed / blind / historical-OOS credit again. Nothing is
> disclosed to "balance" it. Detail → §7.2.2. Traps → TR-4, TR-2.

> **Revision r13 (2026-08-25, owner ruling — the canonical outcome unit is a price-scale-invariant
> return, and the two side vocabularies are separated).** A measurement audit
> ([`reports/micro-unit-semantics-audit.md`](../reports/micro-unit-semantics-audit.md)) found this
> spec internally contradictory, and the contradiction faithfully implemented. **§4 defined the
> primary outcome as a mid-price DIFFERENCE — dollars — while §5.5 gated it against
> `family_median_spread_bps`, genuine basis points.** `micro_features.mid_outcome()` implemented §4
> literally, `scout.py` renamed the result `effect_bps` without converting it, and the
> economic-relevance gate has therefore been evaluating **dollars ≥ basis points** for the whole
> era. Two consequences, both structural. **(1) The gate was dimensionally invalid**, so every
> `killed_economic` decision recorded before r13 is void as an economic judgement. **(2) The
> estimator was itself meaningless across the corpus**: pooling dollar deltas over symbols spanning
> ~$160 (PG) to ~$600 (SPY) compares quantities that are not commensurable, whatever they are later
> tested against. A parallel defect sat dormant one layer down — walk-forward and sealed-evaluation
> effects are fed from `desk_forward`'s `return_pct`, which is PERCENT, and conditions 3 and 4 of
> `WF_SURVIVOR_RULE_V1` compare them against the same bps floor: a 100× error that never fired only
> because the sole registered sequence carries `econ_floor: null`.
>
> r13 fixes the measurement layer and nothing else. **The canonical primary outcome is
> `return_bps = (mid_horizon − mid_start) / mid_start × 10_000`**, direction-signed, computed by
> the `bps_move` primitive `micro_features.py` already owned and the outcome path simply never
> called. The ambiguous `value` key is REMOVED rather than redefined — an unlabelled number is what
> let dollars masquerade as basis points — and every outcome row, fold summary and economic floor
> now states its own unit, with a single unit-checked door (`require_bps_floor`) that every
> magnitude comparison passes through. The walk-forward feed converts percent to bps at its one
> boundary. r13 also separates the two side vocabularies that previously collided: **aggressor side
> is `buy | sell`, candidate direction is `long | short`**, disjoint, individually validated, with
> one explicit adapter — before r13 the outcome signer flipped only on `"sell"`, so a `"short"`
> candidate was silently NOT flipped and would then have been killed as wrong-direction. That
> defect never fired: every candidate registered to date carries `sidedness: null`.
>
> **Nothing else moves.** No threshold, grid, formula, embargo, fold parameter, floor multiple,
> p-value rule, sample floor or concentration ceiling is touched — r13 changes only the UNIT a
> magnitude is expressed in and the vocabulary a direction is named in. `ECON_FLOOR_SPREAD_MULTIPLE`
> stays `1.0`. **Re-keying:** the outcome unit joins the frozen `outcome` spec fields, so every r13
> candidate computes a different `spec_hash`/`candidate_id` from its pre-r13 namesake — old rows
> stay permanently on record, permanently distinguishable, and are never reinterpreted under the new
> convention. A pre-r13 economic floor carries no `unit` key and is REFUSED by the gate rather than
> silently read as bps. Detail → §0 Units, §4, §5.5. Traps → TR-34.
>
> **r13 (completion, 2026-08-25) — the sign convention is applied ONCE, and units are proved, not
> assumed.** Implementing r13 exposed three places where its own semantics were not carried
> through. All are corrected under the SAME revision: no methodology changes here — the outcome
> definition, the floor formula, every constant, every threshold and every gate stay exactly as
> r13 already fixed them — so a new revision number would misrepresent a completion as a change.
>
> **(1) Direction was applied twice.** A value reaching walk-forward or the sealed evaluator has
> ALREADY been direction-signed — at the outcome by `mid_outcome`, or at source for the playbook
> feed (`desk_forward`: *"a POSITIVE number means price went the way the wall implied"*, restated
> by `walkforward.playbook_observations`: *"never a second, independent sign derivation"*). Both
> stages nevertheless re-derived an expected sign from `sidedness` (`"positive" if long else
> "negative"`), so a genuinely successful SHORT candidate — which arrives POSITIVE — would have
> been scored wrong-direction and refused survival. §6.6 condition 3 and §8.1 condition 2 require
> the effect to lie *"in the registered direction"*; **in canonical signed space that IS positive,
> for long and short alike.** `sidedness` stays recorded, served and vocabulary-checked; it no
> longer re-derives a sign the outcome layer already applied. Latent: every registered candidate
> and sequence to date is `long` or unsided, where the two readings coincide.
>
> **(2) Units are proved on BOTH sides of every comparison.** r13's first pass proved the floor's
> unit but trusted the effect because a variable was named `effect_bps`. A name is not a proof:
> `require_return_bps_effect` now gates every effect magnitude, every fold observation (missing,
> unknown, legacy or MIXED units refuse before a single value is averaged), and every sealed
> observation at its own boundary.
>
> **(3) Candidate direction is validated at every public scientific boundary** — candidate
> registration, spec freeze, anchor extraction, screening, fold-spec registration and survivor
> evaluation — so an invalid vocabulary can never enter a frozen spec merely because the candidate
> later dies as `insufficient` and never reaches the outcome signer.
>
> **Legacy walk-forward rows.** Fold results persisted before r13 carry a PERCENT magnitude
> (`desk_forward`'s `return_pct`) and no `unit` key. They are retained untouched and SERVED with
> the explicit historical token `legacy_percent` — never converted, never rewritten, never
> relabelled `return_bps`, and never pooled into a new r13 computation: a sequence whose sufficient
> folds carry a non-canonical unit REFUSES a verdict rather than averaging percent into basis
> points. Each served row and decay-view row discloses its own unit, so no reader — and no column
> header — can take 0.019 percent for 0.019 bps.
> Detail → §0 Units, §4, §5.5, §6.6, §8.1. Traps → TR-34, TR-35.
>
> **r13 (contract pass, 2026-08-25) — every scientific boundary fails CLOSED, and discovery-derived
> direction is frozen before OOS.** Four remaining gaps, all closed without changing any constant,
> threshold, geometry or gate.
>
> **(1) Mode A fitted before it validated.** `register_mode_a_origin` neither validated `sidedness`
> — which it hashes into `spec_hash` and writes to a permanent row — nor proved its TRAINING
> observations' unit before `fit_training_quantile` consumed them. A quantile fitted over mixed
> units is a threshold in no unit at all, and it was then frozen into the spec. Both checks now
> precede the work they protect, inside the training half; the freeze order (train → fit → freeze →
> ONLY THEN the validation reveal) is unchanged.
>
> **(2) The sealed evaluator failed too late.** An invalid direction or a wrongly-united
> observation did fail — but only after `build_vault_state` and `accessor.read_snapshot_rows` had
> already read protected shard data. Both facts are knowable from the call arguments alone, so both
> are now checked BEFORE any shard read. No vault identity, rule-hash, assignment or exposure check
> is weakened; they all still run on every call that gets past that point.
>
> **(3) Scout asserted its own unit provenance.** Anchors carried `outcome_bps` with no unit, and
> `screen_candidate` passed the canonical unit to the economic gate as a literal — so the
> provenance existed only because the consumer claimed it, and the key's NAME proved nothing about
> its contents. Every extraction path now stamps `outcome_unit` read off the outcome row itself,
> and `require_canonical_anchor_units` verifies it before any pooling, permutation or gate; missing,
> unknown, percent, legacy and MIXED all refuse.
>
> **(4) The direction-freeze contract (§5.1, §6.6).** Scout may screen **unsided** — exploratory
> discovery asks "is there an effect", not "which way do I trade" — and that stays legal. But
> choosing `long` or `short` from Scout's exposed effect sign is **itself a discovery-derived
> parameter**. That choice IS permitted (Scout is discovery evidence), on one condition: it must be
> frozen into the registered spec BEFORE any out-of-sample window is revealed. The pipeline is
> therefore:
>
> `exposed Scout diagnostic → choose long|short from discovery evidence only → freeze it in the
> registered spec (re-keys spec_hash, stamps registered_at) → ONLY THEN reveal/evaluate
> historical_oos windows → sealed only after that`.
>
> Enforced by two mechanisms that already existed plus one that did not: `sidedness` is part of the
> frozen `spec_fields`, so changing it re-keys `spec_hash` and stamps a new `registered_at`;
> `classify_evidence_class` (§6.7) then demotes any window already exposed at that instant to
> `historical_exposed_diagnostic`, which earns zero graduation credit — so a post-hoc direction is
> worthless by construction. **New:** `sequence_verdict` now refuses survivor credit outright to a
> sequence carrying no frozen direction. (The sealed evaluator already refused an unsided spec via
> its completeness check.) Detail → §5.1, §6.4, §6.6, §6.7, §8.1. Traps → TR-36.
>
> **Revision r14 (2026-08-26, owner ruling — the corpus lifecycle is completed: session-count
> semantics, executable readiness floors, corpus-era freshness provenance, production exposure
> logging, and the exploratory release path for HMAC-NOT-selected pool members).** A data-bottleneck
> preflight ([`reports/data-bottleneck-preflight.md`](../reports/data-bottleneck-preflight.md))
> found five contract gaps between "the corpus is too small" and "the corpus can be grown lawfully".
> Nothing here re-keys a candidate: no `spec_fields` member changes, no constant is re-valued, and
> `config_fingerprint` stays `08e471b10130e1e2`. Five changes:
>
> **(1) Session COUNT vs session COVERAGE (§0, §1).** A session IS an ET RTH trading date, and every
> fold-geometry floor counts DISTINCT SESSION DATES. RTH coverage is a different quantity. The
> preflight itself made the error it was auditing for, writing "the corpus is 3 sessions, not 11" —
> the corpus has ELEVEN session dates and 3.0089 full-session equivalents of coverage, and both
> statements are true about different things. Readiness now serves `distinct_session_dates` and
> `full_session_equivalents` under those names, with a basis sentence, and neither is ever
> substituted for the other. `distinct_sessions`/`session_equivalents` are retained at identical
> values as their pre-r14 spellings.
>
> **(2) The 60-session floor never meant a fold could run (§1, §6.6).**
> `WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS = 60` is arithmetic over two constants;
> `DIAGNOSTIC_GEOMETRY` carries `embargo_sessions = 5`, so `build_folds` emits nothing until 65.
> Verified: 60 → **0 folds**, 65 → 1, 105 → 3. A corpus could therefore read `floor_met` while being
> unable to construct a single fold. Readiness now serves `first_fold_min_session_dates` (65) and
> `survivor_min_session_dates` (105) beside the actual `folds_constructible` count, and the retained
> 60 carries the basis token `train_plus_test_arithmetic_only`. **No floor is lowered and
> `DIAGNOSTIC_GEOMETRY` is untouched** — the numbers were always these; only the reporting was
> misleading.
>
> **(3) Corpus-era freshness provenance (§6.7).** An empty exposure registry meant two different
> things — "a legacy corpus nobody initialized" and "a fresh era where genuinely nothing has been
> served" — and `scout_candidate_walkforward_floor_check` had to fail closed on both, counting zero
> eligible windows. The tempting workaround was to serve a handful of clean sessions purely to make
> the registry non-empty, which destroys evidence to satisfy a predicate. Instead the registry gains
> ONE new row kind: a **corpus-era registration** naming a `corpus_id`, an instant and the
> operator's stated provenance basis. It names no window, so it can never make a window read as
> exposed. **The invariant: empty exposure rows ALONE are never proof of freshness** — a corpus is
> baseline-established iff it carries either an era registration or at least one genuine exposure
> row. Anything else refuses.
>
> **(4) Production exposure logging (§6.7).** §6.7 has always said every read of a window's outcomes
> appends an exposure entry, but `log_exposure` had no production caller outside r2 initialization,
> so the registry was write-once and `historical_oos` rested on freeze-order alone. The tick
> observation reader is now that boundary. Both purposes log — a TRAIN read exposes its window
> exactly as a TEST read does, which is what makes a training read masquerading as a clean test read
> structurally impossible — and a TEST read must prove `logged_at` is strictly after the spec's
> `registered_at`. Logging is deduped per `(corpus_id, window)`: exposure is a boolean fact, and a
> Mode A sequence re-reading one training window at every origin must not grow the ledger without
> bound. r2 initialization is unchanged.
>
> **(5) The exploratory release path — a FOURTH shard state (§7.4, §7.5 point 7).** `sealed →
> assigned → exposed` is reachable only by an HMAC-SELECTED member. A registered universe's
> NOT-selected members (~75 % of any pool at `VAULT_SEAL_HEX_BELOW = 4`) had no lawful way out at
> all, with two consequences proven against the real tranche (80 recorded / 21 selected / 59 not
> selected): those 59 could never become ordinary evidence, and `_whole_pool_released_universe_ids`
> could never become true, so the nonced rule could never be revealed and audited. §7.5 point 7
> already authorizes the missing act — "a shard's identity becomes public ONLY when that shard is
> actually **exposed for exploratory use** OR assigned to a candidate family" — and §7.2 already
> defines whole-pool release over members "the shard ledger never individually tracked". This is
> that implementation, not a new methodology.
>
> `exploratory_released` is a SIBLING terminal state, never a fourth step: never sealed, bound to no
> family, consuming no single shot, and structurally incapable of satisfying `SEALED_PASS_RULE_V1`
> condition 5. `release_unselected_shard` refuses on six grounds, each recomputed rather than
> asserted: unregistered universe · a secret that does not match the universe's own committed
> `vault_secret_commitment` · a pair outside `expected_recording_pairs()` · an HMAC that says
> SELECTED · a dataset that already carries any shard row · and a release that would breach §7.2.2's
> residual-uncertainty floor.
>
> **That last refusal is the non-obvious one and it binds hard.** Every release publicly discloses
> one pool position as NOT selected, so releases are self-limiting: release *all* of them and the
> unknown positions collapse onto exactly the still-hidden selected set, pinning every sealed
> shard's identity by subtraction. **At least one unselected member must therefore remain withheld
> as a decoy while any selected member is still sealed.** For the existing 80-pair tranche that
> means at most 58 of the 59 are ever releasable while all 21 stay sealed. Whole-pool release
> becomes reachable for the first time — but only after every selected member has itself been
> exposed, which is what lifts the floor. `VAULT_SEAL_HEX_BELOW` is unchanged.
>
> Detail → §0, §1, §6.7, §7.4, §7.5. Traps → TR-37, TR-38, TR-39.
>
> **Revision r14.1 (2026-08-26, owner ruling — corpus identity is bound to physical data, partial
> pools are usable, and the reserved decoy is precommitted).** A post-commit audit found r14's fixes
> correct but the OOS architecture they enabled still unexecutable and still reachable by three
> laundering routes. Nothing here re-keys a candidate; no constant is re-valued;
> `config_fingerprint` stays `08e471b10130e1e2`. Six changes:
>
> **(1) A mixed released/sealed date is USABLE (§7.4, §6.2).** Seal assignment is per
> `(symbol, session_date)`, so a healthy 8-symbol date normally holds ~6 not-selected and ~2 sealed
> members. r14's tick reader refused the WHOLE date if any member was withheld, which made the real
> HMAC design unusable. The fix is **not** "silently drop the withheld ones" — silence is how a
> corpus shrinks without saying so. A fold now reads a **PRECOMMITTED eligible-member set**, so a
> sealed member is a NON-MEMBER rather than an exclusion, and the fold reports its **realized**
> symbol/session breadth computed from the observations that exist rather than assumed from the
> panel size. `WF_FOLD_MIN_*` and `WF_MIN_SYMBOLS` are unchanged and applied to that realized
> breadth.
>
> **(2) `corpus_id` is BOUND to physical data (§6.7).** r14's corpus-era registration took a
> free-text provenance string it explicitly did not parse — so a caller could point a new
> `corpus_id` at already-exposed datasets and declare them fresh. Registration is now STRUCTURED and
> immutable: `{corpus_id, universe_id, universe_registered_at, rule_commitment,
> vault_secret_commitment, expected_pair_count, freshness_boundary}`, and the registrar proves the
> universe exists before the row is written. **Conflicting re-registration of the same `corpus_id`
> refuses**; idempotency requires every frozen field byte-identical. Free-text notes may accompany a
> registration and may never establish freshness.
>
> **(3) Membership scopes every inventory (§6.2, §7.5).** A `corpus_id` no longer means "every
> visible dataset whose date happens to match". A dataset is a member only if the frozen release
> plan marks its position releasable, its `schema_basis` is the recorder's own (a legacy dataset at
> a registered pair is a §7.2.2 COLLISION, never a member), its `created_utc` reaches the
> `freshness_boundary`, and the vault no longer withholds it. **`corpus_manifest_hash` now hashes
> the actual `(dataset_id, checksum)` membership**, not the date list — so a swapped member moves
> the hash even when the calendar does not.
>
> **(4) Release derives dataset identity from the store (§7.4).** r14's release accepted
> `symbol`/`session_date`/`content_checksum`/`event_count` as parameters and proved only that the
> *supplied pair* was unselected — so a caller holding dataset A could name unselected pair B. The
> public boundary is now `release_unselected_dataset(dataset_store, dataset_id, …)`, which DERIVES
> every one of those from `DatasetStore.get` and never asks. Disclosure-incident lookup is
> case-normalized and universe-scoped.
>
> **(5) The release plan is PRECOMMITTED, and so is the decoy (§7.2.2).** r14 refused the release
> that would pin the hidden partition, but "release until the transition refuses" let the operator
> decide, one release at a time and with earlier releases visible, WHICH member became the withheld
> decoy. That is a hidden selection freedom. Before any release, one immutable **release-plan
> record** now partitions the whole pool deterministically into `sealed_path` · `barred` ·
> `reserved_decoy` · `releasable`, from the registered rule, the HMAC and the incident ledger and
> from nothing else. The decoy is the lowest **`RELEASE_PLAN_RULE_V1`** rank —
> `HMAC-SHA256(vault_secret, "rapid-microscope-decoy-r14.1:{universe}:{symbol}:{date}")`,
> **domain-separated from `compute_seal`** so a revealed decoy leaks nothing about any other
> position's seal bit — and the rule name is hashed into the plan identity. A **hiding commitment**
> (nonce ‖ canonical plan) is persisted pre-release in its own fifth hash chain; only class SIZES
> are served while the pool is unresolved. Release order can no longer change which member stays
> withheld. **The reserve lifts only when nothing is hidden** — otherwise whole-pool release (§7.2)
> would be permanently unreachable, so the rule's own purpose is what releases it, never an
> operator's judgment.
>
> **(6) Exposure is committed BEFORE the first outcome read (§6.7).** r14 read the outcomes and then
> logged, so a crash between the two left a window that had been read while the registry said it had
> not — and a later spec would have classified it `historical_oos`. The order is now: validate ·
> resolve members · prove completeness · **append the exposure** · only then read. A read that fails
> after the precommit leaves the window burned. That is the conservative direction: a window wrongly
> marked exposed costs evidence, a window wrongly marked fresh costs the scientific claim.
>
> Operator support: the exact-80-pair assumption is lifted for a LATER era (the starter tranche's own
> 80-pair invariants are unchanged and still enforced for it), a later era writes to its own
> artifact directory, and four production stages exist for corpus-era registration, release-plan
> commitment, release and sacrificial probe logging — all dry by default.
>
> Detail → §6.2, §6.7, §7.2.2, §7.4, §7.5. Traps → TR-40, TR-41, TR-42.

---

## 0. Shared conventions

- **Units (r13).** Returns/moves in percent or bps **as named per field, and every field states
  its own unit** — a magnitude whose unit must be inferred from a variable name is a defect, not a
  convention. **The canonical scientific outcome unit of this era is `return_bps`**, a
  price-scale-invariant return in basis points (§4); it is the unit of every Scout effect, every
  walk-forward fold and pooled effect, every sealed-evaluation effect, and every economic floor.
  **An absolute price difference is never a scientific magnitude** — it is not comparable between
  price levels, so it never enters an estimator, a pooled average, or a gate; it may be served
  only as an explicitly named diagnostic (`delta_price`). Shares are integer counts.
- **Session COUNT vs session COVERAGE (r14).** A **session** is an ET RTH trading date, and every
  fold-geometry floor in this spec is counted in **`distinct_session_dates`** — never in coverage.
  RTH coverage is the separate, differently-named quantity **`full_session_equivalents`**
  (RTH minutes covered ÷ 390). They are not interchangeable in either direction: 11 dates of
  90-minute windows is eleven session dates AND 2.54 session-equivalents, and substituting either
  number for the other either overstates the corpus or understates it against the floors. Both are
  served, under those names, with the basis stated on the payload. Coverage is a corpus QUALITY
  measure and is never compared against a session-date floor.
- **Side vocabularies (r13).** Two closed, disjoint vocabularies, never interchangeable.
  **Aggressor side** — `buy | sell` — names who crossed the spread on a trade; it is the
  observer's domain. **Candidate direction** — `long | short` — names the hypothesis a registered
  candidate takes; it is `sidedness` in the ledger, the walk-forward and the sealed evaluator.
  Direction-signing uses `positive = the thesis direction`. An unsided candidate is `null` and is
  not flipped. **A value outside its vocabulary raises; it is never silently treated as
  positive.** Conversion between the two happens only through the one named adapter.
- **The sign is applied ONCE (r13).** The pipeline is
  `raw market return → direction signing (exactly one application) → canonical return_bps`.
  After that single signing, for a long and a short candidate alike:

  | raw move | registered direction | canonical `return_bps` | reading |
  |---|---|---|---|
  | up | `long` | **positive** | thesis worked |
  | down | `long` | **negative** | thesis failed |
  | down | `short` | **positive** | thesis worked |
  | up | `short` | **negative** | thesis failed |

  **No downstream layer may re-invert a sign on the basis of `long` vs `short`.** Scout,
  walk-forward, the sealed evaluator, graduation and every serving surface read a canonical
  effect the same way: positive = the registered thesis succeeded, negative = it failed. Where a
  rule says the effect must lie "in the registered direction" (§6.6 condition 3, §8.1 condition
  2), that means POSITIVE — for both directions. `sidedness` remains recorded and served as the
  candidate's registered direction; it is never a second sign derivation.
- **Sessions.** A session is an ET RTH trading date (`session_date`); the desk's session-honesty
  module (`desk_sessions.py`) is the arbiter of what counts as a session.
- **Determinism.** Every random draw uses `random.Random` streams under the recipe
  `f"{MICRO_SEED}:{scope_id}:{purpose}[:{fold_or_origin}[:{i}]]"` — no global RNG, no wall-clock,
  no unseeded randomness in any persisted artifact. Identical inputs reproduce byte-identical
  outputs.
- **Read-side law.** Every module this spec governs READS the frozen product (engine, detectors,
  band context, referee) and never feeds back into any of it. The engine-derived aggressor side
  and window features are consumed from the replay snapshot — never recomputed.
- **The availability law (r2).** Every feature value carries three instants: `anchor_at` (the
  event/moment the value describes), `observed_through` (the last event consumed to compute it),
  and `available_at` = the instant of `observed_through` (never earlier than `anchor_at`). A
  prefix feature has `observed_through = anchor_at`. A deferred construct — anything requiring
  later observations, e.g. `refill_consistent` (needs `REFILL_M_QUOTES` subsequent quotes) or
  response-over-K-trades (needs `RESPONSE_K_TRADES` subsequent trades) — becomes available only
  when those observations exist: it is written at its `observed_through` row, referencing its
  `anchor_at`, and is `unavailable` (counted, never guessed) when the session ends first.
  **Outcomes for a conditioned anchor begin at or after the conditioning feature set's maximum
  `available_at`** — never at `anchor_at` when the condition looks later. TR-17 enforces all of
  this deterministically.
- **Evidence classes** (stamped on every served study/fold/screen output; the era's spine):

| Class | Definition | Maximum claim it can carry |
|---|---|---|
| `historical_exposed_diagnostic` | Computed over a corpus whose outcomes were inspectable before the evaluated spec was frozen (today: the whole playbook bar corpus; the 12 legacy tick symbol-days) | Machinery works; temporal-stability DIAGNOSTICS. Zero graduation credit, zero gate satisfaction, never confirmation. |
| `historical_oos` | Spec frozen and registered FIRST, then evaluated on data whose relevant outcomes were not inspectable at freeze time (clean-horizon folds; sealed vault shards) | "Historically repeated out of sample under a frozen spec." Eligible for graduation gates. |
| `live_confirmatory` | Genuinely new sessions after a Referee registration boundary | The Referee's territory exclusively; this era's machinery never emits it. |

  Classes never mix in one pooled statistic; every payload carries `evidence_class` verbatim.

---

## 1. Pre-registered constants (module constants in `micro_*.py`; NEVER `Config` fields)

| Constant | Value | Meaning |
|---|---|---|
| `MICRO_SEED` | `314159` | Root seed for every stream in this family |
| `MICRO_ALGO_VERSION` | `1` | Bumps only as a named revision |
| `SNAPSHOT_FORMAT_VERSION` | `"micro-snapshot-v1"` | The snapshot representation chosen by the §2.4 benchmark; a representation change is a new version, old snapshots stay readable-or-refused, never rewritten |
| `MICRO_HORIZON_TRADES` | `(20, 100)` | Event-time outcome horizons (trades after anchor) |
| `MICRO_HORIZON_SHARES` | `(5_000, 50_000)` | Volume-time outcome horizons (shares after anchor) |
| `MICRO_HORIZON_CLOCK_SECONDS` | `(30, 60, 300)` | Clock outcome horizons; **no sub-second horizon exists** (DO-NOT #1) |
| `SCOUT_BLOCK_PERMUTATIONS` | `2_000` | Draws for the §5.3 screening null |
| `SCOUT_SCREEN_ALPHA` | `0.05` | Descriptive screening level for kill/advance ranking — never a confirmatory claim |
| `SCOUT_MAX_VARIANTS_PER_FAMILY` | `24` | Hard grid bound per (family, corpus), counted over the UNION of all grid versions ever run there |
| `ECON_FLOOR_SPREAD_MULTIPLE` | `1.0` | The §5.5 economic-relevance floor = this multiple × the family's median quoted spread (bps) at its discovery anchors. **A research cost PROXY, not an execution or tradability model** — served with that sentence |
| `WF_TRAIN_MIN_SESSIONS` | `40` | Fold-geometry floor, in DISTINCT SESSION DATES. **(r14) Their sum (60) is arithmetic, NOT a fold floor** — `build_folds` needs `train + embargo + test` contiguous dates, so under `DIAGNOSTIC_GEOMETRY` fold 0 needs **65** and 60 yields ZERO folds. Served as `train_plus_test_arithmetic_only` |
| `WF_TEST_MIN_SESSIONS` | `20` | Fold-geometry floor, in DISTINCT SESSION DATES (see above) |
| `WF_MIN_SUFFICIENT_FOLDS` | `3` | Below this, sequence-level refusal. **(r14)** The first count at which a `walkforward_survivor` verdict is reachable under `DIAGNOSTIC_GEOMETRY` is therefore `(40+5+20) + 2*20 = 105` session dates, served as `survivor_min_session_dates` |
| `WF_FOLD_MIN_SIGNAL_SESSIONS` | `8` | Per-fold floor: validation sessions carrying ≥1 observation |
| `WF_FOLD_MIN_OBSERVATIONS` | `30` | Per-fold floor |
| `WF_FOLD_MIN_SYMBOLS` | `2` | Per-fold floor whenever symbol breadth is claimed |
| `SEALED_MIN_OBSERVATIONS` | `30` | **(r9)** The ONLY sufficiency floor at sealed-shard scope (§8.1). A shard is one symbol × one session-date (§7.3), so session and symbol breadth are `not_applicable_single_shard` there — never silently 1. Never sourced from a candidate or caller spec |
| `DIAGNOSTIC_GEOMETRY` | `train=40, embargo=5, test=20, step=20` | Pinned geometry of the ONE playbook-corpus diagnostic acceptance run (§6.6). The `embargo=5` here is that run's predeclared choice, not a universal law — see §6.3 |
| `VAULT_SEAL_HEX_BELOW` | `4` | Seal iff the last hex digit of the §7.3 HMAC < 4 (≈25% of a universe) |
| `TRANCHE_MINIMUMS` | §7.6 table | The starter-tranche diversity floors |
| `RECORDER_PAGE_BUDGET_PER_MINUTE` | `200` | Tick-fetch throttle (the bar path's discipline, applied to the tick path at last) |
| `KILL_REASONS` | `("killed_null", "killed_direction", "killed_insufficient_n", "killed_concentration", "killed_economic", "killed_fragile", "superseded")` | The CLOSED kill vocabulary; free-text goes in `notes`, never in `reason` |
| `MICRO_FEATURE_WINDOW_TRADES` | `(20, 100)` | Event-time FEATURE windows (deliberately separate constants from the outcome horizons) |
| `MICRO_FEATURE_WINDOW_SHARES` | `(5_000, 50_000)` | Volume-time feature windows |
| `REFILL_M_QUOTES` | `20` | `refill_consistent` observation window: same-side quote updates after the execution; `available_at` = the M-th update; session-end first ⇒ `unavailable` |
| `RESPONSE_K_TRADES` | `20` | Response-asymmetry window: trades after the print; `available_at` = the K-th trade |
| `BURST_BASELINE_TRAILING_WINDOWS` | `20` | Burst baseline = median of this many prior non-overlapping same-length windows in the SAME session prefix; fewer than `5` ⇒ burst undefined (counted) |
| `DEPLETION_WINDOW_QUOTES` | `20` | Quote-depletion observation bound: consecutive same-side quote updates at an unchanged price; ends at a price change or the bound; `available_at` = the REVEALING quote (r6, §3) — the bound-hitting quote, or the price-CHANGING quote for a price-change termination |
| `IMPACT_FLATNESS_SCALE_BPS` | `5.0` | The frozen flatness scale: `flatness = clamp(1 − |Δmid_bps| / 5.0, 0, 1)`; `failed_aggression_score = dominant_side_volume_share × flatness` per feature window |
| `DIVERGENCE_TRAILING_SECONDS` | `120.0` | Divergence-at-level price/volume window: TRAILING `[τ − 120s, τ]`, as-of the touch — supersedes Card 9.1's symmetric "window around the touch"; `available_at` = τ |
| `DIVERGENCE_DELTA_VOLUME_FRACTION` | `0.25` | Card 9.1's δ fraction, frozen HERE as a module constant (never a Config field): `δ = 0.25 × median trailing-120s volume` over the session-prefix baseline windows |
| `QUOTE_SIZE_UNITS` | `("shares", "round_lots", "unverified")` | The dataset-level size-unit vocabulary (§2.6) |
| `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` | `"2025-11-03"` | Vendor-documented rule the recorder stamps from: Alpaca CTA/UTP displayed quote sizes are SHARES for windows on/after this date, ROUND LOTS before it; re-verify against vendor docs at recording time and record the verification |
| `WF_SURVIVOR_SIGN_CONSISTENCY` | `0.7` | The §6.6 survivor rule's fold-sign agreement floor |

Every value above was chosen on 2026-08-16, before any outcome was read — arbitrary-but-frozen;
a change to any of them is a named revision, never a tuning act.

Every record embeds the constants it used verbatim (`micro_parameters()` — the desk pattern) and
keys on their hash; a monkeypatched constant must move the parameters hash AND the result identity
(counter-tested).

---

## 2. The observer contract (`micro_observer.py` + `micro_snapshots.py`)

### 2.1 Attachment
`DatasetStore.replay(dataset_id, config)` gains an additive, default-`None` `observer=` kwarg that
calls the engine's existing `TapeEngine.add_observer` seam before the event loop. `observer=None`
is byte-identical to today (the engine's observer-equivalence test already proves snapshots are
unaffected; a counter-test pins the kwarg default). **No second replay implementation exists.**

### 2.2 The prefix law (streaming-only state) + availability (r2)
Snapshot row *i* is a pure function of events `1..i` (plus the engine snapshot after event *i*).
The writer flushes row *i* before consuming event *i+1*. **No whole-dataset normalizer, baseline,
calibration, or end-of-session statistic may enter any row.** Session-anchored accumulations
(cumulative delta) are legal because the anchor precedes every row. Event-time baselines use only
prior events. Deferred constructs (§0 availability law) are written at their `observed_through`
row referencing their `anchor_at` — never attached retroactively to an earlier row. Enforced by
the TR-1 prefix/tail traps and the TR-17 availability trap (§9).

### 2.3 Snapshot identity and verification
Snapshot key = `(dataset_id, dataset_checksum, MICRO_ALGO_VERSION, SNAPSHOT_FORMAT_VERSION,
feature_source_hash, config_fingerprint, params_hash)` where `feature_source_hash` =
sha256 over the feature-module bytes. The loader re-verifies `dataset_checksum`,
`config_fingerprint`, and `feature_source_hash` on every read and refuses on mismatch
(the `DatasetIntegrityError` discipline). Snapshots are derived, append-only, rebuildable, and
own nothing. Every persisted feature value carries `anchor_at`, `observed_through`, and
`available_at` (§0); prefix features may encode the three compactly, deferred features never.

### 2.4 Granularity is decided by measurement, not assumption
Before any snapshot format is frozen, J-02 runs a benchmark on ≥2 real datasets including the
largest (NVDA `72ca8bc0`, 1.97M events): candidate representations (per-event rows; per-event
sampled-at-anchors; fixed-stride event blocks) are measured for bytes-on-disk amplification vs
the raw dataset, one-pass build time, and anchor-query latency. The chosen representation and the
measured numbers are recorded in the J-02 handoff and pinned as `SNAPSHOT_FORMAT_VERSION`.
Per-event rows are NOT presumed — the raw corpus is already ~1 GB and the tranche corpus will be
multiples of that.

### 2.5 Reuse table (compute nothing twice)
Read from the engine snapshot, never re-derived: aggressor side (+ its `side_source`: `quote_rule`
| `tick_test` | `carried` | `unknown`), the five-window features (`aggressive_*`,
`net_aggressive_volume`, `buy/sell_price_impact`, `average_spread`, `absorption_score`,
`bid/ask_refresh_score`, `reference_price`), tape state, bid/ask/spread/last. New research
features (§3) are additive representations the engine does not compute.

### 2.6 The dataset schema-basis + size-unit contract (r2)
Every NEWLY recorded dataset carries two manifest fields, stamped at record time:
- `schema_basis` — the event-row schema version, including whether the optional Card-5.1
  preservation fields (§7.1) are present;
- `quote_size_unit` ∈ `QUOTE_SIZE_UNITS` — stamped from the dated vendor rule
  (`ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`: Alpaca CTA/UTP displayed quote sizes are SHARES for
  windows on/after 2025-11-03, ROUND LOTS before; the recorder records the rule text + the
  verification note beside the stamp).

Every LEGACY dataset (all 18 on disk) is `quote_size_unit: "unverified"` until a recorded,
auditable verification act says otherwise — never a silent relabel. **The old universal "SIP
quote sizes are round lots" pin (Card 5.1 / trap T12) is superseded by this per-dataset
contract.**

Consequences, fail-closed: features that compare quote sizes only to quote sizes within one
dataset (quote imbalance, microprice) are unit-invariant and always legal; **any cross-basis
feature relating trade SHARES to displayed liquidity — execution-vs-replenishment, any
share-denominated depletion/replenishment magnitude, any trade-share/displayed-size ratio — is
REFUSED with a typed error unless the dataset's `quote_size_unit` is verified**, and any pooled
statistic across datasets of mixed units is refused outright (TR-18). Unit normalization exists
only as a recorded verification act (a named, auditable manifest annotation), never as silent
arithmetic in a feature path.

---

## 3. Feature families (Wave 1 — L1 only)

Per-row disclosures everywhere: `side_source`, and per-window `fallback_frac` (share of trades
classified by the tick test rather than the quote rule — measured 29–76% on the current corpus)
and `unknown_frac`. Any aggressor-derived quantity is served beside those two fractions.

- **F-FLOW** — per-print signed volume (engine side × size); session-anchored cumulative delta
  `CD_t = Σ_{i≤t, side_i≠unknown} sign(side_i)·size_i` (Card 9.1's accumulator verbatim;
  unknowns excluded and counted); rolling imbalance over the `MICRO_FEATURE_WINDOW_TRADES` /
  `MICRO_FEATURE_WINDOW_SHARES` event-time windows beside the engine's clock windows; same-side
  run length at anchor (consecutive prints with the same engine side; `unknown` breaks the run;
  the anchor print counts); volume burst = window volume ÷ the median of the prior
  `BURST_BASELINE_TRAILING_WINDOWS` non-overlapping same-length windows of the SAME session
  prefix (fewer than 5 ⇒ undefined, counted). **Divergence-at-level (Card 9.1, amended r2)**:
  at consecutive touches τ1 < τ2 of the same recorded band, bearish divergence iff
  `price_extreme(τ2) > price_extreme(τ1)` AND `CD(τ2) ≤ CD(τ1) − δ`, where `price_extreme(τ)`
  = the max/min mid over the TRAILING window `[τ − DIVERGENCE_TRAILING_SECONDS, τ]` (as-of,
  never symmetric) and `δ = DIVERGENCE_DELTA_VOLUME_FRACTION × median trailing-120s volume`
  over the same session-prefix baseline windows; `available_at = τ`. Prefix features all carry
  `available_at = anchor_at`.
- **F-RESPONSE** — impact efficiency = signed mid move (bps, aggressor-signed) per 1,000
  aggressive shares over a feature window; efficiency trend = current window efficiency minus
  the prior non-overlapping same-length window's (the exhaustion signature: rising aggression
  with falling efficiency); failed aggression = the engine's `absorption_score` (reused)
  plus the continuous complement, pinned as
  `failed_aggression_score = dominant_side_volume_share × clamp(1 − |Δmid_bps| /
  IMPACT_FLATNESS_SCALE_BPS, 0, 1)` (dominant share = max(buy, sell) ÷ directional volume,
  0.0 when none); **response asymmetry** = the signed mid move over the `RESPONSE_K_TRADES`
  trades after a buy-aggressive vs a sell-aggressive print — a DEFERRED construct:
  `observed_through` = the K-th subsequent trade, `available_at` there, `unavailable` when the
  session ends first.
- **F-LIQUIDITY** — spread level (engine) and spread change (feature-window mean minus the
  prior non-overlapping same-length window's); quote imbalance
  `(bid_size − ask_size)/(bid_size + ask_size)` and microprice
  `(ask·bid_size + bid·ask_size)/(bid_size + ask_size)` — both instantaneous at the in-effect
  NBBO and as feature-window means, and both unit-invariant WITHIN a dataset (legal at any
  `quote_size_unit`); quote depletion = the drawdown of same-side displayed size across
  consecutive quote updates at an unchanged price, observed over at most
  `DEPLETION_WINDOW_QUOTES` updates (ends at a price change or the bound; a DEFERRED
  construct whose `available_at` is the **REVEALING** quote, not the last measured one —
  **measurement end ≠ knowledge time** (r6): a bound-terminated run is revealed by the
  bound-hitting quote, so `available_at` is that quote; a price-change-terminated run is only
  revealed by the price-CHANGING quote, so `available_at` is THAT quote — which is excluded from
  the depletion measurement itself, exactly as its own conditioning data would be); replenishment (`refill_consistent`: displayed size
  restored at the same price within the next `REFILL_M_QUOTES` same-side quote updates after
  executions against it — a DEFERRED construct, `available_at` = the M-th update or
  `unavailable`; **the ONLY permitted label** — "iceberg", "institutional", "spoof" and any
  intent language are banned); execution-vs-replenishment ratio (executed trade volume at a
  price ÷ displayed-size restoration there, windowed) — **CROSS-BASIS: refused unless the
  dataset's `quote_size_unit` is verified (§2.6)**, as is any share-denominated
  depletion/replenishment magnitude.

Quote sizes reach the observer on `QuoteEvent` rows — they are dropped only inside the engine's
`FeatureEngine`, which this spec does not touch.

---

## 4. Outcomes (the closed set)

For an anchor event: the forward **mid RETURN in basis points (r13)**

```
return_bps = (mid_at_horizon − mid_at_outcome_start) / mid_at_outcome_start × 10_000
```

at every horizon in §1's three horizon families; session-truncated with
truncation flagged and truncated rows excluded from averages (the playbook rail's honesty rule);
**direction-signed** (`long | short`, §0) when a hypothesis direction exists, unflipped when the
candidate is unsided. **The outcome is a RETURN, never an absolute price difference (r13)** — a
dollar move is not comparable between a $160 and a $600 symbol, so pooling one across a corpus
estimates nothing and comparing one to a basis-point floor is dimensionally invalid. A
non-positive starting mid has no basis to express a return against and is `unmeasured`, exactly
as a missing one is. The raw signed dollar move MAY be served beside the primary as an explicitly
named `delta_price` diagnostic; it is never pooled, never averaged, never gated, and never
compared against a spread floor. **Mid is the ONLY primary basis (r2)**: a row lacking
a quote mid at either end is `unmeasured` — excluded and counted, never silently measured off
the last trade. A separately named `last_trade_basis` outcome column MAY be served beside the
primary as a sensitivity reading; it is never pooled with, substituted for, or averaged into
the mid-basis primary. **Outcome start = the conditioning feature set's maximum `available_at`**
(= `anchor_at` when every conditioning feature is prefix; strictly later for deferred
constructs) — TR-17(c) enforces it. Quoted spread at the outcome start (bps) is served beside
every outcome as the cost-proxy column — never netted into the outcome silently. No sub-second
horizon exists anywhere.

---

## 5. The Scout and the exploratory candidate ledger (`scout.py`, `scout_ledger.py`)

### 5.1 Candidate spec (frozen at ledger append)
`{candidate_id, family_id, family_root_id, feature: {name, transform, params},
structure_context: {kind: "playbook_signal"|"band_touch"|"none", …frozen references},
outcome: {horizon_key, sidedness}, fitting_rule?: <a named rule string, §6.4>, econ_floor:
{multiple, family_median_spread_bps, floor_bps, proxy_sentence}, corpus_manifest:
[dataset/record ids + checksums], grid_version, registered_at, spec_hash}`.

**`family_root_id` (r2) is COMPUTED, never declared**:
`sha256(canonical(feature_family_name, structure_context_kind, outcome_horizon_family))[:16]`.
Every renamed, re-parameterized, or derived family with the same triple computes the SAME root —
so the single-shot sealed-exposure key (§7.4) cannot be reset by renaming, and every export
bundle's lineage is canonical (TR-20).

### 5.2 The ledger
Hash-chained append-only JSONL (the `desk_playbook_log.py` pattern): every evaluated variant —
including every kill — is one permanent row carrying its result summary, `decision:
survive|<KILL_REASONS>`, `reason` (closed vocabulary), `notes`, and the family's running
`variants_tried` (the union-N denominator across all grid versions). Rows are never rewritten;
`superseded` rows point at their successor. Tamper = chain-verification failure (TR-11).

### 5.3 Screening procedure (descriptive, never confirmatory)
Cluster unit = `session_date` for BOTH families, always — **frozen, corpus-size-invariant
(r2)**; symbol-day breadth is a served disclosure beside it, never an alternative clustering.
Effect = mean of session-cluster mean deltas (candidate cell vs its comparator).
Null = **within-session circular block permutation** with block length ≥ the label span in events
of the longest horizon evaluated (computed per session, ceiling) — a plain row shuffle is BANNED
(anti-conservative under overlapping labels; TR-8 calibration trap pins pass-rate ≤ 1.5× nominal
alpha on an autocorrelated null fixture). Clock-horizon effects additionally use non-overlapping
anchor subsampling (every anchor at least one horizon apart within a session, seeded selection).
`p_screen` at `SCOUT_SCREEN_ALPHA` ranks kills/advances; it is served with the label
`descriptive screen — not a confirmatory p-value`.

### 5.4 Mandatory disclosures per screened candidate
Session/symbol concentration (top-1 session share, top-1 symbol share); ToD-bucket slices
(open/mid/close — the referee's buckets, reused); fallback-tercile stratification for any
aggressor-derived feature (effect within low/mid/high `fallback_frac` terciles) — **the caveat is
FAMILY-SCOPED (r13): F-FLOW and F-RESPONSE read the engine's aggressor side classification and
carry it; F-LIQUIDITY (quote imbalance, microprice, spread change) never reads `side` at all and
does not. A high corpus-wide `fallback_frac` is not by itself evidence that a F-LIQUIDITY result,
or the corpus as a whole, is weak**; the family's
best-of-N expected-max-under-null line (N = union variants tried; a DISCLOSURE, never a decision
rule); `evidence_class` of the corpus screened.

### 5.5 Economic relevance (separate column, never a merged verdict)
`econ_interesting = |effect_bps| ≥ ECON_FLOOR_SPREAD_MULTIPLE × family_median_spread_bps`,
computed from the discovery anchors' quoted spreads, with the formula and inputs frozen in the
candidate spec BEFORE any outcome is read (registration-ordering enforced, TR-9). Served beside —
never multiplied into — the statistical screen, always with the proxy sentence: *quoted spread is
a research cost proxy, not a full execution or tradability model*.

**Both sides of that comparison are `return_bps` (r13), and the floor states its unit.** The
effect is the §4 canonical outcome; the floor is a median of `spread_bps` over the candidate's own
discovery anchors. Every comparison passes through one unit-checked door, and a floor that does
not declare basis points — including any floor persisted before r13, which carries no unit at all
— is REFUSED rather than silently compared against.

**What clearing this floor does and does not establish (r13).** Three concepts, never conflated:

| Concept | What it means | What establishes it |
|---|---|---|
| **Statistical effect** | The relationship differs from the dependence-honest null | `p_screen` under §5.3's block permutation — a descriptive screen, not a confirmatory p-value |
| **Economically interesting** | The measured effect magnitude exceeds the registered quoted-spread cost proxy | `econ_interesting` — this column, and nothing more |
| **Profitable / executable** | A strategy makes money after real execution | An explicit execution model this era does NOT build: entry and exit rules, bid/ask fill basis, spread paid, slippage, fees, latency, liquidity and capacity, partial fills, and short borrow/locate where applicable — followed by live confirmation under the Referee's own spec |

The Rapid Microscope establishes at most the **second** category before live confirmation.
`econ_interesting` is therefore never described as "profitable", "tradable", or "an edge" on any
surface, in any report, or in any code comment — it clears a cost PROXY, which is a necessary and
very far from sufficient condition. A Scout survivor is a candidate that has not yet been killed,
never a finding.

---

## 6. The chronological walk-forward engine (`walkforward.py`, `micro_accessor.py`)

### 6.1 The accessor is the only door
`micro_accessor.py` is the sole legal reader of snapshot, ledger-input, and vault event data
(import-ban guard; TR-3). It is constructed with an `origin` (a session date) and refuses — with
a typed error, never an empty result — any read beyond it; sealed shards are invisible to it
except as §7.5 metadata.

### 6.2 Fold spec (frozen per corpus-era, before fold 1)
`{corpus_id, corpus_manifest_hash, geometry: {train_sessions, test_sessions, step_sessions,
embargo_sessions, embargo_derivation}, clustering_unit, floors (§1), registered_at,
geometry_hash}`. `clustering_unit` is frozen at registration and is `session_date` for both
families (§5.3's r2 rule — no corpus-size-dependent switching, ever). Fold boundaries fall ONLY
on session-date boundaries. Step ≥ test span (pooled
statistics over overlapping validation windows are refused). **Changing geometry after fold 1
voids every survivor state of that corpus-era** (recorded as a voiding event; TR-13).

### 6.3 Purge and embargo
Labels are session-truncated (§4), so no label crosses a session-date fold boundary — **purge is
exact by construction** and asserted, not assumed (TR-6). The embargo is **derived per fold-spec
from actual cross-boundary dependencies**, deterministically, and the derivation is recorded in
`embargo_derivation`: if session-truncated labels + prefix-only features + session-date boundaries
leave no identified cross-boundary dependency, **E=0 is a legitimate outcome**; a nonzero E must
name the dependency it covers (e.g. multi-session feature memory, known regime autocorrelation).
The diagnostic acceptance run pins E=5 as ITS predeclared choice only.

### 6.4 Mode A — rolling-origin discovery
At each origin T: candidate generation, ranking, and threshold FITTING run only through the
origin-T accessor. **The frozen spec identity is the fitting RULE** — e.g.
`training_quantile(0.90)` — never the fold's realized numeric value; realized fitted values are
recorded as fold provenance. Only a RULE change (or any other spec-field change) starts a new
constant-rule sequence; per-origin refits under the same rule do NOT (TR-14 pins both directions).
Fitting rules are functionals of DATA only, never of the candidate pool (pool-invariance trap
TR-10). The validation window is revealed only after the spec hash is recorded; freeze order is
in the fold ledger.

### 6.5 Mode B — fixed hypothesis
A human-authored spec is registered (ledger row, spec hash, timestamp) FIRST; evaluation then
runs on later windows and/or assigned vault shards. Evaluation of a spec against data whose
outcomes were inspectable before its registration is auto-classed `historical_exposed_diagnostic`.

### 6.6 Reporting: the temporal-stability (decay) view
Per constant-rule sequence: per-fold effect, n, sessions, sign, ToD-regime slices, symbol breadth,
and the recent-vs-older consistency line. Pooling across sequences is refused. Every fold and
sequence carries its `evidence_class`; class-mixing in one pooled number is refused (TR-5).
Below-floor folds report `insufficient`; a sequence with < `WF_MIN_SUFFICIENT_FOLDS` sufficient
folds refuses a sequence-level verdict. The tick family refuses fold construction outright until
its corpus clears the §1 floors (TR-15 pins the refusal at today's 11 sessions).

**The explicit survivor rule — `WF_SURVIVOR_RULE_V1` (r2, frozen):** a constant-rule sequence
qualifies as `walkforward_survivor` iff ALL of:
1. ≥ `WF_MIN_SUFFICIENT_FOLDS` sufficient folds, every one of class `historical_oos` and
   process label `rule_process` (§6.8);
2. fold-sign agreement with the registered sidedness ≥ `WF_SURVIVOR_SIGN_CONSISTENCY` over the
   sufficient folds (a zero or opposite-sign fold counts against) — **in canonical signed space
   (§0) agreement means POSITIVE, identically for a long and a short candidate (r13)**;
3. the pooled session-clustered effect lies in the registered direction — **i.e. is POSITIVE
   (r13)** — with magnitude ≥ the family's pre-registered economic floor (§5.5), **both sides of
   that comparison proved to be in their declared unit, never assumed from a field name**;
4. no sufficient fold passes the §5.3 screen in the OPPOSITE direction — **i.e. no eligible fold
   is NEGATIVE at floor-clearing magnitude (r13)**;
5. zero voiding events on the corpus-era.
Anything less is not a survivor — there is no discretionary override.

**The diagnostic acceptance run**: the 155-session playbook bar corpus (the 2025-06 orphan
excluded, disclosed), `DIAGNOSTIC_GEOMETRY`, a small predeclared set of already-frozen playbook
setup definitions, producing 5 folds / 100 validation sessions — every output labeled
`historical_exposed_diagnostic`, worth zero graduation credit, and never re-run with tuned
parameters.

### 6.7 The exposure registry — the deterministic `historical_oos` rule (r2)
A corpus-scoped, hash-chained **exposure registry** records every serving of a window's outcome
data: any GET/report/study/screen/fold that returned outcome aggregates or rows for (corpus,
session-window) appends an exposure entry (surface, window, timestamp). The class rule is then
mechanical: a (spec, validation-window) pair is `historical_oos` **iff** the window has NO
exposure entry timestamped before the spec's `registered_at` AND the shard(s) covering it were
not `exposed` before that instant. At r2 the registry is honestly initialized: every window of
the playbook bar corpus and of the 12 legacy tick symbol-days is pre-marked exposed (their
aggregates have been served for months). **Human/agent rule**: authors — human or agent — read
research data only through served, registry-logged surfaces; the accessor is the only door and
direct file/sqlite reads are guard-banned (TR-3), so there is no unlogged read path. A spec
registered after any logged serving of its validation window is auto-classed
`historical_exposed_diagnostic` (TR-22) — the rule needs no judgment about who remembers what.

**Corpus-era freshness provenance (r14).** An empty registry means two different things and must
not answer the same way to both. The registry therefore carries a second row kind: a **corpus-era
registration** `{record_kind: "corpus_era_registration", corpus_id, registered_at, provenance}`. It
names NO window, so it can never make a window read as exposed and never suppresses the r2 seeding
guard. **The invariant: empty exposure rows ALONE are never proof of freshness.** A corpus is
baseline-established iff it carries either an era registration (explicitly fresh) or at least one
genuine exposure row (legacy, r2-initialized); anything else fails closed and counts ZERO eligible
windows. **Serving clean sessions purely to make a registry non-empty is forbidden** — it destroys
evidence to satisfy a predicate.

**The production write path (r14).** §6.7 has always required a read to append an entry; before r14
`log_exposure` had no production caller outside r2 initialization, so `historical_oos` rested on
freeze-order alone. The tick observation reader is now that boundary. **Both purposes log** — a
TRAIN read exposes its window exactly as a TEST read does, which is what makes a training read
masquerading as a clean test read structurally impossible — and a TEST read must prove its
`logged_at` is strictly after the spec's `registered_at`. Entries are deduped per
`(corpus_id, window)`: exposure is a boolean fact, and a Mode A sequence re-reading one training
window at every origin must not grow an append-only ledger without bound.

**A retention/availability probe is a SACRIFICIAL exposure (r14).** A tick fetch on a date READS
that date's tape. Calling it "metadata only" because the bytes were discarded is a fiction the
registry cannot check, and unknown exposure history is never "never exposed" (§7.8). A probe is
therefore logged as a real exposure under its own surface, and that date is thereafter barred from
every clean-OOS date rule. Probe a date already burned (a §7.2.1(f) screening session) where one
will do.

### 6.8 Process labels: candidate-rule vs proposer-process evidence (r2)
Every sequence carries a process label. `rule_process`: every generation, ranking, and fitting
step inside the walk-forward was the frozen algorithmic rule — no human/proposer choice
intervened after the first reveal. `operator_process`: a human or proposer selection step
occurred after any fold reveal (choosing among Mode-A outputs, re-ordering, re-prioritizing).
`operator_process` sequences are diagnostic-grade for graduation — they may inform NEW
registrations but never satisfy `WF_SURVIVOR_RULE_V1` (TR-21). An operator selection logged
BEFORE the first reveal (a registered shortlist) keeps `rule_process` for the sequences it
selected, because nothing revealed informed it.

---

## 7. The recorder and the Validation Vault (`tick_recorder.py`, `vault.py`)

### 7.1 The recorder job (Card 5.2, brought forward)
Chunked fetch via the adapter's `iter_historical_chunks` (900s sub-windows), throttled at
`RECORDER_PAGE_BUDGET_PER_MINUTE`, per-chunk checkpointing, resumable and idempotent (an
already-recorded window is answered store-first), single-flight job manager + CLI (the
deep-backfill precedent), operator-gated and credentialed; every recording lands through the
existing `DatasetStore.record` unchanged in discipline (append-only, checksummed, split frozen
at registration). Paired bar backfill (the existing `desk_deep_backfill` CLI) runs for the same
symbol-days so band context joins. Recording failure modes (vendor timeout, partial window,
credential absence) are per-chunk `failed` outcomes with detail — never a raise, never a
fabricated row.

**Recorder progress is NON-OUTCOME while the pool is unexposed (r11/TR-32 — supersedes the r5/r7
shape).** `GET /research/desk/micro/recorder/compute`, the CLI, and every other LIVE progress
surface — UI, MCP, or any future transport — serve ONLY non-outcome operational state:

| served live | withheld from live progress |
|---|---|
| `chunks_done`, `chunks_total` | fetched / reused / unchanged / failed counts |
| `percent_complete`, `elapsed_seconds` | exact OR bucketed trade totals |
| `chunks_per_minute` | exact OR bucketed quote totals |
| | symbol, date, dataset id, shard id, per-chunk byte/event counts |
| | any field whose CHANGE proves a particular known chunk's realized state |

`chunks_per_minute` is admissible only because it is deterministically derived from position and
time fields already served, and so adds no independent outcome information.

**Why the earlier r5/r7 shape was insufficient.** r5 required aggregate-only fields and r7 replaced
exact volumes with coarse buckets, but both reasoned FIELD-BY-FIELD. Iteration 23 mounted the
COMPOSITION attack and broke them on both transports: (1) with one line/response per completed chunk
and exact cumulative outcome counters, an observer who polls often enough that `chunks_done` advances
by exactly one differences those counters against the deterministic, operator-known plan and pins
that chunk's realized outcome — a whole run was reconstructed exactly, failed symbol-day included;
and (2) the coarse volume buckets leaked by EXISTENCE rather than magnitude, because running totals
advance ONLY on a `fetched` chunk, so a bucket TRANSITION across a single-chunk advance proves that
chunk was fetched. r7's differencing-resistance argument defeated recovery of the VOLUME but not
this existence proof. The requirement is therefore OUTCOME-BASED, not field-based: **no sequence of
operator-visible progress snapshots, composed with the known registered plan, may reveal a specific
withheld symbol/date/chunk's realized success or failure with certainty.**

Detailed per-chunk identities and exact counts remain in the INTERNAL recorder state for recovery,
idempotency and audit. **There is no operator-only bypass** — using one would itself be a human
exposure event that destroys the tranche's blindness. TERMINAL/batch reporting is a DISTINCT
lifecycle stage: TR-4's disclosed per-chunk/per-symbol vendor-failure list remains REQUIRED there
under the existing lawful disclosure rules, and the terminal run-log row still carries the exact
counts. TR-2's inference trap (§7.5) and TR-32 cover the live paths.

**Event and byte VOLUMES elsewhere remain coarse buckets pre-release (r7, unchanged for non-live
surfaces).** The iteration-11 audit proved the contradiction: on a one-symbol-day run the "aggregate"
`trades_total` IS that withheld shard's exact count. §7.5's no-exact-count rule is the stronger
confidentiality contract and wins. While ANY member of the ORIGINAL registered pool is unexposed,
every readiness / API / UI / MCP surface serves trades recorded, quotes recorded, and bytes recorded
ONLY as **predeclared coarse buckets** (`trades_total_bucket: "1M–10M"`, never
`trades_total: 3842117`). On LIVE RECORDER PROGRESS specifically, r11/TR-32 goes further and serves
no volume field at all.

The scheme must be **differencing-resistant**: never a per-shard count while that shard is
withheld; never an exact delta between successive progress snapshots; never finer buckets as the
pool shrinks; and no series of responses taken before and after individual exposures may
algebraically reconstruct a withheld member's exact count. Exact volumes may be served only after
**whole-pool release** (§7.2's original-pool definition). Non-sensitive operational counters —
chunks completed/total, success/fail/pending, percent complete, retry count, throughput range —
stay exact, provided none carries shard identity or permits reconstruction.

**Traps (r7).** A one-symbol-day run while withheld ⇒ no exact trade/quote count appears anywhere ·
a multi-shard pool ⇒ coarse aggregate buckets only · exposing one shard and re-querying ⇒ the
remaining withheld counts cannot be solved exactly from the before/after pair · the final pool
member released ⇒ exact totals may be served · no API/UI/MCP path leaks exact counts earlier.

**The Card-5.1 data-preservation prerequisite (r2) — a HARD gate before any bulk recording.**
Before the recorder may record ANY universe (starter tranche included), the event schema ships
the preservation fields: optional `conditions: list[str]` and `exchange: str` on
`RawTrade`/`TradeEvent` and the dataset trade rows, and the vendor-supplied quote
conditions/venue equivalents on `RawQuote`/`QuoteEvent` and quote rows where the feed provides
them — plus any other immutable vendor identifiers the SDK response carries (tape, trade id)
as optional row fields. Optional means: absent-key backward compatibility — every EXISTING
dataset and committed fixture loads byte-identically and its checksum still verifies; the
frozen engine ignores the new fields entirely (the equivalence and golden-trace tests pass
byte-unmodified); the fields exist for research consumers and future data families (Card 9.10's
condition dependency starts accruing on new recordings). The recorder structurally asserts the
schema basis (fields present + `quote_size_unit` stamping per §2.6) before its first fetch and
refuses otherwise (TR-19). Whatever is recorded first is what the corpus keeps forever — the
store is immutable, so preservation precedes volume.

### 7.2 Pre-registered recording universes
A recording batch is legal only under a UNIVERSE registered before any fetch: `{universe_id,
symbol_rule (the explicit panel list), date_rule (an explicit date range or rule), registered_at,
rule_commitment}` — appended to the vault ledger first. The recorded batch must be the rule's
complete output net of disclosed vendor failures; a verifier recomputes the expected set and refuses
cherry-picked batches (TR-4).

**The rule commitment is NONCED, and the rule stays hidden until whole-pool release (r7).** A bare
`sha256` of the rule is NOT a hiding commitment — `symbol_rule` and `date_rule` are low-entropy and
dictionary-enumerable, so a third party could verify guesses against the published digest. At
registration, therefore: canonicalize the COMPLETE `symbol_rule` + `date_rule`; generate a
high-entropy random **commitment nonce**; compute
`rule_commitment = sha256(nonce ‖ canonical_rule)`; persist the nonce PRIVATELY with the immutable
universe registration; serve ONLY `rule_commitment`. The nonce is never served pre-release.

**"Whole-pool release" is the release of every member of the ORIGINAL registered pool** — including
members the shard ledger never individually tracked. Disclosure is NEVER gated merely on "all
ledger-tracked shards exposed" (the iteration-11 audit reproduced a two-GET subtraction attack
against exactly that weaker gate). Only after whole-pool release may any surface reveal the
canonical `symbol_rule`, the canonical `date_rule`, and the nonce — at which point an auditor
recomputes `rule_commitment` and proves the rule never changed after registration. Every API, UI and
MCP surface is bound by this: none may serve enough rule-axis information to reconstruct the
withheld set before whole-pool release. The operator who registered the universe already knows the
rule; **that is not the threat model** — the protection is for third parties and blind evaluators.

**Traps (r7).** One ledger-tracked shard exposed while untracked pool members remain withheld ⇒
rule contents hidden · ALL tracked shards exposed but one untracked pool member withheld ⇒ still
hidden · after the final pool member is released ⇒ rule + nonce reveal and recompute EXACTLY to the
original commitment · a plausible-rule dictionary attack against the served commitment cannot
verify guesses without the nonce · no other surface serves the symbol or date axes pre-release.

**The Tier-B resolution order (preflight correction 2026-08-16 — a contract clarification, not
a methodology change).** Card 5.2's Tier-B mid-cap names are PROVISIONAL; its screening
CRITERIA are the contract and are re-evaluated at recording time. The mandatory order, which a
weak executor may not reinterpret:
1. evaluate the frozen Card-5.2 Tier-B screening criteria;
2. record, in the vault ledger: the screening criteria/spec hash, the screen's as-of
   timestamp, the input/provenance basis, the COMPLETE screening output, and the resolved
   Tier-B symbol list;
3. freeze that resolved list;
4. use the resolved list — and nothing else — as the Tier-B portion of `symbol_rule`;
5. register the recording universe;
6. record the vault-secret commitment and compute the opaque HMAC seal assignment (§7.3);
7. only then begin vendor fetches.
After universe registration: **no Tier-B re-screen, no substitution because a symbol is
inconvenient, no replacement from vendor availability or observed data** — a vendor failure is
a DISCLOSED per-chunk/per-symbol failure in the batch report, never a silent swap. The current
provisional names are never hard-coded as permanently valid; only the resolved, recorded list
of step 2 is.

### 7.2.1 Tier-B resolution — the frozen operational protocol (r10)

Everything in this subsection is PRE-RECORDING operational detail. **The six Card-5.2 screening
criteria are unchanged and are restated here verbatim only so the protocol is self-contained:**
market cap USD 2B–20B; price USD 15–100; trailing 30-session ADV ≥ 3M shares; median RTH quoted
spread ≤ 8 bps; primary US listing; no pending M&A. Recent market-cap moves MAY cause provisional
names to fail — that is the expected behaviour of a recording-time screen, never a reason to widen
a criterion.

**(a) Candidate universe.** The Nasdaq Trader symbol directories `nasdaqlisted` and `otherlisted`,
as of the screening cutoff. Chosen so the frozen numeric/market criteria perform the selection
rather than membership in an independently committee-selected index. Reproducibility requires
preserving the SOURCE SNAPSHOT, not merely its hash — a later reader must reproduce the exact
candidate universe after Nasdaq updates the live files, so the live URL is never a dependency.
Persist immutably at the cutoff: the exact raw bytes of both files; the SHA-256 of each raw file;
Nasdaq's embedded file-creation timestamp; the retrieval UTC timestamp; the parser/version hash;
and the resulting pre-filter membership hash.

**(b) Mechanical exclusions, applied BEFORE the six-factor screen** — ETF flag `Y`; test issue
`Y`; warrants; rights; units; preferred stock; funds/ETNs and other non-common-equity instruments.
The exclusion parser and its rules are frozen and tested before screening. **A security whose type
is ambiguous is never silently admitted:** it is marked `unresolved` and excluded, with provenance.

**(c) Primary US listing.** Passes only a common-stock / class-common-stock security registered
under Exchange Act §12(b) whose primary listed venue is Nasdaq, NYSE, or NYSE American. ADRs/ADSs,
preferreds, warrants, units, OTC securities and other non-common-equity instruments fail. The
frozen Nasdaq Trader snapshot is the listing-directory owner; SEC filing/cover-page exchange and
class information is the authoritative cross-check. **Any disagreement between the two is recorded
and FAILS CLOSED** — never resolved toward whichever source lets the candidate pass.

**(d) Market cap.** The latest SEC-reported common shares outstanding legally available as of the
cutoff × the frozen close basis defined below. Persist: CIK; accession/form; fact/concept; fact
period/end date; filing date; raw shares value; price source/session/raw close; derived USD market
cap.

*The source hierarchy (r11).* **Primary:** SEC CompanyFacts `dei:EntityCommonStockSharesOutstanding`,
legally available by the cutoff. **Fallback — ONLY when the primary is unavailable:** the latest
10-Q or 10-K filed and accepted by the SEC at or before the cutoff, using that filing's COVER-PAGE
shares-outstanding disclosure. Prefer the filing's own Inline-XBRL dimensional cover-page facts where
present — if CompanyFacts merely omitted the aggregation but the filing itself carries correctly
class-dimensioned `dei:EntityCommonStockSharesOutstanding` facts, consume those filing-level facts;
where the filing provides no usable structured cover-page facts but visibly states the count, a
deterministic cover-page extractor may read that same disclosure. The fallback exists because a
missing structured extraction must not silently turn this criterion into a test of XBRL tagging
quality; it recovers the SAME point-in-time quantity from the authoritative filing. **There is no
third source**, and `us-gaap:CommonStockSharesOutstanding` is explicitly NOT the fallback (a
balance-sheet fact with a different measurement date, stale in practice). Persist additionally for a
fallback extraction: form; accession; filing date; SEC acceptance timestamp; report period;
cover-page as-of date of the count; EVERY common-stock class disclosed with its class name and raw
outstanding value; extraction method; exact SEC document identity; and a content hash / evidence
excerpt locator sufficient to reproduce the extraction.

*Fail-closed, unchanged by the fallback.* The fallback is an EVIDENCE-RECOVERY mechanism, never a new
capitalization methodology. **Where a multi-class or otherwise ambiguous capitalization means one
listed ticker price × the filing's shares basis does not unambiguously represent issuer market cap,
`market_cap_status = unresolved` and the candidate FAILS CLOSED** — a candidate may legitimately
remain unresolved after the fallback. It is forbidden to sum classes and multiply by one class's
price, to use one class only, to substitute public float or weighted-average diluted shares, to infer
a synthetic class price, or to pick whichever treatment lands the issuer inside $2B–$20B. If neither
primary nor fallback yields an unambiguous point-in-time shares basis, the status is `unresolved`.

*The frozen close basis (r11 provenance correction).* r10 called this an "official close"; the
screening runner in fact uses **Yahoo Finance unadjusted daily `Close` for the most recent fully
completed trading session strictly before the screening cutoff**. That is the honest name for the
basis actually used, and it is the SAME basis for BOTH the USD 15–100 price criterion and the
market-cap multiplication. Persist the source, the session date and the raw `Close`. The price vendor
is never switched on the basis of a candidate's result.

**(e) ADV.** The arithmetic mean of raw share volume over the **30 most recent fully completed
regular US trading sessions strictly before the cutoff** — sessions, never 30 calendar days. The
exact 30-session list and input volumes are persisted.

**(f) Median RTH quoted spread** (previously undefined; closed here). The **5 most recent fully
completed regular US trading sessions strictly before the cutoff**. For candidates still eligible
after the cheaper non-spread filters, compute the median quoted spread in bps across eligible
in-effect RTH NBBO observations over those five sessions, on the existing canonical quote basis.
No hand-picked days. **Those five sessions are SCREENING/EXPOSED data and may NEVER be used as
J-06 sealed historical-OOS recording dates.** The exact five-session list and source provenance are
persisted. Identity-bearing progressive results are not served while this screening fetch runs.

**(g) Pending M&A.** A candidate FAILS iff, at the cutoff, public SEC/issuer evidence establishes a
definitive, announced merger / acquisition / business-combination / take-private transaction
involving the candidate that remains PENDING rather than closed or terminated. Rumour or
speculation alone does not fail; a completed or terminated transaction does not remain a failure
merely because it was recent. Search protocol: relevant filings over the prior 24 calendar months,
PLUS the most recent 10-K and every later 10-Q/8-K through the cutoff. Flagged for transaction-
status inspection: 8-K Item 1.01; 8-K Item 2.01; PREM14A; DEFM14A; S-4 / F-4; SC 13E-3; and
equivalent issuer-IR definitive-transaction announcements. **An 8-K Item 1.01 alone is NOT a
failure — it is a search hit requiring transaction classification.** Persist: filings searched;
accession numbers; dates; relevant transaction status; a deterministic pass/fail explanation; and
the retrieval timestamp. **"No search hit" without the complete frozen search record is not
evidence.**

**(h) Deterministic resolution.** Ticker-alphabetical selection is REJECTED — deterministic, but it
imports an irrelevant lexical bias. The five provisional Card-5.2 names `DKNG`, `ETSY`, `AFRM`,
`SOFI`, `RKLB` are SEEDS, not grandfathered passes: all five face the identical frozen six-factor
screen. Then: (1) retain passing provisional names in their already-documented order; (2) if fewer
than three pass, fill the missing slots from other eligible exchange-universe survivors; (3) rank
replacement survivors by ascending `sha256("rapid-microscope-tier-b-r10:" + normalized_ticker)`;
(4) take only enough replacements to reach exactly three Tier-B names for the J-06 starter tranche.
No human choice after results are visible. **If fewer than three eligible Tier-B names exist in
total: STOP** — never loosen a criterion, never manually substitute.

**(i) The frozen minimum starter panel.** Once the three Tier-B names resolve, the J-06 minimum
legal starter panel is exactly eight symbols, following the existing frozen Tier-A/Tier-C ordering
so no post-screen human selection remains: `PG`, `AAPL`, `MSFT`, `NVDA`, the three resolved Tier-B
names, and `SPY`. With ten dates this is exactly **80 planned symbol-days** before disclosed vendor
failures (the ≥8-symbol and ≥10-date floors are Cartesian under §7.2, so 80 is the true minimum —
Card 5.2's "~30–50" prose estimate is arithmetically unreachable and is superseded here).

**(j) Screen-once discipline.** The candidate universe, source hierarchy, cutoff, criteria, and
selection rule are all frozen BEFORE the screen runs, and the screen then runs EXACTLY ONCE. The
complete provenance record of §7.2 step 2 — including every candidate's six raw criterion inputs,
per-criterion pass/fail, all failures, the deterministic ordering, and any `unresolved` candidate —
is persisted and immutable before the resolved list may become the Tier-B portion of `symbol_rule`.
No hidden manual exclusions.

### 7.2.2 Batch verification is TYPED, and a disclosed pool position is spent (r12)

**Disclosed vendor failures must carry provenance.** §7.2's verifier recomputes the expected set
and accepts the batch only net of disclosed vendor failures. Those failures are an INPUT backed by
recorder run evidence — a terminal, unrecovered per-chunk/per-symbol failure recorded by the run
that hit it — never a set computed from what happens to be missing. A caller that derives
`disclosed_failures` by subtracting the recorded set from the expected set has written a check that
cannot fail; that is not TR-4. The generic verifier stays a primitive that validates a batch against
a rule net of failures its caller VOUCHES for; the vouching belongs to the caller, and for a
recording universe the caller must derive it from run evidence and expose no parameter for it.

**Every registered pair without a genuine shard has exactly one typed condition:**

| condition | meaning | acceptance |
|---|---|---|
| `unrecovered_vendor_failure` | a terminal vendor failure, with the run's own failure detail as evidence, never later recovered | the ONE lawful disclosure (§7.2) |
| `legacy_dataset_collision` | the pair is occupied by a dataset this recorder did not write | **blocks** |
| `unexplained` | no genuine shard and no evidence of any kind | **blocks** |

A collision DOMINATES vendor-failure evidence for the same pair: otherwise one vendor hiccup on a
collided pair would restore the laundering route. Acceptance is false while any registered pair
lacks a genuine shard for any reason other than the first row.

**What counts as a genuine shard** is ONE predicate shared by the recorder walk (what may be
skipped as already-recorded) and by acceptance (what may be counted): the recorder's own
`schema_basis`, the exact registered `(symbol, session_date)`, the required full regular-session
window, a valid content checksum, and a healthy store record. Two definitions is how a legacy
partial came to be counted as "already recorded" by one and rejected by the other.

**Repairing an already-registered universe.** A collision discovered after registration is repaired
by COMPLETION, never substitution and never a second universe: record the same registered pair
genuinely, through the same recorder, into the same universe, with the original nonce, rule
commitment, vault-secret commitment and HMAC assignment untouched. The colliding legacy dataset is
immutable, stays on disk, stays permanently exploratory, and stays reported as a collision — it is
never deleted, rewritten, relabelled, or counted. The pre-registration STOP is unchanged and
unweakened for every FUTURE registration.

**Pool-position disclosure incidents.** Revealing whether a specific pool member is or is not
HMAC-selected, outside the `sealed → assigned → exposed` lifecycle, is a leak even when the position
is NOT selected — it is public information an attacker may condition on. Such a disclosure is
recorded as a named, immutable incident in its own hash-chained ledger (a fourth chain, for the same
structural reason the screen-provenance chain is separate: an incident row must never resolve as a
universe registration or a lifecycle transition). Recording an incident moves no shard's exposure
state — no new lifecycle transition exists. The consequence is PERMANENT: the disclosed position may
never receive sealed, blind or historical-OOS credit, enforced at `assign_shard`, which is the
transition that grants that credit. Its dataset remains a lawful member of the recorded tranche for
corpus-size and coverage purposes only. **No second member is ever disclosed to "balance" a leak.**
A disclosure of a SEALED member's identity has NO lawful representation here and must not be
recorded as if contained — it escalates to the owner. After any incident, TR-2 is re-run with the
disclosure treated as attacker-known: no still-unexposed selected shard's identity may become
determinable with certainty, which requires strictly more unknown positions than remaining selected
shards (otherwise the hidden set is pinned) and at least two candidate identities per sealed row.

### 7.3 Split vs seal — two independent assignments
- **Split** (train/holdout tag, Card 5.2's published rule, unchanged): `holdout` iff the last hex
  digit of `sha256(f"{symbol}:{YYYY-MM-DD}")` ∈ {0,1,2}.
- **Seal** (vault membership, NEW and opaque): sealed iff the last hex digit of
  `HMAC-SHA256(vault_secret, f"{symbol}:{YYYY-MM-DD}")` < `VAULT_SEAL_HEX_BELOW`. The secret
  lives OUTSIDE the repo at the path named by `TAPEOLOGY_VAULT_SECRET_FILE`, is never committed,
  logged, or served; its commitment `sha256(vault_secret)` is recorded in the universe
  registration, so assignment is auditable after reveal while sealed membership cannot be
  inferred from public information before exposure. Losing the secret orphans assignment audit —
  the commitment row says so; the shards themselves stay sealed.

### 7.4 Shard lifecycle (one-way)
`sealed → assigned → exposed`, recorded in a hash-chained append-only exposure ledger with
timestamps; no transition back; deletion impossible. Assignment binds ONE candidate family LINE
to the shard, keyed on the COMPUTED `family_root_id` (§5.1) — **sealed exposure is
root-family-level and single-shot**: a renamed or re-parameterized family computes the same
root and can never treat the same shard as fresh, and a failed sealed verdict is a permanent
root-family fact carried in every later export bundle (TR-12, TR-20).

**The exploratory release path (r14) — a SIBLING terminal state, not a fourth step.** The sealed
path above is reachable only by an HMAC-SELECTED member. §7.5 point 7's other disjunct — a shard
"actually **exposed for exploratory use**" — applies to the pool's NOT-selected members, and is
implemented as the terminal state `exploratory_released`:

`unresolved pool member → exploratory_released` (append-only, one row, no transition back)

Its refusals are recomputed at the transition, never asserted by the caller: the universe must be
registered; the supplied secret must match that universe's own committed `vault_secret_commitment`;
the pair must be a member of `expected_recording_pairs()`; **the HMAC must independently recompute
to NOT SELECTED**; the dataset must carry no shard row at all (which is what stops a SEALED member
taking the shortcut, and stops a double release); and the release must not breach §7.2.2's
residual-uncertainty floor.

A released row is **never sealed, bound to no family, consumes no single shot, and earns no sealed
or blind credit** — `family_root_id` and `assigned_at` are permanently `null`, `sealed_at` is
`null`, and `SEALED_PASS_RULE_V1` condition 5 is structurally unsatisfiable for it. It serves its
symbol, session date and raw `content_checksum` (so the salted commitment verifies against it, r3
point 2), plus an explicit `release_basis` and `sealed_credit: false`.

**Releases are self-limiting, and this binds hard.** Each release publicly discloses one pool
position as NOT selected. Release every unselected member and the unknown positions collapse onto
exactly the still-hidden selected set, pinning every sealed shard by subtraction. §7.2.2's floor is
therefore enforced at this transition: **at least one unselected member remains withheld as a decoy
while any selected member is still sealed.** Whole-pool release (§7.2) becomes reachable — for the
first time, since before r14 a ~25 %-sealed universe could never satisfy it at all — but only after
every selected member has itself been exposed, which is what lifts the floor.

### 7.5 Sealed metadata minimization — OPAQUE pre-exposure (r3)
While sealed, a shard serves only: a surrogate `shard_id`, its `universe_id`, a coarse size
bucket (order of magnitude), a **salted** commitment, `sealed_at`, and the exposure state.
**Symbol and date range are NOT served pre-exposure** — they would let bar-level public
outcomes (desk/playbook, served for every date) be looked up against sealed membership; both
are revealed at ASSIGNMENT and recorded in the exposure ledger. Exact event counts, bytes, and
any feature/outcome aggregate are withheld until exposure.

**Join resistance is the actual requirement (r3).** Field-level minimization is not enough: a
served value that merely *identifies* the shard on another surface leaks everything that
surface serves. Therefore:

1. **Surrogate identity.** The served `shard_id` is a vault-minted opaque token bearing no
   derivable relation to the `DatasetStore` dataset id (not the id, not a hash of it, not a
   prefix). The surrogate → dataset-id mapping lives only in the sealed-side ledger and is
   revealed at assignment.
2. **Salted commitment.** The pre-exposure commitment is `HMAC(vault_secret, content_checksum)`
   — not the raw `content_checksum`, which is served publicly per dataset and would join
   directly. The raw checksum is revealed at exposure, at which point the salted commitment can
   be re-derived and verified against it, preserving auditability.
3. **Refusal on the pre-existing surfaces.** `GET /research/datasets` / `/research/datasets/{id}`,
   the `datasets` MCP tool, and any `get_endpoint` path resolving to them REFUSE a sealed
   dataset id with a typed refusal until its exposure is recorded. The refusal states only that
   the id is sealed — never symbol, window, counts, or universe.
4. **Readiness serves tranche AGGREGATES only, on BOTH sides (r5).** While ANY member of a
   recorded pool remains unexposed, readiness serves counts and coarse per-universe totals and
   NOTHING per-shard — not for the sealed side and **not for the exploratory side either**. A
   complete identity-labelled list of the non-sealed side is forbidden precisely because its
   complement against the registered universe (§7.2, known to the operator by construction)
   reveals the withheld set. No served artifact may present a complete identity-labelled
   partition of "exploratory" versus "sealed".
5. Recorder run logs commit per-shard identity and counts by hash while sealed.
6. **Corpus enumerators honour the seal (r4).** A refusal wired only into a route is bypassed by
   any module that enumerates the store itself. Therefore every corpus-wide enumerator —
   `edge_report._all_datasets`, `pnl_scan._split_datasets`, the Scout's corpus manifest, the
   snapshot builder and its compute manager, and any future sibling — EXCLUDES withheld shards
   (state ≠ `exposed`) at its single `DatasetStore.list()` choke point, and **DISCLOSES the
   exclusion**: a `withheld_excluded` count (never the ids) travels into the report body and
   into any append-only row the run writes. Silent exclusion is forbidden — these call sites
   already hold that "a partial report is a misleading report", and the era's denominator rail
   forbids a corpus that shrinks without saying so. A run whose entire eligible corpus is
   withheld reports that honestly rather than emitting an empty-but-shaped result.
7. **The opaque research pool (r5).** A newly recorded tranche is ONE POOL. Membership in it is
   public (the operator registered the universe); **position within it is not**. A shard's
   identity becomes public ONLY when that shard is actually exposed for exploratory use or
   assigned to a candidate family — at which moment it leaves the pool through the normal
   exposure surfaces governed by the exposure ledger. Unused pool members stay opaque and
   **indistinguishable from one another**: no served id, ordering, index, timestamp, size, state
   label, or per-shard statistic may separate an unexposed exploratory shard from an unexposed
   sealed one. The internal vault and exposure ledgers retain exact identities and HMAC
   decisions for audit; no API, UI, or MCP surface may serve enough of them to reconstruct the
   hidden partition. If an implementation requires every non-sealed shard to become individually
   visible immediately after recording, the IMPLEMENTATION changes — decoy recordings and
   accepted residual leakage are both rejected.
8. **The HMAC's role, restated (r5).** `HMAC(vault_secret, …)` is an INTERNAL deterministic and
   auditable assignment mechanism. It is not, and must never be served as, a public global
   partition — a partition whose complement is computable is not a vault.

No pre-exposure field may equal, contain, or be derivable from any field the public surfaces
serve for the same shard, and no exploratory statistic may be computed from one. **The
governing test is a deterministic inference trap (r5), not a field whitelist: given the
registered universe (§7.2) plus EVERY public artifact the system serves — readiness, recorder
progress, datasets, backtests, PnL ledger, Scout, walk-forward, graduation, MCP, UI — an
attacker must not be able to determine the identity of ANY still-unexposed vault-eligible shard
with certainty.** TR-2 proves this by construction — and it exercises the operator compute acts
(snapshot build, Scout run, edge report, PnL sweep) BEFORE sweeping, so it cannot pass merely
because the rig computed nothing.

### 7.6 The starter tranche (this era's recording acceptance)
Minimums (all must hold): ≥30 symbol-days; ≥8 distinct Card-5.2-panel symbols including `PG`,
≥3 Tier-B mid-caps, ≥1 Tier-C ETF; ≥10 distinct trading dates spanning ≥6 calendar weeks; no
single date >20% and no single symbol >25% of the tranche's symbol-days; ≥60% full-session
windows (Card 5.2's 09:30–11:00 + 15:00–16:00 ET fallback windows allowed for the remainder,
window provenance recorded). Per-shard completeness reporting: feed, trade/quote counts (hash-
committed while sealed), coverage gaps, classification readiness (`fallback_frac`), checksum,
exposure state. **The ~150-symbol-day research-readiness gate is neither lowered nor satisfied by
this tranche** — readiness reporting states per-study whether its predeclared floor is met, and
any claim below floor fails closed.

### 7.7 The legacy corpus
The 12 pre-existing tick symbol-days (18 datasets) are **permanently exploratory** — never
sealed, never `historical_oos`, regardless of whether an individual file happens never to have
been analyzed. Retrospective sealed shards (past dates recorded fresh) carry the standing
disclosed caveat that bar-level outcomes of their dates are public in the desk/playbook corpus;
a **bar-reconstructibility diagnostic** (a fixed regression recipe of each feature family on
same-session bar features, computed on exploratory data) is REPORTED beside sealed evidence —
it is a diagnostic only, **never a gate, never tunable, and never an authority**; independence is
decided by the deterministic provenance/exposure rules above alone.

### 7.8 Vault-ledger integrity — fail closed, recover only on evidence (r6)

**The invariant: unknown exposure history may NEVER be interpreted as "never exposed."** A
truncated tail that silently makes shards look fresh is the worst failure this system can have.

Every vault/exposure predicate calls `verify_chain()` FIRST. Any verification failure raises a
typed refusal and halts ALL vault work — no sealing, no assignment, no exposure check, no sealed
evaluation, no graduation — until a lawful recovery completes. There is no warn-and-continue path,
and operator attestation alone can NEVER certify missing history; the attestation is audit
metadata, not evidence.

**Lawful recovery** (the only way back) must, in order: halt vault/sealed work · record the
corruption event separately and immutably · preserve the corrupt ledger BYTE-FOR-BYTE for forensics
· identify the last verified chain row · reconstruct the missing suffix from trusted immutable
sources (durable recorder/vault operation artifacts, immutable §8.1 evaluation artifacts,
append-only graduation/export records, or a backup whose hash was committed BEFORE the corruption)
· verify the reconstruction is internally consistent and that every exposure, assignment and
evaluation event is accounted for · write a NEW ledger epoch/recovery record citing the corrupt
ledger hash, last verified row + hash, reconstruction sources + hashes, recovered suffix hash,
operator identity and time, and an explicit recovery reason. Only then may predicates resume.

**If the missing suffix cannot be PROVEN complete, recovery HALTS — full stop (r8).** The owner
deleted the graded resume branch after the iteration-13 review proved it unsafe: the tail anchor
carries a row COUNT and the final row's hash but no per-row identity, so a same-length suffix
naming an unrelated dataset satisfied the check while the genuinely destroyed shard vanished from
every ledger, `verify_chain()` reported clean, and `seal_shard` would re-seal it fresh under
another universe. **Row-count equality is not evidence of identity and must NEVER authorize
recovery.** Therefore, for this era:

- any missing, truncated, or tampered suffix keeps EVERY vault predicate fail-closed;
- a reconstructed suffix is accepted ONLY if it can be proven against pre-existing trusted
  commitments; matching row count alone is never sufficient;
- operator attestation cannot substitute for missing identity evidence;
- no affected shard becomes fresh, sealable, assignable, or `historical_oos` merely because the
  reconstructed ledger now verifies internally;
- if completeness cannot be proven, the affected vault/tranche stays BLOCKED.

Graded recovery returns only under a FUTURE named revision built on a real identity commitment —
and that commitment must NOT be a mere SET of dataset ids: it must preserve enough to prove the
exact historical suffix (at minimum ordered row/event identities, preferably a canonical
checkpoint/manifest or Merkle-style commitment tied to the ledger chain). That migration is not
designed ad hoc inside a fix. **Safety wins over degraded availability: unknown or unprovable
exposure history means the vault is unavailable, never "fresh".**

**Traps.** Truncating the tail ⇒ all exposure predicates fail closed · mutating an interior row ⇒
fail closed · replacing the ledger with a last-known-good prefix ⇒ still fail closed when a later
committed checkpoint proves history should exist · a successful hash-pinned reconstruction restores
the EXACT prior exposure state · an unverifiable recovery can never make an affected shard fresh
again.

---

## 8. Graduation (`micro_graduation.py`)

States, strictly ordered; every transition is an append-only ledger event with full provenance:

1. `exploratory` — any ledgered candidate. Claims: descriptive only.
2. `walkforward_survivor` — a constant-rule sequence satisfying `WF_SURVIVOR_RULE_V1` (§6.6)
   in full: sufficient `historical_oos` + `rule_process` folds, the sign-agreement floor, the
   economic floor in the registered direction, no opposite-direction fold pass, no voiding
   event. Diagnostic-class and `operator_process` folds contribute nothing.
3. `sealed_survivor` — additionally passed its single-shot root-family-level sealed-shard
   evaluation (§7.4, keyed on `family_root_id`) under a spec frozen before assignment.
4. `referee_handoff_ready` — the export bundle exists and validates: frozen spec hash;
   `family_root_id` lineage; the COMPLETE exposure provenance (every ledger trial including
   kills, every fold with its evidence class AND process label, every shard touched, every
   failure); proposed confirmation boundary; family/multiplicity metadata (union-N, sibling
   candidates, prior sealed verdicts of the root family). **This state does NOT imply the current Referee can register
   or adjudicate the candidate**: a flow-context predicate requires a FUTURE named revision of
   `docs/referee-statistical-spec.md`; where a candidate maps onto the existing referee
   vocabulary (setup × side × existing context predicates × existing measures), the bundle is
   registrable through the existing operator act unchanged. The Referee's modules are
   byte-untouched this era either way.

No state ever moves backward except by a voiding event (§6.2), which is itself permanent history.

### 8.1 The sealed verdict has one owner — `SEALED_PASS_RULE_V1` (r6)

**The ledger owns history; the evaluator owns the answer.** A caller-supplied `passed: bool` is
inadmissible for a single-shot permanent verdict. Sealed evaluation has exactly ONE scientific
owner module, `micro_sealed_evaluation.py`; `micro_graduation.py` and `vault.py` remain
persistence and transition machinery and neither accepts nor invents the scientific answer.

**The evaluator's mandatory sequence** (any step failing ⇒ typed refusal, never a verdict):
1. require an ASSIGNED sealed shard and a candidate spec frozen BEFORE that assignment;
2. load the candidate's canonical registered spec and verify its `spec_hash`, `family_root_id`,
   outcome basis, sidedness, economic floor, and the sample/breadth floors below;
3. obtain the shard ONLY through the sanctioned accessor/exposure path (§6.1, §7.4);
4. RECOMPUTE the sealed outcomes from the canonical snapshot/outcome machinery — a
   caller-computed effect value is never authoritative;
5. derive the verdict deterministically from `SEALED_PASS_RULE_V1`;
6. persist an immutable **evaluation artifact** (below);
7. pass ONLY that artifact's id + hash to the graduation transition.

**`SEALED_PASS_RULE_V1` (frozen; r9 replaces condition 1).** A (root family, shard) evaluation
`passes` iff ALL of:
1. **(r9) the shard's recomputed observations meet the SEALED-SPECIFIC pinned floor**
   `SEALED_MIN_OBSERVATIONS` (§1). The walk-forward per-fold breadth floors are **NOT** reused
   here: a sealed shard is ONE symbol × ONE session-date (§7.3), so session and symbol breadth are
   inapplicable at shard scope and MUST be recorded explicitly as
   `min_signal_sessions: not_applicable_single_shard` and
   `min_symbols: not_applicable_single_shard` — **never silently set to 1**. Below the observation
   floor the verdict is `insufficient`, which is neither a pass nor a fail and consumes the single
   shot ONLY if the shard was exposed (an exposure is irreversible either way).
   **No sufficiency value may be sourced from the candidate or caller spec.** A caller supplying
   floors, altered thresholds, or any equivalent override is REFUSED — the evaluator owns the rule.
   *Scientific rationale (record it wherever the rule is served): the walk-forward stage owns
   BREADTH — `WF_SURVIVOR_RULE_V1` establishes temporal, session and symbol breadth before a
   candidate may reach the sealed stage at all. The sealed stage owns UNTOUCHED REPLICATION on one
   hidden symbol-day. Mechanically reusing breadth floors at shard scope conflates the two.*
2. the session-clustered effect lies in the family's REGISTERED direction (§5.1 sidedness) —
   **i.e. is POSITIVE in canonical signed space (§0, r13). The observations were direction-signed
   ONCE by the canonical outcome machinery step 4 recomputes them from, so a successful SHORT
   candidate arrives positive exactly as a successful long one does; this condition never
   re-derives a sign from `sidedness`.** The observations must also PROVE their unit before they
   are pooled — a caller-supplied magnitude with no declared unit is refused here, before any
   verdict is derived and before the single shot is consumed;
3. its magnitude ≥ the family's own pre-registered economic floor (§5.5) — the same floor the
   walk-forward applied, not a new one, **with both the effect's unit and the floor's unit proved
   rather than assumed (r13)**;
4. the evaluation rule id/version/hash recorded at assignment is byte-identical to the one applied
   (a rule changed after assignment fails CLOSED). **(r9) The rule hash is computed from the
   SEALED-SPECIFIC rule actually executed; it must never certify one set of floors while execution
   applied another** — the artifact records the rule definition/hash AND the actual applied values,
   and the two must agree byte-for-byte with runtime behaviour;
5. the shard's evidence class is `historical_oos` and its process label `rule_process` (§6.7/§6.8).
Anything less is a FAIL, and a fail is permanent for the root family (§7.4). There is no
discretionary override and no partial credit.

**The evaluation artifact** (immutable, hash-addressed, sufficient to reproduce the verdict):
candidate + spec identity and hashes · `family_root_id` · shard identity and checksum AFTER lawful
assignment · evidence class · process label · outcome basis · n / sessions / symbol breadth ·
effect and economic-floor inputs · registered direction · rule id/version/hash · the deterministic
verdict · the closed-vocabulary failure reason when not a pass.

**Traps (all deterministic).** A caller-asserted boolean is impossible/refused · mutating ANY
evaluation input changes the artifact hash and invalidates the transition · an unregistered rule,
or one changed after assignment, fails closed · re-running the evaluator over identical inputs
yields a byte-identical artifact and verdict · a second sealed evaluation for the same
(`family_root_id`, shard) is refused · a failed verdict travels in every later export bundle.

### 8.2 The proposed confirmation boundary — lineage-wide (r6)

Survivor rows are NOT the basis; the LINEAGE is. Define:

- **`lineage_data_frontier`** = `max(observed_through)` across every evidence item ever touched by
  the computed `family_root_id` lineage — surviving candidates, killed and superseded siblings,
  walk-forward folds of ANY verdict, diagnostic and `operator_process` folds, assigned/exposed
  sealed shards including failed and `insufficient` evaluations, and any other outcome-bearing read
  in the exposure registry (§6.7). `observed_through` is used, never anchor/event time, so a
  deferred construct cannot backdate the frontier.
- **`evidence_safe_boundary`** = `lineage_data_frontier` + the applicable dependency embargo (§6.3),
  applied in its registered session/market semantics — never as an ad-hoc wall-clock delta.
- **`proposed_confirmation_boundary`** = the first eligible market/session boundary STRICTLY after
  `max(evidence_safe_boundary, handoff_created_at)`.

At actual Referee registration the immutable `confirmation_start_boundary` must be no earlier than
BOTH the bundle's proposed boundary and the Referee's own registration-time boundary:
`final = next_eligible(max(proposed_confirmation_boundary, referee_registration_boundary))`.
**Backdating is never permitted.**

The bundle persists the whole derivation: `lineage_data_frontier`, the evidence ids contributing to
the max, `frontier_observed_through`, the embargo rule id and value, `evidence_safe_boundary`,
`handoff_created_at`, and `proposed_confirmation_boundary`.

**Traps.** A killed sibling of the same `family_root_id` with a LATER `observed_through` than the
survivor must push the proposed boundary past it — proving lineage knowledge cannot be laundered
through candidate selection. A deferred feature with `anchor_at < observed_through` must move the
boundary by its `observed_through`.

---

## 9. The trap suite (all deterministic, all in CI)

| Trap | Asserts |
|---|---|
| TR-1 prefix/tail | Truncated-dataset snapshot rows byte-identical to the full run's prefix (3 cut points incl. i=1); appending one tail event changes no prior row |
| TR-2 sealed sweep (r3: join-resistance; r5: inference trap) | Every registered route + MCP tool serves only §7.5 metadata (or a typed refusal) for a sealed shard — AND the sweep is adversarial, not a whitelist review: seal a fixture shard, collect every value any surface serves for it pre-exposure, and assert none equals, contains, or derives the dataset id, raw `content_checksum`, symbol, window, or event counts. Explicitly includes `/research/datasets{,/{id}}`, the `datasets` MCP tool, `get_endpoint`, `micro_readiness` (no per-shard row at all, EITHER side) and the recorder progress path. **r5 inference trap** — the decisive assertion: record a fixture pool under a registered universe (§7.2) whose symbol rule and date rule the trap KNOWS, expose a proper subset, then assert that the union of every public artifact (readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward, graduation, MCP, UI) plus that known universe leaves ≥2 candidate identities for every still-unexposed vault-eligible shard — i.e. no unexposed shard is identifiable with certainty, and no complete identity-labelled exploratory/sealed partition is derivable by subtraction · **r12 composed disclosure**: with one pool position publicly disclosed as NOT selected (§7.2.2), no served surface starts identifying pool pairs, the incident record itself is never served, and the residual space still leaves strictly more unknown positions than remaining selected shards — counter-case: disclosing every non-selected position DOES pin the hidden set |
| TR-3 accessor fence | Origin-T accessor refuses reads > T with a typed error; corpus aggregates exclude > T exactly; import-ban: only `micro_accessor` opens snapshot/vault data paths |
| TR-4 cherry-pick refusal | A recording batch ≠ its universe rule's computed set (net of disclosed failures) is refused. **r12 — the disclosed set may not be manufactured by arithmetic:** a registered expected pair + a legacy-dataset collision + ZERO vendor-failure evidence + no genuine shard must NOT pass by inserting that pair into a caller-supplied `disclosed_failures` set through the production verification path (the production caller exposes no such parameter and derives the set from recorder run evidence) · a pair that failed and was later recorded is not an unrecovered failure · a collision DOMINATES vendor-failure evidence for the same pair · counter-test: the pre-fix subtraction, run directly against the generic primitive, DOES pass — so the refusal is a fix, not a tautology |
| TR-5 class mixing | Pooling `historical_exposed_diagnostic` with `historical_oos` rows in one statistic is refused; diagnostic folds contribute zero to graduation |
| TR-6 purge exactness | A planted label crossing a fold boundary fails the build; session-truncation asserted per fold |
| TR-7 stale identity | Snapshot cache MISSES on a changed fingerprint-relevant config field and on a mutated feature-module byte (source-hash) |
| TR-8 screening calibration | On an autocorrelated known-null fixture (200 seeds), screen pass-rate ≤ 1.5 × `SCOUT_SCREEN_ALPHA`; the banned plain row-shuffle demonstrably fails this fixture (counter-test) |
| TR-9 econ-floor ordering | A candidate whose econ-floor inputs were read before its spec registration is refused; the floor formula hash predates the first outcome read |
| TR-10 pool invariance | Adding 100 null candidates at an origin changes no prior candidate's fitted threshold or pass/fail |
| TR-11 ledger integrity | Union-N spans grid versions (v1 N=40 + v2 N=25 ⇒ disclosure N=65); in-place edit of row k breaks chain verification at k |
| TR-12 sealed single-shot | Second evaluation attempt of the same family on the same shard is refused; the failed verdict appears in the family's later export bundle |
| TR-13 geometry freeze | A second geometry on the same corpus is refused without a voiding event; the voiding event clears every survivor state of that corpus-era |
| TR-14 rule identity | A per-origin refit under an unchanged fitting rule does NOT start a new sequence; changing the rule string DOES |
| TR-15 tick refusal | The fold engine pointed at the 18-dataset corpus returns the typed floor-refusal naming the failed minima — never an empty fold report |
| TR-16 end-to-end oracles | A synthetic known-null corpus survives nothing end-to-end (Scout + folds); a synthetic planted-effect corpus is recovered with the planted sign and magnitude within tolerance (mid-basis primary); byte-identical rerun |
| TR-17 future-event availability | (a) every row with `observed_through` after `anchor_at` has `available_at` = the `observed_through` instant; (b) truncating a dataset at T reproduces byte-identically exactly the rows with `available_at` ≤ T — none later; (c) a planted outcome starting before its conditioning set's max `available_at` is refused by the outcome join |
| TR-18 units gate | A fixture with `quote_size_unit: "unverified"` (and a mixed-unit pool) refuses every cross-basis feature with a typed error; the verified twin serves them; no silent normalization path exists (source-scan) |
| TR-19 preservation prerequisite | The recorder refuses to start any universe recording unless the row schema carries the Card-5.1 preservation fields and the §2.6 stamping; a freshly captured fixture round-trips conditions/exchange; every legacy fixture loads byte-identically with its checksum verifying |
| TR-33 pool-position disclosure (r12 §7.2.2) | `assign_shard` refuses a disclosed pool position permanently, while an undisclosed one still assigns normally · an incident is idempotent on its id and refuses a conflicting rewrite · a claimed SEALED-member leak is REFUSED rather than recorded as contained · the incident chain is a fourth, separate ledger that no universe/shard predicate can resolve |
| TR-20 root lineage | A re-registered family with the same (feature family, context kind, outcome family) triple COMPUTES the same `family_root_id` (the rename attack is refused at the sealed door); a genuinely different triple computes a different root |
| TR-21 process label | A sequence containing a logged operator selection after any fold reveal is `operator_process` and is refused at `walkforward_survivor`; a pre-reveal registered shortlist keeps `rule_process` |
| TR-22 exposure registry | A spec registered after a logged serving of its validation window is auto-classed `historical_exposed_diagnostic`; the registry's r2 initialization marks every playbook-corpus and legacy-tick window exposed |
| TR-23 sealed-verdict ownership (r6 §8.1) | A caller-asserted `passed` boolean is impossible/refused · mutating any evaluation input changes the artifact hash and invalidates the transition · a rule unregistered, or changed after assignment, fails closed · re-running the evaluator on identical inputs yields a byte-identical artifact and verdict · a second sealed evaluation for the same (`family_root_id`, shard) is refused · a failed verdict travels in every later export bundle |
| TR-24 lineage boundary (r6 §8.2) | A KILLED sibling of the same `family_root_id` with a later `observed_through` than the survivor pushes `proposed_confirmation_boundary` past it (lineage knowledge cannot be laundered through candidate selection) · a deferred feature with `anchor_at < observed_through` moves the boundary by its `observed_through` · the final Referee boundary is never earlier than either the proposed or the registration boundary |
| TR-25 vault-ledger integrity (r6 §7.8) | Tail truncation ⇒ every exposure predicate fails closed · interior-row mutation ⇒ fails closed · a last-known-good prefix still fails closed when a committed checkpoint proves later history existed · a hash-pinned reconstruction restores the exact prior exposure state · an unverifiable recovery never makes an affected shard fresh again — **under r8 that means the recovery is REFUSED and the tranche stays blocked** (the `exposure_unknown` state this row originally named was deleted with r8's graded-resume branch; see TR-29) |
| TR-30 sealed sufficiency is evaluator-owned (r9 §8.1) | A spec carrying `floors={1,1,1}` is REFUSED and can never make one observation pass · 29 sealed observations ⇒ `insufficient` · 30 otherwise-valid observations ⇒ sufficiency can clear · session and symbol breadth are recorded `not_applicable_single_shard`, never silently 1 · changing ANY caller floor field cannot change the verdict · the artifact's `rule_hash`, its applied-floor values, and runtime behaviour agree byte-for-byte · an `insufficient` verdict still CONSUMES that family's single sealed shot on the assigned shard (no fresh shard on thin data — that would be repeated holdout sampling) |
| TR-29 recovery is halt-only (r8 §7.8) | The demonstrated attack: seal `d-1`/`d-2`/`d-3`, destroy the row containing `d-3`, present a SAME-LENGTH reconstructed suffix containing an unrelated `d-fake` ⇒ recovery REFUSES, and `d-3` never becomes sealable again under another universe · same row count with REORDERED identities ⇒ refuse · same row count with a SUBSTITUTED identity ⇒ refuse · same final-row count but a missing earlier exposure ⇒ refuse · a cleanly internally re-chained forged suffix is NOT proof of historical completeness · operator attestation never substitutes for missing identity evidence |
| TR-27 nonced rule commitment (r7 §7.2) | One ledger-tracked shard exposed while untracked pool members remain withheld ⇒ rule contents hidden · ALL tracked shards exposed but one untracked ORIGINAL-pool member still withheld ⇒ still hidden · after the final pool member is released ⇒ `symbol_rule` + `date_rule` + nonce reveal and recompute EXACTLY to the registered `rule_commitment` · a plausible-rule dictionary attack against the served commitment cannot verify guesses without the nonce · no other API/UI/MCP surface serves the symbol or date axes pre-release |
| TR-28 coarse pre-release volumes (r7 §7.1, NON-LIVE surfaces) | A one-symbol-day run while withheld ⇒ no exact trade/quote/byte count appears on ANY surface · a multi-shard pool ⇒ coarse bucket labels only, never rounded numbers · expose one shard and re-query ⇒ the remaining withheld counts cannot be solved exactly from the before/after response pair (differencing resistance) · buckets never narrow as the pool shrinks · the final ORIGINAL-pool member released ⇒ exact totals may be served. **LIVE recorder progress is governed by TR-32 instead, which serves no volume field at all.** |
| TR-32 live-progress composition (r11 §7.1) | Poll/observe any live progress transport (REST, CLI, UI, MCP) frequently enough that `chunks_done` advances by exactly one, and difference every served field against the deterministic operator-known plan ⇒ NO specific chunk's realized success/failure is recoverable with certainty · a coarse volume bucket TRANSITION across a single-chunk advance must not prove that chunk was `fetched` (running totals advance only on fetch) · bucketing the outcome counters is NOT sufficient (an exact 0→1 boundary still pins the first failure) · internal exact state and the TERMINAL TR-4 disclosed-failure list remain lawful |
| TR-34 measurement semantics (r13 §0/§4/§5.5) | Price-scale invariance: $10.00→$10.05 and $100.00→$100.50 produce the IDENTICAL outcome (+50 bps), and $10.00→$10.05 vs $100.00→$100.05 produce DIFFERENT ones (+50 vs +5 bps) despite an identical dollar delta · rescaling both prices by any positive factor leaves the outcome unchanged · every `*_bps` magnitude reaching a gate is proved to be basis points at the Scout, walk-forward and sealed-evaluation stages · a floor that does not declare `bps` (including every pre-r13 floor) is refused, never silently compared · a direction outside `long|short` and an aggressor side outside `buy|sell` each RAISE, including on an unmeasured or truncated row, and a `short` candidate's outcome is the exact negation of the `long` one |
| TR-35 sign-once + unit provenance (r13 completion §0/§4/§5.5/§6.6/§8.1) | A successful SHORT candidate (canonical effect POSITIVE) passes the walk-forward and sealed direction conditions exactly as a successful long one does, and a failed short (NEGATIVE) fails both · a side-relative positive short return survives percent→bps conversion, fold summary and pooled effect without becoming negative · opposite-direction detection is NEGATIVE for both directions · every public boundary (candidate registration, spec freeze, anchor extraction, screening, fold-spec registration, survivor evaluation) refuses `buy`/`sell`/`SHORT`/`Long`/`positive`/`negative`/`flat`/`""` while `None` stays legal · mixed-unit and missing-unit observations refuse BEFORE averaging, at the walk-forward and sealed boundaries alike · a percent effect against a bps floor refuses · a pre-r13 fold row serves as `legacy_percent` with its magnitude verbatim, is never displayed as bps, and is refused entry to any new r13 sequence verdict |
| TR-36 fail-closed boundaries + direction freeze (r13 contract pass §5.1/§6.4/§6.6/§8.1) | Mode A refuses an invalid direction BEFORE either observation provider is called, and refuses missing/percent/mixed TRAINING units BEFORE `fit_training_quantile` consumes a value and BEFORE the validation window is revealed (proved with recording providers) · the sealed evaluator refuses an invalid direction and non-canonical observation units BEFORE `accessor.read_snapshot_rows` is reached (proved with a spy accessor) · every Scout anchor carries an `outcome_unit` read off the outcome row, and a missing/percent/legacy/MIXED anchor refuses the screen — the gate's unit is the anchors' proved one, never a literal the consumer supplies · an UNSIDED sequence receives no walk-forward survivor credit, while a direction frozen before the OOS reveal proceeds normally for `long` and `short` alike · a direction chosen AFTER a window's exposure earns `historical_exposed_diagnostic` from the real exposure registry, never `historical_oos` · the `fallback_frac` caveat is asserted only of F-FLOW/F-RESPONSE, never of F-LIQUIDITY |
| TR-37 session-count semantics + executable readiness floors (r14 §0/§1/§6.6) | `distinct_session_dates` and `full_session_equivalents` are BOTH served, carry different values on a partial-window corpus, and neither is substituted for the other · `build_folds` at 60 session dates yields ZERO folds, at 65 yields exactly one (train 40 / embargo 5 / test 20), at 104 yields two and at 105 yields `WF_MIN_SUFFICIENT_FOLDS` · the readiness floor row serves `first_fold_min_session_dates=65`, `survivor_min_session_dates=105` and the ACTUAL `folds_constructible`, while the retained 60 carries the `train_plus_test_arithmetic_only` basis · no geometry constant moves and `config_fingerprint` is unchanged |
| TR-38 corpus-era freshness + production exposure logging (r14 §6.7) | A legacy corpus with an empty registry fails closed and counts ZERO eligible windows · a corpus carrying an explicit era registration with zero exposure rows counts its unexposed windows honestly · an era registration can never make any window read as exposed, and never suppresses the r2 re-seed guard · a TEST read logs exposure strictly after the spec's `registered_at`, and refuses when it cannot prove that ordering · a window revealed once classifies `historical_exposed_diagnostic` for every later spec · a TRAIN read exposes its window identically, so no training read can later pass as a clean test read · re-reading one window five times appends ONE row, not five · a retention probe is logged as a real exposure and its date is barred from the clean-OOS set thereafter |
| TR-39 exploratory release of NOT-selected pool members (r14 §7.4/§7.5 point 7/§7.2.2) | An HMAC-NOT-selected registered-pool member releases to `exploratory_released` and stops being withheld · an HMAC-SELECTED member is REFUSED that path · a dataset already carrying any shard row is refused, and a released row can afterwards be neither sealed nor assigned — no sealed/blind credit, no single shot consumed · a pair outside `expected_recording_pairs()` is refused · a secret not matching the universe's committed `vault_secret_commitment` is refused · releasing every unselected member is refused at the LAST one, leaving at least one decoy, so the hidden set is never determinable by subtraction · whole-pool release becomes reachable once every selected member is exposed, and the revealed rule recomputes exactly to the registered `rule_commitment` · `VAULT_SEAL_HEX_BELOW` is unchanged |
| TR-40 partial-pool OOS on a mixed date (r14.1 §7.4/§6.2) | A date holding 6 HMAC-not-selected released members and 2 sealed ones is USABLE: the reader reads exactly the 6, the 2 sealed dataset ids receive ZERO read calls, and the fold's realized symbol breadth is reported as 6 rather than the panel's 8 · a bound corpus's members never include a legacy same-date sibling, a member of another registered universe, a dataset created before the freshness boundary, or a still-withheld one · every expected member missing a snapshot REFUSES rather than silently shrinking the corpus · a 105-date universe with a real HMAC partition produces `WF_MIN_SUFFICIENT_FOLDS` folds with no sealed id in any fold window |
| TR-41 corpus identity binding + anti-laundering (r14.1 §6.7/§6.2) | An unbound `corpus_id` has no membership and refuses · a corpus era can only bind to a universe that exists · conflicting re-registration of the same `corpus_id` refuses while a byte-identical replay is idempotent · an already-exposed legacy dataset given a brand-new `corpus_id` can neither enter its membership nor be released into it · `corpus_manifest_hash` moves when a member id, a member checksum or the member count changes, and is order-independent |
| TR-42 precommitted release plan + store-derived release (r14.1 §7.2.2/§7.4) | The release boundary takes NO caller-supplied `symbol`/`session_date`/`checksum`/`event_count` -- all are derived from the store · a dataset whose store identity is not a pool member, is not recorder output, or predates the universe REFUSES · release without a committed plan refuses · the reserved decoy refuses while anything is sealed and becomes releasable exactly when nothing is · the same universe + same secret yields the same decoy and the same final released set under ANY release order · a conflicting plan commitment refuses and the commitment serves class SIZES only · exposure is present in the registry before the first outcome row is read, and survives a crash mid-read |
| TR-26 depletion revealing quote (r6 §3) | Price-change termination: `available_at` equals the first CHANGED-price quote, not the last same-price one · bound termination: `available_at` equals the bound-hitting quote · truncating immediately BEFORE the revealing quote makes the depletion value non-existent/unavailable, and including it makes the value appear deterministically |

Plus the standing suite: engine golden trace + observer equivalence + frozen-default profile,
fingerprint pin `08e471b10130e1e2`, referee modules byte-untouched, no-execution scan, copy
discipline, MCP contract, replay-script static sweep.

---

## 10. Stated assumptions and limits (served, not hidden)

1. L1 only: trades + top-of-book quotes. For the LEGACY datasets, trade conditions/exchange
   were dropped at the vendor boundary and are unrecoverable; from this era's recorder on, the
   Card-5.1 preservation fields (§7.1) carry them on every NEW recording — so condition-aware
   studies (Card 9.10) remain blocked on the legacy corpus but their data prerequisite accrues
   going forward. Auction/average-price/TRF prints in legacy data still masquerade as ordinary
   prints; served as a standing caveat on legacy-corpus flow statistics.
2. Aggressor labels are inferred (quote rule → tick test); 29–76% of current-corpus labels are
   tick-test inferences. Every aggressor-derived statistic carries `fallback_frac` and the
   tercile stratification; no label is ever treated as ground truth.
2b. Displayed quote sizes have a DATED unit basis (§2.6): Alpaca CTA/UTP moved to shares on
   2025-11-03; earlier windows are round lots; every legacy dataset is `unverified` until a
   recorded verification. No cross-basis liquidity arithmetic exists outside verified units.
3. Quoted spread is a research cost proxy — no fill model, no queue model, no impact model is
   claimed anywhere in this era.
4. The current tick corpus (12 symbol-days) supports plumbing and clearly-labeled exploratory
   diagnostics only; every readiness payload says which floors are unmet.
5. Retrospective sealed shards conceal L1 micro detail only; bar-level outcomes of their dates
   are public. The reconstructibility diagnostic reports this; provenance rules, not the
   diagnostic, decide admissibility.
6. Nothing in this era emits `live_confirmatory` evidence; the Referee remains the only source
   of confirmatory claims, unchanged.
7. **`referee_evidence.strategy_trade_readiness` is seal-unaware — a deliberate, disclosed
   compatibility limitation of this era (r5 owner ruling).** It counts dataset FILES through its
   own enumeration and may therefore include withheld, unexposed Rapid-Microscope shards. The
   era's byte-freeze rail on `referee_*.py` is PRESERVED: the file is not edited, and
   `DatasetStore` is NOT intercepted to change frozen Referee behaviour indirectly (that would
   breach the freeze's behavioural meaning even with identical bytes). Instead, wherever that
   metric is served, it carries the caveat verbatim: *"Legacy Referee readiness metric —
   seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope
   shards and must not be used as the canonical Rapid-Microscope readiness count."* The new
   seal-aware `micro_readiness` surface is the CANONICAL owner of every Rapid-Microscope
   corpus/readiness decision. Enforced: the stale count awards ZERO gate or graduation credit; no
   Scout, walk-forward, vault, graduation, or readiness-floor decision may consume it; no UI, API,
   or MCP surface may present it as equivalent to the seal-aware count, and where both appear
   their differing semantics are labelled explicitly; a guard/source-scan proves Rapid-Microscope
   gates read only the seal-aware owner. The actual Referee fix is deferred to a future named
   Referee revision. **Escalation condition:** if audit finds `strategy_trade_readiness` is
   consumed by a live promotion or certificate decision rather than being a readiness/reporting
   value, STOP and escalate — that case requires a named Referee revision, not disclosure.
