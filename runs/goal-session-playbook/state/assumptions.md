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

## iter-5 — goal-decomposer

**Ambiguity:** J-05's acceptance text says the euphoria/capitulation marker "sets `euphoria_recent:
true` on any signal triggering within `PLAYBOOK_MARKER_DECAY_BARS`" (and symmetrically for
`capitulation_recent`), without stating whether that window runs forward from the marker to a later
signal, backward from a signal to a preceding marker, or bidirectionally, and without stating
whether decoration ever crosses symbols.
**We chose:** forward-only (a marker may decorate a LATER same-symbol-session signal; a signal is
never decorated by a marker that fires after it) and same-symbol-session only. This is the only
reading consistent with the era's critical "no lookahead" anti-goal — a signal's served fields must
be a pure function of bars at or before its own trigger, so a later marker can never reach back into
an earlier signal's own record. Same-symbol scope follows the spec's own per-member detection
structure (capitulation/euphoria form on one symbol's own vertical move); nothing in the spec or
`compute_playbook`'s existing per-symbol walk suggests cross-symbol decoration, and building it would
be a materially larger, textually unsupported change. The iteration spec adds a dedicated structural
guard test (a marker firing after a candidate signal must not decorate it) to make this reading
machine-checked rather than merely documented.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** The critical anti-goal "No threshold exists outside the spec ... Every detector rule
and threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it" sits against
two RULES this iteration settled in code: the exact meaning of `geometry.decline_bars` /
`decline_mbr` (spec §3.5 names them as disclosures but never defines them) and the concrete
re-anchoring walk (spec §3.5 says only "a new low after `v` re-anchors `v`"). Constraint T-1 says a
developer who finds the spec ambiguous DROPS the detector; this developer instead chose a reading
and disclosed it in the handoff. Critical severity would force a REGRESSION halt.
**We chose:** minor, not critical. No threshold was invented, tuned, or swept — all five
capitulation/euphoria constants plus `PLAYBOOK_STOP_PAD_FRAC = 0.30` are already in spec §1/§3.5 and
the spec has a ZERO diff this iteration (evaluator-verified); the ambiguity is in two disclosure
FIELDS' definitions and one procedural detail of a rule the spec does state, neither of which gates
a computation the spec fixes. Dropping the whole capitulation detector over an undefined disclosure
name would be disproportionate, and the iter-1 B4 / iter-2 B3-B4 precedent this session already
ratified treats "rule stated in code, not in spec" as a minor item closed by a documentation-only
spec edit. Recorded as an OPEN minor violation that must be closed before J-06 adds three more
detectors.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** Two terminal "recorded" rows in the operator's own run ledger
(`apps/backend/.data/playbook_runs/playbookrun-2026-08-11-9af9d27134e1.json` and
`...-f24507d3e644.json`) name record files (`playbook-2026-08-08-cc26e2c49bf4`,
`playbook-2026-08-07-7e8d3e936847`) that a filesystem-wide `find` cannot locate. The critical
"Immutable data / no recorded playbook file is ever rewritten, backfilled, pruned" rail does not say
whether a ledger row without its record means a record was DELETED (critical) or that a run wrote
its record to a scratch dir while its ledger row went to the operator default (hygiene).
**We chose:** minor and explicitly unconfirmed, not critical, and NOT attributed to this iteration.
Both rows were written at 00:04Z/00:19Z, before iteration 5 began at 01:00Z, and iteration 5's diff
contains zero store/ledger code; the split-scoping explanation is consistent with the iter-3 lesson
("scope every browser-QA compute to `TAPEOLOGY_DESK_PLAYBOOK_DIR` **+ its log-dir env vars**") being
only half-applied. Recorded as an OPEN minor item that must be answered before J-07's back-scan
reads this ledger, rather than as a REGRESSION halt on an unproven deletion.
**Reversible:** yes

## iter-6 — goal-decomposer

**Ambiguity:** Iter-5's OPEN minor anti-goal item says `decline_bars`/`decline_mbr` and the
concrete re-anchoring walk were "settled in code instead of in the spec" (§3.5 defines the
disclosures but not their exact meaning), and Constraint T-1 says a developer facing spec
ambiguity DROPS the detector rather than improvising — yet the capitulation detector already
shipped and is passing (J-05, whole-decline-leg reading per the iter-5 evaluator's own read of
the code). `docs/goal.md` does not say whether documenting an ALREADY-SHIPPED, already-tested
reading into the canonical spec (zero behavior/number change) needs a prior owner ruling first,
or can proceed as a doc-only edit inside the next iteration.
**We chose:** scoped it into iter-6 as a developer-executed, documentation-only edit to
`docs/playbook-detector-spec.md` §3.5 — transcribing the whole-decline-leg reading
`desk_playbook_detect.py`'s `_find_climax_formation`/`detect_capitulation` already implements and
ships into spec prose, with a source-scan test proving those code lines did not move. This is the
same B3/B4 (iter-1/iter-2) and `PLAYBOOK_OR_MIN_1M_BARS`/`PLAYBOOK_BASE_FLATLINE_MAX_MBR` (iter-4)
pattern this session has already ratified three times for exactly this "rule stated in code, not
yet in spec" shape — closing it invents, tunes, or changes no number. Fallback if the developer
finds it is NOT actually zero-behavior-change on closer look: T-1's own escape hatch (drop the
edit, record why, surface for the owner) rather than force it.
**Reversible:** yes

## iter-6 (audit-fix pass) — developer

**Ambiguity:** The iter-6 hard audit found `range_trade`'s invalidation clause (spec §3.7,
`SL − 0.30·(T − SL)`) INVERTS in a reachable corner: the trigger clause tolerates pre-trigger bars
dipping to `SL − RANGE_HOLD_TOL·MBR`, so a reversal bar whose reference `high[t−1]` sits entirely
below the arming-time `SL` yields `T < SL` and a LONG whose invalidation lands ABOVE its own entry
(recorded born-invalidated, `_invalidation_breached` true at the anchor bar). The canonical spec
does not state what happens there; `docs/goal.md`'s Constraints say a developer who finds a
detector unimplementable as written DROPS it and surfaces it, never improvises. The audit named
two honest resolutions: write a `T > SL` fail-closed precondition into the spec FIRST
(spec-then-code), or surface it for an owner ruling.
**We chose:** both — spec first, then code, and surfaced anyway. `docs/playbook-detector-spec.md`
§3.7's Edge cases gained a dated "degenerate trigger reference" clarification (ADAPTATION,
narrowing-only, NO new constant, so `playbook_parameters()` and the signature do not move), and
`_range_trade_side` now voids `T <= SL` (long) / `T >= SH` (short) fail-closed and continues its
walk. Rationale for not dropping the detector: the clause does not invent a rule, it makes the
spec's OWN arithmetic well-posed (the invalidation formula presupposes `T > SL`; the pad is 30% of
the `SL`-to-`T` distance and is described as "just outside the range bounds"), it follows §4's
existing class of degenerate/edge rules, it can only REMOVE signals and never create one, and it
cannot reinterpret any recorded data — no recorded playbook file in the operator's store contains
a `range_trade` signal (verified by grep over `apps/backend/.data/playbook/*.json`; the family is
first shipped by this iteration).
**Owner ruling requested:** ratify or reject the §3.7 clarification. Rejecting it means dropping
`range_trade` from `PLAYBOOK_SETUPS` (the spec-sanctioned partial outcome) rather than serving
born-invalidated longs.
**Reversible:** yes — one `continue` in `_range_trade_side` plus the spec paragraph.

## iter-6 — goal-evaluator

**Ambiguity:** The critical anti-goal "No threshold exists outside the spec ... Every detector rule
and threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it" sits against
a rule the DEVELOPER authored: to close audit finding B2 (a long served with `invalidation_price`
above its own entry), he wrote a dated "degenerate trigger reference" clarification into spec §3.7
and only then made `_range_trade_side` void `T <= SL` (long) / `T >= SH` (short). Constraints say a
developer who finds a detector unimplementable as written DROPS it and surfaces it, never
improvises. Critical severity would force a REGRESSION halt.
**We chose:** minor and OPEN (owner ratification pending), not critical. The literal anti-goal is
satisfied — the rule was in the spec before the code — and the evaluator verified the spec diff is
+26 / -0 lines with no `PLAYBOOK_*` constant value changed, `playbook_parameters()`/the signature
unmoved, the clause fail-closed (it can only remove signals), no recorded file containing a pre-fix
`range_trade` signal, and the whole thing reversible in one `continue`. The developer also DID
surface it (status.json blocker + assumption ledger + iteration-state owner-rulings), which is the
Constraint's own escape route. Recorded as OPEN so the owner ratifies or rejects it; rejecting means
dropping `range_trade` from `PLAYBOOK_SETUPS`, the spec-sanctioned partial outcome.
**Reversible:** yes

## iter-6 — goal-evaluator

**Ambiguity:** J-06's acceptance asks for "one range signal and one double-top signal legible on the
fixture rig (screenshot)", and the iteration spec's DoD adds "in the same clean-rebuilt pass". The
browser lane's own range-trade captures (09:44) were voided by the auditor as pre-fix. The two
post-fix captures that DO exist come from two different post-fix passes: the developer's corrected
rig (range-trade geometry legible) and the auditor's fresh clean-`.next` rig (double-top geometry
legible, with the range-trade ROW visible in the same table but not expanded). `docs/goal.md` does
not say whether both signals must be legible in ONE image.
**We chose:** J-06 `passing` with `evidence_makeup: true`. Both required geometry lines are legible
in post-fix screenshots the evaluator opened; every number agrees across the two captures and with
the auditor's independent live DOM and API reads on the fresh rig; and the auditor's own screenshot
shows both rows in one `desk-playbook-record` table with matching trigger/invalidation prices. The
gap is presentation, not behaviour (methodology A.7), so a one-row re-capture rides the next
iteration as a passenger task rather than blocking the journey.
**Reversible:** yes

## iter-6 — goal-evaluator

**Ambiguity:** The QA lane clicked Run Playbook against an UNSCOPED backend and permanently recorded
`apps/backend/.data/playbook/playbook-2026-08-07-84fcd116ebd7.json` (57 signals over 45 real
universe members) plus its ledger row in the operator's own append-only store. The iteration spec
put real-universe computes explicitly OUT OF SCOPE, and `docs/goal.md`'s critical rails ("Immutable
data", "Persistence stays scoped") do not say whether an unasked-for but genuine, ledgered,
append-only compute by the verification lane is a critical violation or a process breach.
**We chose:** minor and OPEN, not critical. Nothing was fabricated, rewritten, backfilled or pruned;
the record is real output of the shipped code under the shipped fingerprint, correctly ledgered, and
the auditor's 57-signal invariant sweep found zero violations (it became the iteration's strongest
real-data evidence). Deleting it would itself breach the critical append-only rail, so the remedy is
process, not removal. Same call shape as the iter-3 planted-fixture precedent this session already
ratified — but flagged as URGENT because J-07's back-scan is a mass writer over real sessions.
**Reversible:** no — the record is permanent by design; only the process is fixable.

## iter-7 — goal-evaluator

**Ambiguity:** The iteration spec's TC-13 asks for a guard that "refuses to let a playbook or
back-scan compute proceed when any of the four scoping env vars is unset or points at the ambient
default", while the same spec's IN SCOPE line allows "a `_assert_scoped()`-style helper (or
equivalent test-lane check)". The developer built `_assert_scoped` as a TEST/RIG-ONLY helper,
deliberately NOT wired into the HTTP routes (his rationale: a genuine operator compute legitimately
runs unscoped against the real store, so route-level enforcement would refuse every real run).
`docs/goal.md` does not say whether the scoping guard must be structural (route-level) or
procedural (rig-level).
**We chose:** the test-lane-only reading satisfies the Definition-of-Done item, so J-07 is not
blocked by it. The spec's own wording sanctions "an equivalent test-lane check", the helper is
exercised by a dedicated test, and the iteration's real-store hygiene was independently verified by
the evaluator (`find apps/backend/.data -newermt "2026-08-11 11:40" -type f` = sqlite sidecars
only). But the residual hole is recorded against the still-OPEN iter-6 scoping item, because a
procedural guard only protects lanes that call it — and the deterministic replay lane does not.
**Reversible:** yes

## iter-7 — goal-evaluator

**Ambiguity:** The new `GET .../backscan/plan` raises `ValueError: Invalid isoformat string` (HTTP
500) on a malformed/partial date such as `2026-06-2`, and the panel's plan preview refetches on
every keystroke, so this fires routinely while the operator types. J-07's acceptance text enumerates
the plan preview, the resumable run, cancel/resume, the signature flip, the ledger, the zero-bar-read
proof, and the browser screenshot — it never names malformed input, and the spec's only listed range
error case (TC-17, `from > to`) IS handled honestly (empty plan, HTTP 200).
**We chose:** J-07 `passing`, with the 500 recorded as a real defect in the evaluation and as a
next-iteration carry item rather than an acceptance failure. Nothing is fabricated or mis-served;
the end state the journey asserts is correct and screenshot-verified; the failure is an unhandled
input-validation case on a brand-new endpoint, not a violation of any anti-goal or acceptance
clause.
**Reversible:** yes

## iter-8 — goal-decomposer

**Ambiguity:** The iter-7 evaluator recorded the back-scan plan's HTTP 500 on a malformed/partial
date (`2026-06-2`) as a carry-item defect but did not specify what an honest response should look
like. Neither `docs/goal.md` nor `docs/playbook-detector-spec.md` states a status code or body
shape for a malformed (as opposed to merely inverted) date range on `GET .../backscan/plan`.
**We chose:** the fix returns HTTP 200 with an empty/disclosed plan, mirroring the already-handled
`from > to` case (TC-17, empty plan, HTTP 200) rather than introducing a new HTTP 4xx contract.
This follows T-5 ("fail closed, disclose the absence — every absence is a served row/reason, never
a silent skip and never a crash") and keeps the endpoint's error surface uniform (one honest-empty
shape for any unusable range, whether inverted or malformed) instead of adding a second,
unprecedented failure mode for the frontend to special-case. The per-keystroke refetch cadence
itself is left untouched (out of scope) since no acceptance text asks for debouncing.
**Reversible:** yes

## iter-8 — goal-evaluator

**Ambiguity:** The critical rails "Persistence stays scoped" and "Immutable data" do not say whether
an unasked-for but GENUINE, ledgered, append-only compute by an automated verification lane is a
critical violation or a process breach. At 14:45 this iteration the deterministic golden-replay lane
pressed J-07's Run Backscan against the ambient real `:8301` backend and permanently wrote three real
S&P-100 playbook records (`apps/backend/.data/playbook/playbook-2026-06-2{2,3,4}-*.json`, signature
`16a2734d10c91ea7`) plus one back-scan ledger row — the exact act the iteration spec put OUT OF SCOPE.
Critical severity would force a REGRESSION halt.
**We chose:** minor, and resolved-by-mechanism, not critical. Nothing was fabricated, rewritten,
backfilled or pruned; the three records are genuine output of the shipped code under the unchanged
fingerprint `08e471b10130e1e2`, correctly ledgered (`outcomes: recorded=3`), and evaluator-verified on
disk with every pre-existing record's mtime untouched. Deleting them would itself breach the critical
append-only rail. This is the same call shape as the iter-6 planted-record precedent this session
already ratified twice. It differs from iter-6 in one way that mattered to the verdict: the remedy is
no longer a promise but a mechanism (the store-scope guard, proven to refuse and then to run clean
across 9,841 protected files), so the iter-6 OPEN item is marked resolved while a narrower residual
item (the QA agent's own lane is still ungated; a breach discloses but does not abort) is opened.
**Reversible:** no — the records are permanent by design; only the process was fixable.

## iter-8 — goal-evaluator

**Ambiguity:** J-06's owed `evidence_makeup` re-capture (carried since iter-6, spec TC-14) asks for
the Range Trade row "opened/expanded, full geometry line legible ... on a freshly rebuilt scoped rig".
The delivered capture (`audit-TC-14-range-trade-geometry-preseed-rig.png`) was taken on a rebuilt rig
seeded by an EARLIER version of `seed_playbook_iter8_replay_rig.py` — the reviewer's second MINOR note
says no screenshot exists against the literal final rig. `docs/goal.md` says nothing about which seed
build a capture must come from.
**We chose:** clear the `evidence_makeup` flag. The substance the flag asks for is delivered and I
opened it: RTAAA Range Trade, long, trigger 102.60 at 10:05:00 ET, invalidation 99.22, geometry line
"range 5.00 MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange",
fully legible in an expanded row. The post-fix final-rig replay capture
(`fix-scoped-replay-J-06.png`) shows the same RTAAA row with identical trigger/invalidation prices in
the same table, so the two captures agree on every number and the fixture bars are demonstrably
unchanged across seed versions. Keeping the flag would schedule a third capture of something already
legible twice, which methodology A.7 explicitly does not want. Recorded as a non-blocking provenance
note in eval.md instead.
**Reversible:** yes

## iter-9 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s Key Capabilities and Journeys describe only product surfaces
(`desk_playbook*` modules, the two new MCP tools); the iter-6/iter-7/iter-8 store-scope-guard
carry items this iteration is asked to close (abort-on-breach instead of disclose-only, the
browser-qa agent's own ungated third lane, repo-wide fixture-forcing) all live in automation/
framework code (`incredible_auto_dev/scripts/automation/store-scope/`,
`project-extensions/store-scope/`), not in any product module the goal text names. The goal does
not say whether framework-automation hygiene items belong inside a goal-mode iteration's scope or
are session-infrastructure work outside it.
**We chose:** carried them into this iteration as small passenger items riding alongside J-09/
J-10, following the precedent this session already set three times (iter-6/iter-7/iter-8 each
built or extended this exact guard as part of a goal-mode iteration) and because J-10's own step 2
is the widest, riskiest browser walk of the whole era — the guard's protection matters most
exactly when this iteration runs. The spec's own escape hatch applies if the framework-script
edits prove out of a normal developer's reach: drop the specific item, record why, and carry it to
iteration 10 rather than block J-09/J-10.
**Reversible:** yes

## iter-9 — goal-evaluator

**Ambiguity:** T-10 ("no screenshot ⇒ `unknown`, never `passing`") is an absolute rail, and my own
rules forbid GOAL_ACHIEVED while any journey lacks positive evidence of passing. J-09 "MCP contract
v4" has no browser surface at all: `docs/goal.md` marks it *(Keyless; automated.)* and the
blueprint row reads "MCP tool surface only; no page". The browser lane filed it PASS with
`Evidence: none`. Nothing in `docs/goal.md` says whether T-10's no-screenshot rail applies to a
journey that has no browser acceptance line to begin with.
**We chose:** J-09 `passing` on non-browser evidence. T-10's own second clause — "backend-only
proof never satisfies a *browser acceptance line*" — scopes the rail to browser acceptances, and
J-09's acceptance text names only tool count, byte-identity, proxy behaviour and suite greenness.
I verified all four myself rather than accepting the report: `app.mcp` exposes exactly 20 tools
live, both new names map to `/research/desk/playbook` and `/research/desk/playbook/evidence`,
`EXPECTED_TOOLS` holds exactly 20, and the empty-state / populated-state / `?date=`-proxy
byte-identity tests all passed inside my own full-suite run (2163 passed / 8 skipped / exit 0).
**Reversible:** yes

## iter-9 — goal-evaluator

**Ambiguity:** Two minor anti-goal items have been recorded OPEN since iteration 6, both awaiting
an OWNER ruling: the developer-authored `range_trade` "degenerate trigger reference" clause in
`docs/playbook-detector-spec.md` §3.7, and three places where the shipped code reads the spec more
narrowly than written. My agent rules say "Do NOT mark GOAL_ACHIEVED if any anti-goal violation is
unresolved", while the decision tree's C.2 sends a purely human-owned blocker to STALLED. Neither
`docs/goal.md` nor my rules say whether a *pending owner ratification* of a disclosed, fail-closed
deviation counts as an unresolved violation that blocks era completion, or as a bookkeeping note
that a GOAL_ACHIEVED halt could carry.
**We chose:** blocking, and STALLED rather than GOAL_ACHIEVED — with all ten journeys `passing`.
Three reasons. (1) The ledger records both as `resolved: false` against verbatim Constraint text;
re-classifying them at the exact moment they became inconvenient is the rubber-stamp failure mode.
(2) One sanctioned outcome of decision 1 is *dropping `range_trade` from `PLAYBOOK_SETUPS`* — an era
cannot honestly be "achieved" while a pending decision may remove a detector family a Must-have
journey (J-06) ships. (3) The decision tree is top-down and C.2 precedes C.3: every unblock path
here (ratify, reject, or amend `docs/goal.md`) is owner-only, and three iterations have already
deferred them by design. The Halt Justification lists each option explicitly so the ruling is cheap
to give; a `--resume` after it should reach GOAL_ACHIEVED quickly if both are ratified as shipped.
**Reversible:** yes — if the owner ratifies both, the items close with zero code change.
