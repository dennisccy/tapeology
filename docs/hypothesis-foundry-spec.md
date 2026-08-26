# The Hypothesis Foundry Spec — candidate construction, freeze, and exhaustion

> **This file is the implementation-ready methodology spec for the Foundry era's OWN new
> machinery: source compilation, `CandidateSpec` construction, the generic interpreter, the
> freeze barrier, and the deterministic exhaust runner.** It is subordinate to `docs/goal.md`
> (the "Foundry Constitution", sections 1-12) — that file is the ratified owner-policy source of
> truth; this file is its condensed, section-numbered implementation reference so a developer or
> a source-record author can cite one short document instead of the whole goal file. Every
> section number below (`§1`-`§12`) matches the corresponding goal.md Foundry Constitution
> section, so a citation such as "spec §2.3" and "goal.md §2.3" name the identical rule. Where
> this file and `docs/goal.md` ever appear to disagree, `docs/goal.md` wins — this file is a
> derivation, never an amendment.
>
> **This spec explicitly does NOT restate or fork the Rapid Validation statistical decision
> rail.** `scout.screen_candidate` (`app/research/scout.py`) remains the sole statistical judge:
> its null, permutation count, alpha, minimum cell/session floors, concentration ceiling,
> economic-floor multiple, fragility rule, and decision vocabulary are frozen by
> `docs/rapid-validation-spec.md` and are referenced here by name only. This spec defines only
> how a candidate is CONSTRUCTED, FROZEN, and EXHAUSTED before and after it reaches that
> unchanged judge.
>
> **Revision v1 (2026-08-26, goal-hypothesis-foundry-iter-1).** First committed revision. Written
> alongside the source-registry/CandidateSpec compiler machinery it documents
> (`app/research/foundry_source_registry.py`, `app/research/foundry_compiler.py`) and proven only
> against seven hermetic fixture source records — no real source object is authored under this
> revision (that is `J-06`, Binding Execution Order step 6). A future revision that changes
> scientific meaning re-keys forward (new spec hash, never a silent edit of a decision already
> compiled under an earlier hash) exactly like `docs/rapid-validation-spec.md`'s own revision
> discipline.

---

## 0. Scope of this document

This spec fixes the meaning of:

- the closed source-disposition vocabulary (`§7.1`) and the fields every checked-in source
  record must carry (`§1.4`);
- the owner meta-policy that decides, mechanically, whether a source compiles, aliases, excludes,
  or blocks (`§2`);
- the canonical `CandidateSpec` schema and its hash discipline (`§3`);
- the generic candidate interpreter's population-symmetry and boolean-projection rules (`§4`);
- the Foundry family/denominator contract (`§5`);
- the economic-floor ordering rule (`§6`);
- the source/variant state machines (`§7`);
- the real epoch, manifest, and freeze-barrier contract (`§8`);
- the deterministic exhaust runner's resume/replay contract (`§9`);
- the evidence boundary this era may spend (`§10`);
- what an `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` label does and does not mean (`§11`).

Sections are numbered to match `docs/goal.md`'s Foundry Constitution exactly. Only `§1.4`, `§2`,
and `§3` are implemented in code as of this revision (`goal-hypothesis-foundry-iter-1`,
`app/research/foundry_source_registry.py` + `app/research/foundry_compiler.py`); `§4`-`§9` are
fixed in MEANING here so later iterations implement against a stable text, not a moving target,
per the goal's own Binding Execution Order.

---

## 1. Source scope — finite and ratified

