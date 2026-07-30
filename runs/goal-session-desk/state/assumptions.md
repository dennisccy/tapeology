# Goal Session desk — Assumption Ledger

Append-only. An entry is added whenever scoring or planning required *interpreting*
`docs/goal.md` rather than just reading evidence. The human reviews these to catch
silent interpretation calls early.

## iter-17 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-13 Acceptance ends with a conjunct: "a **`[NEW]`-flagged
demo-narrator walkthrough** covers the briefing's price disclosure end to end", and the iteration
spec's DEFINITION OF DONE item 4 names `Demo Verdict: RECORDED`. The artifact that exists
(`reports/phase-goal-desk-iter-17-demo-results.md`, gallery `reports/demo/goal-desk-iter-17/`) IS a
demo-narrator walkthrough and IS `[NEW]`-flagged on its J-13 steps, but (i) its verdict reads
`RECORDED_WITH_NOTES` (three click timeouts plus one text expectation — all selector brittleness, not
product defects: UT-07 proves the row click-through works and UT-08 proves the skip section renders),
and (ii) it was recorded against the AMBIENT store at `:3301` BEFORE the audit's F1 fix, so all eight
frames show only the legacy state — and the pre-F1 legacy string at that, i.e. no band range and no
close anywhere in the film (I opened `step-03.png` and confirmed it). goal.md does not say whether a
walkthrough that narrates a real-but-unpopulated state "covers the disclosure end to end", nor
whether an incomplete showcase recording is a product gap or an evidence gap.

**We chose:** Score J-13 `passing` and record the walkthrough shortfall as a CAPTURE DEFECT
(`evidence_makeup: true`, methodology A.7) rather than an unmet acceptance conjunct — so it does not
downgrade the journey and does not block GOAL_ACHIEVED. Five strands, each checked by me directly:
(i) methodology A.7 names "the walkthrough recording is missing or badly cropped" and "a screenshot
showing a different-but-equally-valid data range than the spec's example numbers" as capture defects,
and its rail — "never applies when the asserted BEHAVIOR is unmet" — does not fire here, because the
film shows a state the product genuinely produced, not behaviour contradicting the claim; (ii) the
behaviour the film should have shown is proven three independent ways: `UT-05-result.png` (in-band
BRK-B and out-of-band LIN in ONE frame, scoped rig, `location.origin` asserted before capture), the
scoped snapshot on disk (63/63 ranked rows carry `reference_close`, 0/38 skip rows do, checksum
recomputes), and my own re-derivation of every row's value from the stored `1d` bars with ZERO
mismatches; (iii) the agent contract is explicit that an evidence/recording gap must "never [be]
scored as blocking" and must "never [be] a new iteration's goal" — it rides a make-up capture; (iv)
the in-session precedent one iteration back is identical in shape (iter-16 scored J-12 `passing` with
`evidence_makeup: true` for a framing shortfall and returned GOAL_ACHIEVED); (v) the independent
auditor, who rated this DoD item "NOT met", still recommended shipping and reached the same
product-vs-artifact split, as did the ux-regression reviewer.

**Reversible:** yes — one short re-filming run (`Depth: evidence` or a passenger task on whichever
lane next touches `/desk`) on a fixture-scoped rig with a freshly computed screen produces the
literal artifact, with zero program change; the flag clears on any fresh capture. If the owner reads
the conjunct strictly, J-13 returns to `partial` until that re-filming lands — and the practical
obstacle is now documented (two `next dev` processes from one source tree share `.next` and
cross-contaminate which backend the ambient page serves).

