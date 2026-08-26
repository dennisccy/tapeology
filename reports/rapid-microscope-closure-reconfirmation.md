# The Rapid Microscope — post-closure re-confirmation

**Branch** `goal/rapid-microscope` · **HEAD** `55510af0` · verification only.
No study run, no data touched, no ledger rewritten, no session state mutated.

---

## THE FINDING THAT GOVERNS THIS RECORD

**The Rapid Microscope era was already formally closed on 2026-08-24.** It was not left open.

```
e790d99a  goal(rapid-microscope): iter 33 — GOAL_ACHIEVED (passing+7 failing+0 regressed+0)
adb25d13  chore(goal): rapid-microscope finalization artifacts — GOAL_ACHIEVED
```

That is exactly the two-commit closure convention every prior completed era used. The closure was
produced by the real Goal Mode machinery, not by hand:

| Closure element | Evidence |
|---|---|
| Goal Mode session | `runs/goal-session-rapid-microscope/` |
| Terminal session state | `session.json`: `"status": "GOAL_ACHIEVED"`, `"last_verdict": "GOAL_ACHIEVED"`, `finished_at` 2026-08-24T23:39:33Z, 34 iterations, 22,357 s wall |
| Evaluator verdict | `iter-33/eval.md` → **`**Verdict:** GOAL_ACHIEVED`** |
| Two-key confirmation | `iter-33/eval-confirm.md` → **`**Verdict:** CONFIRM_ACHIEVED`** |
| Deterministic gates | `iter-33/gate-report.md`, `coherence.md`, `scan-report.md`, `journey-history.pre.json` |
| Finalization artifacts | `summary.md`, `telemetry.jsonl`, `trace/`, `journey-scripts/`, `state/` (13 files incl. `retro-input.md`, `project-story.md`, `lessons.md`, `proposer-result.json`) |
| Journeys at closure | 12 of 12 passing |

The second key was not a rubber stamp. `iter-33/eval-confirm.md` records an adversarial pass that
re-computed all twelve journey text fingerprints, opened the evidence screenshot itself, checked the
PnL history md5, and flagged two admitted gaps as *owed photographs of proven behaviour* rather than
capability gaps.

**Therefore no new closure was performed, and none should be.** Manufacturing a second
`GOAL_ACHIEVED` — by synthesizing an iteration-34 artifact set for an evaluator to re-render a
verdict it already gave — would fabricate exactly what a closure record exists to prevent. What
follows is verification that the standing closure still holds, which is the only honest work left.

## WHAT HAPPENED AFTER CLOSURE

Nine commits landed on the branch after `adb25d13`:

```
ea418c28  fix(micro): spec r13 — canonical return_bps outcome unit, separated side vocabularies
b54f83d9  fix(micro): r13 completion — sign applied once, units proved, legacy rows disclosed
e0136130  fix(micro): r13 contract pass — fail-closed boundaries, anchor unit provenance, direction freeze
2239a810  docs(micro): data-bottleneck preflight — read-only acquisition plan
3a9044aa  feat(micro): spec r14 — corpus lifecycle completed for the data bottleneck
6205d998  feat(micro): spec r14.1 — corpus identity + partial-pool OOS correctness
7245fbba  feat(micro): spec r14.2 — physical evidence may earn OOS credit exactly once
144f8d30  feat(micro): spec r14.3 — Study 2 decides on the Scout rail; the one real diagnostic ran
55510af0  docs(micro): Rapid Microscope closure audit + candidate-design owner memo
```

**r13 is the one that could plausibly have invalidated the closure**, and it deserves to be stated
plainly: a post-`GOAL_ACHIEVED` audit found that §4 defined the primary outcome as a mid-price
DIFFERENCE (dollars) while §5.5 gated it against a floor in basis points — so the economic-relevance
gate compared **dollars against basis points for the entire era**, on results the closure had already
certified.

That is a real defect found after a real closure. The question this document answers is whether the
closure survives it.

## DETERMINISTIC GATES — RE-RUN AT HEAD

| Gate | Command / source | Result |
|---|---|---|
| Journey drift since closure | `goal_gate.py hash-journeys docs/goal.md --history …/journey-history.json` | **`changed: []`** — all 12 journey texts byte-stable |
| Journeys passing | `goal_gate.py journeys …/journey-history.json` | **`{"total": 12, "passing": 12, "blocking": []}`**, exit 0 |
| Full backend suite | `pytest -p no:randomly` | **3,747 passed · 8 skipped · 0 failed**, exit 0 |
| Config fingerprint | `Config().config_fingerprint()` | **`08e471b10130e1e2`** — matches the era's frozen value |
| Referee isolation | SHA-256 of each `referee_*.py` vs `main` | **6 of 6 byte-identical** |

The only edit to `docs/goal.md` after closure is a **16-line additive preamble** recording r13. It
changes no journey, and says so in its own text: *"The era's journeys below are the record of what
was BUILT and are not rewritten; what r13 changes is the unit those journeys' numbers were always
meant to be in."* The `changed: []` gate result is the mechanical confirmation of that claim.

