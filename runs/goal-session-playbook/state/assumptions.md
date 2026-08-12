# Goal Session playbook — Assumption Ledger

Append-only. One entry whenever scoring an iteration required interpreting an
ambiguous goal rather than just reading evidence. Zero entries is normal.

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

## iter-10 — goal-decomposer

**Ambiguity:** R-3.2(b) directs a second `range_trade` geometry disclosure ("whether the prior
swing turned at midrange, the BOOK midrange rule") beside the existing `crossed_midrange` field,
binding its mechanical definition to reuse an already pre-registered constant and to be written
into `docs/playbook-detector-spec.md` spec-first — but neither R-3.2(b) nor `docs/goal.md` names
the served field itself.
**We chose:** the iteration spec commits to `geometry.turned_at_midrange: boolean` (optional key,
same shape as the existing `crossed_midrange?: boolean` in `apps/frontend/lib/types.ts:1523`) as
the ONE canonical name, registered as such in this iteration's Data-contract addition and in
`blueprint.md`'s "Playbook records" row, so the spec edit, the detector code, `types.ts`, the
`/desk` chip, and the blueprint all agree without a naming round-trip. The spec does not dictate
the mechanical bar-by-bar test itself (that stays the developer's spec-first authoring job, per
the `docs/playbook-detector-spec.md` "is canonical" discipline and the iter-5 lesson that
decomposer-invented field definitions need a degeneracy check before being treated as binding) —
only two ALREADY pre-registered candidates are named as options (`PLAYBOOK_RANGE_HOLD_TOL_MBR`,
already this detector's own "held" tolerance; or the existing `swing_pivots` primitive keyed by
`PLAYBOOK_PIVOT_LOOKBACK_BARS`), and R-3.2(b)'s own drop-and-surface escape hatch is carried
verbatim into the DEFINITION OF DONE as a legitimate alternative outcome.
**Reversible:** yes — a rename before the field ships touches only the spec paragraph, one dict
key, one `types.ts` line, one JSX chip, and this blueprint row; no signature or stored record is
keyed by the field's name.

## iter-10 — goal-evaluator

**Ambiguity:** Whether the two "The spec is canonical" items carried `resolved: false` since
iteration 6 are discharged by the owner's R-3 ruling. My rules say "Do NOT mark GOAL_ACHIEVED if any
anti-goal violation is unresolved", but neither `docs/goal.md` nor my rules state what evidence
turns an owner ruling into a discharge — whether the ruling alone closes the item, or the spec
catch-up edits it directs must also have landed.
**We chose:** discharge requires BOTH, and I verified both. R-3.1 needs no code and closes on the
ruling alone (the owner is the only party who could ratify, and the block is in the snapshot commit
the iteration was dispatched from — so it is not a developer self-authorisation). R-3.2 explicitly
directs spec edits, so I treated it as open until I had read all five landed in
`docs/playbook-detector-spec.md` (+44/-16) AND git-proved zero detector change (`+13/-0`, one
function) AND confirmed R-3.2(b)'s three binding constraints in source (disclosure-only, reuses
`PLAYBOOK_RANGE_HOLD_TOL_MBR`, optional/never backfilled). Both marked resolved.
**Reversible:** yes

## iter-10 — goal-evaluator

**Ambiguity:** UT-05's `FAIL` (the invalid-date input's border never turns amber). The word "amber"
appears nowhere in `docs/goal.md`, so this is a test-designer expectation, not an acceptance line or
an anti-goal; the semantic contract it guards (`aria-invalid="true"`, the verbatim error message,
an honest empty state) is intact and visible in the screenshot I opened. Nothing says whether such a
row should count against a journey's status.
**We chose:** it does NOT downgrade any journey — it is cosmetic and pre-existing (`page.tsx` has
exactly one diff hunk this iteration, at 5094-5107; the date input lives at 5583-5592), so it is
neither a regression nor a violation. But I did NOT talk it away either: it is a real `| FAIL |`
cell, the deterministic results gate blocks on it (I ran it: rc=1), and I let that stand rather than
argue the gate should ignore a P2 row. Recorded as a next-iteration fix-or-drop item.
**Reversible:** yes

## iter-10 — goal-evaluator

**Ambiguity:** J-09 carries `DEFERRED-BUDGET` (no lane re-verified it; it has no golden script), yet
I independently confirmed its substantive acceptance live — `app.mcp` exposes exactly 20 tools and
the suite that pins the 20-tool tuple ran green. My instructions say a deferred journey keeps its
prior status and blocks GOAL_ACHIEVED; they do not say whether the evaluator's OWN live check
counts as this iteration's re-verification.
**We chose:** it does not. J-09 keeps `status: passing` (carried), but `last_verified_iter` stays
`goal-playbook-iter-9` and its `spec_hash` is carried forward rather than re-stamped, so the drift
audit keeps meaning what it says. The live check is recorded in the evidence field as an
evaluator observation, explicitly not a lane verdict. Fail-closed: "I spot-checked it" must not be
able to launder a journey that no verification lane ran.
**Reversible:** yes

