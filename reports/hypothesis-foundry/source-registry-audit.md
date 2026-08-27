# Hypothesis Foundry — Source Registry Audit

**Type:** Fresh-context, independent scientific audit (goal.md §1.4's "fresh-context independent
source-registry audit"). The auditing agent had no prior visibility into how this registry was
built, only the ratified rulebook, the artifact itself, and the primary sources it cites.

**Date:** 2026-08-27

**Artifact under audit (as first drafted):** `docs/hypothesis-foundry/source-registry.json`
(11 records, `source_registry_hash`
`ded18b8b896b3b995cc3517c92dce469a1eec8f92357aa9bf612a137ae87a1e5`).

**POST-AUDIT DISPOSITION (added after this audit ran, before commit — no candidate outcome was
read at any point in this process, so this is not the barred "second real generation epoch";
§8.3/§8.4's freeze barrier had not yet been crossed — nothing was ever committed to Git under the
first `source_registry_hash` above).** Both items this audit flagged in its own "Overall Verdict"
section below were fixed in the generator (`apps/backend/scripts/
generate_hypothesis_foundry_real_epoch.py`) and the registry was regenerated fresh:

1. **The missing `audit_note`/`source_hash` fields** are fixed: the generator now serializes the
   full record (`_full_record_view`) for the checked-in JSON instead of reusing
   `foundry_source_registry._canonical_source_record()` (the hash-canonicalization projection,
   which correctly excludes those fields from the HASH but should never have been reused as the
   artifact serializer). Verified: every one of the 11 records in the regenerated
   `source-registry.json` now carries a non-empty `audit_note` and `source_hash`.
2. **`card-9.6-shuffled-side-persistence`'s `direction_derivation`** was corrected from the
   unsupported literal `"long"` to the honest `BLOCKED_DIRECTION` sentinel, exactly as this audit
   recommended — the record has no return/outcome variable at all, so no direction concept
   mechanically applies, and `compile_source_disposition`'s own fixed, uniform precedence (checked
   identically for every record, never picked per-record) now produces `BLOCKED_DIRECTION` for
   this record instead of `BLOCKED_UNSUPPORTED_STUDY_FORM`. The same unsupported `"long"` value on
   `card-9.7-event-time-feature-windows` was corrected the same way for consistency (harmless
   either way there, since supersession is checked first).

Because item 2 changes an actual `direction_derivation` field, `source_registry_hash` and
therefore `epoch_id` changed on regeneration (the disposition-derivation logic itself was never
touched — no compiler/precedence code changed, only the input record's own field value, which the
audit itself proved was wrong). **The final, committed artifact's `source_registry_hash` is
`ed40dbc25e8fdb961258512dc01ccbaa4633e0ddb6f374288c6c78d681bd098d`** (`epoch_id:
epoch:afd19e9c11a6534f`) — every per-record finding below was re-verified by the developer against
this final registry and remains accurate in substance; only the two corrected fields/dispositions
noted above differ from what this report originally described. The rest of this report is left
exactly as the fresh-context auditor wrote it, as the authoritative record of what was
independently checked and how.

**Files reviewed:**
- `docs/goal.md` (Vision; Foundry Constitution §1–§7.1)
- `docs/hypothesis-foundry-spec.md` (§1–§3, §7.1)
- `docs/research-directions.md` (lines 1070–1337, Era 9 + Rapid-Microscope/Foundry opening notes;
  lines 2020–2050, era ledger)
- `apps/backend/app/research/micro_readiness.py` (lines 100–165, `PILOT_STUDY_IDS` /
  `PILOT_STUDY_STATUS`)
- `apps/backend/app/research/scout.py` (`pilot_study_candidate_grid()`, `STRUCTURE_CONTEXT_KINDS`)
- `docs/goal-archive/goal-2026-08-26.md` (lines 650–680, J-09 step 1)
- `apps/backend/app/research/micro_features.py` (lines 370–400, `quote_imbalance`,
  `impact_efficiency`, `failed_aggression_score`)
