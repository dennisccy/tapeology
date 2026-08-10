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