## iter-11 — goal-decomposer

**Ambiguity:** The iteration-10 evaluator asked J-09 "MCP contract v4" to get a "saved replay
script" because it is the only journey with none. But `demo_runner.py` (the engine behind every
`journey-scripts/*.json` golden in this repo) supports exactly five browser action types —
`goto`/`click`/`fill`/`wait_for`/`expect` — and no API/MCP-call action type exists anywhere in this
codebase's history. J-09's own acceptance text (ratified at iter-9, "Do not redo" this iteration)
names only tool count, byte-identity, proxy behaviour, and suite greenness — none of which any
browser page renders (the blueprint itself records J-09 as "MCP tool surface only; no page").
Neither `docs/goal.md` nor the evaluator's note says what a browser-replay golden for a page-less
journey should assert.
**We chose:** author a golden that opens `/desk` and asserts a static, already-shipped shell string
distinct from J-01.json's/J-08.json's own assertions (the `desk-evidence-signature` label text is
offered as a candidate) — honestly scoped as coverage of the DATA the MCP tools proxy
byte-identically, not of MCP transport/registration itself. That half of J-09's acceptance stays
covered by the already-existing, already-pinned `test_mcp_server.py::EXPECTED_TOOLS`/`TOOL_NAMES`
test plus a live, same-iteration browser-qa confirmation (mirroring the iter-9 evaluator's own
manual check), not by a new framework action type. The alternative — teaching `demo_runner.py` an
API/MCP-call step — was rejected as unrequested, cross-cutting framework risk for a three-item
mechanical iteration.
**Reversible:** yes — the golden script is additive test infrastructure; nothing it asserts is
load-bearing on any served field or record shape.

## iter-11 — goal-decomposer

**Ambiguity:** UT-05 (the invalid-date Playbook Signals input's border staying grey instead of
turning amber) was left open by the iteration-10 evaluator with two sanctioned outcomes: fix the
CSS class, or drop the expectation, since `docs/goal.md` never mentions a border color and the
evaluator noted the owner could decline the extra pass entirely. No owner input on this specific
point has been communicated for this iteration.
**We chose:** fix, scoped to the one flagged input only (`page.tsx:5583-5592`), not the shared
`ASOF_INPUT_CLASS` constant (which also styles two KEPT, frozen Era-B/R-2 surfaces carrying the
identical latent collision) and not the Backscan panel's own From/To inputs (which never had this
affordance and were never named by UT-05). This is the cheaper, more honest default absent a
contrary owner signal — it makes an already-disclosed state (`aria-invalid` + visible error text)
also visible on the input's own edge, at minimal, well-isolated blast radius.
**Reversible:** yes — a one-input CSS override with no data, schema, or signature implications.

## iter-11 — goal-evaluator

**Ambiguity:** `reports/phase-goal-playbook-iter-11-demo.json` step 2 narrates the UT-05 amber-border
fix as shipped (`"new": true, "verified": true`) when I proved in source it was never built
(`page.tsx:5591` unchanged). My rules say a MINOR anti-goal violation forces CONTINUE and that
GOAL_ACHIEVED is barred while any anti-goal violation is unresolved. Nothing in `docs/goal.md` says
whether a false claim in a non-product showcase artifact is one of ITS anti-goals.
**We chose:** not an anti-goal violation of `docs/goal.md`, so it does not bar GOAL_ACHIEVED — but
recorded loudly, in four durable places (eval.md Halt Justification, evaluator-log, iteration-state
blockers, lessons.md), as an open honesty defect that must be corrected before the era's showcase
artifacts are published. I walked all ten immutable rails plus the Era-B and playbook-era anti-goals
individually: the demo narration is not a signal/chip/evidence cell (so the copy-discipline rail does
not reach it), carries no $ figure or prediction, touches no record, and moved no data. It offends
`.claude/core.md`'s "every claim cites evidence", which is framework law, not a goal.md anti-goal.
Fail-closed reasoning applied to the OTHER direction too: I did not let the green results gate stand
as evidence of a repair, since UT-05 is absent from this run's table rather than PASS.
**Reversible:** yes — correcting or re-recording the demo closes it with zero product change.

## iter-11 — goal-evaluator