- `apps/backend/app/research/foundry_source_registry.py` (`compile_source_disposition`,
  `SourceRecord` dataclass, `_canonical_source_record`)
- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` (the generator that produced
  the checked-in JSON, consulted to trace one finding to its root cause)

---

## Registry-level checks

- **Record count:** exactly 11 records. ✓
- **Disposition vocabulary:** every record carries exactly one `disposition` from the closed
  §7.1 vocabulary; no fixture/placeholder values. ✓
- **Required source objects:** all objects in goal.md §1.1/§1.2 are accounted for — Study 1 and
  Study 3 are each one record (parked mechanism + frozen pilot proxy declaration share one id,
  matching `micro_readiness.PILOT_STUDY_STATUS` / `scout.pilot_study_candidate_grid()`'s own
  shared id vocabulary); Cards 9.3–9.5 and 9.7 are one record each; Card 9.6 is split into two
  records per §1.3's own explicit instruction; Card 9.1/Study 2 is one combined excluded record;
  Card 9.2 is one excluded record; Cards 9.8–9.11 are one combined excluded record (mirroring
  goal.md's own single-arrow treatment of that foursome). Nothing required is silently absent. ✓
- **Compiled count:** `grep '"disposition": "COMPILED"'` returns zero hits. Having read every
  cited source passage myself, I am independently persuaded zero is correct: every Wave-1 card
  either uses an undefined magnitude word (9.4), states an explicitly non-directional
  confirm/veto/co-occurrence mechanism (9.3, 9.5, 9.6-run-length), uses a statistical form Scout
  cannot express (9.6-shuffled), or is superseded into existing vocabulary (9.7); the two pilot
  studies are proxy-only by explicit constitutional rule; and Study 2/9.2/9.8–9.11 are
  constitutionally pre-excluded. No record's ratified text actually supplies a threshold+
  direction+population triple sufficient to compile.

---

## Per-record findings

### `pilot-study-1-range-wall-failed-aggression`
**Disposition under audit:** `ALIASED_PROXY_ONLY`. **Verdict: CONFIRMED.**
All three `quoted_spans` are exact, verified substrings of `micro_readiness.py`'s comment block
and `PILOT_STUDY_STATUS['range_wall_failed_aggression']` dict values (confirmed by direct read of
lines 100–160). The `do_not` string ("screen the failed_aggression_score proxy under this
mechanism's name") is copied verbatim from the source, and `operative_formula_refs` correctly
names `failed_aggression_score`, the exact feature `scout.pilot_study_candidate_grid()` wires into
this proxy's frozen request. `ALIASED_PROXY_ONLY` is the disposition goal.md §1.1 mandates by name
for this exact object, and nothing here launders the proxy as the full three-part mechanism. Note:
this record's `audit_note` field is absent from the checked-in JSON — see Overall Verdict.

### `pilot-study-3-capitulation-exhaustion`
**Disposition under audit:** `ALIASED_PROXY_ONLY`. **Verdict: CONFIRMED.**
Same pattern as Study 1: all quoted spans verified verbatim against `micro_readiness.py`; the
`do_not` string ("screen a single direction-agnostic threshold under this mechanism's name")
matches the source exactly; `operative_formula_refs: ["failed_aggression_score"]` matches
`scout.pilot_study_candidate_grid()['capitulation_exhaustion']`'s actual `feature_name` exactly
(the request is direction-agnostic, `sidedness: None`, consistent with `direction_derivation:
BLOCKED_DIRECTION`). The mechanism statement's ordered-sequence framing ("extreme SELL aggression,
THEN collapsing...") is preserved and correctly distinguished from the proxy's single
direction-agnostic threshold. `audit_note` is likewise absent from the JSON.

### `card-9.3-top-of-book-imbalance`
**Disposition under audit:** `BLOCKED_DIRECTION`. **Verdict: CONFIRMED.**
The quoted span matches `docs/research-directions.md` line 1196 verbatim. The card states the
feature "adds confirm/veto information beyond the trade-derived features" — explicitly agnostic
about which side of that binary applies, never asserting bid-heavy-at-support mechanically implies
long. That is correctly `BLOCKED_DIRECTION`, not a block on threshold: `threshold_provenance:
natural_semantic_boundary` is legitimate because the card's own parenthetical uses "bid-heavy"
language, matching goal.md §2.3 category 3's own worked example ("a signed variable's zero
boundary when the source itself says positive-vs-negative / bid-heavy-vs-ask-heavy") — though this
depends on the current codebase's `quote_imbalance()` (`(bid_size - ask_size) / total`, a *signed*
ratio) rather than the card's own literal `bid_size / (bid_size + ask_size)` formula, since only
the signed form has a natural zero boundary. This substitution is defensible but non-obvious, and
the JSON's missing `audit_note` (see Overall Verdict) is exactly the field that should explain it
to a reader who only has this file.

### `card-9.4-burst-climax-detection`
**Disposition under audit:** `BLOCKED_SPEC_GAP`. **Verdict: CONFIRMED.**
Quoted span matches line 1210 verbatim. `unresolved_magnitude_words: ["extremes", "genuine"]` is
accurate: "session extremes" (how close to session high/low counts as "at" the extreme is never
stated) and "genuine breaks" ("genuine" is exactly the class of undefined-magnitude word §2.2
lists) both appear in the quoted text with no numeric pin anywhere in the card. This is
independently reinforced (though not needed for the disposition) by the fact that neither "session
extreme" nor "zone break" is a member of `scout.STRUCTURE_CONTEXT_KINDS`
(`playbook_signal`/`band_touch`/`none`, confirmed by grep) — there is no legal population for this
mechanism today even setting the magnitude-word gap aside.

### `card-9.5-spread-dynamics-regime`
**Disposition under audit:** `BLOCKED_DIRECTION`. **Verdict: CONFIRMED.**
Quoted span matches line 1224 (Unicode `≥`/`—` normalized to ASCII, which the generator's own
comment discloses as whitespace-normalization, not a meaning change). The mechanism is explicitly
a co-occurrence/veto statement: widening is stated only as "a veto" on some other, unnamed setup's
entries, and narrowing-plus-imbalance is stated only to "precede breaks" without naming that
break's direction. No mechanical long/short mapping exists in the quoted text, so `BLOCKED_
DIRECTION` (rather than treating the frozen `ratio >= 1.5` constant as compilable) is correct.

### `card-9.6-shuffled-side-persistence`
**Disposition under audit:** `BLOCKED_UNSUPPORTED_STUDY_FORM`. **Verdict: CONCERN — RESOLVED
post-audit.** (Fixed exactly as recommended below: `direction_derivation` corrected to the
`BLOCKED_DIRECTION` sentinel; the record's mechanical disposition in the final committed registry
is `BLOCKED_DIRECTION`, per `compile_source_disposition`'s own precedence. See the header note
above.)
The comparator call is right: the quoted evaluation method — observed `P(next same | run >= k)`
vs. a seeded within-session label-shuffle null — is genuinely a different statistical form from
`scout.screen_candidate`'s candidate-vs-comparator outcome-mean/permutation screen, which has no
mechanism for a same-sequence shuffle test. But `direction_derivation` is set to the literal string
`"long"`, and that is not supported by the cited text. The quoted source reads "**long** same-side
print runs continue beyond chance" — "long" there is an adjective modifying run *length*, not a
trading-direction claim (contrast the sibling record below, which correctly reads the adjacent
"adds confirm information" clause as directionless). More fundamentally, this study has no
return/outcome variable at all — its dependent variable is "next print's side," not a price
return — so there is no basis to mechanically derive a `long|short` sidedness for it. Per
`compile_source_disposition`'s own fixed precedence (verified by reading the function: direction
is checked at step 4, before the comparator-form check at step 5), correcting `direction_derivation`
to the `BLOCKED_DIRECTION` sentinel would change this record's disposition to `BLOCKED_DIRECTION`.
Both are non-compile block outcomes, so no candidate is wrongly compiled either way — but the typed
disposition currently on record is not what the compiler's own precedence would produce from an
honestly-filled direction field, and a future reader would draw the wrong lesson from it (that only
a new statistical-form adapter is needed, when in fact no direction concept applies to this study
at all).

### `card-9.6-run-length-at-touch`
**Disposition under audit:** `BLOCKED_DIRECTION`. **Verdict: CONFIRMED.**
Quoted span ("run length at a zone touch adds confirm information") matches the source exactly.
This sibling record correctly recognizes that "adds confirm information" states no run-side
(buy-run vs. sell-run) / band-side (support vs. resistance) mapping to long vs. short, and no
ratified mirrored-rejection statement exists for this feature — so inventing that mapping would be
new science, not derivation. `aliases_lineage_ids` correctly cross-references its sibling
`card-9.6-shuffled-side-persistence` and the reverse link is consistent (no contradiction). The
split of Card 9.6 into two records is scientifically defensible: the two clauses have materially
different statistical forms (a shuffle-null probability test vs. a threshold-on-run-length
membership test), exactly matching §1.3's own instruction that Card 9.6 "may contain more than one
study statement... They receive separate dispositions if their statistical forms differ."

### `card-9.7-event-time-feature-windows`
**Disposition under audit:** `ALIASED_VARIANT_VOCABULARY`. **Verdict: CONFIRMED.**
Both quoted spans match line 1244 (card) and line 1108 (Rapid-Microscope opening note "Brought
forward" bullet — confirmed by direct line count) verbatim. This is a clean supersession case: the
2026-08-16 opening note explicitly brings 9.7 forward "as first-class representations at frozen
sizes," which is a formula/meaning-scoped replacement of the card's own open "which windowing
wins" question with an already-decided current representation — exactly §1.3's own worked example
for this card. `superseded_fields` and `supersession.newer_source_ref` correctly cite that bullet.
Minor note (non-disposition-changing, since `compile_source_disposition` checks `supersession`
before `direction_derivation`): `direction_derivation` is also set to `"long"` here, and Card 9.7
is a pure window-representation comparison ("which windowing has higher |ρ| where") with no
trading-direction content either — the same unsupported value as the 9.6-shuffled record above,
just harmless in this case because supersession fires first in the precedence.

### `card-9.1-study-2-delta-divergence-excluded`
**Disposition under audit:** `EXCLUDED_PREVIOUSLY_KILLED`. **Verdict: CONFIRMED.**
All three quoted spans (the `CD_t` formula, "it is pilot study 2," and "Study 2 killed on the
merits (p 0.366)") are exact, verified substrings of the cited passages (Card 9.1 line 1157, the
opening note's identity claim at line ~1101, and the era-ledger row at line 2045 — all confirmed by
direct line count). This is the one record where a p-value is quoted, and it is used correctly:
as historical provenance establishing *that* Study 2 was already run and killed (which is what
mandates `EXCLUDED_PREVIOUSLY_KILLED` per goal.md §1.2's literal text), never as a magnitude
argument for why it should be blocked now. Combining Card 9.1 and pilot Study 2 into one record is
correct because the opening note itself establishes their identity ("it is pilot study 2"); this
also correctly explains why Study 2 (unlike Studies 1/3) is excluded rather than
`ALIASED_PROXY_ONLY` — `micro_readiness.PILOT_STUDY_STATUS['delta_divergence_level_tests']` is
`FULL_MECHANISM_READY`, not parked, consistent with it having actually been screened and killed.
The mirrored bearish/bullish direction rule is correctly labeled "provenance only, not recompiled."

### `card-9.2-delta-by-price-profile-excluded`
**Disposition under audit:** `EXCLUDED_PREREQUISITE_UNMET`. **Verdict: CONFIRMED.**
Both quoted spans match the card (line 1185) and the opening note's "Deferred unchanged" bullet
(line 1110, confirmed exact) verbatim. The card's own Build step names Card 8.2's binning as its
literal prerequisite, and the opening note confirms it was never built ("Deferred unchanged").
This is a clean prerequisite-unmet case with no outcome-based reasoning anywhere in it — the
prerequisite's absence blocks compilation before any Scout screen could exist.

### `cards-9.8-9.11-wave2-gate-closed`
**Disposition under audit:** `EXCLUDED_GATE_CLOSED`. **Verdict: CONFIRMED.**
All three quoted spans match the opening note (lines 1111 area, confirmed exact for the "Wave 2
(9.8-9.11) stays gated" sentence) and the era-ledger row (line 2045) verbatim. Combining all four
Wave-2 cards into one record mirrors goal.md's own single-arrow "Cards 9.8–9.11 →
EXCLUDED_GATE_CLOSED" treatment, and `aliases_lineage_ids` correctly enumerates all four
constituent card ids. The "zero `historical_oos`" fact is cited only to establish that the
re-pointed gate's condition remains unmet — not as an argument about likelihood of success — which
is the same disciplined use of a historical fact seen in the Study-2 record.

---

## Overall Verdict

The registry's **scientific decisions** are, with one specific exception, sound: every citation I
checked is a faithful, verifiable, essentially verbatim quotation from the named ratified source at
the stated location (several down to the exact line number), the enumeration-vs-block calls track
the constitution's own rules correctly, the two proxy records preserve their `do_not` restrictions
verbatim without laundering a partial proxy as the full mechanism, the one supersession case
(Card 9.7) is a textbook match to §1.3's own worked example, and the three exclusion records
correctly use historical facts (a prior p-value, a prior kill, an unmet gate) as provenance rather
than as likelihood arguments. Zero compiled candidates is the scientifically correct outcome given
how genuinely undirected, unthresholded, or pre-excluded every one of the 11 objects is — I did not
find a record I believe should have compiled, nor one that was blocked/excluded/aliased when it
should have compiled.

Two items should be fixed before this registry is treated as final:

1. **The checked-in JSON is missing the `audit_note` field on all 11 records**, though goal.md
   §1.4 and `hypothesis-foundry-spec.md` §1.4 both list it as a required per-record field (and the
   `SourceRecord` dataclass declares it as a required, non-optional `str`). I traced the root
   cause: `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` does construct a
   real, well-written, outcome-free `audit_note` string for every one of the 11 records in memory
   (verified by reading the script directly — e.g. the Card 9.6 shuffled-side-persistence note
   correctly explains the comparator-form reasoning) — but the script then builds the persisted
   JSON via `foundry_source_registry._canonical_source_record()`, the module's internal
   hash-canonicalization helper, which deliberately excludes `audit_note` (along with
   `source_hash` and `extra`) from its projection because those fields are correctly excluded from
   the *hash* input. Reusing that hash-projection helper as the *artifact* serializer silently
   drops a field that should never have been dropped from the human/audit-facing file. **Fix:**
   serialize the full record (e.g. `dataclasses.asdict(record)` plus `disposition`) for the
   checked-in JSON, not the hash-canonicalization projection.
2. **`card-9.6-shuffled-side-persistence`'s `direction_derivation: "long"` is not supported by its
   own cited text** (see that record's finding above) and, under the compiler's own fixed
   precedence, correcting it to the `BLOCKED_DIRECTION` sentinel would change this record's
   disposition from `BLOCKED_UNSUPPORTED_STUDY_FORM` to `BLOCKED_DIRECTION`. The same unsupported
   `"long"` value also appears on `card-9.7-event-time-feature-windows`, where it is harmless
   (supersession is checked first) but should be tidied for consistency.

Neither item changes the epoch's bottom line (zero compiled candidates either way), and item 2 is
a single-field, single-record fix. I am not raising any other concerns — I looked specifically for
a record that should have compiled, an invented threshold, a fabricated direction rule, a
citation that didn't actually appear in its source, and an audit-style argument smuggling in an
outcome/p-value/effect/PnL claim, and found none beyond the two items above.

**Both items above were fixed post-audit, before any commit — see the header note at the top of
this report for the final `source_registry_hash`/`epoch_id` and what changed.**