The first real Foundry epoch may consider only source statements already ratified in the
repository before `docs/goal.md` (this era's goal document) opened: the Rapid Microscope's parked
Study 1 (`range_wall_failed_aggression`) and Study 3 (`capitulation_exhaustion`); Era 9 Wave-1
Cards 9.3-9.7; the frozen Study 1/Study 3 pilot proxy declarations; and the explicit exclusions
(Card 9.1/Study 2 previously-killed, Card 9.2 prerequisite-unmet, Cards 9.8-9.11 gate-closed, and
everything outside this registry). See `docs/goal.md §1.1`/`§1.2` for the complete required-object
list — this spec does not re-enumerate it, since goal.md is its single source of truth and
duplicating it here would create two places a future reader could disagree about the list.

### 1.3 Formula-scoped supersession law

Supersession is **formula/meaning scoped, not card-number scoped**: when a later frozen Rapid
Validation revision replaced an operational formula/window/threshold for a concept a card
originally named, the newer frozen rule wins for that field and the older card value becomes
provenance only (`ALIASED_VARIANT_VOCABULARY`/`ALIASED_LINEAGE`, never a silently-reused stale
constant). Implemented as the `supersession` field on `SourceRecord`
(`app/research/foundry_source_registry.py`): a non-`None` value marks the record as the OLDER
member of a supersession pair, names the newer ref its `superseded_fields` cite, and selects
which alias disposition applies.

### 1.4 Source-record decision audit

Every checked-in source record — real or hermetic-fixture — carries exactly these fields (the
`SourceRecord` dataclass in `app/research/foundry_source_registry.py` is this list, verbatim):

| Field | Meaning |
|---|---|
| `source_id` | canonical, stable identifier |
| `source_path`, `section_ref` | exact repository path + stable section/card/study reference |
| `quoted_spans` | one or more `(text, location)` pairs — the exact quoted source span(s) and precise location backing every load-bearing decision below |
| `source_excerpt` | the cited source text itself, so the exact-quote lint (`§1.4` mechanical lint, below) can verify a span against it without a live repository read |
| `source_hash` | `sha256` of `source_excerpt` |
| `mechanism_statement` | the mechanism this record represents, in the source's own terms |
| `operative_formula_refs` | current operative formula/feature identifiers this record compiles against |
| `superseded_fields` | mapping of field name → superseding ref, empty unless this record is superseded |
| `foundry_family_key`, `variant_ordinal` | pre-declared family grouping + this variant's position within it (mechanical bookkeeping, never chosen by outcome) |
| `threshold_provenance` | one of the three `§2.3` natural-boundary categories, or `None` when the mechanism needs no threshold |
| `unresolved_magnitude_words` | non-empty exactly when compiling this record would require inventing a numeric meaning for a magnitude word (`§2.2`) — forces a block |
| `direction_derivation` | the mechanical direction rule, or the literal sentinel `BLOCKED_DIRECTION` |
| `comparator_derivation` | the mechanical comparator rule, or the literal sentinel `BLOCKED_UNSUPPORTED_STUDY_FORM` |
| `proxy_of` | non-`None` only for a pilot-proxy record; carries the parked study it stands in for and its preserved `do_not` restriction |
| `supersession` | non-`None` only for an older, formula-superseded record; carries the newer ref and the alias disposition it selects |
| `aliases_lineage_ids` | lineage/alias ids this record is linked to |
| `audit_note` | why each decision follows from the quoted rules — **never** citing a candidate outcome, p-value, effect, observation count, Scout verdict, or PnL result |
| `extra` | caller-supplied metadata the compiler NEVER reads (proves TC-11: an injected `effect_bps`/`p_value`/`n` cannot move a disposition or hash) |

Mechanical registry lint (`foundry_source_registry.lint_quoted_spans`) verifies every recorded
quoted span is an exact substring of `source_excerpt` at its recorded character offset. It
deliberately does not use keyword matching as a proxy for scientific meaning — an exact-position
substring match only, so a mismatched span fails closed rather than fuzzily "close enough".

---

## 2. Owner meta-policy — block unresolved science

The compile function (`foundry_source_registry.compile_source_disposition`) evaluates a
`SourceRecord` against this fixed precedence, deterministically, with no fixture/source-specific
branch anywhere in the function body:

1. **Proxy** (`proxy_of` set) → `ALIASED_PROXY_ONLY`, `do_not` preserved verbatim.
2. **Supersession** (`supersession` set) → `ALIASED_VARIANT_VOCABULARY` or `ALIASED_LINEAGE`
   (whichever the record's `supersession.alias_kind` names), `superseded_fields` cite the newer
   ref.
3. **Unresolved magnitude word** (`unresolved_magnitude_words` non-empty) → `BLOCKED_SPEC_GAP`
   (`§2.2`: "defining what words such as `high`, `extreme`, `collapse`... mean numerically" is
   new science, never a mechanical choice).
4. **No mechanical direction** (`direction_derivation == "BLOCKED_DIRECTION"`) → `BLOCKED_DIRECTION`.
5. **Unsupported statistical form** (`comparator_derivation == "BLOCKED_UNSUPPORTED_STUDY_FORM"`)
   → `BLOCKED_UNSUPPORTED_STUDY_FORM`.
6. **Illegal threshold provenance** (`threshold_provenance` set but not one of the three `§2.3`
   categories) → `BLOCKED_UNIT_CONTRACT` is reserved for cross-unit arithmetic specifically (see
   `docs/goal.md` Anti-goals); an out-of-band threshold is a `§2.2` new-science case and is
   caught by step 3 above via `unresolved_magnitude_words`, so this step never independently
   fires for the fixtures this revision defines. It is reserved here for a future source whose
   gap is a genuine unverified unit crossing rather than a magnitude word.
7. Otherwise → `COMPILED`.

Exclusion dispositions (`EXCLUDED_PREVIOUSLY_KILLED`/`EXCLUDED_PREREQUISITE_UNMET`/
`EXCLUDED_GATE_CLOSED`) are not reached by this function at all — they are declared directly on a
`SourceRecord` via its `explicit_exclusion` field (checked before step 1) for the real registry's
Study 2/Card 9.1/9.2/9.8-9.11 rows (`J-06`); no hermetic fixture this revision uses one, since none
of the seven required taxonomy examples is an exclusion case.

### 2.1/2.2 Enumeration vs. block

A finite family enumerates only when each member is a SEPARATE, individually-authored
`SourceRecord` sharing one `foundry_family_key` — the compiler never expands one record into many
alternatives on its own initiative (that would be exactly the "mere existence of two features in
code is not permission to enumerate" trap `§2.1` warns against). Two records sharing a family key
must each independently reach `COMPILED` on their own merits; the family's `variant_ordinal`
values are author-declared (mechanical bookkeeping, not derived from anything the compiler
computes), and the compiler only verifies they are unique within the family.

### 2.3 Natural-boundary law

`threshold_provenance`, when present, must be one of exactly three values (module constants in
`foundry_source_registry.py`): `THRESHOLD_LITERAL_RATIFIED`, `THRESHOLD_FROZEN_FEATURE_CONTRACT`,
`THRESHOLD_NATURAL_SEMANTIC_BOUNDARY`. A zero/boolean boundary is legal only under the third
category and never licenses reinterpreting a magnitude word — that case is represented as
`unresolved_magnitude_words`, not as an illegal `threshold_provenance` value, so it is caught at
step 3 of the precedence above.

---

## 3. CandidateSpec — the frozen scientific object

`app/research/foundry_compiler.py`'s `CandidateSpec` dataclass implements every field
`docs/goal.md §3` requires. `candidate_spec_hash` is `sha256` over a canonical JSON serialization
(`json.dumps(..., sort_keys=True)`) of every field EXCEPT the hash fields themselves
(`manifest_hash`, `source_registry_hash`, `compiler_hash`, `candidate_spec_hash`) — so:

- shuffling the order fields are constructed/serialized in never changes the hash (dict key
  order is normalized by `sort_keys=True`);
- mutating any other field — `horizon_key` is the canonical worked example — always changes the
  hash;
- a caller-attached, non-schema value (the `extra` escape hatch on `SourceRecord`, or any field
  outside the dataclass entirely) can never reach the hash, because the hash walks only the
  dataclass's own declared fields.

This revision's `foundry_compiler.compile_sources()` produces a `CandidateSpec` only for a source
that reaches `COMPILED` and needs no deferred/population resolution — i.e. every coordinate is
immediately available (no `refill_consistent`-style deferred join). The generic interpreter that
resolves deferred conditioning (`§4`, `foundry_interpreter.py`) is explicitly future work
(`docs/goal.md` Binding Execution Order step 3); a source whose compilation would require it is
left `FROZEN_READY`-incomplete this revision rather than approximated.

### 3.1 Legal outcome horizons

`horizon_key` must be a member of `scout.HORIZON_KEYS` — verified from that module at compile
time, never hard-coded twice. As of this revision that set is `{"trades_20", "trades_100"}`.

### 3.2 Direction is mandatory

Enforced structurally: `foundry_compiler` never constructs a `CandidateSpec` for a source whose
disposition is not `COMPILED`, and `COMPILED` is unreachable (`§2` step 4) for a record whose
`direction_derivation` is the `BLOCKED_DIRECTION` sentinel.

---

## 4. Generic candidate interpretation (future work, meaning fixed here)

The interpreter is new candidate-CONSTRUCTION machinery, never a second statistical rail. Per
`docs/goal.md §4.1`, for each source population anchor: resolve every conditioning component via
its `resolution_join_rule` (joining only through the observer's own emitted provenance identity,
never nearest-time matching); exclude-and-count an anchor with any unresolved component from BOTH
cells; set `candidate_available_at = max(component.available_at)`; measure identical outcomes for
candidate and comparator from that instant; the comparator is the complement of membership inside
that same eligible/timing-resolved population. `§4.2`'s boolean projection
(`feature_value >= 1.0`) into `scout.screen_candidate` and `§4.2.1`'s Foundry-owned trial-ledger
boundary (never the Scout ledger) apply unchanged when this module is built.

## 5. Foundry family denominator and multiplicity (future work, meaning fixed here)

`foundry_family_id` groups every predeclared alternative representation of one mechanism lineage,
frozen before outcomes (`§5.1`). The complete family variant count must be
`<= scout.SCOUT_MAX_VARIANTS_PER_FAMILY` before evaluation or the whole family is
`BLOCKED_VARIANT_EXPLOSION` — never truncated, split, or subset-evaluated (`§5.2`). Every sibling
variant is screened with the COMPLETE frozen denominator as `n_variants_tried`, even before
siblings execute (`§5.3`). This era adds no Bonferroni/FDR correction (`§5.4`).

## 6. Economic-floor ordering (future work, meaning fixed here)

The manifest freezes the EXISTING quoted-spread floor RULE, never a result-dependent number
(`docs/goal.md §6`). The numeric floor materializes only during real evaluation, from the legal
already-exposed corpus, and is appended as an `EVALUATION_INTENT_RECORDED` row BEFORE the outcome
is measured — it can never be back-filled after the fact.

## 7. State machine

### 7.1 Source dispositions (implemented this revision)

The closed vocabulary — `app/research/foundry_source_registry.py`'s `SOURCE_DISPOSITIONS`:

```
COMPILED
ALIASED_PROXY_ONLY
ALIASED_VARIANT_VOCABULARY
ALIASED_LINEAGE
EXCLUDED_PREVIOUSLY_KILLED
EXCLUDED_PREREQUISITE_UNMET
EXCLUDED_GATE_CLOSED
BLOCKED_SPEC_GAP
BLOCKED_MISSING_PRIMITIVE
BLOCKED_UNSUPPORTED_STUDY_FORM
BLOCKED_UNSUPPORTED_RELATION
BLOCKED_DIRECTION
BLOCKED_VARIANT_EXPLOSION
BLOCKED_UNIT_CONTRACT
```

No required source may silently disappear from this vocabulary; a source not otherwise decided
reaches `COMPILED` only via the `§2` precedence above, never a default.

### 7.2 Variant states (future work, meaning fixed here)

`FROZEN_READY → EVALUATION_INTENT_RECORDED → {EVALUATED_INSUFFICIENT, EVALUATED_KILLED,
DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN}`, mapped mechanically from the unchanged Scout kill ladder
(`docs/goal.md §7.2`). There is no second Foundry verdict.

### 7.3 Integrity/refusal (future work, meaning fixed here)

A ledger/freeze/replay/protected-access defect halts the epoch as `FOUNDRY_INTEGRITY_HALT` — not
a scientific terminal result, and never silently patched after a first outcome read.

---

## 8. Real generation epoch and freeze barrier (future work, meaning fixed here)

Exactly one real `epoch_id` may ever exist this era (`§8.1`); hermetic fixture epochs — including
every fixture this revision defines — do not count and never share an `epoch_id` namespace with
it. The tracked manifest artifacts live under `docs/hypothesis-foundry/` (`§8.2`) and are NOT
created by this revision — they are generated once, at Binding Execution Order step 6 (`J-06`),
by running this revision's compiler against the real ratified sources. The freeze record pins
every science-affecting hash including this spec's own (`§8.4`); the freeze-set is an enumerated
checked-in path+sha256 manifest, never an adjective chosen at runtime.

## 9. Deterministic exhaust runner (future work, meaning fixed here)

Canonical family-then-ordinal order, invariant to effect/p-value/n/sibling verdicts (`§9.1`); the
Foundry trial ledger is the source of truth and the checkpoint is only a derived cache (`§9.2`);
no candidate rescue after first-read lock (`§9.3`).

## 10. Evidence boundary (future work, meaning fixed here)

Every real Foundry candidate uses only the already-exposed `historical_exposed_diagnostic`
corpus through the sanctioned accessor (`§10.1`); no fresh corpus registration, retention probe,
storage provisioning, recording, release, Vault act, historical-OOS fold, graduation, or Referee
act occurs in this era (`§10.2`).

## 11. OOS-rule-frozen survivor semantics (future work, meaning fixed here)

`DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` means only that a pre-outcome, already-frozen
`CandidateSpec` passed the unchanged Scout diagnostic rail on already-exposed evidence; it is
never walk-forward survivor, historical OOS evidence, Vault survivor, Referee-ready, confirmed
edge, or a profitable-strategy claim (`docs/goal.md §11`).

---

## 12. What this revision proves, and what it deliberately does not

Proven this revision, hermetically, over exactly the seven fixture source archetypes
`docs/goal.md` J-02 step 2 names (a compileable natural-boundary scalar; two explicitly-frozen
legal variants in one family; an unresolved-magnitude-word source; a proxy-only source; an
unsupported-statistic source; an alias/supersession pair; a directionless mechanism):

- the `§7.1` disposition vocabulary is closed and every fixture reaches exactly one member of it;
- the `§2` owner meta-policy precedence is mechanical and fixture-agnostic;
- the `§1.4` exact-quote lint fails closed on a mismatched span;
- the `§3` `CandidateSpec` schema is complete, its hash is order-invariant and
  science-field-sensitive, and no non-schema fixture field can move it.

Deliberately NOT built this revision: the real 11 required source objects (`J-06`); the generic
interpreter / deferred-conditioning resolution (`§4`, `J-03`); the Foundry family registry, ledger,
and freeze barrier (`§5`-`§8`, `J-03`/`J-04`); the exhaust runner (`§9`, `J-07`); any real epoch,
manifest, freeze commit, or candidate outcome read. A block is a legitimate scientific output, not
an implementation gap — nothing in this revision "rescues" a fixture that should honestly block.