**Ambiguity:** Two of this iteration's three planned items (the UT-05 border fix, the
`TAPEOLOGY_BAR_INDEX_DB` scoping entry) were never built, so its own DEFINITION OF DONE is unmet
(TC-4/TC-5/TC-7/TC-8/TC-9/TC-10). My decision tree scores the ERA (journeys + anti-goals + coherence
+ drift), not an iteration's checklist; nothing states which wins when an iteration under-delivers
while the era's own bar is fully met.
**We chose:** the era's bar wins — GOAL_ACHIEVED. Neither unbuilt item is a Must-have journey
acceptance or an anti-goal: I read J-03's acceptance text verbatim in `docs/goal.md` and it names no
border colour (UT-05 is a test-designer P2 expectation, already ruled non-downgrading at iter-10),
and the iteration spec itself classifies the scoping entry as "a latent hazard, not a violation" — I
verified every scoped launcher (`qa_playbook_iter7_fixture_scoped_backend.sh:86`,
`qa_desk_iter5...:81`, `qa_playbook_iter6...:63`) already exports that var, that
`apps/backend/.data/bar_index.db` mtime is still 2026-08-10 07:58, and that the store-scope guard
reports all 9,841 protected files unchanged. Holding CONTINUE would spend another iteration on work
`docs/goal.md` never asks for — and this iteration just demonstrated the engine may not build it
anyway. Both items are carried into the halt justification so the owner can overrule cheaply.
**Reversible:** yes — `--resume` after a one-line owner instruction reopens the session.

## iter-12 — goal-decomposer

**Ambiguity:** The dispatch prompt names three carried, disclosed-not-fixed items (the UT-05
amber-border CSS collision, the `TAPEOLOGY_BAR_INDEX_DB` scoping-guard gap, and a false
`new`/`verified` claim plus nonexistent `role=tab` clicks in
`reports/phase-goal-playbook-iter-11-demo.json`) and asks the decomposer to decide whether any
belongs as a cheap passenger item in this iteration. `docs/goal.md` names none of the three — J-11
touches only the evidence fold — so nothing in the goal text says whether disclosed-but-unfixed
carried defects from a prior iteration belong inside the NEXT iteration's scope, or ride
indefinitely until a dedicated pass.
**We chose:** fold the first two in as cheap, isolated passengers (both are single-call-site or
single-tuple-entry fixes, one CSS class and one test-only guard string, with zero risk to J-11's
own diff), following this session's own iter-9 precedent for carrying small disclosed hygiene items
alongside a journey's own work. We excluded the third: correcting a historical showcase JSON file
is not source code and produces no journey/anti-goal effect — it is showcase-artifact bookkeeping,
out of a developer/reviewer's normal scope, so it is named in this iteration spec's NOTES as a
carried flag for whoever next regenerates or publishes the era's showcase materials, not built here.
**Reversible:** yes — both passenger fixes are isolated, single-file, low-blast-radius changes with
no schema, signature, or record effect; dropping either back to "carried, not fixed" costs nothing.

## iter-12 — goal-evaluator

**Ambiguity:** J-11's Acceptance requires a browser capture of "at least one cell whose
`n_unmeasured` is greater than zero beside its own `n`". The captured cell
(`open_high_break/long/1m`) shows `n_unmeasured: 15` beside `n: 0` — literally satisfying the
sentence, but the journey's own stated PURPOSE is that "a thin-looking `n` ... is legible as
'59 of 90 signals were unmeasurable there,' never mistaken for a small sample", whose paradigm case
is a NON-ZERO `n` beside a large `n_unmeasured` (`double_top:short@1m`, `n: 31` beside
`n_unmeasured: 59`). On the scoped fixture rig no visible row carries both `n > 0` and
`n_unmeasured > 0`; that pairing exists only on the operator's real corpus, where the developer
confirmed it over REST, not on screen.
**We chose:** J-11 `passing`. The acceptance sentence is the binding text and it is met literally
and visibly (both numbers rendered side by side in one row); the mechanism is proven identical for
every cell by TC-2 (`n + n_truncated + n_unmeasured` sums to the pool, and the mdd siblings share
one count) and by the browser lane's byte-for-byte cross-check of the rendered row against a direct
`curl` of the same endpoint. I did NOT quietly upgrade the demonstration either: the strongest
real-corpus pairing (31 beside 59) was verified over REST only, and that limit is recorded here and
in the eval rather than narrated as if it had been photographed.
**Reversible:** yes — one capture on the real corpus closes it with zero product change.

## iter-12 — goal-evaluator

**Ambiguity:** The amber-border passenger fix is present and scoped in source and pinned by a
source-scan guard test, but no browser row exercised it this run (UT-05 is absent from
`reports/phase-goal-playbook-iter-12-ui-test-results.md`). My rules bar GOAL_ACHIEVED while an
anti-goal is open and demand a screenshot for any BROWSER acceptance; nothing states how to score a
visual fix that is not any journey's acceptance line and not an anti-goal.
**We chose:** it does not gate GOAL_ACHIEVED, and it is not scored as verified either. `docs/goal.md`
never mentions a border colour (ruled non-downgrading at iter-10 and iter-11), so the fix-or-drop
item's completion is hygiene, not journey evidence. I read the source myself
(`page.tsx:5637`, `!border-amber-500`, Tailwind v3's important modifier — the correct mechanism for
this equal-specificity collision) and recorded it as fixed-in-source, unverified-on-screen, in
plain words. The symmetry rail from iter-11 is preserved: a green results table that never ran the
failing check is not evidence of a repair, in either direction.
**Reversible:** yes — one browser row re-added next pass closes it.
