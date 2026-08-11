# Goal Session playbook — Assumption Ledger

Append-only. One entry whenever scoring an iteration required interpreting an
ambiguous goal rather than just reading evidence. Zero entries is normal.

## iter-0 — goal-evaluator

**Ambiguity:** J-10's acceptance text bundles kept-product behaviour ("full suite green under the
unchanged pin", "every browser step evidenced by screenshot", "nav = exactly three routes") with a
clause that only becomes true at the END of the era ("MCP = exactly 20 tools"). The goal never says
how to score J-10 while the era is mid-flight, and the iteration spec explicitly left the call to
the evaluator.
**We chose:** `partial` — the kept half is fully evidenced (screenshots of the cockpit,
`/structure`, and every shipped `/desk` section; suite 1926 pass / 8 skip; fingerprint
`08e471b10130e1e2`), while the 20-tool clause is recorded as not-yet-satisfiable rather than as a
failure of the kept product. This mirrors what the previous era's baseline did with its own
sentinel journey (`runs/goal-session-desk/iter-0/eval.md`, J-07).
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-10's required verification (TC-14, the golden-script replay) was executed by
nobody, and the auditor explicitly recommended recording J-10 as `unknown-by-replay` for iter-1.
The goal never says whether a sentinel journey keeps its status when the iteration provably touches
none of its surfaces.
**We chose:** kept J-10 at `partial` (its prior status) under the evidence-durability rule — the
frontend diff is empty and the only shipped-file change is `desk_routes.py` at +75/-0 inside one
new block, so iter-0's screenshots still show the current product. The un-run replay is recorded as
an explicit gap and demanded of the next iteration, rather than expressed as a status downgrade.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** `docs/goal.md` marks "No threshold exists outside the spec" *(critical)*, but
`desk_playbook_detect.py:276` settles a spec RULE (§3.1's "Principles: P4 when pre-break pullbacks
were shallow and dry") in code without inventing any threshold or sweeping anything. The auditor
recorded being genuinely unsure between GAP and IMPORTANT. Critical severity would force a
REGRESSION halt.
**We chose:** minor, not critical — nothing is fabricated, no threshold is invented, no sweep
exists, and the field is a disclosure label that gates no computation. Recorded as an open minor
violation requiring an owner ruling in `docs/playbook-detector-spec.md` before J-08 groups evidence
by principle.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** The iter-1 audit (`docs/handoffs/goal-playbook-iter-1-audit.md` B3/B4) flagged
`PLAYBOOK_OR_MIN_1M_BARS` missing from spec §1's table, and the code's `principles = ["P4"] if
spike_verdict == "constructive"` mapping existing without matching spec prose, as each needing an
"owner ruling" before further code relies on them. Neither the audit nor `docs/goal.md` says
whether that "owner" must be the human operator or can be resolved inside the goal-mode chain when
the fix is zero-behavior-change documentation catch-up.
**We chose:** scoped both into iter-2 as developer-executed, documentation-only edits to
`docs/playbook-detector-spec.md` — B3 transcribes a value/rationale already stated in the spec's own
§2 prose and already in code (`desk_playbook.py:94`'s comment) into §1's table; B4 states in spec
prose the exact discriminator (`spike_into_trigger_verdict == "constructive"`) the already-shipped,
already-tested code already uses, reusing a discriminator §0 already defines. Neither invents a
threshold, changes a value, or alters tested behavior — both catch the spec up to what iter-1
already shipped, per the audit's own "defensible"/"the right call" language. Fallback if either
turns out NOT zero-behavior-change on closer look: T-1's own escape hatch (drop it from the
iteration, record the drop, surface it for the human operator explicitly) rather than force a
resolution.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-02's acceptance text in `docs/goal.md` says J-01-era records must serve "with the
honest `\"measurement not recorded in this record\"` absence". That exact sentence exists nowhere in
the product — the backend instead serves a structural absence (no `forward` key on the signal, empty
`baseline_anchors`/`summary`/`signals_beyond_cap`, `payload_version` 1) plus a register sentence in
its own words. The same quoted string is also listed under J-03 as UI copy for legacy records.
**We chose:** counted J-02's absence requirement as met by the structural, machine-detectable
absence (proven never-backfilled and SHA-256-unchanged by
`test_j01_era_record_serves_verbatim_with_honest_absence_and_unchanged_sha`), and moved the literal
sentence into J-03's binding carry list, where the goal itself places it as page copy.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** The critical anti-goal "No threshold exists outside the spec" plus §1's own header
("the COMPLETE tunable surface — nothing else exists") sit against a new numeric knob the code now
depends on: the cross-symbol pooling cap for `baseline_anchors`/`summary`, implemented as the rail's
existing `DESK_FORWARD_MAX_TOUCHES_PER_ROW`, which appears in no row of `docs/playbook-detector-spec.md`
§1. J-02's own step 3 demands "signal caps + beyond-cap disclosure" without naming a constant.
**We chose:** not a violation. The spec's §0 Measurement paragraph already delegates this area
verbatim ("Horizons, measures, dual MDD, truncation honesty, and the seeded random-anchor baseline
are the rail's, unchanged"), the number is imported rather than invented, it is echoed into
`playbook_parameters()` as `rail_max_touches_per_row` so a future change re-keys records, and no code
path iterates it against outcomes. Recorded as an observation only — if the owner disagrees, the fix
is one spec row, not a code change.
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** The iter-2 evaluator's next-step recommendation asked to "reuse the rail's own
long/short helper instead of repeating it," naming `desk_forward.py`'s `_side_sign` as that helper.
`docs/goal.md` never says whether a carried recommendation must be followed literally even when
closer reading shows the named helper is semantically wrong for the target vocabulary.
**We chose:** did NOT literally reuse `desk_forward._side_sign` — its body
(`-1.0 if side == "resistance" else 1.0`) is built for the rail's own support/resistance wall
vocabulary; called with playbook's `"short"` side it returns `+1.0` (since `"short" != "resistance"`),
which would silently flip every short signal's forward return and MDD sign positive. `_measure_from`'s
own docstring confirms `sign` is caller-supplied, not a mandated `_side_sign` call — the rail's own
caller at `desk_forward.py:716` computes its own sign for its own vocabulary the same way. Instead,
iter-3 consolidates the three duplicated `1.0 if side == "long" else -1.0` literals (two in
`desk_playbook.py`, one in `desk_playbook_detect.py`) into one new playbook-owned `side_sign` helper
in `desk_playbook_features.py`, satisfying the evaluator's actual concern (one owner, not three
copies) without importing an incompatible helper or touching `desk_forward.py`.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-03's step 1 in `docs/goal.md` lists the provenance line as "record id, signature,
parameters hash, fingerprint", but no `parameters_hash` field is served anywhere by
`desk_playbook.py`/`desk_playbook_compute.py`, and the iteration's IN SCOPE forbids inventing
fields. `compute_playbook_input_signature`'s own recipe already folds the canonical parameters blob
(plus bar checksums and the config fingerprint) into `playbook_input_signature`, and the full
parameters blob is embedded verbatim in every payload. J-03's binding "Acceptance:" paragraph says
only "provenance", without enumerating fields.
**We chose:** counted the provenance requirement as MET by record id +
`playbook_input_signature` + `config_fingerprint` + the rendered sentence stating what the
signature hashes (visible in `reports/qa/goal-playbook-iter-3-evidence/J-03-TC2-populated-table.png`).
Rejected the alternative of a client-computed parameters hash, which would compute a served value
in the browser — the exact single-source-of-truth violation the era's anti-goals forbid. Flagged
for an owner ruling before J-07/J-08 reuse the same provenance line.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** The browser-QA lane planted a synthetic `payload_version` 1 record into the
operator's live playbook store (`apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json`)
to exercise TC-5. `docs/goal.md`'s foundation invariant "no fabricated data" and the critical
"no recorded playbook file is ever rewritten, backfilled, pruned, or superseded" rail do not say
whether a self-disclosing test fixture APPENDED to a real store by the verification lane is a
critical violation (which would force a REGRESSION halt) or a hygiene defect.
**We chose:** minor, not critical. Nothing was rewritten or perturbed (append only); the record
declares itself in its own payload (`playbook_input_signature: "bqa-legacy-fixture-signature"`,
register "…(browser-qa TC-5 fixture)"); it is git-ignored and never left the machine; and the
critical "evidence pools ONE signature" rail structurally prevents it from ever entering a
distribution. Recorded as an OPEN minor violation whose fix (delete the file; scope future plants
to `TAPEOLOGY_DESK_PLAYBOOK_DIR`) is required before the era can be declared achieved.
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** The auditor's F1 fix to `apps/frontend/app/desk/page.tsx` (the dbi base-shape label,
"ascending base" -> "descending base") landed AFTER the browser pass, so the only screenshot for
J-04's TC-2 (`reports/qa/goal-playbook-iter-4-evidence/UT-03-result.png`) shows the pre-fix wording.
`docs/goal.md` never says whether a screenshot that predates an in-iteration fix still satisfies a
browser acceptance line.
**We chose:** J-04 `passing` with `evidence_makeup: true`. J-04's own acceptance asks that "at least
one signal of each new setup [be] legible in the J-03 section on the fixture rig (screenshot)" — the
DBI row IS legible with its chip, side and full geometry in that screenshot, and the fix changed one
descriptive word to match the measurement already served (no field, number, or behavior moved; guarded
by a new source-scan test plus its seeded counter-test). Treated as a capture defect (methodology A.7),
so a one-row re-capture rides the next iteration as a passenger task rather than blocking the journey.
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** The Copy-discipline constraint says the served `PLAYBOOK_REGISTER` "state[s] what was
measured and what was NOT". After this iteration the register (`desk_playbook.py:159`) and the `/desk`
blurb still name only the opening-range-break family, while new records carry `jbe`/`dbi`/`cup_handle`
signals. The goal does not say whether an under-describing register is a J-04 acceptance failure or an
era-level copy defect.
**We chose:** era-level OPEN minor violation, not a J-04 failure. J-04's acceptance enumerates fixture
goldens, silent near-misses, the lookahead property test, SHA-256 re-keying, browser legibility, suite
green and pin unchanged — the register is not among them, and every per-signal disclosure is honest and
complete. Recorded as an unresolved minor violation that must be fixed before the era can be declared
achieved (and before J-05/J-06 widen the gap further).
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** The critical anti-goal "No threshold exists outside the spec ... BEFORE the code that
uses it" sits against two constants this iteration introduced — `PLAYBOOK_BASE_FLATLINE_MAX_MBR = 1.0`
and `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC = 0.25` — whose spec table rows were added in the SAME
commit as the code. The coherence auditor flagged both as needing "the same owner ruling" as the
`PLAYBOOK_OR_MIN_1M_BARS` precedent.
**We chose:** not a violation. The evaluator read the pre-iteration spec (`git show ac6e9ad:docs/playbook-detector-spec.md`)
and both VALUES already existed there in prose — line 242's "base range <= 1.0 MBR — the
flatline-at-the-high variation" and line 148's "(25% desirable -> disclosure)". Only the naming and
tabulation are new, which is the iter-2 B3/B4 spec catch-up pattern this session already ratified.
Nothing was invented, tuned, or swept. Flagged for owner visibility alongside the auditor's B1/B3
constants questions.
**Reversible:** yes
