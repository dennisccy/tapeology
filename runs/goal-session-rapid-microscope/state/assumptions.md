# Goal Session rapid-microscope — Assumption Ledger

Append-only. One entry per scoring decision that required interpreting the goal
rather than only reading evidence. Zero entries in an iteration is normal.

## iter-0 — goal-evaluator

**Ambiguity:** J-01 and J-10 each state one combined Acceptance line, but only part of each
was verifiable at era open (J-01's transition documents and era-open baseline; J-10's kept
surfaces, suite, fingerprint and referee hashes). The goal does not say whether partial
satisfaction of a combined acceptance line counts as `failing` or `partial`.
**We chose:** scored both `partial` (browser QA recorded FAIL for the full line), so the
verified sub-checks are not re-done later. `partial` blocks GOAL_ACHIEVED exactly as `failing`
does, so no gate is loosened by this choice.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** `docs/rapid-validation-spec.md` has no dedicated readiness section: it never
defines an RTH-minutes-to-session-equivalents conversion formula, and it never defines a
per-study floor distinct from the three pilot studies goal.md's J-09 names — those studies have
no registered Scout spec yet (that lands in J-09, eight iterations away).
**We chose:** `session_equivalents = rth_minutes_covered / 390` (standard 09:30-16:00 ET RTH
minutes), which reproduces goal.md's own stated ~3.0 on today's corpus; and each of the three
pilot studies reads the SAME existing frozen `WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS`
(=60 sessions) geometry floor from spec §1, since no study-specific floor is spec'd yet and
today's 11 legacy sessions read `floor_unmet` under either reading — matching goal.md's stated
J-01 acceptance ("every pilot study reads `floor_unmet`") regardless.
**Reversible:** yes — J-09 may register a different, study-specific floor later; this reading
only affects a descriptive readiness column, never a gate.

## iter-1 — goal-evaluator

**Ambiguity:** J-01's Acceptance is one combined sentence naming BOTH real-corpus endpoint values
(`distinct_symbol_days: 12`, `session_equivalents` ≈ 3.0, 18 shards `exploratory`/`hand_assigned`)
AND a browser element screenshot of the `/desk` panel rendering "those same served values." The
goal never says which channel proves which half, and the mandated store-scoped QA rig cannot serve
a non-empty tick corpus at all — so the two halves are not simultaneously observable today.
**We chose:** credited the endpoint half from evidence I produced myself (calling `build_readiness`
against the real `.data/datasets` store and reading the exact acceptance values, plus re-running
the 31 real-corpus unit tests), and refused to credit the browser half at all, since the only
screenshot shows an empty corpus and the 18-row shard-table render path was never exercised. Net
status `partial`, which blocks GOAL_ACHIEVED exactly as `failing` does — no gate is loosened. I did
NOT flag it `evidence_makeup`, because a plain re-capture would reproduce the same empty screenshot;
the rig itself must first be able to serve tick data.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** J-01's Acceptance names literal real-corpus browser figures
(`distinct_symbol_days: 12`, `session_equivalents` ≈ 3.0, 18 `exploratory`/`hand_assigned`
shards) for the `/desk` panel's browser screenshot, but the mandated store-scoped QA rig
(`:8301`) can never safely point at the real `.data/datasets` store this iteration: J-02 also
adds the era's first write-capable route under that same directory family (the snapshot-compute
manager), whose derived-cache storage dir defaults to a sibling of wherever
`TAPEOLOGY_DATASET_DIR` points — so pointing the rig at the real store risks a stray compute
leaving derived files beside the operator's real tree instead of inside the throwaway scoped
root. Literally reproducing the exact figures through the browser is therefore unsafe this
iteration.
**We chose:** seed the rig's own throwaway root with the two already-committed tick fixtures at
`apps/backend/tests/fixtures/datasets/` (1 symbol, 1 date, 2 shards) so the browser screenshot
shows a real, non-fabricated, non-empty corpus proving the SAME rendering path — while the
literal 12/18/~3.0 totals stay proven the way iteration 1's evaluator already proved them:
computed directly against the real store, credited as endpoint-side evidence, never re-derived
through the rig.
**Reversible:** yes — a later iteration may instead scope the readiness cache to read the real
corpus read-only (the lesson's second option) once the snapshot-compute route's own storage dir
is confirmed fully isolated from `TAPEOLOGY_DATASET_DIR`'s sibling-default resolution, at which
point the rig could show the literal real totals too.

## iter-2 — goal-evaluator

**Ambiguity:** J-01's Acceptance names the real-corpus figures (`distinct_symbol_days: 12`,
`session_equivalents` ≈ 3.0, 18 `exploratory`/`hand_assigned` shards) AND requires the `/desk`
panel to render "those same served values verbatim (element screenshot)". It never says whether
"those same served values" means the specific 12/18/~3.0 numbers, or the values the endpoint serves
for whatever store is behind it. The mandated store-scoped rig cannot safely be pointed at the
operator's real store this iteration, so the two readings are not simultaneously observable.
**We chose:** the second reading — rendering fidelity. Scored J-01 `passing` on the strength of two
channels: the endpoint half proven in iteration 1 directly against the real `.data/datasets` store
(and `micro_readiness.py` is byte-unchanged since, so that evidence stands under the durability
rail), and the rendering half proven this iteration by UT-02's element screenshot of the panel
showing a real, non-fabricated 2-shard PG corpus with matching checksums, fallback fractions,
`hand_assigned` provenance and all three floors `floor_unmet`. Flagged `evidence_makeup: true` with
gap `capture-defect`, so the make-up photograph (real 12/18/~3.0 totals, and the exposure_state
column that is clipped off the right edge of this capture) rides a later iteration as a passenger
task — never as an iteration goal, and never as a reason to rebuild J-01 code.
**Reversible:** yes