## iter-18 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-14 step 1 states the opposite-band selection rule twice in ways
that can be read against each other: "the nearest band on the side the row's own selected band is
NOT on ... The selection is deterministic and stated on the record: distance ascending, then class
rank descending (`_CLASS_RANK` ... an unclassified band ranks lowest, never highest), then
`band_score` descending, resolved by `min`'s first-of-tie stability over `compute_tradability`'s own
served order (the `_select_best_band` precedent)." The trailing parenthetical names the existing
helper whose key is CLASS-first, which is what shipped; the sentence's own ordering and the
journey's title ("the nearest wall on the OTHER side") say DISTANCE-first. goal.md does not say
which wins, and its Acceptance paragraph pins only byte-identity with some band in the canonical
list — a criterion the shipped rule satisfies.
**We chose:** Read DISTANCE-first as the requirement and score J-14 `partial`. Four strands, each
checked by me: (i) "nearest" appears three times (title, step 1's first clause, and the ordering
clause), while the `_select_best_band` reference is attached to TIE STABILITY, not to the key order;
(ii) J-14's own rationale in goal.md complains that class-first selection hides nearer bands
("nothing on the page says a nearer band on the other side exists"), so implementing the new column
with class-first reproduces the defect the journey exists to remove; (iii) I measured the divergence
against `compute_tradability` for all 63 ranked members of the owner's own screen at as_of
2026-07-29 — 2 rows differ (HONA 336.96 vs 153.67 bps; META 232.58 vs 92.05 bps), so this is a
user-visible behavioural difference, not a wording quibble; (iv) the shipped code's own docstring
(`desk_screen.py:89`) and frontend comment (`page.tsx:273`) both claim "the nearest band", so the
implementation is inconsistent with itself under either reading. The opposite call (score `passing`,
log an assumption) was available and would have closed the era; I judged that closing on a column
whose headline promise fails on 3% of real rows is the worse error in a project whose first rail is
honest measurement.
**Reversible:** yes — either direction is a small change. Distance-first is a one-key edit in
`_select_opposite_band` plus its goldens; grade-first can be ratified instead by editing goal.md's
J-14 wording and both "nearest" comments. Nothing recorded blocks either: the only snapshot carrying
these fields lives in a throwaway rig, and the owner's own store has none.

## iter-19 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-14 Acceptance ends with two capture conjuncts — "plus one
screenshot of a row tooltip carrying its `bands_by_class` line (T-10: no screenshot => `unknown`,
never `passing`)" and "a **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's
opposite-wall disclosure end to end, narrated over POPULATED ranked rows". Neither exists after this
run: the tooltip is a native HTML `title` attribute (`apps/frontend/app/desk/page.tsx:346`,
`deskRowDrillInTitle`), which the browser chrome paints outside CDP's screenshot surface, so
`J-14-tooltip-hover-attempt.png` (which I opened) shows no hint box at all; and the engine dispatched
this iteration `lean`, so the demo-narrator lane runs after the evaluator. goal.md does not say
whether an uncapturable artifact, or an artifact whose lane has not run yet, leaves the journey short
of its acceptance.
**We chose:** Score J-14 `passing` and record both as CAPTURE DEFECTS (`evidence_makeup: true`,
methodology A.7) rather than unmet acceptance conjuncts. Five strands, each checked by me directly:
(i) A.7 names "the walkthrough recording is missing or badly cropped" as a capture defect and its
rail — "never applies when the asserted BEHAVIOR is unmet" — does not fire, because the behaviour is
proven three independent ways (the near+far screenshot I opened, my own 100-row re-derivation from
the stored price files, and the golden/unit tests inside a green full suite); (ii) the tooltip's
CONTENT is proven without a photograph: `page.tsx:299-301` builds the exact
`bands by class A .. B .. C .. unclassified ..` string, the browser lane read that live `title`
attribute via DOM eval (`A 10 · B 0 · C 0 · unclassified 0` for BRK-B), and the recorded row's own
`bands_by_class` is `{"A":10,"B":0,"C":0,"unclassified":0}` — the same numbers; (iii) the photograph
is not obtainable by any lane in this rig, so treating it as blocking would loop the session forever
on an artifact that cannot exist — exactly the framework's #1 anti-pattern; (iv) my agent contract is
explicit that an evidence/recording gap must never be scored as blocking and never become an
iteration's goal; (v) the in-session precedents are identical in shape (iter-16 J-12 framing, iter-17
J-13 film — both scored `passing` with `evidence_makeup` and both confirmed by the second key).
**Reversible:** yes — the film clears on the finalization lane's own recording (or a `Depth: evidence`
run) with zero program change, and the flag clears on any fresh capture. The tooltip photograph is
NOT reversible in this rig; if the owner reads that conjunct literally, J-14 returns to `partial`
permanently unless the clause is reworded to "read out of the live DOM" or the product replaces the
native `title` with an on-page popover — a change no journey currently asks for.