## THE r13 SUPERSESSION, VERIFIED IN THE DURABLE LEDGER

The r13 note makes a falsifiable promise: *"Every pre-r13 `killed_economic` decision is void as an
economic judgement and is superseded by a re-keyed r13 row beside it — old rows are never deleted and
never reinterpreted."*

Checked against the real Scout ledger, row by row:

| Rows | `econ_floor.unit` | Meaning |
|---|---|---|
| 0–11 | **`None`** | pre-r13 — a floor with no declared unit, exactly what r13 now refuses |
| 12–17 | **`bps`** | the r13 re-key: same six candidates, **new `candidate_id`s**, unit-checked floors |
| 18 | `bps` | the r14.3 Study 2 diagnostic |

Old rows are present and unaltered. New rows sit beside them under fresh candidate identities. The
arithmetic matches the audit: 6 pre-r13 + 6 re-keyed + 1 Study 2 = **13 distinct candidates**. The
promise was kept in durable state, not merely in prose.

## WHY THE POST-CLOSURE WORK DOES NOT REOPEN THE ERA

Three independent reasons, and the first is the load-bearing one:

**1. The journeys are what was certified, and they have not moved.** The closure certified twelve
journeys describing what the funnel *is able to do*. r13 corrected the unit those journeys' numbers
are expressed in; it did not remove a capability, weaken a gate, or invalidate a journey. The
fingerprint gate returning `changed: []` is the mechanical statement of that.

**2. No gate was weakened, and the record shows the opposite direction of travel.** r13 through r14.3
added refusals — unit provenance at every magnitude comparison, corpus-identity binding,
release-as-exposure precommit, one-dataset-per-registered-position, constructible-vs-sufficient fold
semantics, an unamendable Mode B predeclaration, and Study 2's decision moved onto the frozen Scout
rail. The suite grew 2,691 → 3,747. A closure is threatened by erosion, and there was none.

**3. The post-closure science consumed no certified evidence.** The vault was never opened (21 sealed,
0 assigned, 0 exposed), no `historical_oos` row was ever created, and the graduation ledger is still
empty. The one real diagnostic run (Study 2, r14.3) spent only already-exposed legacy tape and was
KILLED. Nothing the closure certified was traded away to produce it.

## STANDING VERDICT

# GOAL_ACHIEVED — standing, re-confirmed at HEAD

Not newly issued. The verdict is the evaluator's own from `iter-33/eval.md`, two-key confirmed in
`iter-33/eval-confirm.md`, and it survives the nine post-closure commits under every deterministic
gate above.

## ZERO SURVIVORS — THE RECORD

| | |
|---|---|
| Rapid Microscope infrastructure | **complete** — all ten scientific rails present and exercised |
| Real exploratory candidates evaluated | **13** across 4 families, 19 hash-chained ledger rows |
| Survivors | **0** |
| Study 2 (delta divergence at level tests) | **KILLED** — `killed_null`, effect +0.487 bps, p 0.366, econ floor 1.526 bps |
| Studies 1 and 3 | **intentionally deferred**, `PARKED_PENDING_OWNER_SPEC` — within the goal's binding allowance to defer up to two of three pilots |
| `historical_oos` candidates | **0** |
| Graduation | **0** — nothing left `exploratory` |
| Validation Vault | **untouched** — 21 sealed, 0 assigned, 0 exposed, single shots unspent |
| Expensive OOS acquisition | **none justified** — storage and retention remain dormant capabilities |

**This is not a failure to find profitability.** The project built an instrument that measures
historical candidate effects under a pre-registered methodology, pointed it at thirteen real
candidates, and recorded what it saw. Twelve were killed before r14.3; the thirteenth was killed by
it. The goal's own standard is met exactly as written:

> *"The era succeeds if it kills bad ideas honestly; it does NOT need to discover an edge."*
> *"Zero survivors is a passing grade."*

The distinction the closure standard demands — **honest kills versus an incapable funnel** — resolves
to *honest kills*: `sequence_verdict` reaches a real verdict on a dense fixture, `screen_candidate`
returns `survive` on fixtures, and Study 2 cleared all three of Scout's sufficiency floors on real
data (14 ≥ 5 candidate, 5,599 ≥ 5 comparator, 2 ≥ 2 usable sessions) before dying on the merits. The
machinery can say yes. It said no on this evidence.

## ARTIFACT STATE

**No session artifact was created, edited or regenerated by this task.** Every prior completed era
(`referee`, `clean_slate`, `desk`, `fast_wall`, `tradable_wall`, `playbook`) carries exactly the
standard entry set and nothing else, so there is no precedent for a post-closure artifact inside a
session directory — and hand-mutating a terminal session's state is precisely what would damage the
auditability this record exists to protect. `runs/goal-session-rapid-microscope/` is left byte-identical
to what the engine wrote.

`docs/goal.md` still holds The Rapid Microscope, unarchived. Archiving to `docs/goal-archive/` is the
established convention *when the next era is authored*, which is deliberately not this task.

## NEXT OWNER ACT

A new goal may now be authored separately. The Rapid Microscope record is closed, complete and
auditable; nothing in it is pending.