## iter-19 — goal-evaluator

**Ambiguity:** This iteration's own spec NOTES say "Never write a screen/universe snapshot into
`apps/backend/.data`", and its BACKGROUND repeats the scoped-rig lesson. The evidence lanes did the
opposite: the ambient store gained a real price top-up run (`topup-2026-07-29-5de907c83fc4.json`,
12:00:29Z–12:04:53Z, 404 of 404 pairs attempted, 390 new bar-series files) and FOUR new screen
snapshots (13:06/13:15/13:22/13:24 local), and the browser lane's own report discloses it ("Data rig:
the running ambient rig (`apps/backend/.data`)"). `docs/goal.md` itself requires only that every run
be an "explicit operator act", that snapshots be append-only and pinned, that recording/fetching be
"an explicit, logged act", and that live top-ups be "operator-run verifications reported honestly".
It does not say whether an agent-triggered POST against the owner's own store is such an act, nor
whether breaching an ITERATION plan is an anti-goal violation.
**We chose:** Record it as a disclosed process deviation (a breach of this iteration's own plan) and
NOT as a `docs/goal.md` anti-goal violation, so it does not drive REGRESSION — the same call this
session made at iters 9, 14 and 15, now with a larger footprint. Verified by me directly, not
assumed: (i) the 369 bar-series files that existed before today are untouched (`find … ! -newermt`
count 369, and every file written today has creation time equal to its modification time, i.e. new
series never rewritten); (ii) no snapshot was rewritten — all ten stored screens recompute their
stored `file_checksum`, the six pre-iteration ones still carry `opposite_band` on 0 rows, and each
new screen is a NEW file under a new bar-store signature, so the identical-pin refusal was respected
rather than worked around; (iii) the fetch was explicit and logged, which is exactly what the
"persistence stays scoped" rail demands — an honest record naming all 404 attempted pairs including
verbatim failure text; (iv) no scheduler, cron, or page-load GET triggered any of it (the run carries
compute-manager start/finish stamps); (v) the evidence is if anything STRONGER for having been taken
against the real store — my own 100-row re-derivation ran against those same real files, and the
divergent HONA row exists only in real data. The effect on the owner is real and disclosed in the
verdict: their Desk now ranks 100 names instead of 63.
**Reversible:** no — the appended run record, the four screens and the 390 fetched series are
permanent by design (deleting them would itself breach the append-only rail). If the owner reads
"explicit operator act" as "the human, not an agent", the remedy is a rail that forces every evidence
lane to point at a copy of the data (and a check that the SERVING process actually has it), not an
undo of these files.

## iter-20 — goal-evaluator

**Ambiguity:** `docs/goal.md` makes a `[NEW]`-flagged demo-narrator walkthrough an acceptance
conjunct of J-13 and J-14, and my own agent contract says an evidence/recording gap must "never [be]
scored as blocking" and must never become an iteration's goal. Iteration 20 WAS such an iteration (it
was dispatched `Depth: evidence` on the prior evaluator's own recommendation) and its recording lane
produced nothing (`Demo Verdict: SKIPPED`, empty gallery). goal.md does not say whether a missing
walkthrough leaves a journey short of acceptance, and the framework's two rails point opposite ways.
**We chose:** Split the two questions rather than answer them with one status. (i) The JOURNEY status
stays `passing` for J-13 and J-14 with `evidence_makeup: true` — methodology A.7, since the asserted
behaviour is proven (I opened the fresh screenshot and re-derived all its numbers from the recorded
snapshot on disk, 5 sampled rows byte-identical, 100/100 rows carrying the new fields), and only the
artifact is missing; the same call iters 17/18/19 made. (ii) The VERDICT is nonetheless `CONTINUE`,
not `GOAL_ACHIEVED`, because iteration 19's independent second key
(`runs/goal-session-desk/iter-19/eval-confirm.md`) already refused the finish citing this exact
missing recording, so a first key asserting achievement would be knowingly contradicted rather than
merely optimistic — and because a machine-doable next step exists (fix the malformed demo script and
re-record), which is what `Depth: evidence` is for. I did NOT return STALLED even though one
remaining conjunct (J-14's tooltip PHOTOGRAPH) is genuinely human-owned, because productive
non-human work remains; the owner decision is raised explicitly in the recommendation instead.
**Reversible:** yes — one valid demo script and one recording run close (i)'s flags on J-13 and J-14
with zero program change. The tooltip photograph is NOT reversible in this rig: if the owner reads
that clause literally, J-14 stays short of acceptance permanently unless the clause is reworded to
"read out of the live DOM" or the native `title` is replaced by an on-page panel.

## iter-21 — goal-decomposer

**Ambiguity:** Iteration 20's own next-step recommendation asked to "express the sideways reveal of
the two right-hand columns as a sideways scroll of the table rather than a click on a button that does
not exist." Reading `scripts/automation/lib/demo_runner.py` directly shows its action vocabulary is
exactly `{"goto", "click", "fill", "expect", "wait_for"}` (`:36`) — no scroll primitive exists, and
adding one would be a tooling code change, which `Depth: evidence` explicitly does not carry (it
"dispatches capture + evaluation only, skipping developer and reviewer"). Separately, every ranked row
(`apps/frontend/app/desk/page.tsx:335-427`) is one stretched `next/link` anchor covering the whole row,
so a `click` on the `band`/`opposite` cells navigates to `/structure` rather than scrolling anything.
`docs/goal.md`'s J-14 acceptance already requires, and prior iterations already captured, a literal
screenshot with both a near and a far opposite wall legible in one frame (a browser-QA deliverable,
separate from the demo-narrator walkthrough); its walkthrough conjunct only says the film must "cover…
end to end, narrated over POPULATED ranked rows" — it does not restate the screenshot's own
legibility/single-frame requirement for the walkthrough's own frames.
**We chose:** Direct this iteration's demo script to narrate the `band`/`opposite` disclosures via
accurate `narration`/`point_out` text plus `expect` text assertions over the populated screen, and to
NOT attempt any click-driven reveal of those columns (since every available click target inside the
ranked table navigates away and no scroll action exists) — treating the walkthrough's "end to end,
narrated over populated rows" clause as satisfied by correct narration over a populated recording, with
the separate pixel-legibility requirement resting on the already-existing browser-QA screenshots. If a
future record run's natural (unscrolled) capture happens to show the columns anyway, that is a bonus,
not a requirement.
**Reversible:** yes — if the owner reads the walkthrough conjunct as also requiring the two rightmost
columns visually legible inside the demo gallery's own frames specifically, the remedy is a small,
explicit `demo_runner.py` enhancement (a `scroll` action type driving `element.evaluate("el =>
el.scrollLeft = el.scrollWidth")` on the `overflow-x-auto` container, never a click) — a lean-depth
tooling change, not a rewording of goal.md, and nothing recorded this iteration would need to be
redone.

## iter-21 — goal-evaluator

**Ambiguity:** `docs/goal.md` makes a `[NEW]`-flagged demo-narrator walkthrough an acceptance
conjunct of J-13 ("covers the briefing's price disclosure end to end") and J-14 ("covers the
briefing's opposite-wall disclosure end to end, narrated over POPULATED ranked rows"). The film
recorded this iteration satisfies that text only if "covers … end to end" is read as ACCURATE
NARRATION over a populated recording: `Demo Verdict: RECORDED`, both new steps `[NEW]`-flagged and
tagged J-13/J-14, but its three frames are one byte-identical image (md5 `3b02db86…`) in which the
`band` column is truncated at the frame's right edge and the `opposite` column is off-frame entirely
(both sit past the ranked table's `overflow-x-auto` clientWidth; `demo_runner.py` has no scroll
action and every in-row click navigates to `/structure`). goal.md does not say whether the
walkthrough's OWN frames must display the columns it narrates.
**We chose:** Read the conjunct as satisfied — narration over populated rows, with the pixel
legibility resting on the separate screenshot conjunct — and clear J-13's `evidence_makeup`, while
recording the frame shortfall openly in the verdict rather than as an unmet clause. Four strands,
each checked by me directly: (i) I re-derived every number the narration quotes from the recorded
snapshot on disk (`screen-2026-07-20-ca185294a384.json`, stored `file_checksum` recomputes) — BRK-B
band `488.5`–`490.9100036621094` close `490.9100036621094`, LMT `508.78920085992235`–`512.3115234375`
close `508.7699890136719`, BRK-B opposite resistance A `490.9700012207031`–`494.3949890136719` at
`1.2221702174772953` bps, DIS at `1128.2895954803862` bps — zero mismatches, so the film misstates
nothing; (ii) the frame I opened does show the populated recording, its provenance block and the
`band` column's own range, i.e. it is genuinely over populated rows; (iii) both columns ARE legible
in one frame in this same iteration's separate browser-QA captures (`UT-J-13-result.png`,
`UT-J-14-result.png`), which is where goal.md puts that requirement; (iv) methodology A.7 names a
badly-cropped recording a capture defect, and its rail ("never applies when the asserted BEHAVIOR is
unmet") does not fire. The decomposer logged the same call before authoring the script
(`assumptions.md` iter-21 — goal-decomposer). Note this assumption does NOT change my verdict: the
halt rests on J-14's tooltip photograph, not on the film.
**Reversible:** yes — a small `demo_runner.py` `scroll` action (`el.scrollLeft = el.scrollWidth` on
the `overflow-x-auto` container, never a click) plus one re-record makes the columns visible inside
the film's own frames; that is a lean-depth tooling change with zero product change, and nothing
recorded this iteration would need to be redone.

## iter-22 — goal-evaluator

**Ambiguity:** The entire GOAL_ACHIEVED verdict rests on a `docs/goal.md` edit I did not witness being
made. The file gained **T-10a** ("OWNER RATIFICATION, 2026-07-30") plus a J-14 acceptance clause
naming `project-extensions/qa-rig/`, and the rig itself appeared as three new files. Both are
UNCOMMITTED working-tree changes, and `docs/goal.md`'s own anti-goals say the enhancement loop "MUST
NOT edit human-authored journeys, this Anti-goals section, or any other part of this file" — T-10a sits
OUTSIDE the `AUTO:journeys` marker block, so if an in-loop agent wrote it, that would itself be a
critical violation rather than a ratification. Nothing in the repository records authorship.
**We chose:** Treat the edit as the owner's own ratification and score J-14 against the new text.
Four strands, each checked by me directly: (i) timing — `docs/goal.md` was modified at 08:26:18 and
the rig files at 08:22–08:26, i.e. AFTER iteration 21's halt (`iter-21/eval.md` 00:17) and BEFORE this
iteration's snapshot (`iter-22/snapshot-sha` 08:48), a window in which `session.json` recorded
`status: STALLED` and no pipeline lane — proposer included — was dispatched; (ii) direction — the edit
STRENGTHENS the bar it touches: the screenshot requirement is restated as standing "unchanged", T-10's
"no screenshot ⇒ `unknown`" is preserved verbatim, a DOM read-out is explicitly demoted to "NOT the
artifact", and three new obligations are added (named rig, `--require-title` guard, quote the reported
`title` and attach BOTH frame and crop) — the opposite of what a loop-preserving agent edit would look
like; (iii) content — it answers exactly option (3) of iteration 21's four-way question to the owner
("approve a desktop-capture set-up"), with a variant that never touches the real desktop; (iv) the
artifact it authorizes is self-validating, so crediting it cannot launder a false pass: the rig writes
nothing unless a new X window appeared AND the hovered element's own `title` carries the substring, its
refusal path was re-tested live this run (exit 4, no file), and I confirmed in the frame that the
tooltip overlaps the bare desktop outside the browser window.
**Reversible:** yes — if the edit turns out not to be yours, the remedy is to revert those goal.md
lines and the verdict returns to iteration 21's `STALLED` state with the same four options open;
nothing in the product changed this run (zero diff under `apps/`), so no code would need undoing, and
the photograph itself stays valid evidence of what the page renders either way.
